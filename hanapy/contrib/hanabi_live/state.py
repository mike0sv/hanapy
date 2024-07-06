from typing import Optional

from hanapy.contrib.hanabi_live.actions import HLAction
from hanapy.core.config import GameConfig, GameState
from hanapy.core.player import PlayerMemo, PlayerView


class HLGameState:
    def __init__(self, name: str):
        self.name = name
        self._player_num: Optional[int] = None
        self._config: Optional[GameConfig] = None
        self._deck_size: Optional[int] = None
        self._player_view: Optional[PlayerView] = None

    @property
    def player_view(self) -> PlayerView:
        if self._player_view is None:
            raise ValueError("HLGameState is not initialized")
        return self._player_view

    @property
    def player_num(self):
        if self._player_num is None:
            raise ValueError("HLGameState is not initialized")
        return self._player_num

    @property
    def config(self):
        if self._config is None:
            raise ValueError("HLGameState is not initialized")
        return self._config

    @property
    def deck_size(self):
        if self._deck_size is None:
            raise ValueError("HLGameState is not initialized")
        return self._deck_size

    def set_player_num(self, player_num: int):
        self._player_num = player_num

    def set_config(self, config: GameConfig):
        self._config = config

    def init_player_view(self):
        self._player_view = PlayerView(
            name=self.name,
            me=self.player_num,
            memo=PlayerMemo.create(),
            config=self.config,
            cards=[],
            state=GameState.create(self.config, self.deck_size),
        )

    def apply_action(self, action: HLAction):
        print("applied", action)

    def get_player_view(self) -> PlayerView:
        return self.player_view
