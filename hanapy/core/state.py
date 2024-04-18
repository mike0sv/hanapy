from typing import List

from msgspec import Struct

from hanapy.core.action import PlayerPos
from hanapy.core.card import Card
from hanapy.core.config import PublicGameState
from hanapy.core.deck import Deck
from hanapy.core.player import CommonMemo, PlayerMemo, PlayerState, PlayerView


class BaseGameState(Struct):
    pass


class GameState(BaseGameState):
    players: List[PlayerState]
    deck: Deck
    public: PublicGameState
    memo: CommonMemo

    def get_current_player_view(self) -> PlayerView:
        return self.get_player_view(self.public.current_player)

    def get_player_view(self, player: int) -> PlayerView:
        return PlayerView(
            name=f"player {player}",
            me=player,
            memo=self.players[player].memo,
            common_memo=self.memo,
            cards=[p.cards if i != player else [] for i, p in enumerate(self.players)],
            state=self.public,
        )

    def card_at(self, playerpos: PlayerPos) -> Card:
        return self.players[playerpos.player].cards[playerpos.pos]

    def update_player_memo(self, player: int, memo: PlayerMemo) -> None:
        self.players[player].memo = memo

    @property
    def game_ended(self) -> bool:
        return (
            self.public.lives_left < 1
            or self.public.turns_left < 1
            or self.public.played_cards.is_complete(self.public.config.num_colors, self.public.config.max_card_number)
        )

    def next_player(self):
        self.public.current_player += 1
        self.public.current_player %= self.public.config.players
