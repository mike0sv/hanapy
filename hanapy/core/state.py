from dataclasses import dataclass
from typing import Dict, List

from hanapy.core.action import PlayerPos
from hanapy.core.card import Card, Color
from hanapy.core.deck import Deck
from hanapy.core.player import PlayerMemo, PlayerState, PlayerView


class BaseGameState:
    pass


@dataclass
class PlayedCards:
    cards: Dict[Color, int]

    def is_valid_play(self, card: Card) -> bool:
        return card.number - 1 == self.cards.get(card.color, 0)

    def play(self, card: Card) -> None:
        if self.is_valid_play(card):
            self.cards[card.color] += 1

    def is_complete(self, num_colors: int, max_card_number: int) -> bool:
        return len(self.cards) == num_colors and all(v == max_card_number for v in self.cards.values())


@dataclass
class DiscardPile:
    cards: List[Card]


@dataclass
class GameConfig:
    max_lives: int
    max_cards: int
    players: int
    max_clues: int
    num_colors: int
    max_card_number: int
    unlimited_clues: bool = False


@dataclass
class GameState(BaseGameState):
    players: List[PlayerState]
    current_player: int
    deck: Deck
    clues_left: int
    lives_left: int
    played_cards: PlayedCards
    discarded_cards: DiscardPile
    config: GameConfig
    turns_left: int

    def get_current_player_view(self) -> PlayerView:
        return self.get_player_view(self.current_player)

    def get_player_view(self, player: int) -> PlayerView:
        return PlayerView(player, self.players[player].memo)

    def card_at(self, playerpos: PlayerPos) -> Card:
        return self.players[playerpos.player].cards[playerpos.pos]

    def update_player_memo(self, player: int, memo: PlayerMemo) -> None:
        self.players[player].memo = memo

    @property
    def game_ended(self) -> bool:
        return (
            self.lives_left < 1
            or self.turns_left < 1
            or self.played_cards.is_complete(self.config.num_colors, self.config.max_card_number)
        )
