import re
from abc import ABC, abstractmethod
from typing import ClassVar, Generic, List, Optional, Tuple, TypeVar

from rich import print

from hanapy.core.action import Action, ClueAction, DiscardAction, PlayAction
from hanapy.core.card import Clue, Color
from hanapy.core.errors import HanapyError
from hanapy.core.player import PlayerView
from hanapy.players.console.render import print_card_clues, print_card_clues_detailed, print_player_view

CP = TypeVar("CP")


class CommandParseError(HanapyError):
    def __init__(self, cmd: str, reason: str, command: Optional["Command"]):
        self.cmd = cmd
        self.command = command
        self.reason = reason
        super().__init__(reason)


class Command(ABC, Generic[CP]):
    prefix: ClassVar[str]
    arg_count: ClassVar[int]
    arg_help: ClassVar[str] = ""
    help_msg: ClassVar[str]

    def get_help(self):
        return f"[bold]{self.prefix}[/bold] [white]{self.arg_help}[/white] | {self.help_msg}"

    def match(self, cmd: str) -> Optional[List[str]]:
        if not cmd.startswith(self.prefix):
            return None
        cmd, *args = re.split(r"\s+", cmd)
        if cmd != self.prefix:
            return None
        if len(args) != self.arg_count:
            raise CommandParseError(cmd, f"wrong number of args for {self.prefix} command", self)
        return args

    @abstractmethod
    def try_parse(self, cmd: str, view: PlayerView) -> Optional[CP]:
        raise NotImplementedError

    @abstractmethod
    def execute(self, view: PlayerView, params: CP):
        raise NotImplementedError


def match_command(cmd: str, view: PlayerView, commands: List[Command]) -> Tuple[Command[CP], CP]:
    for c in commands:
        param = c.try_parse(cmd, view)
        if param is not None:
            return c, param
    raise CommandParseError(cmd, f"Unknown command {cmd}", None)


class HelpCommand(Command[bool]):
    prefix = "help"
    arg_count = 0
    help_msg = "print this help"

    def __init__(self, commands: List[Command]):
        self.commands = commands

    def try_parse(self, cmd: str, view: PlayerView) -> Optional[bool]:
        match = self.match(cmd)
        if match is None:
            return None
        return True

    def execute(self, view: PlayerView, params: CP):
        print("Available commands: ")
        for c in self.commands:
            print(f" - {c.get_help()}")
        print("-" * 10)


class ActionCommand(Command[CP], Generic[CP]):
    def execute(self, view: PlayerView, params: CP):
        return

    @abstractmethod
    def get_action(self, view: PlayerView, params: CP) -> Action:
        raise NotImplementedError


class ClueActionCommand(ActionCommand[Clue]):
    prefix = "clue"
    arg_count = 2
    arg_help = "<player> <number/color>"
    help_msg = "give clue to player. examples: `clue 1 r` or `clue 0 3`"

    def try_parse(self, cmd: str, view: PlayerView) -> Optional[Clue]:
        match = self.match(cmd)
        if match is None:
            return None
        player, clue = match
        try:
            player_num = int(player)
        except ValueError:
            raise CommandParseError(cmd, f"wrong player {player}", self) from None
        if player_num == view.me or player_num < 0 or player_num >= view.config.player_count:
            raise CommandParseError(cmd, f"wrong player {player}", self)
        try:
            number = int(clue)
            color = None
        except ValueError:
            try:
                color = Color.parse(char=clue, colors=view.config.cards.colors)
            except ValueError:
                raise CommandParseError(cmd, f"wrong color/number value {clue}", self) from None
            number = None
        return Clue(to_player=player_num, color=color, number=number)

    def get_action(self, view: PlayerView, params: Clue) -> Action:
        return ClueAction(player=view.me, clue=params)


class CardNumAction(ActionCommand[int]):
    arg_count = 1
    arg_help = "<position>"

    def try_parse(self, cmd: str, view: PlayerView) -> Optional[int]:
        match = self.match(cmd)
        if match is None:
            return None
        c = match[0]
        if not c.isnumeric():
            raise CommandParseError(cmd, f"wrong card number {c}", self)
        num_card = int(c)
        if num_card > view.config.hand_size or num_card < 1:
            raise CommandParseError(cmd, f"wrong card number {c}", self)
        return num_card - 1


class PlayActionCommand(CardNumAction):
    prefix = "play"
    help_msg = "play card from position"

    def get_action(self, view: PlayerView, params: int) -> Action:
        return PlayAction(player=view.me, card=params)


class DiscardActionCommand(CardNumAction):
    prefix = "discard"
    help_msg = "discard card from position"

    def get_action(self, view: PlayerView, params: int) -> Action:
        return DiscardAction(player=view.me, card=params)


class ViewCluesCommand(Command[int]):
    prefix = "view"
    arg_count = 1
    arg_help = "<player>"
    help_msg = "view <player> clues"

    def try_parse(self, cmd: str, view: PlayerView) -> Optional[int]:
        match = self.match(cmd)
        if match is None:
            return None
        player = match[0]
        try:
            player_num = int(player)
        except ValueError:
            raise CommandParseError(cmd, f"wrong player {player}", self) from None
        if player_num < 0 or player_num >= view.config.player_count:
            raise CommandParseError(cmd, f"wrong player {player}", self)
        return player_num

    def execute(self, view: PlayerView, params: int):
        cards = view.state.clued[params]
        print_card_clues(params, cards)
        print_card_clues_detailed(cards, view.config.cards)


class CleanCommand(Command[bool]):
    prefix = "clean"
    arg_count = 0
    help_msg = "print game state"

    def try_parse(self, cmd: str, view: PlayerView) -> Optional[bool]:
        match = self.match(cmd)
        if match is None:
            return None
        return True

    def execute(self, view: PlayerView, params: CP):
        print("-" * 20)
        print_player_view(view)


DEFAULT_COMMANDS: List[Command] = [
    ClueActionCommand(),
    PlayActionCommand(),
    DiscardActionCommand(),
    ViewCluesCommand(),
    CleanCommand(),
]
DEFAULT_COMMANDS.insert(0, HelpCommand(DEFAULT_COMMANDS))
