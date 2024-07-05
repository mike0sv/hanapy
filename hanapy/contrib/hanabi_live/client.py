import asyncio
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Type, Union

import websockets

from hanapy.contrib.hanabi_live.ws_client import Msg, get_access_token
from hanapy.players.console.player import ConsolePlayerActor
from hanapy.runtime.asyncio import get_event_loop
from hanapy.runtime.buffers import BufferingHanapyClient, EventWaitAborted
from hanapy.runtime.events import Event, RegisterPlayerEvent
from hanapy.runtime.players import ClientPlayerProxy
from hanapy.types import EventHandlers
from hanapy.utils.log import init_logger

logger = logging.getLogger(__name__)

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

    async def on_message(self, message_type: str, data: Msg):
        if message_type in _handlers:
            for handler in _handlers[message_type]:
                await handler(self, message_type, data)
            return
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

    @on("user", "welcome", "userList", "tableList", "chatList", "chat", "gameHistory")
    async def skip(self, message_type: str, data):
        # logger.info("user %s", data)
        pass

    @on(RegisterPlayerEvent)
    async def register_player(self, event: RegisterPlayerEvent):
        logger.info(event.to_dict())


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

                    await self.adapter.on_message(message_type, json_data)

        get_event_loop().create_task(listen_for_events())

    async def connect(self):
        logger.debug("[client] creating connection")
        await self.run_loop()
        while self._websocket is None:
            await asyncio.sleep(1)
            logger.debug("[client] waiting for connection")

    async def is_running(self) -> bool:
        return self.listening


async def run_client(username: str, password: str, address: str):
    player = ConsolePlayerActor(username)

    client = HLClient(username, password, address)
    client.add_event_handlers(player.get_event_handlers())
    player_proxy = ClientPlayerProxy(username, client, player)

    try:
        await player_proxy.run(is_host=False, auto_start_players=None)
    except EventWaitAborted:
        print("exiting")


async def main():
    await init_logger(logging.INFO)
    await run_client(username="kek1", password="123", address="127.0.0.1:9000")  # noqa: S106


if __name__ == "__main__":
    asyncio.run(main())
