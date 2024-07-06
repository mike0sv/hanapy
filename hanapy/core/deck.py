from dataclasses import dataclass
from typing import List, Optional

from hanapy.core.card import Card, Card2
from hanapy.core.config import CardConfig


@dataclass
class Deck:
    cards: List[Card2]

    def draw(self) -> Card2:
        return self.cards.pop()

    def peek(self) -> Optional[Card2]:
        return self.cards[-1] if len(self.cards) else None

    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def size(self):
        return len(self.cards)


class DeckGenerator:
    def generate(self, config: CardConfig) -> Deck:
        raise NotImplementedError
