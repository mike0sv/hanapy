from typing import Optional, Tuple

from hanapy.conventions.cells import ClueTypeCell
from hanapy.core.card import Card, Clue
from hanapy.core.player import PlayerView


class ConventionsView:
    def __init__(self, view: PlayerView):
        self.view = view

    @property
    def me(self):
        return self.view.me

    def chop(self, player: Optional[int] = None):
        player = player or self.view.me
        return next(i for i, card in reversed(list(enumerate(self.view.state.clued[player]))) if not card.is_touched)

    def chop_card(self, player: int) -> Tuple[int, Card]:
        if player == self.view.me:
            raise ValueError()
        chop = self.chop(player)
        return chop, self.view.cards[player][chop]

    def finesse(self, player: Optional[int] = None):
        player = player or self.view.me
        return next(i for i, card in enumerate(self.view.state.clued[player]) if not card.is_touched)

    def get_clue_focus(self, clue: Clue) -> Tuple[int, Card]:
        chop, card = self.chop_card(clue.to_player)
        if clue.touches(card):
            return chop, card

        cards = self.view.cards[clue.to_player]
        touched = clue.get_touched(cards)
        newly_touched = [t for t in touched if not self.view.state.clued[clue.to_player][t].is_touched]
        focus = touched[0] if len(newly_touched) == 0 else newly_touched[0]

        return focus, cards[focus]

    @property
    def clue_type_cell(self) -> ClueTypeCell:
        return self.view.memo.get(ClueTypeCell)

    def can_be_critical(self, focus: int, clue: Clue) -> bool:
        if clue.to_player == self.me:
            raise NotImplementedError
        card = self.view.cards[clue.to_player][focus]
        if self.view.state.played.is_obsolete(card, self.view.config.cards.max_number):
            return False
        discarded = len([c for c in self.view.state.discarded.cards if c == card])
        if discarded + 1 == self.view.config.cards.counts[card.number]:
            return True
        return False

    def is_save_clue(self, clue: Clue) -> Tuple[int, bool]:
        focus, card = self.get_clue_focus(clue)
        if focus != self.chop(clue.to_player):
            return focus, False
        return focus, self.can_be_critical(focus, clue)
