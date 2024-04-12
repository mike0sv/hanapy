from typing import List

from hanapy.core.deck import DeckGenerator
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerState
from hanapy.core.state import DiscardPile, GameConfig, GameState, PlayedCards


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
            0,
            deck,
            config.max_clues,
            config.max_lives,
            PlayedCards(cards={}),
            DiscardPile(cards=[]),
            config,
            len(players),
        )

    def run(self) -> None:
        while True:
            current_player_actor = self.player_actors[self.state.current_player]
            current_player_view = self.state.get_current_player_view()
            action = current_player_actor.get_next_action(current_player_view)
            update = action.to_update(self.state)
            update.validate(self.state)

            for i, player in enumerate(self.player_actors):
                player_memo = player.observe_update(self.state.get_player_view(i), update)
                self.state.update_player_memo(i, player_memo)

            update.apply(self.state)

            if self.state.game_ended:
                break
