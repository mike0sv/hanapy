import logging
from typing import List, Type, Union

from hanapy.conventions.cells import ClueTypeCell, EarlyGameCell
from hanapy.conventions.view import ConventionsView
from hanapy.core.action import Action, ClueAction, DiscardAction, PlayAction, StateUpdate
from hanapy.core.card import Clue
from hanapy.core.player import PlayerView

logger = logging.getLogger(__name__)


class RankingConventionsView(ConventionsView):
    def __init__(self, view: PlayerView, conventions: List["RankingConvention"]):
        super().__init__(view)
        self.conventions = conventions

    def has_convention(self, convention: Union[Type["RankingConvention"], "RankingConvention"]) -> bool:
        if isinstance(convention, type):
            return any(isinstance(c, convention) for c in self.conventions)
        return any(c == convention for c in self.conventions)


class RankingConvention:
    def observe(self, view: RankingConventionsView, update: StateUpdate):
        pass

    def score(self, view: RankingConventionsView, action: Action) -> float:
        if isinstance(action, PlayAction):
            return self.score_play(view, action.card)
        if isinstance(action, DiscardAction):
            return self.score_discard(view, action.card)
        if isinstance(action, ClueAction):
            return self.score_clue(view, action.clue)
        raise NotImplementedError

    def score_play(self, view: RankingConventionsView, card: int) -> float:
        return 0.0

    def score_discard(self, view: RankingConventionsView, card: int) -> float:
        return 0.0

    def score_clue(self, view: RankingConventionsView, clue: Clue) -> float:
        return 0.0

    def on_init(self, view: RankingConventionsView):
        pass


class ClassifyClue(RankingConvention):
    def on_init(self, view: RankingConventionsView):
        logger.debug("adding ClueTypeCell")
        view.view.memo.add(ClueTypeCell.create(view.view.config))

    def observe(self, view: RankingConventionsView, update: StateUpdate):
        clue = update.clue
        if clue is not None:
            if clue.to_player == view.view.me:
                self.observe_clue_for_me(view, clue)
            else:
                self.observe_clue(view, clue)

        playerpos = update.discard or update.play
        if playerpos is not None:
            cell = view.clue_type_cell
            cell.pop_card(update.player, playerpos.pos, add_new=(update.new_card is not None))

    def observe_clue_for_me(self, view: RankingConventionsView, clue: Clue):
        pass

    def observe_clue(self, view: RankingConventionsView, clue: Clue):
        focus, is_save = view.is_save_clue(clue)
        if is_save:
            logger.debug("%s is save clue for card %s", clue, focus)
            view.clue_type_cell.set_save(clue.to_player, focus)
        else:
            logger.debug("%s is play clue for card %s", clue, focus)
            view.clue_type_cell.set_play(clue.to_player, focus)


class Chop2IsSave(RankingConvention):
    def observe(self, view: RankingConventionsView, update: StateUpdate):
        clue = update.clue
        if clue is None:
            return
        if clue.number != 2:
            return
        focus = view.get_clue_focus(clue)
        if focus != view.chop(clue.to_player):
            return
        logger.debug("%s is save clue for 2 in chop", clue)
        view.clue_type_cell.set_save(clue.to_player, focus)


class EarlyGame(RankingConvention):
    def on_init(self, view: RankingConventionsView):
        logger.debug("adding EarlyGameCell")
        view.view.memo.add(EarlyGameCell())

    def observe(self, view: RankingConventionsView, update: StateUpdate):
        if update.discard is not None and update.play is None and view.is_early_game:
            logger.debug("early game ended")
            view.end_early_game()


class Stalling5Save(RankingConvention):
    def observe(self, view: RankingConventionsView, update: StateUpdate):
        if not view.has_convention(EarlyGame):
            return
        clue = update.clue
        if clue is None:
            return
        if clue.number != 5 or not view.is_early_game:
            return
        logger.debug("%s is 5 stalling save clue for %s", clue, clue.touched)
        for card in clue.touched:
            view.clue_type_cell.set_save(clue.to_player, card)

    def score_clue(self, view: RankingConventionsView, clue: Clue) -> float:
        if not view.has_convention(EarlyGame):
            return 0
        if clue.number == 5 and view.is_early_game:
            return 50
        return 0


class DiscardFromChop(RankingConvention):
    def score_discard(self, view: RankingConventionsView, card: int) -> float:
        if view.view.state.played.is_obsolete(view.view.my_cards[card], view.view.config.cards.max_number):
            return 100
        return -1000 if card != view.chop() else 0


class NoClueUnplayable(RankingConvention):
    def score_clue(self, view: RankingConventionsView, clue: Clue) -> float:
        card_indexes = clue.get_touched(view.view.cards[clue.to_player])
        cards = [view.view.cards[clue.to_player][i] for i in card_indexes]
        max_number = view.view.config.cards.max_number
        played = view.view.state.played
        if any(played.is_obsolete(c, max_number) for c in cards):
            return -1000
        card_set = set(cards)
        if len(card_set) != len(cards):
            return -1000
        if any(
            card in card_set
            for i, player_cards in enumerate(view.view.cards)
            if i != view.me
            for ic, card in enumerate(player_cards)
            if view.view.state.clued[i][ic].is_touched
        ):
            return -1000
        # todo "maybe" unplayable
        return 0


class PlayOnlyTouched(RankingConvention):
    def score_play(self, view: RankingConventionsView, card: int) -> float:
        if not view.view.my_cards[card].is_touched:
            return -100
        return 0


class PlayOnlyKnown(RankingConvention):
    def score_play(self, view: RankingConventionsView, card: int) -> float:
        if view.view.state.played.is_valid_play(view.view.my_cards[card]):
            return 100
        return 0


class PlayOnlyOnPlayClue(RankingConvention):
    def score_play(self, view: RankingConventionsView, card: int) -> float:
        is_play = view.clue_type_cell.is_play(view.me, card)
        if is_play and view.get_single_path_len(view.me, card) == 1:
            return 100
        if view.clue_type_cell.is_save(view.me, card):
            return -100
        return 0


class PlayClueOnlyConnected(RankingConvention):
    def score_clue(self, view: RankingConventionsView, clue: Clue) -> float:
        is_save = view.is_save_clue(clue)
        if is_save:
            return 0
        if view.is_play_clue_connected(clue):
            return 100
        return -500


# DEFAULT_CONVENTIONS = [ClassifyClue(), DiscardFromChop(), ClueUnplayable()]

DEFAULT_CONVENTIONS = [
    o()
    for o in locals().values()
    if isinstance(o, type) and issubclass(o, RankingConvention) and o != RankingConvention
]

print("[", ", ".join(f"{o.__class__.__name__}()" for o in DEFAULT_CONVENTIONS), "]")
