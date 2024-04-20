from typing import List

from hanapy.core.config import GameConfig
from hanapy.core.player import MemoCell


class ClueTypeCell(MemoCell):
    play: List[List[bool]]
    save: List[List[bool]]

    @classmethod
    def create(cls, config: GameConfig):
        hand_size = config.hand_size
        return ClueTypeCell(
            play=[[False for _ in range(hand_size)] for _ in range(config.player_count)],
            save=[[False for _ in range(hand_size)] for _ in range(config.player_count)],
        )

    def set_play(self, player: int, card: int):
        self.play[player][card] = True

    def set_save(self, player: int, card: int):
        self.save[player][card] = True

    def pop_card(self, player: int, card: int, add_new: bool):
        self.play[player].pop(card)
        self.save[player].pop(card)
        if add_new:
            self.play[player].insert(0, False)
            self.save[player].insert(0, False)
