from typing import Dict

from hanapy.contrib.bots.ranking_conventions.bot import RankingConventionsBotPlayer
from hanapy.contrib.bots.simple import SimpleBotPlayer
from hanapy.core.player import Bot
from hanapy.players.console.player import ConsolePlayerActor

BOTS: Dict[str, Bot] = {
    "console": ConsolePlayerActor,
    "simple": SimpleBotPlayer,
    "simple_log": SimpleBotPlayer.bot(log=True),
    "rank_conv": RankingConventionsBotPlayer.bot(log=False),
    "rank_conv_log": RankingConventionsBotPlayer.bot(log=True),
}
