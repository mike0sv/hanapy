from typing import Dict

from hanapy.contrib.bots.ranking_conventions.bot import RankingConventionsBotPlayer
from hanapy.contrib.bots.simple import SimpleBotPlayer
from hanapy.core.player import Bot

BOTS: Dict[str, Bot] = {
    "simple": SimpleBotPlayer,
    "simple_log": SimpleBotPlayer.bot(log=True),
    "rank_conv_log": RankingConventionsBotPlayer.bot(log=True),
}
