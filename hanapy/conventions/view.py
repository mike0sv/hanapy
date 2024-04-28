from typing import List, Optional, Tuple

from hanapy.conventions.cells import ClueTypeCell, EarlyGameCell
from hanapy.core.action import ClueResult
from hanapy.core.card import Card, CardInfo, Clue
from hanapy.core.player import PlayerView


class ConventionsView:
    def __init__(self, view: PlayerView):
        self.view = view

    @property
    def me(self):
        return self.view.me

    def chop(self, player: Optional[int] = None) -> int:
        player = player or self.view.me
        return next(i for i, card in reversed(list(enumerate(self.view.state.clued[player]))) if not card.is_touched)

    def chop_card(self, player: int) -> Tuple[int, Card]:
        if player == self.view.me:
            raise ValueError()
        chop = self.chop(player)
        return chop, self.view.cards[player][chop]

    def chop_card_info(self, player: int) -> Tuple[int, CardInfo]:
        chop = self.chop(player)
        return chop, self.view.state.clued[player][chop]

    def finesse(self, player: Optional[int] = None):
        player = player or self.view.me
        return next(i for i, card in enumerate(self.view.state.clued[player]) if not card.is_touched)

    def get_clue_focus_card(self, clue: Clue) -> Tuple[int, Card]:
        chop, card = self.chop_card(clue.to_player)
        if clue.touches(card):
            return chop, card

        cards = self.view.cards[clue.to_player]
        touched = clue.get_touched(cards)
        newly_touched = [t for t in touched if not self.view.state.clued[clue.to_player][t].is_touched]
        focus = touched[0] if len(newly_touched) == 0 else newly_touched[0]

        return focus, cards[focus]

    def get_clue_focus(self, clue: ClueResult) -> int:
        chop = self.chop(clue.to_player)
        if chop in clue.touched:
            return chop

        newly_touched = [t for t in clue.touched if not self.view.state.clued[clue.to_player][t].is_touched]
        focus = clue.touched[0] if len(newly_touched) == 0 else newly_touched[0]

        return focus

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
        focus, card = self.get_clue_focus_card(clue)
        if focus != self.chop(clue.to_player):
            return focus, False
        return focus, self.can_be_critical(focus, clue)

    @property
    def is_early_game(self):
        return self.view.memo.get(EarlyGameCell).is_early_game

    def end_early_game(self):
        self.view.memo.get(EarlyGameCell).is_early_game = False

    def is_play_clue_connected(self, clue: Clue):
        if self.is_save_clue(clue):
            return False
        _, card = self.get_clue_focus(clue)
        starting = self.view.state.played.cards[card.color.char]
        if card.number == starting + 1:
            return True

        clued_cards = set(self.get_clued_cards())
        return all(Card(card.color, number) in clued_cards for number in range(starting + 1, card.number))

    def get_clued_cards(self) -> List[Card]:
        res: List[Card] = []
        for player, player_cards in enumerate(self.view.cards):
            if player == self.me:
                res.extend(ci.as_card(True) for ci in self.view.my_cards if ci.is_known)
                continue
            for card_index, card in enumerate(player_cards):
                if self.view.state.clued[player][card_index].is_touched:
                    res.append(card)
        return res

    def get_single_path_len(self, player: int, card_index: int):
        """Get length of path between table and card. If no path or multiple paths return -1"""
        if player != self.me:
            # todo
            raise NotImplementedError

        card_info = self.view.my_cards[card_index]

        clued_cards = set(self.get_clued_cards())

        def _find_path(card: Card) -> Optional[int]:
            starting = self.view.state.played.cards[card.color.char]
            for number in range(starting + 1, card.number):
                if Card(card.color, number) not in clued_cards:
                    return None
            return card.number - starting

        result_path_len = -1
        for c in card_info.iter_possible():
            path = _find_path(c)
            if path is not None:
                if result_path_len != -1 and path != result_path_len:
                    # multiple paths
                    return -1
                result_path_len = path

        return result_path_len
