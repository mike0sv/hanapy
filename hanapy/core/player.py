from abc import ABC, abstractmethod
from typing import List, Optional

from msgspec import Struct

from hanapy.core.action import Action, ClueAction, ClueTouched, StateUpdate
from hanapy.core.card import Card, Color
from hanapy.core.config import PublicGameState


class CardInfo(Struct):
    color: Optional[Color]
    number: Optional[int]

    @classmethod
    def none(cls):
        return CardInfo(color=None, number=None)

    def to_str(self):
        num = str(self.number or "?")
        if self.color is not None:
            return self.color.paint(num + self.color.char)
        return num + "?"


class CluesInfo(Struct):
    cards: List[CardInfo]

    def pop_card(self, card: int):
        self.cards.pop(card)
        self.cards.insert(0, CardInfo.none())

    def apply_clue(self, clue: ClueAction, touched: ClueTouched):
        for card in touched:
            self.cards[card].color = self.cards[card].color or clue.color
            self.cards[card].number = self.cards[card].number or clue.number


class PlayerMemo(Struct):
    info: CluesInfo

    @classmethod
    def create(cls, max_cards: int):
        return PlayerMemo(info=CluesInfo(cards=[CardInfo.none() for _ in range(max_cards)]))


class PlayerView(Struct):
    name: str
    me: int
    memo: PlayerMemo
    cards: List[List[Card]]
    state: PublicGameState


class PlayerActor(ABC):
    @abstractmethod
    async def on_game_start(self, view: PlayerView):
        raise NotImplementedError

    @abstractmethod
    async def get_next_action(self, view: PlayerView) -> Action:
        raise NotImplementedError

    @abstractmethod
    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        raise NotImplementedError


class PlayerState(Struct):
    cards: List[Card]
    memo: PlayerMemo

    def loose_card(self, card_position: int) -> Card:
        card = self.cards[card_position]
        self.cards.pop(card_position)
        return card

    def gain_card(self, card: Card) -> None:
        self.cards.insert(0, card)
