import logging
from typing import List

from hanapy.core.config import DiscardPile, GameConfig, PlayedCards, PublicGameState
from hanapy.core.deck import DeckGenerator
from hanapy.core.errors import InvalidUpdateError
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerState
from hanapy.core.state import GameState

logger = logging.getLogger(__name__)


class BaseGame:
    def get_loop(self) -> "GameLoop":
        raise NotImplementedError


class GameLoop:
    def __init__(self, players: List[PlayerActor], deck_generator: DeckGenerator, config: GameConfig):
        self.player_actors = players
        deck = deck_generator.generate()
        player_states = [
            PlayerState(cards=[deck.draw() for _ in range(config.max_cards)], memo=PlayerMemo())
            for _ in range(len(players))
        ]
        self.state = GameState(
            player_states,
            deck,
            0,
            public=PublicGameState(
                config.max_clues, config.max_lives, PlayedCards(cards={}), DiscardPile(cards=[]), config, len(players)
            ),
        )

    async def run(self) -> None:
        while True:
            current_player_actor = self.player_actors[self.state.current_player]
            current_player_view = self.state.get_current_player_view()
            while True:
                action = await current_player_actor.get_next_action(current_player_view)
                update = action.to_update(self.state)
                try:
                    update.validate(self.state)
                    break
                except InvalidUpdateError as e:
                    print(e.args)
                    continue

            for i, player in enumerate(self.player_actors):
                player_memo = await player.observe_update(self.state.get_player_view(i), update)
                self.state.update_player_memo(i, player_memo)

            update.apply(self.state)
            self.state.next_player()
            if self.state.game_ended:
                break
