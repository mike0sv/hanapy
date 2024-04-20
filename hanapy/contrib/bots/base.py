import logging
from abc import ABC

from hanapy.core.action import StateUpdate
from hanapy.core.config import GameResult
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView

logger = logging.getLogger(__name__)


class BaseBotPlayer(PlayerActor, ABC):
    def __init__(self, name: str, log: bool = False):
        super().__init__(name)
        self.log = log

    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
        return view.memo

    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        return view.memo

    async def on_game_end(self, view: PlayerView, game_result: GameResult):
        pass
