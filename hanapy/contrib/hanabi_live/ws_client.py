import asyncio

import requests
import websockets
import json
import logging

from hanapy.utils.log import init_logger

logger = logging.getLogger(__name__)


def get_access_token(username, password, server_address):
    url = f'http://{server_address}/login'
    data = {
        'username': username,
        'password': password,
        'version': '6387'
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    return cookies.get('hanabi.sid', None)


class WsClient(object):
    def __init__(self, username, password, address):
        self.address = address
        self.username = username
        self.password = password
        self.websocket = None

    async def on_message(self, message):
        index = message.find(' ')
        type_part = message[:index]
        json_part = message[index + 1:]
        json_data = json.loads(json_part)
        logger.debug(f"< {type_part} {json.dumps(json_data, indent=2)}")

    async def send(self, message_type, data):
        await self.websocket.send(f'{message_type} {json.dumps(data)}')

    async def start(self):
        logger.debug("logging in...")
        token = get_access_token(self.username, self.password, self.address)
        logger.debug("authentication ok")
        uri = f"ws://{self.address}/ws"
        logger.debug(f"connecting to websocket url {uri}")
        async with websockets.connect(uri, extra_headers={'Cookie': f'hanabi.sid={token}'}) as websocket:
            self.websocket = websocket
            logger.info("connection established")
            async for message in websocket:
                await self.on_message(message)

async def main():
    await init_logger(logging.DEBUG)
    client = WsClient(username='kek1', password='123', address='127.0.0.1:9000')
    await client.start()

if __name__ == '__main__':
    asyncio.run(main())
