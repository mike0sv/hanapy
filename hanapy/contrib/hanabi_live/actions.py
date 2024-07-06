from typing import Generic, Optional, TypeVar, Union

from msgspec import convert

from hanapy.contrib.hanabi_live.const import (
    COMMAND_ACTION_TYPE_COLOR_CLUE,
    COMMAND_ACTION_TYPE_DISCARD,
    COMMAND_ACTION_TYPE_PLAY,
    COMMAND_ACTION_TYPE_RANK_CLUE,
)
from hanapy.contrib.hanabi_live.models import (
    ActionClue,
    ActionDiscard,
    ActionDraw,
    ActionPlay,
    ActionStatus,
    ActionStrike,
    ActionTurn,
    CommandData,
)
from hanapy.core.action import Action, ClueAction, ClueResult, DiscardAction, PlayAction, PlayerPosCard, StateUpdate
from hanapy.core.card import Card, CardInfo, Color
from hanapy.core.player import PlayerView

_Action = Union[ActionStrike, ActionDraw, ActionPlay, ActionDiscard, ActionClue, ActionStatus, ActionTurn]

TA = TypeVar("TA", bound=_Action)


class HLAction(Generic[TA]):
    def __init__(self, action: TA):
        self.action = action

    @classmethod
    def from_action_data(cls, data: dict):
        type_ = data["type"]
        action_type, hl_action_type = action_type_mapping[type_]
        return hl_action_type(action=convert(data, action_type))

    def apply(self, player_view: PlayerView, state_update: StateUpdate):
        raise NotImplementedError(self.__class__.__name__)


suite_index_color_mapping = {0: "r", 1: "y", 2: "g", 3: "b", 4: "p"}

suite_index_color_mapping_rev = {v: k for k, v in suite_index_color_mapping.items()}


def get_card(action: Union[ActionPlay, ActionDraw, ActionDiscard], player_view: PlayerView) -> Card:
    assert action.rank is not None
    assert action.suitIndex is not None
    return Card(
        number=action.rank,
        color=Color.parse(suite_index_color_mapping[action.suitIndex], player_view.config.cards.colors),
        order=action.order,
    )


class HLActionDraw(HLAction[ActionDraw]):
    def apply(self, player_view: PlayerView, state_update: StateUpdate):
        player_index = self.action.playerIndex
        assert player_index is not None
        state_update.player = player_index
        player_view.state.clued[player_index].insert(
            0, CardInfo.create(player_view.config.cards, order=self.action.order)
        )
        state_update.new_card_dealed = True
        if player_index == player_view.me:
            return
        card = get_card(self.action, player_view)
        player_view.cards[player_index].insert(0, card)
        state_update.new_card = card


def pop_player_card(player_index: int, card: Card, player_view: PlayerView):
    pos = next(i for i, c in enumerate(player_view.state.clued[player_index]) if c.order == card.order)
    del player_view.state.clued[player_index][pos]
    if player_index != player_view.me:
        del player_view.cards[player_index][pos]
    return pos


class HLActionDiscard(HLAction[ActionDiscard]):
    def apply(self, player_view: PlayerView, state_update: StateUpdate):
        player_index = self.action.playerIndex
        assert player_index is not None
        card = get_card(self.action, player_view)
        player_view.state.discarded.cards.append(card)
        pos = pop_player_card(player_index, card, player_view)
        state_update.discard = PlayerPosCard(player=player_index, pos=pos, card=card)
        state_update.player = player_index


class HLActionStatus(HLAction[ActionStatus]):
    def apply(self, player_view: PlayerView, state_update: StateUpdate):
        action_clues = self.action.clues
        assert action_clues is not None
        state_update.clues = action_clues - player_view.state.clues_left
        player_view.state.clues_left = action_clues


class HLActionClue(HLAction[ActionClue]):
    def apply(self, player_view: PlayerView, state_update: StateUpdate):
        assert self.action.clue is not None
        assert self.action.target is not None
        assert self.action.clue.value is not None
        assert self.action.list is not None
        assert self.action.giver is not None
        is_color_clue = self.action.clue.type == COMMAND_ACTION_TYPE_COLOR_CLUE - 2
        value = self.action.clue.value
        clue = ClueResult(
            to_player=self.action.target,
            color=Color.parse(suite_index_color_mapping[value], player_view.config.cards.colors)
            if is_color_clue
            else None,
            number=None if is_color_clue else value,
            touched=[],
        )
        for i, card in enumerate(player_view.state.clued[self.action.target]):
            if card.order in self.action.list:
                card.touch(clue)
                clue.touched.append(i)
        state_update.clue = clue
        state_update.player = self.action.giver


class HLActionPlay(HLAction[ActionPlay]):
    def apply(self, player_view: PlayerView, state_update: StateUpdate):
        player_index = self.action.playerIndex
        assert player_index is not None
        card = get_card(self.action, player_view)
        player_view.state.played.play(card)
        pos = pop_player_card(player_index, card, player_view)
        state_update.player = player_index
        state_update.play = PlayerPosCard(player=player_index, pos=pos, card=card)


class HLActionStrike(HLAction[ActionStrike]):
    def apply(self, player_view: PlayerView, state_update: StateUpdate):
        state_update.lives -= 1
        player_view.state.lives_left -= 1


class HLActionTurn(HLAction[ActionTurn]):
    def apply(self, player_view: PlayerView, state_update: StateUpdate):
        pass


action_type_mapping = {
    "draw": (ActionDraw, HLActionDraw),
    "discard": (ActionDiscard, HLActionDiscard),
    "clue": (ActionClue, HLActionClue),
    "play": (ActionPlay, HLActionPlay),
    "strike": (ActionStrike, HLActionStrike),
    "status": (ActionStatus, HLActionStatus),
    "turn": (ActionTurn, HLActionTurn),
}


def action_to_command_data(action: Action, table_id: int, player_view: PlayerView) -> CommandData:
    target: Optional[int]
    value: Optional[int]
    if isinstance(action, ClueAction):
        target = action.clue.to_player
        if action.clue.color is not None:
            type_ = COMMAND_ACTION_TYPE_COLOR_CLUE
            value = suite_index_color_mapping_rev[action.clue.color.char]
        else:
            assert action.clue.number is not None
            type_ = COMMAND_ACTION_TYPE_RANK_CLUE
            value = action.clue.number
    elif isinstance(action, PlayAction):
        type_ = COMMAND_ACTION_TYPE_PLAY
        target = player_view.my_cards[action.card].order
        value = None
    elif isinstance(action, DiscardAction):
        type_ = COMMAND_ACTION_TYPE_DISCARD
        target = player_view.my_cards[action.card].order
        value = None
    else:
        raise NotImplementedError(action.__class__.__name__)
    return CommandData(tableID=table_id, type=type_, target=target, value=value)
