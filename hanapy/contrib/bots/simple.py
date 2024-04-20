import logging
from functools import partial

from hanapy.contrib.bots.base import BaseBotPlayer
from hanapy.core.action import Action, ClueAction, DiscardAction, PlayAction
from hanapy.core.card import Clue
from hanapy.core.player import PlayerView

logger = logging.getLogger(__name__)


class SimpleBotPlayer(BaseBotPlayer):
    @classmethod
    def bot(cls, log: bool):
        return partial(SimpleBotPlayer, log=log)

    async def get_next_action(self, view: PlayerView) -> Action:  # noqa: C901
        can_discard = view.state.clues_left < view.config.max_clues
        can_clue = view.state.clues_left > 0
        # if have known playable cards, play them
        for i, card_info in enumerate(view.my_cards):
            if can_discard and view.state.played.is_obsolete(card_info, view.config.cards.max_number):
                return DiscardAction(player=view.me, card=i)
            if view.state.played.is_valid_play(card_info):
                return PlayAction(player=view.me, card=i)

        # if any player have single
        if can_clue:
            for player, cards in enumerate(view.cards):
                if player == view.me:
                    continue
                for card in cards:
                    if not view.state.played.is_valid_play(card):
                        continue
                    color_clue = Clue(to_player=player, color=card.color, number=None)
                    if len(color_clue.get_touched(cards)) == 1:
                        return ClueAction(player=view.me, clue=color_clue)
                    number_clue = Clue(to_player=player, number=card.number, color=None)
                    if all(view.state.played.is_valid_play(cards[t]) for t in number_clue.get_touched(cards)):
                        return ClueAction(player=view.me, clue=number_clue)

        if can_discard:
            card_index = 0
            for i, c in enumerate(view.my_cards):
                if not c.is_touched:
                    card_index = i
            return DiscardAction(player=view.me, card=card_index)
        return PlayAction(player=view.me, card=1)
