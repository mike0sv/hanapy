import asyncio
import logging
from typing import Callable, List, Optional, Sequence

from hanapy.core.card import CluedCards
from hanapy.core.config import DiscardPile, GameConfig, GameState, PlayedCards
from hanapy.core.deck import DeckGenerator
from hanapy.core.errors import InvalidUpdateError
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerState
from hanapy.core.state import GameData

logger = logging.getLogger(__name__)


class BaseGame:
    def get_loop(self) -> "GameLoop":
        raise NotImplementedError


RandomSeed = Optional[int]
GameVariant = Callable[[Sequence[PlayerActor], RandomSeed], BaseGame]


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
            state=GameState(
                clues_left=config.max_clues,
                lives_left=config.max_lives,
                clued=CluedCards.create(player_count, config.hand_size, config.cards),
                played=PlayedCards.empty(config.cards.colors),
                discarded=DiscardPile.new(),
                turns_left=player_count,
                current_player=0,
                cards_left=deck.size(),
            ),
            config=config,
        )

    def enum_player_views(self):
        yield from ((p, self.data.get_player_view(i)) for i, p in enumerate(self.player_actors))

    async def run(self) -> None:
        memos = await asyncio.gather(*[player.on_game_start(view) for player, view in self.enum_player_views()])
        for player, memo in enumerate(memos):
            self.data.update_player_memo(player, memo)

        while True:
            current_player_actor = self.player_actors[self.data.state.current_player]
            current_player_view = self.data.get_current_player_view()
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
            update.apply(self.data)
            # todo: do we send old state or new state or both?
            await asyncio.gather(*[player.observe_update(view, update) for player, view in self.enum_player_views()])

            self.data.next_player()
            if self.data.game_ended:
                await asyncio.gather(
                    *[
                        player.on_game_end(view, self.data.get_game_result())
                        for player, view in self.enum_player_views()
                    ]
                )
                break
