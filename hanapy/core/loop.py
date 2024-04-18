import asyncio
import logging
from typing import Callable, List, Sequence

from hanapy.core.config import DiscardPile, GameConfig, PlayedCards, PublicGameState
from hanapy.core.deck import DeckGenerator
from hanapy.core.errors import InvalidUpdateError
from hanapy.core.player import CommonMemo, PlayerActor, PlayerMemo, PlayerState
from hanapy.core.state import GameState

logger = logging.getLogger(__name__)


class BaseGame:
    def get_loop(self) -> "GameLoop":
        raise NotImplementedError


GameVariant = Callable[[Sequence[PlayerActor]], BaseGame]


class GameLoop:
    def __init__(self, players: List[PlayerActor], deck_generator: DeckGenerator, config: GameConfig):
        self.player_actors = players
        deck = deck_generator.generate()
        player_states = [
            PlayerState(cards=[deck.draw() for _ in range(config.max_cards)], memo=PlayerMemo.create(config.max_cards))
            for _ in range(len(players))
        ]
        self.state = GameState(
            players=player_states,
            deck=deck,
            memo=CommonMemo.create(len(players), config.max_cards),
            public=PublicGameState(
                clues_left=config.max_clues,
                lives_left=config.max_lives,
                played_cards=PlayedCards(cards={c.char: 0 for c in config.colors}),
                discarded_cards=DiscardPile(cards=[]),
                config=config,
                turns_left=len(players),
                current_player=0,
                cards_left=deck.size(),
            ),
        )

    def enum_player_views(self):
        yield from ((p, self.state.get_player_view(i)) for i, p in enumerate(self.player_actors))

    async def run(self) -> None:
        await asyncio.gather(*[player.on_game_start(view) for player, view in self.enum_player_views()])

        while True:
            current_player_actor = self.player_actors[self.state.public.current_player]
            current_player_view = self.state.get_current_player_view()
            while True:
                action = await current_player_actor.get_next_action(current_player_view)
                update = action.to_update(self.state)
                try:
                    update.validate(self.state)
                    break
                except InvalidUpdateError as e:
                    await current_player_actor.on_invalid_action(e.args[0])
                    continue
            await current_player_actor.on_valid_action()
            update.apply(self.state)
            # todo: do we send old state or new state or both?
            await asyncio.gather(*[player.observe_update(view, update) for player, view in self.enum_player_views()])

            self.state.next_player()
            if self.state.game_ended:
                await asyncio.gather(
                    *[player.on_game_end(view, self.state.game_winned) for player, view in self.enum_player_views()]
                )
                break
