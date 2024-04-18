from typing import Dict

from hanapy.contrib.bots.simple import SimpleBotPlayer
from hanapy.core.player import Bot

BOTS: Dict[str, Bot] = {"simple": SimpleBotPlayer, "simple_log": SimpleBotPlayer.bot(log=True)}
