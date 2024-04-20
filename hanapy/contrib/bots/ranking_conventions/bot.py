import logging
from functools import partial
from typing import List, Optional

from hanapy.contrib.bots.base import BaseBotPlayer
from hanapy.contrib.bots.ranking_conventions.conventions import DEFAULT_CONVENTIONS, RankingConvention
from hanapy.contrib.bots.utils import get_possible_actions
from hanapy.conventions.view import ConventionsView
from hanapy.core.action import Action, StateUpdate
from hanapy.core.player import PlayerMemo, PlayerView

logger = logging.getLogger(__name__)


class ActionScore:
    def __init__(self, action: Action):
        self.action = action
        self.score = 0.0


class RankingConventionsBotPlayer(BaseBotPlayer):
    def __init__(self, name: str, conventions: List[RankingConvention], log: bool = False):
        super().__init__(name, log)
        self.conventions = conventions

    @classmethod
    def bot(cls, log: bool, conventions: Optional[List[RankingConvention]] = None):
        return partial(RankingConventionsBotPlayer, conventions=conventions or DEFAULT_CONVENTIONS, log=log)

    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
        conview = ConventionsView(view)
        for convention in self.conventions:
            convention.on_init(conview)
        return view.memo

    async def get_next_action(self, view: PlayerView) -> Action:
        possible_actions = [ActionScore(action) for action in get_possible_actions(view)]
        conview = ConventionsView(view)
        for action_score in possible_actions:
            for convention in self.conventions:
                action_score.score += convention.score(conview, action_score.action)

        sorted_actions = sorted(possible_actions, key=lambda x: -x.score)
        if self.log:
            for action_score in sorted_actions:
                print(action_score.action, action_score.score)
        return sorted_actions[0].action

    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        conview = ConventionsView(view)
        for convention in self.conventions:
            convention.observe(conview, update)
        return view.memo
