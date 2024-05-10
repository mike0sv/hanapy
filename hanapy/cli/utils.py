import logging
from typing import Optional

import typer

from hanapy.contrib.bots import BOTS
from hanapy.core.loop import GameVariant
from hanapy.core.player import PlayerActor
from hanapy.utils.log import init_logger
from hanapy.variants import VARIANTS


async def setup_debug(debug: bool):
    level = logging.DEBUG if debug else logging.CRITICAL
    await init_logger(level)


def get_variant(variant: str) -> GameVariant:
    game_variant = VARIANTS.get(variant)
    if game_variant is None:
        raise typer.BadParameter(f"No such game variant '{variant}'. Possible values: {list(VARIANTS)}")
    return game_variant


def get_player(player: str, name: Optional[str] = None) -> PlayerActor:
    bot_impl = BOTS.get(player)
    if bot_impl is None:
        raise typer.BadParameter(f"No such bot '{player}'. Possible values: {list(BOTS)}")
    return bot_impl(name or player)
