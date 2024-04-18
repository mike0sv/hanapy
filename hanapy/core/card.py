from typing import List, Optional

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

    def paint(self, text: str, touched: bool = False):
        if touched:
            text = f"[bold]{text.upper()}[/bold]"
        return f"[{self.value}]{text}[/{self.value}]"


class Card(msgspec.Struct):
    color: Color
    number: int
    clues: int = 0

    def to_str(self, touched: bool):
        res = self.color.paint(f"{self.number}{self.color.char}", touched=touched)
        return res


class CardInfo(msgspec.Struct):
    color: Optional[Color]
    number: Optional[int]

    @classmethod
    def none(cls):
        return CardInfo(color=None, number=None)

    def to_str(self):
        num = str(self.number or "?")
        if self.color is not None:
            res = num + self.color.char
            if self.touched:
                res = res.upper()
            return self.color.paint(res, touched=self.touched)
        res = num + "?"
        return res

    @property
    def touched(self):
        return bool(self.number or self.color)

    def as_card(self) -> Optional[Card]:
        if self.color is not None and self.number is not None:
            return Card(color=self.color, number=self.number)
        return None
