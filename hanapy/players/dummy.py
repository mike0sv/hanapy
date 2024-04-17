from hanapy.core.action import Action, DiscardAction, StateUpdate
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView


class DiscardingPlayer(PlayerActor):
    async def get_next_action(self, view: PlayerView) -> Action:
        return DiscardAction(player=view.me, card=0)

    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        return view.memo
