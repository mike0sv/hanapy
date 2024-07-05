import asyncio

import requests
import websockets
import json


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
        print(f"< {type_part} {json.dumps(json_data, indent=2)}")

    async def send(self, message_type, data):
        await self.websocket.send(f'{message_type} {json.dumps(data)}')

    async def start(self):
        token = get_access_token(self.username, self.password, self.address)
        uri = f"ws://{self.address}/ws"
        async with websockets.connect(uri, extra_headers={'Cookie': f'hanabi.sid={token}'}) as websocket:
            self.websocket = websocket
            async for message in websocket:
                try:
                    await self.on_message(message)
                except json.JSONDecodeError:
                    print("Received non-JSON message:", message)

async def main():
    client = WsClient(username='kek1', password='123', address='127.0.0.1:9000')
    await client.start()

if __name__ == '__main__':
    asyncio.run(main())
