import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, Type, TypeVar

from hanapy.runtime.events import Event, RegisterPlayerEvent, StartGameEvent
from hanapy.runtime.types import PlayerID
from hanapy.variants.classic import ClassicGame

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 55556

ET = TypeVar("ET", bound=Event)

logger = logging.getLogger(__name__)


def run_in_loop(future):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        task = loop.create_task(future)
        task.result()


class HanapyServer(ABC):
    _thread = None

    @abstractmethod
    async def wait_for_event(self, pid: PlayerID, event_type: Type[ET]) -> ET:
        raise NotImplementedError

    # def wait_for_event_sync(self, pid: PlayerID, event_type: Type[ET]) -> ET:
    #     return asyncio.get_event_loop().run_until_complete(self.wait_for_event(pid, event_type))
    # return asyncio.run_coroutine_threadsafe(self.wait_for_event(pid, event_type), asyncio.get_event_loop()).result()

    @abstractmethod
    async def send_event(self, pid: PlayerID, event: Event):
        raise NotImplementedError

    @abstractmethod
    async def run(self):
        raise NotImplementedError

    @abstractmethod
    def list_players(self) -> List[PlayerID]:
        raise NotImplementedError

    async def start_game_loop(self, host_pid: PlayerID):
        from hanapy.runtime.players import ServerPlayerActor

        await self.wait_for_event(host_pid, StartGameEvent)
        players = [ServerPlayerActor(uid, self) for uid in self.list_players()]
        game = ClassicGame(players)
        loop = game.get_loop()
        await loop.run()

    async def start(self, host_pid: PlayerID):
        asyncio.get_event_loop().create_task(self.run())
        asyncio.get_event_loop().create_task(self.start_game_loop(host_pid))


CT = TypeVar("CT")


class EventBuffer:
    def __init__(self):
        self._buf: List[Event] = []

    def add(self, event: Event):
        logger.debug("event buffered %s", event)
        self._buf.append(event)

    def search_event(self, event_type: Type[ET]) -> Optional[ET]:
        for i, event in enumerate(self._buf):
            if isinstance(event, event_type):
                return self._buf.pop(i)  # type: ignore[return-value]
        return None

    async def wait_for_event(self, event_type: Type[ET]) -> ET:
        event = self.search_event(event_type)
        while event is None:
            await asyncio.sleep(0.1)
            event = self.search_event(event_type)
        return event


class BufferingHanapyServer(HanapyServer, Generic[CT]):
    def __init__(self):
        self.player_buffers: Dict[PlayerID, EventBuffer] = {}
        self.player_clients: Dict[PlayerID, CT] = {}

    def register_player(self, pid: PlayerID, client: CT):
        logger.debug("[server] player registered %s %s", pid, client.__class__.__name__)
        self.player_buffers[pid] = EventBuffer()
        self.player_clients[pid] = client

    def list_players(self) -> List[PlayerID]:
        return list(self.player_buffers)

    @abstractmethod
    async def send(self, client: CT, event: Event):
        raise NotImplementedError

    async def send_event(self, pid: PlayerID, event: Event):
        return await self.send(self.player_clients[pid], event)

    def buffer_event(self, event: Event):
        logger.debug("[server] buffering event %s", event)
        self.player_buffers[event.pid].add(event)

    async def wait_for_event(self, pid: PlayerID, event_type: Type[ET]) -> ET:
        logger.debug("[server] waiting for %s event from %s", event_type.__name__, pid)
        while pid not in self.player_buffers:
            await asyncio.sleep(0.1)
        return await self.player_buffers[pid].wait_for_event(event_type)


class HanapyClient(ABC):
    async def register(self, pid: PlayerID):
        logger.debug("[client] registering self %s", pid)
        await self.send_event(RegisterPlayerEvent(pid))

    @abstractmethod
    async def send_event(self, event: Event):
        raise NotImplementedError

    @abstractmethod
    async def wait_for_event(self, event_type: Type[ET]) -> ET:
        raise NotImplementedError

    # def wait_for_event_sync(self, event_type: Type[ET]) -> ET:
    #     return asyncio.get_event_loop().run_until_complete(self.wait_for_event(event_type))
    # return asyncio.run_coroutine_threadsafe(self.wait_for_event(event_type), asyncio.get_event_loop()).result()
    @abstractmethod
    async def connect(self):
        raise NotImplementedError


class BufferingHanapyClient(HanapyClient, ABC):
    def __init__(self):
        self._buf = EventBuffer()

    def buffer_event(self, event: Event):
        logger.debug("[client] buffered event %s", event)
        self._buf.add(event)

    async def wait_for_event(self, event_type: Type[ET]) -> ET:
        logger.debug("[client] waiting for event %s", event_type.__name__)
        return await self._buf.wait_for_event(event_type)


class HostPortMixin:
    def __init__(self, host: str, port: int):
        super().__init__()
        self.port = port
        self.host = host
