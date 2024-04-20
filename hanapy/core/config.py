from typing import Dict, List, Union

from msgspec import Struct

from hanapy.core.card import Card, CardInfo, CluedCards, Color
from hanapy.types import SeenCards


class PlayedCards(Struct):
    cards: Dict[str, int]

    @classmethod
    def empty(cls, colors: List[Color]):
        return PlayedCards(cards={c.char: 0 for c in colors})

    def is_valid_play(self, card: Union[Card, CardInfo]) -> bool:
        if isinstance(card, Card):
            return card.number - 1 == self.cards[card.color.char]
        as_card = card.as_card()
        if as_card is not None:
            return self.is_valid_play(as_card)
        if card.number is not None:
            return all(card.number - 1 == val for val in self.cards.values())
        return False

    def is_obsolete(self, card: Union[Card, CardInfo], max_number: int) -> bool:
        if isinstance(card, Card):
            return card.number <= self.cards[card.color.char]
        as_card = card.as_card()
        if as_card is not None:
            return self.is_obsolete(as_card, max_number)
        if card.number is not None:
            return all(card.number <= val for val in self.cards.values())
        if card.color is not None:
            return self.cards[card.color.char] == max_number
        return False

    def play(self, card: Card) -> None:
        if self.is_valid_play(card):
            self.cards[card.color.char] += 1

    def is_complete(self, color_count: int, max_card_number: int) -> bool:
        return len(self.cards) == color_count and all(v == max_card_number for v in self.cards.values())

    @property
    def score(self):
        return sum(self.cards.values())

    def get_all_cards(self, colors: List[Color]) -> SeenCards:
        return SeenCards(
            Card(color=Color.parse(c, colors), number=n)
            for c, max_num in self.cards.items()
            for n in range(1, max_num + 1)
        )


class DiscardPile(Struct):
    cards: List[Card]

    @classmethod
    def new(cls):
        return DiscardPile(cards=[])


class CardConfig(Struct):
    colors: List[Color]
    counts: Dict[int, int]

    @property
    def max_number(self):
        return max(self.counts)

    @property
    def color_count(self):
        return len(self.colors)


class GameState(Struct):
    clues_left: int
    lives_left: int
    played: PlayedCards
    discarded: DiscardPile
    clued: CluedCards
    turns_left: int
    current_player: int
    cards_left: int


class GameConfig(Struct):
    max_lives: int
    hand_size: int
    player_count: int
    max_clues: int
    cards: CardConfig
    unlimited_clues: bool = False


class GameResult(Struct):
    is_win: bool
    score: int
    max_score: int
