import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Dict, Generic, List, Optional, Type, TypeVar

from hanapy.runtime.base import EventHandlers, HanapyClient, HanapyServer
from hanapy.runtime.events import Event
from hanapy.types import PlayerID

ET = TypeVar("ET", bound=Event)

logger = logging.getLogger(__name__)


CT = TypeVar("CT")


class EventWaitAborted(Exception):
    pass


class EventBuffer:
    def __init__(self):
        self._buf: List[Event] = []

    def add(self, event: Event):
        self._buf.append(event)

    def search_event(self, event_type: Type[ET]) -> Optional[ET]:
        for i, event in enumerate(self._buf):
            if isinstance(event, event_type):
                return self._buf.pop(i)  # type: ignore[return-value]
        return None

    async def wait_for_event(self, event_type: Type[ET], breaker: Optional[Callable[[], Awaitable[bool]]] = None) -> ET:
        event = self.search_event(event_type)
        while event is None:
            if breaker is not None and await breaker():
                raise EventWaitAborted()
            await asyncio.sleep(0.1)
            event = self.search_event(event_type)
        return event


class BufferingHanapyServer(HanapyServer, Generic[CT]):
    def __init__(self, event_handlers: Optional[EventHandlers] = None):
        super().__init__(event_handlers)
        self.player_buffers: Dict[PlayerID, EventBuffer] = {}
        self.player_clients: Dict[PlayerID, CT] = {}

    def register_player(self, pid: PlayerID, client: CT):
        logger.debug("[server] player registered %s %s", pid, client.__class__.__name__)
        self.player_buffers[pid] = EventBuffer()
        self.player_clients[pid] = client

    def unregister_player(self, pid: PlayerID):
        logger.debug(
            "[server] player unregistered %s",
            pid,
        )
        del self.player_buffers[pid]
        del self.player_clients[pid]

    def list_players(self) -> List[PlayerID]:
        return list(self.player_buffers)

    @abstractmethod
    async def send(self, client: CT, event: Event):
        raise NotImplementedError

    async def send_event(self, pid: PlayerID, event: Event):
        return await self.send(self.player_clients[pid], event)

    async def _receive_event(self, event: Event):
        logger.debug("[server] buffering event %s", event)
        self.player_buffers[event.pid].add(event)

    def buffer_event(self, event: Event):
        pass

    async def wait_for_event(self, pid: PlayerID, event_type: Type[ET]) -> ET:
        logger.debug("[server] waiting for %s event from %s", event_type.__name__, pid)
        while pid not in self.player_buffers:
            await asyncio.sleep(0.1)
        event = await self.player_buffers[pid].wait_for_event(event_type)
        logger.debug("[server] got event %s from %s", event, pid)
        return event


class BufferingHanapyClient(HanapyClient, ABC):
    def __init__(self, event_handlers: Optional[EventHandlers] = None):
        super().__init__(event_handlers=event_handlers)
        self._buf = EventBuffer()

    async def _receive_event(self, event: Event):
        logger.debug("[client] buffered event %s", event)
        self._buf.add(event)

    async def wait_for_event(self, event_type: Type[ET]) -> ET:
        logger.debug("[client] waiting for event %s", event_type.__name__)
        event = await self._buf.wait_for_event(event_type, breaker=self.is_stopped)
        logger.debug("[client] got event %s from server", event)
        return event
