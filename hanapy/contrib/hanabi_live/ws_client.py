import asyncio

import requests
import websockets
import json
import logging

from hanapy.utils.log import init_logger

logger = logging.getLogger(__name__)


def get_access_token(username, password, server_address, ssl):
    schema = "https" if ssl else "http"
    url = f'{schema}://{server_address}/login'
    data = {
        'username': username,
        'password': password,
        'version': '6387'
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    return cookies.get('hanabi.sid', None)

async def on_message_print(message_type, data, send):
    logger.debug(f"< {message_type} {json.dumps(data, indent=2)}")
    await send("222", {"pong": 222})


class WsClient(object):
    def __init__(self, username, password, address, on_message, ssl=False):
        self.address = address
        self.username = username
        self.password = password
        self.websocket = None
        self.ssl = ssl
        self.on_message = on_message

    async def send(self, message_type, data):
        await self.websocket.send(f'{message_type} {json.dumps(data)}')

    async def start(self):
        logger.debug("logging in...")
        token = get_access_token(self.username, self.password, self.address, self.ssl)
        logger.debug("authentication ok")
        schema = "wss" if self.ssl else "ws"
        uri = f"{schema}://{self.address}/ws"
        logger.debug(f"connecting to websocket url {uri}")
        async with websockets.connect(uri, extra_headers={'Cookie': f'hanabi.sid={token}'}) as websocket:
            self.websocket = websocket
            logger.info("connection established")
            async for message in websocket:
                index = message.find(' ')
                type_part = message[:index]
                json_part = message[index + 1:]
                json_data = json.loads(json_part)
                await self.on_message(type_part, json_data, self.send)

async def main():
    await init_logger(logging.DEBUG)
    client = WsClient(username='kek1', password='123', address='127.0.0.1:9000', on_message=on_message_print)
    await client.start()

if __name__ == '__main__':
    asyncio.run(main())
