from typing import Any, Callable, List, Optional

import msgspec.yaml
from msgspec import Struct

from hanapy.contrib.bots import BOTS
from hanapy.core.action import Action, StateUpdate
from hanapy.core.config import GameResult
from hanapy.core.loop import TurnLog
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView
from hanapy.players.console.commands import (
    ActionCommand,
    ClueActionCommand,
    Command,
    CommandParseError,
    DiscardActionCommand,
    PlayActionCommand,
    match_command,
)

GetActionByTurn = Callable[[PlayerView], Optional[Action]]


class ScriptedPlayerActor(PlayerActor):
    def __init__(self, player: PlayerActor, actions: GetActionByTurn):
        super().__init__(player.name)
        self.player = player
        self.actions = actions

    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
        return await self.player.on_game_start(view)

    async def get_next_action(self, view: PlayerView) -> Action:
        scripted = self.actions(view)
        if scripted is not None:
            return scripted
        return await self.player.get_next_action(view)

    async def observe_update(self, view: PlayerView, update: StateUpdate, new_view: PlayerView) -> PlayerMemo:
        return await self.player.observe_update(view, update, new_view)

    async def on_game_end(self, view: PlayerView, game_result: GameResult):
        return await self.player.on_game_end(view, game_result)


class ScriptedPlayerConfig(Struct):
    player: str
    actions: List[str]
    name: Optional[str] = None

    def to_player(self) -> PlayerActor:
        if self.player not in BOTS:
            raise ValueError(f"Unknown player '{self.player}'. Possible values: {list(BOTS)}")
        player = BOTS[self.player](self.name or self.player)
        return ScriptedPlayerActor(player, actions=SciptedPlayerActionsList(self.actions))

    @classmethod
    def from_logs(cls, player: str, logs: List[TurnLog]):
        return ScriptedPlayerConfig(player=player, actions=[log.action.as_command() for log in logs])


class SciptedPlayerActionsList:
    def __init__(self, actions: List[str]):
        self.actions = actions
        self.commands: List[Command] = [PlayActionCommand(), DiscardActionCommand(), ClueActionCommand()]

    def __call__(self, view: PlayerView) -> Optional[Action]:
        cmd: Command
        param: Any
        cmd_num = (view.state.turn - 1) // view.config.player_count
        if cmd_num >= len(self.actions):
            return None
        try:
            cmd, param = match_command(self.actions[cmd_num], view, self.commands)
        except CommandParseError as e:
            raise ValueError(
                f"Could not parse command '{self.actions[cmd_num]}' for player {view.me} on turn {view.state.turn}"
            ) from e

        assert isinstance(cmd, ActionCommand)
        return cmd.get_action(view, param)


class ScriptedGameConfig(Struct):
    players: List[ScriptedPlayerConfig]
    seed: int
    variant: str

    @classmethod
    def from_yaml(cls, path: str):
        with open(path) as f:
            return msgspec.yaml.decode(f.read(), type=cls)

    @classmethod
    def from_logs(cls, variant: str, seed: int, players: List[str], logs: List[TurnLog]):
        if len(logs) == 0:
            raise ValueError("Logs are empty")
        config = logs[0].data.config

        return ScriptedGameConfig(
            variant=variant,
            seed=seed,
            players=[
                ScriptedPlayerConfig.from_logs(player, logs[i :: config.player_count])
                for i, player in enumerate(players)
            ],
        )

    def write(self, path: str):
        with open(path, "wb") as f:
            f.write(msgspec.yaml.encode(self))
