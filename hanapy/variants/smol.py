from functools import partial
from typing import Sequence

from hanapy.core.config import CardConfig
from hanapy.core.player import PlayerActor
from hanapy.variants.classic import CLASSIC_COLORS, ClassicGame


class SmolGame(ClassicGame):
    def __init__(self, players: Sequence[PlayerActor], max_colors: int, max_number: int):
        super().__init__(players)
        self.max_colors = max_colors
        self.max_number = max_number

    @classmethod
    def variant(cls, max_colors: int, max_number: int):
        return partial(cls, max_colors=max_colors, max_number=max_number)

    def get_card_config(self) -> CardConfig:
        counts = {i: 2 for i in range(1, self.max_number)}
        counts[1] = 3
        counts[self.max_number] = 1

        return CardConfig(counts=counts, colors=CLASSIC_COLORS[: self.max_colors])
