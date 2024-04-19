from aioconsole import ainput

from hanapy.core.action import Action, ClueAction, DiscardAction, PlayAction, StateUpdate
from hanapy.core.card import Clue, Color
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView
from hanapy.players.console.event_handlers import CONSOLE_EVENT_HANDLERS
from hanapy.players.console.render import (
    print_game_end,
    print_invalid_action,
    print_player_view,
    print_update,
)
from hanapy.types import EventHandlers


class ConsolePlayerActor(PlayerActor):
    def get_event_handlers(self) -> EventHandlers:
        return CONSOLE_EVENT_HANDLERS

    async def on_game_start(self, view: PlayerView):
        print(f"Game started, it's player {view.state.current_player} turn")
        if view.me != view.state.current_player:
            print_player_view(view)

    async def get_next_action(self, view: PlayerView) -> Action:
        print("-" * 20)
        print_player_view(view)
        action = await self.parse_action_from_input(view)
        print("-" * 10)
        return action

    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        print_update(update)
        next_player = (update.player + 1) % view.config.player_count
        if next_player != view.me:
            print("-" * 20)
            print_player_view(view)
            print(f"It's player {next_player} turn")
        return view.memo

    async def on_game_end(self, view: PlayerView, is_win: bool):
        print_game_end(view, is_win)

    async def on_invalid_action(self, msg: str):
        print_invalid_action(msg)

    async def parse_action_from_input(self, view: PlayerView) -> Action:
        hand_size = view.config.hand_size
        text = f"Enter action (play/discard 1-{hand_size}/clue player_num num/col)\n" + "-" * 10 + "\n"
        while True:
            try:
                msg = await ainput(text)
                return self._parse_msg(msg, view)
            except (ValueError, UnicodeDecodeError) as e:
                print("error:", e.args[0])

    def _parse_msg(self, msg: str, view: PlayerView) -> Action:
        tokens = msg.split(" ")
        if len(tokens) == 0:
            raise ValueError("no input")
        cmd, *tokens = tokens
        if cmd == "play":
            if len(tokens) != 1:
                raise ValueError("unknown command")
            num_card = int(tokens[0])
            if num_card > view.config.hand_size or num_card < 1:
                raise ValueError("wrong card num")
            return PlayAction(player=view.me, card=num_card - 1)
        if cmd == "discard":
            if len(tokens) != 1:
                raise ValueError("unknown command")
            num_card = int(tokens[0])
            if num_card > view.config.hand_size or num_card < 1:
                raise ValueError("wrong card num")
            return DiscardAction(player=view.me, card=num_card - 1)
        if cmd == "clue":
            # todo validation
            player_num, clue = tokens
            player = int(player_num)
            try:
                number = int(clue)
                color = None
            except ValueError:
                color = Color.parse(char=clue, colors=view.config.cards.colors)
                number = None
            return ClueAction(player=view.me, clue=Clue(to_player=player, color=color, number=number))
        raise ValueError(f"unknown cmd {cmd}")
