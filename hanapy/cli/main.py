import asyncio
import logging
from functools import wraps
from typing import Optional

import typer
from typer import Option, Typer

from hanapy.contrib.bots import BOTS
from hanapy.players.console.player import ConsolePlayerActor
from hanapy.runtime.asyncio import AsyncClient, AsyncServer
from hanapy.runtime.base import DEFAULT_HOST, DEFAULT_PORT
from hanapy.runtime.buffers import EventWaitAborted
from hanapy.runtime.players import ClientPlayerProxy
from hanapy.variants import VARIANTS

app = Typer(pretty_exceptions_enable=False)


def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        async def coro_wrapper():
            return await func(*args, **kwargs)

        return asyncio.run(coro_wrapper())

    return wrapper


@app.command()
@run_async
async def run(
    name: str = Option(),
    serve: bool = Option(False),
    host: str = Option(DEFAULT_HOST),
    port: int = Option(DEFAULT_PORT),
    variant: str = Option("classic"),
    bot: Optional[str] = Option(None),
    debug: bool = Option(False, "-d"),
):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    game_variant = VARIANTS.get(variant)
    if game_variant is None:
        raise typer.BadParameter(f"No such game variant '{variant}'. Possible values: {list(VARIANTS)}")
    if bot is not None:
        bot_impl = BOTS.get(bot)
        if bot_impl is None:
            raise typer.BadParameter(f"No such bot '{bot}'. Possible values: {list(BOTS)}")
        player = bot_impl()
    else:
        player = ConsolePlayerActor()

    if serve:
        await AsyncServer(host, port).start(name, game_variant)

    client = AsyncClient(host, port)
    client.add_event_handlers(player.get_event_handlers())
    player_proxy = ClientPlayerProxy(name, client, player)

    try:
        await player_proxy.run(is_host=serve)
    except EventWaitAborted:
        print("exiting")


def main():
    app()


if __name__ == "__main__":
    main()
