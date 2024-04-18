from typing import List

from aioconsole import ainput

from hanapy.core.action import Action, ClueAction, DiscardAction, PlayAction, StateUpdate
from hanapy.core.card import Card, Color
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView
from hanapy.players.console.render import (
    print_player_view,
    print_update,
)


class ConsolePlayerActor(PlayerActor):
    async def on_game_start(self, view: PlayerView):
        print(f"Game started, it's player {view.state.current_player} turn")
        if view.me != view.state.current_player:
            print_player_view(view)

    async def get_next_action(self, view: PlayerView) -> Action:
        print("-" * 20)
        print("It's your turn\n")
        print_player_view(view)
        action = await self.parse_action_from_input(
            view.me, view.state.config.max_cards, view.cards, view.state.config.colors
        )
        print("-" * 10)
        return action

    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        print_update(update)
        next_player = (update.player + 1) % view.state.config.players
        if next_player != view.me:
            print("-" * 20)
            print(f"It's player {next_player} turn\n")
            print_player_view(view)
        return view.memo

    async def parse_action_from_input(
        self, me: int, max_cards: int, cards: List[List[Card]], colors: List[Color]
    ) -> Action:
        text = f"Enter action (play/discard 1-{max_cards}/clue player_num num/col)\n" + "-" * 10 + "\n"
        while True:
            msg = await ainput(text)
            try:
                return self._parse_msg(msg, me, max_cards, cards, colors)
            except ValueError as e:
                print("error:", e.args[0])

    def _parse_msg(self, msg: str, me: int, max_cards: int, cards, colors: List[Color]) -> Action:
        tokens = msg.split(" ")
        if len(tokens) == 0:
            raise ValueError("no input")
        cmd, *tokens = tokens
        if cmd == "play":
            if len(tokens) != 1:
                raise ValueError("unknown command")
            num_card = int(tokens[0])
            if num_card > max_cards or num_card < 1:
                raise ValueError("wrong card num")
            return PlayAction(player=me, card=num_card - 1)
        if cmd == "discard":
            if len(tokens) != 1:
                raise ValueError("unknown command")
            num_card = int(tokens[0])
            if num_card > max_cards or num_card < 1:
                raise ValueError("wrong card num")
            return DiscardAction(player=me, card=num_card - 1)
        if cmd == "clue":
            # todo validation
            player_num, clue = tokens
            player = int(player_num)
            try:
                number = int(clue)
                color = None
            except ValueError:
                color = Color.parse(char=clue, colors=colors)
                number = None
            return ClueAction(player=me, to_player=player, color=color, number=number)
        raise ValueError(f"unknown cmd {cmd}")
