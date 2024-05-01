from typing import TYPE_CHECKING, Iterable, List, Literal, Optional, overload

import msgspec
from ordered_set import OrderedSet

if TYPE_CHECKING:
    from hanapy.core.config import CardConfig


class Color(msgspec.Struct, frozen=True):
    char: str
    value: str = ""

    @classmethod
    def parse(cls, char: str, colors: List["Color"]):
        try:
            return next(iter(c for c in colors if c.char == char))
        except StopIteration:
            raise ValueError(f"Cannot parse color [{char}]") from None

    def paint(self, text: str, is_touched: bool = False):
        if is_touched:
            text = f"[bold]{text.upper()}[/bold]"
        return f"[{self.value}]{text}[/{self.value}]"

    @property
    def char_painted(self):
        return f"[{self.value}]{self.char}[/{self.value}]"


class Card(msgspec.Struct, frozen=True):
    color: Color
    number: int
    clues: int = 0

    def to_str(self, touched: bool, colored: bool = True):
        res = f"{self.number}{self.color.char}"
        if colored:
            res = self.color.paint(res, is_touched=touched)
        return res


class Clue(msgspec.Struct):
    to_player: int
    color: Optional[Color]
    number: Optional[int]

    @classmethod
    def new(cls, to_player: int, color: Optional[Color] = None, number: Optional[int] = None):
        return Clue(to_player, color, number)

    @classmethod
    def from_string(cls, to_player: int, clue: str, cards: "CardConfig"):
        try:
            number = int(clue)
            color = None
        except ValueError:
            number = None
            color = Color.parse(clue, cards.colors)
        return Clue(to_player, color, number)

    def touches(self, card: Card) -> bool:
        if self.number is not None and card.number == self.number:
            return True
        if self.color is not None and card.color == self.color:
            return True
        return False

    def get_touched(self, cards: List[Card]) -> List[int]:
        return [i for i, c in enumerate(cards) if self.touches(c)]

    @property
    def value(self):
        return self.number or self.color.paint(self.color.value)  # type: ignore[union-attr]

    def __repr__(self):
        if self.number is not None:
            val = f"num={self.number}"
        elif self.color is not None:
            val = f"col={self.color.char}"
        else:
            val = "???"
        return f"Clue[to={self.to_player},{val}]"


class CardInfo(msgspec.Struct):
    colors: OrderedSet[Color]
    numbers: OrderedSet[int]
    is_touched: bool

    @property
    def number(self) -> Optional[int]:
        if len(self.numbers) == 1:
            return next(iter(self.numbers))
        return None

    @property
    def color(self) -> Optional[Color]:
        if len(self.colors) == 1:
            return next(iter(self.colors))
        return None

    @property
    def is_known(self) -> bool:
        return self.color is not None and self.number is not None

    @classmethod
    def create(cls, card_config: "CardConfig"):
        return CardInfo(
            colors=OrderedSet(card_config.colors),
            numbers=OrderedSet(range(1, card_config.max_number + 1)),
            is_touched=False,
        )

    def to_str(self):
        num = str(self.number or "?")
        if self.color is not None:
            res = num + self.color.char
            if self.is_touched:
                res = res.upper()
            return self.color.paint(res, is_touched=self.is_touched)
        res = num + "?"
        return res

    @overload
    def as_card(self, force: Literal[True] = True) -> Card: ...

    @overload
    def as_card(self, force: Literal[False] = False) -> Optional[Card]: ...

    def as_card(self, force: bool = False) -> Optional[Card]:
        if self.color is not None and self.number is not None:
            return Card(color=self.color, number=self.number)
        if force:
            raise ValueError()
        return None

    def touch(self, clue: Clue):
        if clue.number is not None:
            self.numbers = OrderedSet((clue.number,))
        if clue.color is not None:
            self.colors = OrderedSet((clue.color,))
        self.is_touched = True

    def not_touch(self, clue: Clue):
        if clue.color is not None:
            self.colors.discard(clue.color)
        if clue.number is not None:
            self.numbers.discard(clue.number)

    def iter_possible(self) -> Iterable[Card]:
        for color in self.colors:
            for number in self.numbers:
                yield Card(color=color, number=number)


class CluedCards(msgspec.Struct):
    cards: List[List[CardInfo]]

    def __getitem__(self, item: int) -> List[CardInfo]:
        return self.cards[item]

    @classmethod
    def create(cls, players: int, hand_size: int, card_config: "CardConfig"):
        return CluedCards(cards=[[CardInfo.create(card_config) for _ in range(hand_size)] for _ in range(players)])

    def apply_clue(self, player: int, clue: Clue, touched: List[int]):
        for i, card_info in enumerate(self.cards[player]):
            if i in touched:
                card_info.touch(clue)
            else:
                card_info.not_touch(clue)

    def pop_card(self, player: int, card: int, new: Optional[CardInfo]):
        self.cards[player].pop(card)
        if new is not None:
            self.cards[player].insert(0, new)
