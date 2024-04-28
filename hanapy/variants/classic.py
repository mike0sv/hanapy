import random
from typing import Optional, Sequence

from hanapy.core.card import Card, Color
from hanapy.core.config import CardConfig, GameConfig
from hanapy.core.deck import Deck, DeckGenerator
from hanapy.core.loop import BaseGame, GameLoop
from hanapy.core.player import PlayerActor

CLASSIC_COLORS = [
    Color("r", "red"),
    Color("g", "green"),
    Color("b", "blue"),
    Color("y", "yellow"),
    Color("p", "purple"),
]


class ClassicDeckGenerator(DeckGenerator):
    def __init__(self, random_seed: Optional[int] = None):
        self.random_state = random_seed

    def generate(self, config: CardConfig) -> Deck:
        cards = []
        for col in config.colors:
            for num, count in config.counts.items():
                cards.extend([Card(col, num)] * count)

        if self.random_state is not None:
            random.seed(self.random_state)
        random.shuffle(
            cards,
        )
        return Deck(cards=cards)


class ClassicGame(BaseGame):
    def __init__(self, players: Sequence[PlayerActor], random_seed: Optional[int]):
        self.random_seed = random_seed
        self.players = list(players)

    def get_card_config(self) -> CardConfig:
        return CardConfig(colors=CLASSIC_COLORS, counts={1: 3, 2: 2, 3: 2, 4: 2, 5: 1})

    def get_hand_size(self, player_count: int):
        return {1: 5, 2: 5, 3: 5, 4: 4, 5: 3}[player_count]

    def get_loop(self) -> "GameLoop":
        player_count = len(self.players)
        if player_count < 2 or player_count > 5:
            pass
            # raise ValueError()
        cards = self.get_card_config()
        return GameLoop(
            self.players,
            ClassicDeckGenerator(self.random_seed),
            GameConfig(
                max_lives=3,
                hand_size=self.get_hand_size(player_count),
                player_count=player_count,
                max_clues=8,
                cards=cards,
            ),
        )
