from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    value: str


@dataclass
class Card:
    color: Color
    number: int
    clues: int = 0
