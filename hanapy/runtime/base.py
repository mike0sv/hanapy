import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Dict, List, Type, TypeVar, Union

from hanapy.core.loop import GameVariant
from hanapy.runtime.events import Event, PlayerRegisteredEvent, RegisterPlayerEvent, StartGameEvent
from hanapy.runtime.types import PlayerID

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 55556

ET = TypeVar("ET", bound=Event)
EventHandler = Union[Callable[[ET], bool], Callable[[ET], Awaitable[bool]]]
EventHandlers = Dict[Type[ET], List[EventHandler]]
logger = logging.getLogger(__name__)


async def call_handler(event_handler: EventHandler, event: Event) -> bool:
    res = event_handler(event)
    if not isinstance(res, bool):
        res = await res
    return res


class HanapyBase(ABC):
    def __init__(self, event_handlers: EventHandlers = None):
        self.event_handlers = event_handlers or {}

    def add_event_handler(self, event_type: Type[ET], handler: EventHandler):
        self.event_handlers.setdefault(event_type, [])
        self.event_handlers[event_type].append(handler)

    def add_event_handlers(self, event_handlers: Union[EventHandlers, Dict[Type[ET], EventHandler]]):
        for event_type, handler in event_handlers.items():
            handlers = [handler] if callable(handler) else handler

            for h in handlers:
                self.add_event_handler(event_type, h)

    async def receive_event(self, event: Event):
        for event_type, handlers in self.event_handlers.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    logger.debug(f"Handling {event} with {handler}")
                    if not await call_handler(handler, event):
                        logger.debug(f"Stopped propagating {event}")
                        return
        await self._receive_event(event)

    @abstractmethod
    async def _receive_event(self, event: Event):
        raise NotImplementedError


class HanapyServer(HanapyBase):
    @abstractmethod
    async def wait_for_event(self, pid: PlayerID, event_type: Type[ET]) -> ET:
        raise NotImplementedError

    @abstractmethod
    async def send_event(self, pid: PlayerID, event: Event):
        raise NotImplementedError

    async def broadcast(self, event: Event):
        await asyncio.gather(*[self.send_event(pid, event) for pid in self.list_players()])

    @abstractmethod
    async def run(self):
        raise NotImplementedError

    @abstractmethod
    def list_players(self) -> List[PlayerID]:
        raise NotImplementedError

    async def start_game_loop(self, host_pid: PlayerID, game_variant: GameVariant):
        from hanapy.runtime.players import ServerPlayerActor

        await self.wait_for_event(host_pid, StartGameEvent)
        players = [ServerPlayerActor(uid, self) for uid in self.list_players()]
        game = game_variant(players)
        loop = game.get_loop()
        await loop.run()

    async def start(self, host_pid: PlayerID, game_variant: GameVariant):
        asyncio.get_event_loop().create_task(self.run())
        asyncio.get_event_loop().create_task(self.start_game_loop(host_pid, game_variant))


class HanapyClient(HanapyBase):
    me: int

    async def register(self, pid: PlayerID) -> int:
        logger.debug("[client] registering self %s", pid)
        await self.send_event(RegisterPlayerEvent(pid=pid))
        return (await self.wait_for_event(PlayerRegisteredEvent)).player_num

    @abstractmethod
    async def send_event(self, event: Event):
        raise NotImplementedError

    @abstractmethod
    async def wait_for_event(self, event_type: Type[ET]) -> ET:
        raise NotImplementedError

    @abstractmethod
    async def connect(self):
        raise NotImplementedError

    @abstractmethod
    async def is_running(self) -> bool:
        raise NotImplementedError

    async def is_stopped(self) -> bool:
        return not await self.is_running()


class HostPortMixin:
    def __init__(self, host: str, port: int):
        super().__init__()
        self.port = port
        self.host = host
