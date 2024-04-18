from abc import ABC, abstractmethod
from typing import List, Optional, Union

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
        touched = bool(self.number or self.color)
        num = str(self.number or "?")
        if self.color is not None:
            res = num + self.color.char
            if touched:
                res = res.upper()
            return self.color.paint(res, touched=touched)
        res = num + "?"
        return res


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


class CommonMemo(Struct):
    touched: List[List[bool]]

    @classmethod
    def create(cls, players: int, max_cards: int):
        return CommonMemo(touched=[[False for _ in range(max_cards)] for _ in range(players)])

    def touch(self, player: int, card: Union[int, List[int]]):
        for c in (card,) if isinstance(card, int) else card:
            self.touched[player][c] = True

    def pop_card(self, player: int, card: int):
        self.touched[player].pop(card)
        self.touched[player].insert(0, False)


class PlayerView(Struct):
    name: str
    me: int
    memo: PlayerMemo
    common_memo: CommonMemo
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

    @abstractmethod
    async def on_game_end(self, view: PlayerView, is_win: bool):
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
