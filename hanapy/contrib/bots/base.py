import logging
from abc import ABC

from hanapy.core.action import StateUpdate
from hanapy.core.config import GameResult
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView
from hanapy.players.console.render import print_game_end, print_player_view
from hanapy.runtime.events import GameStartedEvent, ObserveUpdateEvent
from hanapy.types import EventHandlers

logger = logging.getLogger(__name__)


class BaseBotPlayer(PlayerActor, ABC):
    def __init__(self, name: str, log: bool = False):
        super().__init__(name)
        self.log = log

    def get_event_handlers(self) -> EventHandlers:
        if self.log:
            return {
                ObserveUpdateEvent: [lambda event: print_player_view(event.view) or True],
                GameStartedEvent: [lambda event: print_player_view(event.view, detailed=True) or True],
            }
        return {}

    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
        return view.memo

    async def observe_update(self, view: PlayerView, update: StateUpdate, new_view: PlayerView) -> PlayerMemo:
        return view.memo

    async def on_game_end(self, view: PlayerView, game_result: GameResult):
        if self.log:
            print_game_end(view, game_result)
