from typing import List

from msgspec import Struct

from hanapy.core.action import PlayerPos
from hanapy.core.card import Card
from hanapy.core.config import GameConfig, GameState
from hanapy.core.deck import Deck
from hanapy.core.player import PlayerMemo, PlayerState, PlayerView


class BaseGameData(Struct):
    pass


class GameData(BaseGameData):
    players: List[PlayerState]
    deck: Deck
    state: GameState
    config: GameConfig

    def get_current_player_view(self) -> PlayerView:
        return self.get_player_view(self.state.current_player)

    def get_player_view(self, player: int) -> PlayerView:
        return PlayerView(
            name=f"player {player}",
            me=player,
            memo=self.players[player].memo,
            config=self.config,
            cards=[p.cards if i != player else [] for i, p in enumerate(self.players)],
            state=self.state,
        )

    def card_at(self, playerpos: PlayerPos) -> Card:
        return self.players[playerpos.player].cards[playerpos.pos]

    def update_player_memo(self, player: int, memo: PlayerMemo) -> None:
        self.players[player].memo = memo

    @property
    def game_ended(self) -> bool:
        return self.state.lives_left < 1 or self.state.turns_left < 1 or self.game_winned

    @property
    def game_winned(self) -> bool:
        return self.state.played.is_complete(self.config.cards.color_count, self.config.cards.max_number)

    def next_player(self):
        self.state.current_player += 1
        self.state.current_player %= self.config.player_count
