import random
from typing import List

from hanapy.core.card import Card, Color
from hanapy.core.deck import Deck, DeckGenerator
from hanapy.core.loop import BaseGame, GameLoop
from hanapy.core.player import PlayerActor
from hanapy.core.state import GameConfig

CLASSIC_COLORS = [Color("red"), Color("green"), Color("blue"), Color("yellow"), Color("purple")]


class ClassicDeckGenerator(DeckGenerator):
    def generate(self) -> Deck:
        cards = []
        for col in CLASSIC_COLORS:
            cards.extend([Card(col, 1)] * 3)
            cards.extend([Card(col, 2)] * 2)
            cards.extend([Card(col, 3)] * 2)
            cards.extend([Card(col, 4)] * 2)
            cards.extend([Card(col, 5, 1)] * 1)
        random.shuffle(cards)
        return Deck(cards=cards)


class ClassicGame(BaseGame):
    def __init__(self, players: List[PlayerActor]):
        self.players = players

    def get_loop(self) -> "GameLoop":
        player_num = len(self.players)
        if player_num < 2 or player_num > 5:
            raise ValueError()
        return GameLoop(
            self.players,
            ClassicDeckGenerator(),
            GameConfig(3, {2: 5, 3: 5, 4: 4, 5: 3}[player_num], player_num, 8, 5, 5),
        )
