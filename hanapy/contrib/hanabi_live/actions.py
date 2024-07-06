from typing import Generic, TypeVar, Union

from hanapy.contrib.hanabi_live.models import ActionClue, ActionDiscard, ActionDraw, ActionPlay, ActionStrike

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


class HLActionDraw(HLAction[ActionDraw]):
    pass


class HLActionDiscard(HLAction[ActionDiscard]):
    pass


class HLActionClue(HLAction[ActionClue]):
    pass


class HLActionPlay(HLAction[ActionPlay]):
    pass


class HLActionStrike(HLAction[ActionStrike]):
    pass


action_type_mapping = {
    "draw": (ActionDraw, HLActionDraw),
    "discard": (ActionDiscard, HLActionDiscard),
    "clue": (ActionClue, HLActionClue),
    "play": (ActionPlay, HLActionPlay),
    "strike": (ActionStrike, HLActionStrike),
}
