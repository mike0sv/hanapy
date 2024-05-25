import logging
from functools import partial
from typing import List, Optional

from hanapy.contrib.bots import ranking_conventions
from hanapy.contrib.bots.base import BaseBotPlayer
from hanapy.contrib.bots.ranking_conventions.conventions import (
    DEFAULT_CONVENTIONS,
    RankingConvention,
    RankingConventionsView,
)
from hanapy.contrib.bots.utils import get_possible_actions
from hanapy.core.action import Action, StateUpdate
from hanapy.core.player import PlayerMemo, PlayerView

logger = logging.getLogger(__name__)


class ActionScore:
    def __init__(self, action: Action):
        self.action = action
        self.conventions: List[RankingConvention] = []
        self.scores: List[float] = []

    def add(self, view: RankingConventionsView, convention: RankingConvention):
        self.conventions.append(convention)
        self.scores.append(convention.score(view, self.action))

    @property
    def score(self):
        return sum(self.scores, 0)

    def get_detailed_repr(self) -> str:
        return " ".join(
            f"{c.__class__.__name__}: {score}" for c, score in zip(self.conventions, self.scores) if score != 0
        )


class RankingConventionsBotPlayer(BaseBotPlayer):
    def __init__(self, name: str, conventions: List[RankingConvention], log: bool = False):
        super().__init__(name, log)
        self.conventions = conventions
        if log:
            logging.getLogger(ranking_conventions.__name__).setLevel(logging.DEBUG)

    @classmethod
    def bot(cls, log: bool, conventions: Optional[List[RankingConvention]] = None):
        return partial(RankingConventionsBotPlayer, conventions=conventions or DEFAULT_CONVENTIONS, log=log)

    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
        logger.debug("[%s] Initializing conventions: %s", view.me, [c.__class__.__name__ for c in self.conventions])
        conview = RankingConventionsView(view, self.conventions, True)
        for convention in self.conventions:
            convention.on_init(conview)
        return view.memo

    async def get_next_action(self, view: PlayerView) -> Action:
        possible_actions = [ActionScore(action) for action in get_possible_actions(view)]
        conview = RankingConventionsView(view, self.conventions, is_observing=False)
        logger.debug("[%s] Scoring possible actions", view.me)
        for action_score in possible_actions:
            for convention in self.conventions:
                action_score.add(conview, convention)

        sorted_actions = sorted(possible_actions, key=lambda x: (-x.score, str(x.action)))
        if self.log:
            for action_score in sorted_actions:
                logger.debug(
                    "[%s] %s %s %s", view.me, action_score.action, action_score.score, action_score.get_detailed_repr()
                )
        logger.debug("[%s] Best action: %s", view.me, sorted_actions[0].action)
        return sorted_actions[0].action

    async def observe_update(self, view: PlayerView, update: StateUpdate, new_view: PlayerView) -> PlayerMemo:
        logger.debug("[%s] Observing update: %s", view.me, update)
        conview = RankingConventionsView(view, self.conventions, is_observing=True)
        for convention in self.conventions:
            convention.observe(conview, update)
        return view.memo
