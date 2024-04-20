from typing import Iterable

from hanapy.core.action import Action, ClueAction, DiscardAction, PlayAction
from hanapy.core.card import Clue
from hanapy.core.player import PlayerView


def get_possible_actions(view: PlayerView) -> Iterable[Action]:
    yield from (PlayAction(player=view.me, card=i) for i in range(len(view.my_cards)))
    yield from (DiscardAction(player=view.me, card=i) for i in range(len(view.my_cards)))

    for i, other_player in enumerate(view.cards):
        if i == view.me:
            continue
        all_colors = {c.color for c in other_player}
        yield from (ClueAction(player=view.me, clue=Clue(to_player=i, color=c, number=None)) for c in all_colors)
        all_numbers = {c.number for c in other_player}
        yield from (ClueAction(player=view.me, clue=Clue(to_player=i, color=None, number=n)) for n in all_numbers)
