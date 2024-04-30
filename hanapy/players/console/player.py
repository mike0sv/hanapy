from typing import Any, List, Optional

from aioconsole import ainput

from hanapy.core.action import Action, StateUpdate
from hanapy.core.config import GameResult
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView
from hanapy.core.state import GameData
from hanapy.players.console.commands import DEFAULT_COMMANDS, ActionCommand, Command, CommandParseError, match_command
from hanapy.players.console.event_handlers import CONSOLE_EVENT_HANDLERS
from hanapy.players.console.render import (
    print_game_end,
    print_invalid_action,
    print_player_view,
    print_update,
)
from hanapy.types import EventHandlers


class ConsolePlayerActor(PlayerActor):
    def __init__(self, name: str, commands: Optional[List[Command]] = None):
        super().__init__(name)
        self.commands = commands or DEFAULT_COMMANDS

    def get_event_handlers(self) -> EventHandlers:
        return CONSOLE_EVENT_HANDLERS

    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
        print(f"Game started, it's player {view.state.current_player} turn")
        if view.me != view.state.current_player:
            print_player_view(view)
        return view.memo

    async def get_next_action(self, view: PlayerView) -> Action:
        print("-" * 20)
        print_player_view(view)
        action = await self.parse_action_from_input(view)
        print("-" * 10)
        return action

    async def observe_update(self, view: PlayerView, update: StateUpdate, new_view: PlayerView) -> PlayerMemo:
        print_update(update)
        next_player = (update.player + 1) % view.config.player_count
        if next_player != view.me:
            print("-" * 20)
            print_player_view(new_view)
            print(f"It's player {next_player} turn")
        return view.memo

    async def on_game_end(self, view: PlayerView, game_result: GameResult):
        print_game_end(view, game_result)

    async def on_invalid_action(self, msg: str):
        print_invalid_action(msg)

    async def parse_action_from_input(self, view: PlayerView) -> Action:
        command: Command
        param: Any
        text = "Enter action (type `help` for help)\n" + "-" * 10 + "\n"
        while True:
            try:
                cmd = await ainput(text)
                command, param = match_command(cmd, view, self.commands)
                if isinstance(command, ActionCommand):
                    return command.get_action(view, param)
                command.execute(view, param)
            except (CommandParseError, UnicodeDecodeError) as e:
                print("error:", e.args[0])


async def wait_input_callback(game_data: GameData):
    await ainput()


async def print_player_view_callback(me: int, view: PlayerView):
    print_player_view(view, detailed=True)
