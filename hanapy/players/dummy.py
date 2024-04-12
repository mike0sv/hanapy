from hanapy.core.action import Action, DiscardAction, StateUpdate
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView


class DiscardingPlayer(PlayerActor):
    def get_next_action(self, view: PlayerView) -> Action:
        return DiscardAction(view.me, 0)

    def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        return view.memo
