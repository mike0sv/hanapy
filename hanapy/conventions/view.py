from collections import defaultdict
from copy import deepcopy
from functools import wraps
from typing import Dict, List, Optional, Tuple

from hanapy.conventions.cells import ClueTypeCell, EarlyGameCell
from hanapy.core.action import ClueResult, PlayerPosCard
from hanapy.core.card import Card, CardInfo, Clue, Color
from hanapy.core.player import PlayerView

NO_CHOP = -999
NO_CARD = Card(number=-999, color=Color(char=""))


def observing_only(f):
    @wraps(f)
    def inner(*args, **kwargs):
        self: ConventionsView = args[0]
        if not self.is_observing:
            raise AttributeError(f"{f.__name__} can be called only when observing updates")
        return f(*args, **kwargs)

    return inner


def scoring_only(f):
    @wraps(f)
    def inner(self: "ConventionsView", *args, **kwargs):
        if self.is_observing:
            raise AttributeError(f"{f.__name__} can be called only when scoring actions")
        return f(self, *args, **kwargs)

    return inner


class ConventionsView:
    def __init__(self, view: PlayerView, is_observing: bool):
        self.view = view
        self.is_observing = is_observing

    @property
    def me(self):
        return self.view.me

    def chop(self, player: Optional[int] = None) -> int:
        player = player if player is not None else self.view.me
        try:
            return next(
                i for i, card in reversed(list(enumerate(self.view.state.clued[player]))) if not card.is_touched
            )
        except StopIteration:
            return NO_CHOP

    def chop_card(self, player: int) -> Tuple[int, Card]:
        if player == self.view.me:
            raise ValueError()
        chop = self.chop(player)
        if chop == NO_CHOP:
            return chop, NO_CARD
        return chop, self.view.cards[player][chop]

    def chop_card_info(self, player: int) -> Tuple[int, CardInfo]:
        chop = self.chop(player)
        return chop, self.view.state.clued[player][chop]

    def finesse(self, player: Optional[int] = None):
        player = player or self.view.me
        return next(i for i, card in enumerate(self.view.state.clued[player]) if not card.is_touched)

    def get_clue_focus_card(self, clue: Clue) -> Tuple[int, Card]:
        chop, card = self.chop_card(clue.to_player)
        if chop != NO_CHOP and clue.touches(card):
            return chop, card

        cards = self.view.cards[clue.to_player]
        touched = clue.get_touched(cards)
        newly_touched = [t for t in touched if not self.view.state.clued[clue.to_player][t].is_touched]
        focus = touched[0] if len(newly_touched) == 0 else newly_touched[0]

        return focus, cards[focus]

    def get_clue_focus(self, clue: Clue) -> int:
        chop = self.chop(clue.to_player)
        touched = clue.touched if isinstance(clue, ClueResult) else clue.get_touched(self.view.cards[clue.to_player])
        if chop in touched:
            return chop

        newly_touched = [t for t in touched if not self.view.state.clued[clue.to_player][t].is_touched]
        focus = touched[0] if len(newly_touched) == 0 else newly_touched[0]

        return focus

    @property
    def clue_type_cell(self) -> ClueTypeCell:
        return self.view.memo.get(ClueTypeCell)

    def _can_be_critical(self, card: Card) -> bool:
        if self.view.state.played.is_obsolete(card, self.view.config.cards.max_number):
            return False
        if self.view.config.cards.counts[card.number] == 1:
            return True  # ???
        discarded = len([c for c in self.view.state.discarded.cards if c == card])
        if discarded + 1 == self.view.config.cards.counts[card.number]:
            return True
        return False

    def can_be_critical(self, focus: int, clue: Clue) -> bool:
        if clue.to_player == self.me:
            card_info = deepcopy(self.view.my_cards[focus])
            card_info.touch(clue)
            return any(
                self._can_be_critical(card) and not self.view.state.played.is_valid_play(card)
                for card in card_info.iter_possible()
            )
        card = self.view.cards[clue.to_player][focus]
        return self._can_be_critical(card)

    def is_save_clue(self, clue: Clue) -> bool:
        focus = self.get_clue_focus(clue)
        if focus != self.chop(clue.to_player):
            return False
        return self.can_be_critical(focus, clue)

    @property
    def is_early_game(self):
        return self.view.memo.get(EarlyGameCell).is_early_game

    def end_early_game(self):
        self.view.memo.get(EarlyGameCell).is_early_game = False

    def is_play_clue_connected(self, clue: Clue, all_connecting_are_play: bool):
        if self.is_save_clue(clue):
            return False
        _, card = self.get_clue_focus_card(clue)
        starting = self.view.state.played.cards[card.color.char]
        if card.number == starting + 1:
            return True

        clued_cards: Dict[Card, List[PlayerPosCard]] = defaultdict(list)
        for ppc in self.get_clued_cards():
            clued_cards[ppc.card].append(ppc)
        clue_type_cell = self.view.memo.get(ClueTypeCell)
        for number in range(starting + 1, card.number):
            next_card = Card(card.color, number)
            if next_card not in clued_cards:
                return False
            if not all_connecting_are_play:
                continue
            card_pos = clued_cards[next_card]
            if all(not clue_type_cell.is_play(ppc.player, ppc.pos) for ppc in card_pos):
                return False
        return True

    def get_clued_cards(self) -> List[PlayerPosCard]:
        res: List[PlayerPosCard] = []
        for player, player_cards in enumerate(self.view.cards):
            if player == self.me:
                res.extend(
                    PlayerPosCard(player, i, ci.as_card(True)) for i, ci in enumerate(self.view.my_cards) if ci.is_known
                )
                continue
            for card_index, card in enumerate(player_cards):
                if self.view.state.clued[player][card_index].is_touched:
                    res.append(PlayerPosCard(player, card_index, card))
        return res

    def get_single_path_len(self, player: int, card_index: int):
        """Get length of path between table and card. If no path or multiple paths return -1"""
        if player != self.me:
            # todo
            raise NotImplementedError

        card_info = self.view.my_cards[card_index]

        clued_cards = {ppc.card for ppc in self.get_clued_cards()}

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
