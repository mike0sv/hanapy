import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from typing import Optional

from hanapy.runtime.base import HostPortMixin
from hanapy.runtime.buffers import BufferingHanapyClient, BufferingHanapyServer
from hanapy.runtime.events import ConnectionLostEvent, Event, MessageEvent, PlayerRegisteredEvent
from hanapy.runtime.types import PlayerID
from hanapy.utils.ser import dumps, loads

logger = logging.getLogger(__name__)


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    return loop


class AsyncServer(HostPortMixin, BufferingHanapyServer[StreamWriter]):
    _host_pid: PlayerID
    player_num = 0  # fixme

    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.add_event_handler(ConnectionLostEvent, self.player_disconnected_handler)

    def player_disconnected_handler(self, event: ConnectionLostEvent):
        get_event_loop().create_task(self.broadcast(MessageEvent(pid=event.pid, text=f"Player {event.pid} left")))
        return False

    async def send(self, client: StreamWriter, event: Event):
        data = dumps(event) + b"\n"
        logger.debug("[server] sending event %s", event)
        client.write(data)

    async def player_connected_handler(self, reader: StreamReader, writer: StreamWriter):
        logger.debug("[server] new player connected")
        register_event = loads(Event, await reader.readline())
        pid = register_event.pid
        self.register_player(pid, writer)
        await self.broadcast(PlayerRegisteredEvent(pid=pid, player_num=self.player_num, players=self.list_players()))
        self.player_num += 1

        async def listen_for_events():
            listening = True
            while listening:
                data = await reader.readline()
                if not data:
                    listening = False
                    event = ConnectionLostEvent(pid=pid)
                    self.unregister_player(pid)
                else:
                    event = loads(Event, data)
                await self.receive_event(event)

        listen_for_events.__name__ = f"listen_for_events{pid}]"
        _ = asyncio.create_task(listen_for_events())

    async def run(self):
        logger.debug("[server] running server")
        server = await asyncio.start_server(self.player_connected_handler, self.host, self.port, reuse_address=True)
        async with server:
            await server.serve_forever()


class AsyncClient(HostPortMixin, BufferingHanapyClient):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.writer: Optional[StreamWriter] = None
        self.listening = True

    async def run_loop(self):
        while True:
            try:
                future = asyncio.open_connection(self.host, self.port)
                reader, self.writer = await asyncio.wait_for(future, timeout=1)
                break
            except (ConnectionRefusedError, asyncio.TimeoutError):
                await asyncio.sleep(1)
                print("connecting...")
        logger.debug("[client] connected")

        async def listen_for_events():
            while self.listening:
                data = await reader.readline()
                if not data:
                    logger.debug("Connection to server lost, exiting loop")
                    event = ConnectionLostEvent(pid="")
                    self.listening = False
                else:
                    event = loads(Event, data)
                await self.receive_event(event)

        get_event_loop().create_task(listen_for_events())

    async def connect(self):
        logger.debug("[client] creating connection")
        await self.run_loop()
        while self.writer is None:
            await asyncio.sleep(1)
            logger.debug("[client] waiting for connection")

    async def is_running(self):
        return self.listening

    async def send_event(self, event: Event):
        logger.debug("[client] sending event %s", event)
        data = dumps(event) + b"\n"
        self.writer.write(data)  # type: ignore[union-attr]
