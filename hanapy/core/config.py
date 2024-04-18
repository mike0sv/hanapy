from typing import Dict, List

from msgspec import Struct

from hanapy.core.card import Card, Color


class PlayedCards(Struct):
    cards: Dict[str, int]

    def is_valid_play(self, card: Card) -> bool:
        return card.number - 1 == self.cards.get(card.color.char, 0)

    def play(self, card: Card) -> None:
        if self.is_valid_play(card):
            if card.color.char not in self.cards:
                self.cards[card.color.char] = 0
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
