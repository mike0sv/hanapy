from typing import Dict, List, Union

from msgspec import Struct

from hanapy.core.card import Card, CardInfo, CluedCards, Color
from hanapy.types import SeenCards


class PlayedCards(Struct):
    cards: Dict[str, List[Card]]

    @classmethod
    def empty(cls, colors: List[Color]):
        return PlayedCards(cards={c.char: [] for c in colors})

    def is_valid_play(self, card: Union[Card, CardInfo]) -> bool:
        if isinstance(card, Card):
            return card.number - 1 == len(self.cards[card.color.char])
        as_card = card.as_card()
        if as_card is not None:
            return self.is_valid_play(as_card)
        if card.number is not None:
            return all(card.number - 1 == len(stack) for stack in self.cards.values())
        return False

    def is_obsolete(self, card: Union[Card, CardInfo], max_number: int) -> bool:
        if isinstance(card, Card):
            return card.number <= len(self.cards[card.color.char])
        as_card = card.as_card()
        if as_card is not None:
            return self.is_obsolete(as_card, max_number)
        # todo improve logic
        if card.number is not None:
            return all(card.number <= len(stack) for stack in self.cards.values())
        if card.color is not None:
            return len(self.cards[card.color.char]) == max_number
        return False

    def play(self, card: Card) -> None:
        if self.is_valid_play(card):
            self.cards[card.color.char].append(card)

    def is_complete(self, color_count: int, max_card_number: int) -> bool:
        return len(self.cards) == color_count and all(len(stack) == max_card_number for stack in self.cards.values())

    @property
    def score(self):
        return sum(len(stack) for stack in self.cards.values())

    def get_all_cards(self) -> SeenCards:
        res = []
        for stack in self.cards.values():
            res += stack
        return SeenCards(res)


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

    @property
    def total_cards(self):
        return sum(self.counts.values()) * self.color_count


class GameState(Struct):
    turn: int
    clues_left: int
    lives_left: int
    played: PlayedCards
    discarded: DiscardPile
    clued: CluedCards
    turns_left: int
    current_player: int
    cards_left: int

    @classmethod
    def create(cls, config: "GameConfig", cards_left: int):
        return GameState(
            turn=1,
            clues_left=config.max_clues,
            lives_left=config.max_lives,
            clued=CluedCards.create(config.player_count, config.hand_size, config.cards),
            played=PlayedCards.empty(config.cards.colors),
            discarded=DiscardPile.new(),
            turns_left=config.player_count,
            current_player=0,
            cards_left=cards_left,
        )


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
