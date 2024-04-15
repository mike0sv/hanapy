from typing import ClassVar

from hanapy.core.action import Action, StateUpdate
from hanapy.core.player import PlayerMemo, PlayerView
from hanapy.utils.ser import PolyStruct


class Event(PolyStruct):
    __root__: ClassVar = True

    uid: str


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
