from typing import List

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
