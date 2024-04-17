from pprint import pprint
from typing import List

from aioconsole import ainput

from hanapy.core.action import Action, ClueAction, DiscardAction, PlayAction, StateUpdate
from hanapy.core.card import Card, Color
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView
from hanapy.runtime.console.render import print_discarded_cards, print_played_cards, print_players_cards


class ConsolePlayerActor(PlayerActor):
    async def get_next_action(self, view: PlayerView) -> Action:
        print(f"It's {view.name} turn\n")
        print_played_cards(view.state.config, view.state.played_cards)
        print_discarded_cards(view.state.config, view.state.discarded_cards)
        print("player cards: ")
        print_players_cards(view.me, view.state.config.max_cards, view.cards)
        print(f"Lives: {view.state.lives_left}, Clues: {view.state.clues_left}")
        print(f"Enter action (play/discard 1-{view.state.config.max_cards}/clue player_num num/col)")
        print("-" * 10)
        action = await self.parse_action_from_input(view.me, view.state.config.max_cards, view.cards)
        print("-" * 10)
        return action

    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        # pprint(view.to_dict())
        pprint(update.to_dict())
        return view.memo

    async def parse_action_from_input(self, me: int, max_cards: int, cards: List[List[Card]]) -> Action:
        while True:
            msg = await ainput()
            try:
                return self._parse_msg(msg, me, max_cards, cards)
            except ValueError as e:
                print("error:", e.args[0])

    def _parse_msg(self, msg: str, me: int, max_cards: int, cards) -> Action:
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
                color = Color(char=clue)
                number = None
            return ClueAction(player=me, to_player=player, color=color, number=number)
        raise ValueError(f"unknown cmd {cmd}")
