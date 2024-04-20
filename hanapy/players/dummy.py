from hanapy.core.action import Action, DiscardAction, StateUpdate
from hanapy.core.config import GameResult
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView


class DiscardingPlayer(PlayerActor):
    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
        return view.memo

    async def on_game_end(self, view: PlayerView, game_result: GameResult):
        pass

    async def get_next_action(self, view: PlayerView) -> Action:
        return DiscardAction(player=view.me, card=0)

    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        return view.memo
