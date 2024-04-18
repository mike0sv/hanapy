from typing import Dict, List, Union

from msgspec import Struct

from hanapy.core.card import Card, Color
from hanapy.core.player import CardInfo


class PlayedCards(Struct):
    cards: Dict[str, int]

    def is_valid_play(self, card: Union[Card, CardInfo]) -> bool:
        if isinstance(card, Card):
            return card.number - 1 == self.cards[card.color.char]
        if card.as_card() is not None:
            return self.is_valid_play(card.as_card())
        if card.number is not None:
            return all(card.number - 1 == val for val in self.cards.values())
        return False

    def is_obsolete(self, card: Union[Card, CardInfo], max_number: int) -> bool:
        if isinstance(card, Card):
            return card.number <= self.cards[card.color.char]
        if card.as_card() is not None:
            return self.is_obsolete(card.as_card(), max_number)
        if card.number is not None:
            return all(card.number <= val for val in self.cards.values())
        if card.color is not None:
            return self.cards[card.color.char] == max_number
        return False

    def play(self, card: Card) -> None:
        if self.is_valid_play(card):
            self.cards[card.color.char] += 1

    def is_complete(self, num_colors: int, max_card_number: int) -> bool:
        return len(self.cards) == num_colors and all(v == max_card_number for v in self.cards.values())


class DiscardPile(Struct):
    cards: List[Card]


class GameConfig(Struct):
    max_lives: int
    max_cards: int
    players: int
    max_clues: int
    num_colors: int
    max_card_number: int
    colors: List[Color]
    unlimited_clues: bool = False


class PublicGameState(Struct):
    clues_left: int
    lives_left: int
    played_cards: PlayedCards
    discarded_cards: DiscardPile
    config: GameConfig
    turns_left: int
    current_player: int
    cards_left: int
