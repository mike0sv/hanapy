from dataclasses import dataclass
from typing import List, Optional

from hanapy.core.card import Card


@dataclass
class Deck:
    cards: List[Card]

    def draw(self) -> Card:
        return self.cards.pop()

    def peek(self) -> Optional[Card]:
        return self.cards[-1] if len(self.cards) else None

    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def size(self):
        return len(self.cards)


class DeckGenerator:
    def generate(self) -> Deck:
        raise NotImplementedError
