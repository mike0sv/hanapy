from typing import List, Optional, Union

import msgspec


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


class Card(msgspec.Struct):
    color: Color
    number: int
    clues: int = 0

    def to_str(self, touched: bool):
        res = self.color.paint(f"{self.number}{self.color.char}", is_touched=touched)
        return res


class Clue(msgspec.Struct):
    to_player: int
    color: Optional[Color]
    number: Optional[int]

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


class CardInfo(msgspec.Struct):
    color: Optional[Color] = None
    number: Optional[int] = None

    def to_str(self):
        num = str(self.number or "?")
        if self.color is not None:
            res = num + self.color.char
            if self.is_touched:
                res = res.upper()
            return self.color.paint(res, is_touched=self.is_touched)
        res = num + "?"
        return res

    @property
    def is_touched(self):
        return bool(self.number or self.color)

    def as_card(self) -> Optional[Card]:
        if self.color is not None and self.number is not None:
            return Card(color=self.color, number=self.number)
        return None

    def touch(self, clue: Clue):
        self.color = self.color or clue.color
        self.number = self.number or clue.number


class CluedCards(msgspec.Struct):
    cards: List[List[CardInfo]]

    def __getitem__(self, item: int) -> List[CardInfo]:
        return self.cards[item]

    @classmethod
    def create(cls, players: int, max_cards: int):
        return CluedCards(cards=[[CardInfo() for _ in range(max_cards)] for _ in range(players)])

    def touch(self, player: int, clue: Clue, card: Union[int, List[int]]):
        for c in (card,) if isinstance(card, int) else card:
            self.cards[player][c].touch(clue)

    def pop_card(self, player: int, card: int, add_new: bool):
        self.cards[player].pop(card)
        if add_new:
            self.cards[player].insert(0, CardInfo())
