import asyncio
import logging
from functools import wraps
from typing import List, Optional

import typer
from typer import Option, Typer

from hanapy.cli.utils import get_player, get_variant, setup_debug
from hanapy.players.console.player import ConsolePlayerActor
from hanapy.runtime.asyncio import AsyncClient, AsyncServer
from hanapy.runtime.base import DEFAULT_HOST, DEFAULT_PORT
from hanapy.runtime.buffers import EventWaitAborted
from hanapy.runtime.players import ClientPlayerProxy

logging.basicConfig(level=logging.CRITICAL)

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
async def play(
    name: str = Option(),
    serve: bool = Option(False),
    host: str = Option(DEFAULT_HOST),
    port: int = Option(DEFAULT_PORT),
    variant: str = Option("classic"),
    bot: Optional[str] = Option(None),
    debug: bool = Option(False, "-d"),
    seed: Optional[int] = Option(None, "-s", "--seed"),
    auto_start_players: Optional[int] = Option(None, "-a", "--autostart"),
):
    setup_debug(debug)
    game_variant = get_variant(variant)
    player = get_player(bot, name=name) if bot is not None else ConsolePlayerActor(name)

    if serve:
        await AsyncServer(host, port).start(name, game_variant, random_seed=seed)

    client = AsyncClient(host, port)
    client.add_event_handlers(player.get_event_handlers())
    player_proxy = ClientPlayerProxy(name, client, player)

    try:
        await player_proxy.run(is_host=serve, auto_start_players=auto_start_players)
    except EventWaitAborted:
        print("exiting")


@app.command("local")
@run_async
async def play_local(
    variant: str = Option("classic"),
    debug: bool = Option(False, "-d"),
    seed: Optional[int] = Option(None, "-s", "--seed"),
    players: List[str] = Option(..., "-p", "--player"),  # noqa: B008
):
    setup_debug(debug)
    game_variant = get_variant(variant)
    if len(players) < 2:
        raise typer.BadParameter("Should be at least 2 players")
    player_actors = [get_player(p, name=f"[{i}]{p}") for i, p in enumerate(players)]

    game = game_variant(player_actors, seed)
    loop = game.get_loop()
    await loop.run()


def main():
    app()


if __name__ == "__main__":
    main()
