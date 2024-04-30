from typing import ClassVar, List

from hanapy.core.action import Action, StateUpdate
from hanapy.core.config import GameResult
from hanapy.core.player import PlayerMemo, PlayerView
from hanapy.types import EventHandler, PlayerID
from hanapy.utils.ser import PolyStruct


async def call_handler(event_handler: EventHandler, event: "Event") -> bool:
    res = event_handler(event)
    if not isinstance(res, bool):
        res = await res
    return res


class Event(PolyStruct):
    __root__: ClassVar = True

    pid: PlayerID

    def __str__(self):
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
    new_view: PlayerView
    update: StateUpdate


class UpdatePlayerMemoEvent(Event):
    __typename__: ClassVar = "update_player_memo"
    memo: PlayerMemo


class RegisterPlayerEvent(Event):
    __typename__: ClassVar = "register_player"


class PlayerRegisteredEvent(Event):
    __typename__: ClassVar = "player_registered"
    player_num: int
    players: List[str]


class StartGameEvent(Event):
    __typename__: ClassVar = "start_game"


class GameStartedEvent(Event):
    __typename__: ClassVar = "game_started"

    view: PlayerView


class MemoInitEvent(Event):
    __typename__: ClassVar = "memo_init"
    memo: PlayerMemo


class ConnectionLostEvent(Event):
    __typename__: ClassVar = "connection_lost"


class MessageEvent(Event):
    __typename__: ClassVar = "message"
    text: str


class GameEndedEvent(Event):
    __typename__: ClassVar = "game_ended"
    view: PlayerView
    game_result: GameResult


class ActionVerificationEvent(Event):
    __typename__: ClassVar = "action_verification"

    success: bool
    msg: str
