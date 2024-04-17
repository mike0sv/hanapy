import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from typing import Optional

from hanapy.runtime.base import BufferingHanapyClient, BufferingHanapyServer, HostPortMixin
from hanapy.runtime.events import Event, PlayerRegisteredEvent
from hanapy.runtime.types import PlayerID
from hanapy.utils.ser import dumps, loads

logger = logging.getLogger(__name__)

# helper to log details of all tasks
#
# loops = []
#
#
# def log_all_tasks_helper(excluded=None):
#     print("_________tasks:")
#     excluded = excluded or []
#     # get all tasks
#
#     for name, loop in loops:
#         thread = [t for t in threading.enumerate() if t.name == name][0]
#         print(name, loop)
#         print(traceback.print_stack(sys._current_frames()[thread.ident]))
#         for task in asyncio.all_tasks(loop):
#             if task in excluded:
#                 continue
#             task.print_stack()
#         print()
#
#
# def kek():
#     while True:
#         try:
#             log_all_tasks_helper()
#         except RuntimeError:
#             pass
#         time.sleep(10)
#
#
# t = Thread(target=kek, daemon=True, name="monitor")
# # t.start()


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    # name = threading.current_thread().name
    # if (name, loop) not in loops:
    #     print("new loop for thread", name)
    #     loops.append((name, loop))
    return loop


class AsyncServer(HostPortMixin, BufferingHanapyServer[StreamWriter]):
    _host_pid: PlayerID
    player_num = 0  # fixme

    async def send(self, client: StreamWriter, event: Event):
        data = dumps(event) + b"\n"
        logger.debug("[server] sending event %s", event)
        # logger.debug("[server] sending event %s to %s", dumps(event) + b"\n", client)
        client.write(data)
        # await client.drain()
        # get_event_loop().create_task(client.drain())

    async def player_connected_handler(self, reader: StreamReader, writer: StreamWriter):
        # self.send(writer, Event("asd"))
        logger.debug("[server] new player connected")
        register_event = loads(Event, await reader.readline())
        self.register_player(register_event.pid, writer)
        await self.send(writer, PlayerRegisteredEvent(pid=register_event.pid, player_num=self.player_num))
        self.player_num += 1

        async def listen_for_events():
            while True:
                self.buffer_event(loads(Event, await reader.readline()))

        listen_for_events.__name__ = f"listen_for_events{register_event.pid}]"
        _ = asyncio.create_task(listen_for_events())

    async def run(self):
        logger.debug("[server] running server")
        server = await asyncio.start_server(self.player_connected_handler, self.host, self.port, reuse_address=True)
        # get_event_loop().create_task(self.start_game_loop(self._host_pid))
        async with server:
            await server.serve_forever()


class AsyncClient(HostPortMixin, BufferingHanapyClient):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.writer: Optional[StreamWriter] = None

    async def run_loop(self):
        while True:
            try:
                reader, self.writer = await asyncio.open_connection(self.host, self.port)
                # print("123", reader, self.writer)
                break
            except ConnectionRefusedError:
                await asyncio.sleep(1)
                logger.debug("connecting...")
        logger.debug("[client] connected")

        async def listen_for_events():
            while True:
                # print("kek", reader)
                self.buffer_event(loads(Event, await reader.readline()))

        # asyncio.run_coroutine_threadsafe(listen_for_events(), get_event_loop())
        get_event_loop().create_task(listen_for_events())

    async def connect(self):
        logger.debug("[client] creating connection")
        await self.run_loop()
        while self.writer is None:
            await asyncio.sleep(1)
            logger.debug("[client] waiting for connection")

    async def send_event(self, event: Event):
        logger.debug("[client] sending event %s", event)
        data = dumps(event) + b"\n"
        self.writer.write(data)  # type: ignore[union-attr]
        # get_event_loop().create_task(self.writer.drain())
