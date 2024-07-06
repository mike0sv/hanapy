from typing import Generic, TypeVar, Union

from hanapy.contrib.hanabi_live.const import COMMAND_ACTION_TYPE_COLOR_CLUE, COMMAND_ACTION_TYPE_RANK_CLUE
from hanapy.contrib.hanabi_live.models import (
    ActionClue,
    ActionDiscard,
    ActionDraw,
    ActionPlay,
    ActionStrike,
    CommandData,
)
from hanapy.core.action import Action, ClueAction
from hanapy.core.card import Card, Color
from hanapy.core.player import PlayerView

_Action = Union[ActionStrike, ActionDraw, ActionPlay, ActionDiscard, ActionClue]

TA = TypeVar("TA", bound=_Action)


class HLAction(Generic[TA]):
    def __init__(self, action: TA):
        self.action = action

    @classmethod
    def from_action_data(cls, data: dict):
        type_ = data["type"]
        action_type, hl_action_type = action_type_mapping[type_]
        return hl_action_type(action=action_type(**data))

    def apply(self, player_view: PlayerView):
        raise NotImplementedError(self.__class__.__name__)


suite_index_color_mapping = {0: "r", 1: "y", 2: "g", 3: "b", 4: "p"}

suite_index_color_mapping_rev = {v: k for k, v in suite_index_color_mapping.items()}


class HLActionDraw(HLAction[ActionDraw]):
    def apply(self, player_view: PlayerView):
        if self.action.playerIndex == player_view.me:
            return
        assert self.action.playerIndex is not None
        player_view.cards[self.action.playerIndex].insert(0, self.get_card(player_view))

    def get_card(self, player_view: PlayerView) -> Card:
        assert self.action.rank is not None
        assert self.action.suitIndex is not None
        return Card(
            number=self.action.rank,
            color=Color.parse(suite_index_color_mapping[self.action.suitIndex], player_view.config.cards.colors),
        )


class HLActionDiscard(HLAction[ActionDiscard]):
    def apply(self, player_view: PlayerView):
        print(self.action)


class HLActionClue(HLAction[ActionClue]):
    def apply(self, player_view: PlayerView):
        print(self.action)


class HLActionPlay(HLAction[ActionPlay]):
    def apply(self, player_view: PlayerView):
        print(self.action)


class HLActionStrike(HLAction[ActionStrike]):
    def apply(self, player_view: PlayerView):
        print(self.action)


action_type_mapping = {
    "draw": (ActionDraw, HLActionDraw),
    "discard": (ActionDiscard, HLActionDiscard),
    "clue": (ActionClue, HLActionClue),
    "play": (ActionPlay, HLActionPlay),
    "strike": (ActionStrike, HLActionStrike),
}


def action_to_command_data(action: Action, table_id: int) -> CommandData:
    if isinstance(action, ClueAction):
        target = action.clue.to_player
        if action.clue.color is not None:
            type_ = COMMAND_ACTION_TYPE_COLOR_CLUE
            value = suite_index_color_mapping_rev[action.clue.color.char]
        else:
            assert action.clue.number is not None
            type_ = COMMAND_ACTION_TYPE_RANK_CLUE
            value = action.clue.number
    else:
        raise NotImplementedError(action.__class__.__name__)
    return CommandData(tableID=table_id, type=type_, target=target, value=value)
