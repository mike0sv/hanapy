import random
from functools import partial
from typing import Sequence

from hanapy.core.card import Card
from hanapy.core.config import GameConfig
from hanapy.core.deck import Deck, DeckGenerator
from hanapy.core.loop import BaseGame, GameLoop
from hanapy.core.player import PlayerActor
from hanapy.variants.classic import CLASSIC_COLORS


class SmolDeckGenerator(DeckGenerator):
    def __init__(self, max_colors: int, max_number: int):
        self.max_number = max_number
        self.max_colors = max_colors

    def generate(self) -> Deck:
        cards = []
        for col in CLASSIC_COLORS[: self.max_colors]:
            cards.extend([Card(col, 1)] * 3)
            if self.max_number > 1:
                cards.extend([Card(col, self.max_number, 1)] * 1)
            for i in range(2, self.max_number):
                cards.extend([Card(col, i)] * 2)

        random.shuffle(cards)
        return Deck(cards=cards)


class SmolGame(BaseGame):
    def __init__(self, players: Sequence[PlayerActor], max_colors: int, max_number: int):
        self.max_colors = max_colors
        self.max_number = max_number
        self.players = list(players)

    @classmethod
    def variant(cls, max_colors: int, max_number: int):
        return partial(cls, max_colors=max_colors, max_number=max_number)

    def get_loop(self) -> "GameLoop":
        player_num = len(self.players)
        if player_num < 2 or player_num > 5:
            pass
            # raise ValueError()
        return GameLoop(
            self.players,
            SmolDeckGenerator(self.max_colors, self.max_number),
            GameConfig(
                max_lives=3,
                max_cards=self.max_colors,
                players=player_num,
                max_clues=8,
                num_colors=self.max_colors,
                max_card_number=self.max_number,
                colors=CLASSIC_COLORS[: self.max_colors],
            ),
        )
