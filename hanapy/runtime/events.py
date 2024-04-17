from typing import ClassVar

from hanapy.core.action import Action, StateUpdate
from hanapy.core.player import PlayerMemo, PlayerView
from hanapy.runtime.types import PlayerID
from hanapy.utils.ser import PolyStruct


class Event(PolyStruct):
    __root__: ClassVar = True

    pid: PlayerID

    def __repr__(self):
        return f"{self.__class__.__name__}[{self.pid}]"


class WaitForActionEvent(Event):
    __typename__: ClassVar = "wait_for_action"

    view: PlayerView


class ActionEvent(Event):
    __typename__: ClassVar = "action"

    action: Action


class ObserveUpdateEvent(Event):
    __typename__: ClassVar = "observe_update"

    view: PlayerView
    update: StateUpdate


class UpdatePlayerMemoEvent(Event):
    __typename__: ClassVar = "update_player_memo"
    memo: PlayerMemo


class RegisterPlayerEvent(Event):
    __typename__: ClassVar = "register_player"


class StartGameEvent(Event):
    __typename__: ClassVar = "start_game"
