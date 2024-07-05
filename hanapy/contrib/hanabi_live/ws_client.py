import asyncio
import json
import logging
from typing import Callable, List, Optional, Tuple, Type

import requests.utils
import websockets

from hanapy.contrib.hanabi_live.models import HLModel
from hanapy.utils.log import init_logger
from hanapy.utils.ser import dumps, loads

logger = logging.getLogger(__name__)


def get_access_token(username, password, server_address, ssl):
    schema = "https" if ssl else "http"
    url = f"{schema}://{server_address}/login"
    data = {"username": username, "password": password, "version": "6387"}
    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()
    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    return cookies.get("hanabi.sid", None)


async def on_message_print(message_type: str, data: dict, send: Callable):
    logger.debug(f"< {message_type} {json.dumps(data, indent=2)}")
    await send("222", {"pong": 222})


class WsClient:
    def __init__(self, username: str, password: str, address: str, on_message: Callable, ssl: bool = False):
        self.address = address
        self.username = username
        self.password = password
        self.websocket = None
        self.ssl = ssl
        self.on_message = on_message

    async def send(self, message_type: str, data: HLModel):
        if self.websocket is None:
            raise ValueError("WS is not connected")
        await self.websocket.send(f"{message_type} {dumps(data)}")

    async def start(self):
        logger.debug("logging in...")
        token = get_access_token(self.username, self.password, self.address, self.ssl)
        logger.debug("authentication ok")
        schema = "wss" if self.ssl else "ws"
        uri = f"{schema}://{self.address}/ws"
        logger.debug(f"connecting to websocket url {uri}")
        async with websockets.connect(uri, extra_headers={"Cookie": f"hanabi.sid={token}"}) as websocket:
            self.websocket = websocket
            logger.info("connection established")
            async for message in websocket:
                index = message.find(" ")
                type_part = message[:index]
                json_part = message[index + 1 :]
                json_data = json.loads(json_part)
                await self.on_message(type_part, json_data, self.send)


class MessageHandler:
    def __init__(self, handlers: List[Tuple[Optional[str], Optional[Type[HLModel]], Callable]]):
        self.handlers = handlers

    async def on_message(self, message_type: str, data: dict, send: Callable):
        for type_, model, callback in self.handlers:
            if type_ is not None and message_type != type_:
                continue
            msg = loads(model, data) if model is not None else data
            await callback(message_type, msg, send)


async def main():
    await init_logger(logging.DEBUG)
    msg_handler = MessageHandler(
        handlers=[
            (None, None, on_message_print),
        ]
    )
    client = WsClient(username="kek1", password="123", address="127.0.0.1:9000", on_message=msg_handler.on_message)  # noqa: S106
    await client.start()


if __name__ == "__main__":
    asyncio.run(main())
