import asyncio
import contextlib
import logging
import sys
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, Union

import websockets

from hanapy.contrib.hanabi_live.actions import HLAction, action_to_command_data
from hanapy.contrib.hanabi_live.models import (
    CommandData,
    GameActionListMessage,
    GameActionMessage,
    HLModel,
    InitMessage,
    TableMessage,
    TableStartMessage,
    UserMessage,
)
from hanapy.contrib.hanabi_live.state import HLGameState
from hanapy.contrib.hanabi_live.ws_client import Msg, create_table, get_access_token, join_table, table_start
from hanapy.core.config import GameConfig
from hanapy.players.console.player import ConsolePlayerActor
from hanapy.runtime.asyncio import get_event_loop
from hanapy.runtime.buffers import BufferingHanapyClient, EventWaitAborted
from hanapy.runtime.events import (
    ActionEvent,
    Event,
    GameStartedEvent,
    MemoInitEvent,
    PlayerRegisteredEvent,
    RegisterPlayerEvent,
    SetPlayersOrderEvent,
    StartGameEvent,
    WaitForActionEvent,
)
from hanapy.runtime.players import ClientPlayerProxy
from hanapy.types import EventHandlers
from hanapy.utils.log import init_logger
from hanapy.utils.ser import dumps, loads
from hanapy.variants.classic import ClassicGame, get_hand_size

logger = logging.getLogger(__name__)

_MessageHandler = Callable[[str, Union[Msg, HLModel]], Awaitable[Any]]

_handlers: Dict[Union[str, Type[Event]], List[Tuple[Callable, Optional[Type]]]] = defaultdict(list)


def on(*message_types: Union[str, Type[Event]], model: Optional[Type] = None):
    def dec(f):
        for message_type in message_types:
            _handlers[message_type].append((f, model))
        return f

    return dec


class HLHanapyAdapter:
    def __init__(self, client: "HLClient", is_host: bool, pid: str):
        self.client = client
        self.is_host = is_host
        self._table_id: Optional[int] = None
        self.tables: List[TableMessage] = []
        self.players: List[str] = []
        self.started = False
        self.game_state = HLGameState(name=pid)
        self.pid = pid

    @property
    def table_id(self):
        if self._table_id is None:
            raise ValueError("Table not joined")
        return self._table_id

    async def on_message(self, message_type: str, data: Msg):
        if message_type in _handlers:
            for handler, model in list(_handlers[message_type]):
                if model is not None:
                    data = loads(model, data)
                await handler(self, message_type, data)
            return
        raise NotImplementedError(message_type)

    async def on_event(self, event: Event):
        processed = False
        for event_type, handlers in list(_handlers.items()):
            if isinstance(event_type, str):
                continue
            if isinstance(event, event_type):
                for handler, _ in handlers:
                    await handler(self, event)
                    processed = True
        if not processed:
            raise NotImplementedError(event.__class__.__name__)

    @on(
        "welcome",
        "userList",
        "chatList",
        "chat",
        "gameHistory",
        "pregameSpectators",
        "userInactive",
        "soundLobby",
        "chatTyping",
        "voteChange",
        "spectators",
        "clock",
        "noteListPlayer",
    )
    async def skip(self, message_type: str, data):
        # logger.info("user %s", data)
        pass

    @on("tableList", model=List[TableMessage])
    async def on_table_list(self, _, data: List[TableMessage]):
        self.tables = data

    @on("tableGone", model=TableMessage)
    async def on_table_gone(self, _, data: TableMessage):
        if data.id == self._table_id:
            self._table_id = None

    @on("warning", "game", "joined", "userLeft", "init", "connected", "gameActionList")
    async def log(self, message_type: str, data):
        logger.info("%s %s", message_type, data)

    @on("user", model=UserMessage)
    async def on_user(self, message_type: str, data: UserMessage):
        if data.status != 1:
            return
        if data.tableID != self._table_id:
            return
        pid = data.name
        assert pid is not None
        self.players.append(pid)
        await self.client.receive_event(PlayerRegisteredEvent(pid=pid, player_num=-1, players=self.players))

    @on(RegisterPlayerEvent)
    async def register_player(self, event: RegisterPlayerEvent):
        if self._table_id is not None:
            return
        while len(self.tables) == 0:
            await asyncio.sleep(1)
        await self.leave_all_tables()
        self._table_id = self.tables[-1].id
        async with self.wait_for_message("table", self.log):
            await join_table(self.client.send_message, self.table_id)

    @on(StartGameEvent)
    async def on_start_game(self, _: StartGameEvent):
        if not self.is_host:
            return
        await table_start(self.client.send_message, self.table_id, self.players)

    @on(MemoInitEvent)
    async def on_memo_init(self, event: MemoInitEvent):
        self.game_state.player_view.memo = event.memo

    @on(ActionEvent)
    async def on_action_event(self, event: ActionEvent):
        await self.client.send_message("action", action_to_command_data(event.action, self.table_id))

    @contextlib.asynccontextmanager
    async def wait_for_message(self, message_type: str, handler: Callable, model: Optional[Type] = None):
        done = asyncio.Event()

        async def _handler(_, mt: str, data: Msg):
            await handler(mt, data)
            done.set()

        try:
            _handlers[message_type].append((_handler, model))
            yield
            logger.info(f"waiting for {message_type}")
            await done.wait()
        finally:
            _handlers[message_type].remove((_handler, model))

    async def on_table_created(self, _: str, data: TableMessage):
        self._table_id = data.id
        logger.info("created table id: %s", self._table_id)

    async def create_table(self, table_name: str):
        await self.leave_all_tables()
        async with self.wait_for_message("table", self.on_table_created, TableMessage):
            await create_table(self.client.send_message, table_name)

    async def leave_all_tables(self):
        for t in self.tables:
            if t.players is not None and self.client.username in t.players:
                if t.owned:
                    await self.client.send_message("tableTerminate", CommandData(tableID=t.id))
                await self.client.send_message("tableLeave", CommandData(tableID=t.id))

    async def parse_actions_list(self, _, data: GameActionListMessage):
        assert data.list is not None
        for action in data.list:
            self.game_state.apply_action(HLAction.from_action_data(action))

    @on("gameAction", model=GameActionMessage)
    async def on_action(self, _, data: GameActionMessage):
        assert isinstance(data.action, dict)
        self.game_state.apply_action(HLAction.from_action_data(data.action))

    async def parse_init(self, _, data: InitMessage):
        assert data.ourPlayerIndex is not None
        self.game_state.set_player_num(data.ourPlayerIndex)
        assert data.options is not None
        if data.options.variantID != 0:
            raise NotImplementedError("Other variants are not supported")
        assert data.playerNames is not None
        player_count = len(data.playerNames)
        card_config = ClassicGame.get_card_config(...)  # type: ignore[arg-type]
        config = GameConfig(
            max_lives=3,
            hand_size=get_hand_size(player_count),
            player_count=player_count,
            max_clues=8,
            cards=card_config,
        )
        self.game_state.set_config(config, card_config.total_cards)
        await self.client.receive_event(
            SetPlayersOrderEvent(pid=self.pid, player_index=data.ourPlayerIndex, players=data.playerNames)
        )
        self.game_state.init_player_view()

    @on("tableStart", model=TableStartMessage)
    async def on_table_start(self, _, data: TableStartMessage):
        if self.started or data.tableID != self._table_id:
            return
        logger.info("table started")
        self.started = True
        # await asyncio.sleep(1.)
        async with self.wait_for_message("init", self.parse_init, InitMessage):
            await self.client.send_message("getGameInfo1", TableIDModel(tableID=self._table_id))
        async with self.wait_for_message("gameActionList", self.parse_actions_list, GameActionListMessage):
            await self.client.send_message("getGameInfo2", TableIDModel(tableID=self._table_id))
        await self.client.send_message("loaded", TableIDModel(tableID=self.table_id))
        await self.client.receive_event(GameStartedEvent(pid=self.pid, view=self.game_state.get_player_view()))
        if self.game_state.player_num == 0:
            await self.client.receive_event(WaitForActionEvent(pid=self.pid, view=self.game_state.player_view))


class TableIDModel(HLModel):
    tableID: Optional[int] = None


class HLClient(BufferingHanapyClient):
    def __init__(
        self,
        username: str,
        password: str,
        address: str,
        is_host: bool,
        ssl: bool = False,
        event_handlers: Optional[EventHandlers] = None,
    ):
        super().__init__(event_handlers=event_handlers)
        self.address = address
        self.username = username
        self.password = password
        self._websocket = None
        self.ssl = ssl
        self.listening = True
        self.adapter = HLHanapyAdapter(self, is_host, username)

    @property
    def websocket(self):
        if self._websocket is None:
            raise ValueError("Websocket is not connected")
        return self._websocket

    async def send_message(self, message_type: str, data: HLModel):
        payload = dumps(data).decode("utf8")
        logger.info(f"sending {message_type} {payload}")
        await self.websocket.send(f"{message_type} {payload}")

    async def send_event(self, event: Event):
        await self.adapter.on_event(event)

    async def run_loop(self):
        logger.debug("logging in...")
        token = get_access_token(self.username, self.password, self.address, self.ssl)
        logger.debug("authentication ok")
        schema = "wss" if self.ssl else "ws"
        uri = f"{schema}://{self.address}/ws"
        logger.debug(f"connecting to websocket url {uri}")

        async def listen_for_events():
            async with websockets.connect(
                uri, extra_headers={"Cookie": f"hanabi.sid={token}"}, timeout=10
            ) as websocket:
                self._websocket = websocket
                logger.info("connection established")
                async for message in websocket:
                    message_type, json_data = message.split(" ", 1)
                    logger.info(f"got {message_type}")
                    get_event_loop().create_task(self.adapter.on_message(message_type, json_data))
            logger.error("Socket disconnected")

        get_event_loop().create_task(listen_for_events())

    async def connect2(self):
        logger.debug("[client] creating connection")
        await self.run_loop()
        while self._websocket is None:
            await asyncio.sleep(1)
            logger.debug("[client] waiting for connection")

    async def connect(self):
        if self._websocket is None:
            await self.connect2()

    async def is_running(self) -> bool:
        return self.listening


async def run_client(
    username: str, password: str, address: str, is_host: bool, auto_start_players: Optional[int] = None
):
    player = ConsolePlayerActor(username)

    client = HLClient(username, password, address, is_host)

    client.add_event_handlers(player.get_event_handlers())

    if is_host:
        await client.connect2()
        await client.adapter.create_table(f"{username}s table")

    player_proxy = ClientPlayerProxy(username, client, player)

    try:
        await player_proxy.run(is_host=is_host, auto_start_players=auto_start_players)
    except EventWaitAborted:
        print("exiting")


async def main():
    if len(sys.argv) != 3:
        print(f"usage: python {__file__} name is_host")
        return
    name, is_host = sys.argv[1:]
    await init_logger(logging.DEBUG)
    await run_client(
        username=name,
        password="123",  # noqa: S106
        address="127.0.0.1:9000",
        is_host=is_host == "1",
        auto_start_players=2,
    )


if __name__ == "__main__":
    asyncio.run(main())
