import asyncio
import contextlib
import json
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, Union

import websockets

from hanapy.contrib.hanabi_live.models import HLModel
from hanapy.contrib.hanabi_live.ws_client import Msg, create_table, get_access_token
from hanapy.players.console.player import ConsolePlayerActor
from hanapy.runtime.asyncio import get_event_loop
from hanapy.runtime.buffers import BufferingHanapyClient, EventWaitAborted
from hanapy.runtime.events import Event, RegisterPlayerEvent
from hanapy.runtime.players import ClientPlayerProxy
from hanapy.types import EventHandlers
from hanapy.utils.log import init_logger
from hanapy.utils.ser import dumps

logger = logging.getLogger(__name__)

_MessageHandler = Callable[[str, Msg], Awaitable[Any]]

_handlers: Dict[Union[str, Type[Event]], List[Callable]] = defaultdict(list)


def on(*message_types: Union[str, Type[Event]]):
    def dec(f):
        for message_type in message_types:
            _handlers[message_type].append(f)
        return f

    return dec


class HLHanapyAdapter:
    def __init__(self, client: "HLClient"):
        self.client = client
        self._table_id: Optional[int] = None

    async def on_message(self, message_type: str, data: Msg):
        if message_type in _handlers:
            for handler in _handlers[message_type]:
                await handler(self, message_type, data)
            return
        print(_handlers)
        raise NotImplementedError(message_type)

    async def on_event(self, event: Event):
        processed = False
        for event_type, handlers in _handlers.items():
            if isinstance(event_type, str):
                continue
            if isinstance(event, event_type):
                for handler in handlers:
                    await handler(self, event)
                    processed = True
        if not processed:
            raise NotImplementedError(event.__class__.__name__)

    @on("user", "welcome", "userList", "tableList", "chatList", "chat", "gameHistory", "pregameSpectators")
    async def skip(self, message_type: str, data):
        # logger.info("user %s", data)
        pass

    @on("warning", "game", "joined")
    async def log(self, message_type: str, data):
        logger.info("%s %s", message_type, data)

    @on(RegisterPlayerEvent)
    async def register_player(self, event: RegisterPlayerEvent):
        logger.info(event.to_dict())

    @contextlib.asynccontextmanager
    async def wait_for_message(self, message_type: str, handler: _MessageHandler):
        done = asyncio.Event()

        async def _handler(_, message_type: str, data: Msg):
            await handler(message_type, data)
            done.set()

        try:
            _handlers[message_type].append(_handler)
            yield
            await done.wait()
        finally:
            _handlers[message_type].remove(_handler)

    async def on_table_created(self, message_type: str, data: Msg):
        self._table_id = data.get("id")

    async def create_table(self, table_name: str):
        async with self.wait_for_message("table", self.on_table_created):
            await create_table(self.client.send_message, table_name)


class HLClient(BufferingHanapyClient):
    def __init__(
        self,
        username: str,
        password: str,
        address: str,
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
        self.adapter = HLHanapyAdapter(self)

    @property
    def websocket(self):
        if self._websocket is None:
            raise ValueError("Websocket is not connected")
        return self._websocket

    async def send_message(self, message_type: str, data: HLModel):
        payload = dumps(data).decode("utf8")
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
            async with websockets.connect(uri, extra_headers={"Cookie": f"hanabi.sid={token}"}) as websocket:
                self._websocket = websocket
                logger.info("connection established")
                async for message in websocket:
                    message_type, json_data = message.split(" ", 1)

                    await self.adapter.on_message(message_type, json.loads(json_data))

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

    client = HLClient(username, password, address)

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
    await init_logger(logging.INFO)
    await run_client(username="kek1", password="123", address="127.0.0.1:9000", is_host=True, auto_start_players=2)  # noqa: S106


if __name__ == "__main__":
    asyncio.run(main())
