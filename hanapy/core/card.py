import msgspec


class Color(msgspec.Struct, frozen=True):
    char: str
    value: str = ""


class Card(msgspec.Struct):
    color: Color
    number: int
    clues: int = 0

    def __repr__(self):
        return f"{self.number}{self.color.char}"

    # def __init__(self, color: Color, number: int, clues: int = 0):
    #     super().__init__(color=color, number=number,clues=clues)
