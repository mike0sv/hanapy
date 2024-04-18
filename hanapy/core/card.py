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

    def paint(self, text: str):
        return f"[{self.value}]{text}[/{self.value}]"


class Card(msgspec.Struct):
    color: Color
    number: int
    clues: int = 0

    def __repr__(self):
        return self.color.paint(f"{self.number}{self.color.char}")
