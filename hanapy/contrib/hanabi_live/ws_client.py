import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, List, Optional, Tuple, Type

import requests.utils
import websockets

from hanapy.contrib.hanabi_live.models import CommandData, GameActionListMessage, HLModel, Options, TableMessage
from hanapy.utils.log import init_logger
from hanapy.utils.ser import dumps, loads

logger = logging.getLogger(__name__)

Msg = dict  # Union[list, dict, HLModel]
Send = Callable[[str, HLModel], Awaitable[Any]]


def get_access_token(username, password, server_address, ssl):
    schema = "https" if ssl else "http"
    url = f"{schema}://{server_address}/login"
    data = {"username": username, "password": password, "version": "6387"}
    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()
    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    return cookies.get("hanabi.sid", None)


async def on_message_print(message_type: str, data: Msg, send: Callable):
    logger.info(f"< {message_type} {data}")


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

        payload = dumps(data).decode("utf8")
        logger.info(f"> {message_type} {payload}")
        await self.websocket.send(f"{message_type} {payload}")

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

    async def on_message(self, message_type: str, data: Msg, send: Callable):
        for type_, model, callback in self.handlers:
            if type_ is not None and message_type != type_:
                continue
            msg = loads(model, data) if model is not None else data
            await callback(message_type, msg, send)


async def on_table_list(message_type: str, data: Msg, send: Send):
    assert isinstance(data, list)
    if len(data) > 0:
        return

    await create_table(send, "bots only")
    # send("setting", CommandData(name="createTableMaxPlayers"))


async def create_table(send: Send, table_name: str):
    await send(
        "tableCreate",
        CommandData(
            name=table_name,
            options=Options(
                variantName="No Variant",
                timed=False,
                timeBase=0,
                timePerTurn=0,
                speedrun=False,
                cardCycle=False,
                deckPlays=False,
                emptyClues=False,
                oneExtraCard=False,
                oneLessCard=False,
                allOrNothing=False,
                detrimentalCharacters=False,
            ),
            password="",
            maxPlayers=5,
        ),
    )


async def say_text(send: Send, msg: str, room: str):
    await send("chat", CommandData(msg="Hi", room="lobby"))


async def table_start(send: Send, table_id: int, indented_players: List[str]):
    class TableStartModel(HLModel):
        tableID: Optional[int] = None
        intendedPlayers: Optional[List[str]] = None

    await send("tableStart", TableStartModel(tableID=table_id, intendedPlayers=indented_players))


async def join_table(send: Send, table_id: int):
    await send("tableJoin", CommandData(tableID=table_id))


async def on_user(data: Msg, send: Send):
    table_id = data.get("tableID")
    print(table_id)


async def on_table_start(data: Msg, send: Send):
    table_id = data.get("tableID")
    replay = data.get("replay")
    print(table_id, replay)


async def on_table(data: TableMessage, send: Send):
    pass


# high level game state info request
async def get_game_info_1(table_id: int, send: Send):
    await send("getGameInfo1", CommandData(tableID=table_id))


# request all actions played so far
async def get_game_info_2(table_id: int, send: Send):
    await send("getGameInfo2", CommandData(tableID=table_id))


async def on_game_actions_list(data: GameActionListMessage, send: Send):
    pass


async def main():
    await init_logger(logging.INFO)
    msg_handler = MessageHandler(
        handlers=[
            (None, None, on_message_print),
            ("tableList", None, on_table_list),
            ("user", None, on_user),
            ("gameActionList", None, on_game_actions_list),
            ("table", None, on_table),
        ]
    )
    client = WsClient(username="kek1", password="123", address="127.0.0.1:9000", on_message=msg_handler.on_message)  # noqa: S106
    await client.start()


if __name__ == "__main__":
    asyncio.run(main())
