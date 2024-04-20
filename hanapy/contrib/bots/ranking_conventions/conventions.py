from hanapy.conventions.cells import ClueTypeCell
from hanapy.conventions.view import ConventionsView
from hanapy.core.action import Action, ClueAction, DiscardAction, PlayAction, StateUpdate
from hanapy.core.card import Clue


class RankingConvention:
    def observe(self, view: ConventionsView, update: StateUpdate):
        pass

    def score(self, view: ConventionsView, action: Action) -> float:
        if isinstance(action, PlayAction):
            return self.score_play(view, action.card)
        if isinstance(action, DiscardAction):
            return self.score_discard(view, action.card)
        if isinstance(action, ClueAction):
            return self.score_clue(view, action.clue)
        raise NotImplementedError

    def score_play(self, view: ConventionsView, card: int) -> float:
        return 0.0

    def score_discard(self, view: ConventionsView, card: int) -> float:
        return 0.0

    def score_clue(self, view: ConventionsView, clue: Clue) -> float:
        return 0.0

    def on_init(self, view: ConventionsView):
        pass


class ClassifyClue(RankingConvention):
    def on_init(self, view: ConventionsView):
        view.view.memo.add(ClueTypeCell.create(view.view.config))

    def observe(self, view: ConventionsView, update: StateUpdate):
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

    def observe_clue_for_me(self, view: ConventionsView, clue: Clue):
        pass

    def observe_clue(self, view: ConventionsView, clue: Clue):
        focus, is_save = view.is_save_clue(clue)
        if is_save:
            view.clue_type_cell.set_save(clue.to_player, focus)
        else:
            view.clue_type_cell.set_play(clue.to_player, focus)


class DiscardFromChop(RankingConvention):
    def score_discard(self, view: ConventionsView, card: int) -> float:
        if view.view.state.played.is_obsolete(view.view.my_cards[card], view.view.config.cards.max_number):
            return 100
        return -1000 if card != view.chop() else 0


class ClueUnplayable(RankingConvention):
    def score_clue(self, view: ConventionsView, clue: Clue) -> float:
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
        return 0


DEFAULT_CONVENTIONS = [ClassifyClue(), DiscardFromChop(), ClueUnplayable()]
