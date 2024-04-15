import msgspec

from hanapy.utils.ser import PolyStruct


class Color(msgspec.Struct, frozen=True):
    char: str
    value: str = ""


class Card(PolyStruct):
    color: Color
    number: int
    clues: int = 0
