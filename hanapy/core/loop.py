import asyncio
import logging
import os.path
import shutil
import warnings
from copy import deepcopy
from typing import Awaitable, Callable, List, Optional, Sequence

import msgspec
from msgspec import Struct

from hanapy.core.action import Action, StateUpdate
from hanapy.core.config import GameConfig, GameState
from hanapy.core.deck import DeckGenerator
from hanapy.core.errors import InvalidUpdateError
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerState, PlayerView
from hanapy.core.state import GameData
from hanapy.utils.ser import dumps

logger = logging.getLogger(__name__)


class BaseGame:
    def get_loop(self) -> "GameLoop":
        raise NotImplementedError


RandomSeed = Optional[int]
GameVariant = Callable[[Sequence[PlayerActor], RandomSeed], BaseGame]


class TurnLog(Struct):
    turn: int
    data: GameData
    action: Action
    update: StateUpdate


class GameLoop:
    def __init__(self, players: List[PlayerActor], deck_generator: DeckGenerator, config: GameConfig):
        self.player_actors = players
        player_count = len(players)
        if not player_count == config.player_count:
            raise ValueError("Invalid player count")
        deck = deck_generator.generate(config.cards)
        player_states = [
            PlayerState(
                name=p.get_name(), cards=[deck.draw() for _ in range(config.hand_size)], memo=PlayerMemo.create()
            )
            for p in players
        ]
        self.data = GameData(
            players=player_states,
            deck=deck,
            state=GameState.create(config, deck.size()),
            config=config,
        )
        self.logs: List[TurnLog] = []

    def enum_player_views(self):
        yield from ((p, self.data.get_player_view(i)) for i, p in enumerate(self.player_actors))

    async def run(
        self,
        turn_begin_callback: Optional[Callable[[int, PlayerView], Awaitable]] = None,
        turn_end_callback: Optional[Callable[[GameData], Awaitable]] = None,
    ) -> None:
        memos = await asyncio.gather(*[player.on_game_start(view) for player, view in self.enum_player_views()])
        for player, memo in enumerate(memos):
            self.data.update_player_memo(player, memo)

        while True:
            current_player_actor = self.player_actors[self.data.state.current_player]
            current_player_view = self.data.get_current_player_view()

            if turn_begin_callback is not None:
                await turn_begin_callback(self.data.state.current_player, current_player_view)
            while True:
                action = await current_player_actor.get_next_action(current_player_view)
                update = action.to_update(self.data)
                try:
                    update.validate(self.data)
                    break
                except InvalidUpdateError as e:
                    await current_player_actor.on_invalid_action(e.args[0])
                    continue
            await current_player_actor.on_valid_action()
            self.logs.append(
                TurnLog(turn=self.data.state.turn, data=(deepcopy(self.data)), action=action, update=update)
            )
            old_views = [deepcopy(v) for _, v in self.enum_player_views()]
            update.apply(self.data)
            new_memos = await asyncio.gather(
                *[
                    player.observe_update(old_views[i], update, view)
                    for i, (player, view) in enumerate(self.enum_player_views())
                ]
            )
            for player, player_state in enumerate(self.data.players):
                player_state.memo = new_memos[player]

            self.data.next_turn()
            if self.data.game_ended:
                await asyncio.gather(
                    *[
                        player.on_game_end(view, self.data.get_game_result())
                        for player, view in self.enum_player_views()
                    ]
                )
                break
            if turn_end_callback is not None:
                await turn_end_callback(self.data)

    def save_logs(self, log_file: str, as_script: bool, variant, seed, players):
        if log_file.endswith(os.path.sep):
            if as_script:
                warnings.warn("cant save logs as script to directory. specify file", stacklevel=1)
            if os.path.exists(log_file):
                shutil.rmtree(log_file)
            os.makedirs(log_file, exist_ok=True)
            for i, log in enumerate(self.logs, start=1):
                with open(os.path.join(log_file, f"{i}.json"), "wb") as f:
                    f.write(msgspec.json.format(dumps(log), indent=2))
        else:
            if as_script:
                from hanapy.players.scripted import ScriptedGameConfig

                ScriptedGameConfig.from_logs(variant, seed, players, self.logs).write(log_file)
            else:
                with open(log_file, "wb") as f:
                    f.write(msgspec.json.format(dumps(self.logs), indent=2))
