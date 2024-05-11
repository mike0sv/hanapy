import asyncio
from functools import wraps
from typing import List, Optional

import typer
from typer import Argument, Option, Typer

from hanapy.cli.utils import get_player, get_variant, setup_debug
from hanapy.players.console.player import ConsolePlayerActor, print_player_view_callback, wait_input_callback
from hanapy.players.scripted import ScriptedGameConfig
from hanapy.runtime.asyncio import AsyncClient, AsyncServer
from hanapy.runtime.base import DEFAULT_HOST, DEFAULT_PORT
from hanapy.runtime.buffers import EventWaitAborted
from hanapy.runtime.players import ClientPlayerProxy

app = Typer(pretty_exceptions_enable=False)


def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        async def coro_wrapper():
            return await func(*args, **kwargs)

        return asyncio.run(coro_wrapper())

    return wrapper


@app.command("play")
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
    log: Optional[str] = Option(None, "-l", "--log"),
):
    await setup_debug(debug)
    game_variant = get_variant(variant)
    player = get_player(bot, name=name) if bot is not None else ConsolePlayerActor(name)

    if serve:
        server = AsyncServer(host, port)
        await server.start(name, game_variant, random_seed=seed, log_file=log)

    client = AsyncClient(host, port)
    client.add_event_handlers(player.get_event_handlers())
    player_proxy = ClientPlayerProxy(name, client, player)

    try:
        await player_proxy.run(is_host=serve, auto_start_players=auto_start_players)
    except EventWaitAborted:
        print("exiting")


@app.command("replay")
@run_async
async def replay_script(
    script_file: str = Argument(),
    debug: bool = Option(False, "-d"),
    pause: bool = Option(False),
):
    await setup_debug(debug)
    script = ScriptedGameConfig.from_yaml(script_file)
    game_variant = get_variant(script.variant)
    player_actors = [p.to_player() for p in script.players]

    game = game_variant(player_actors, script.seed)
    loop = game.get_loop()

    await loop.run(
        turn_begin_callback=print_player_view_callback if pause else None,
        turn_end_callback=wait_input_callback if pause else None,
    )


@app.command("local")
@run_async
async def play_local(
    variant: str = Option("classic"),
    debug: bool = Option(False, "-d"),
    seed: Optional[int] = Option(None, "-s", "--seed"),
    players: List[str] = Option(..., "-p", "--player"),  # noqa: B008
    pause: bool = Option(False),
    log: Optional[str] = Option(None, "-l", "--log"),
):
    await setup_debug(debug)
    game_variant = get_variant(variant)
    if len(players) < 2:
        raise typer.BadParameter("Should be at least 2 players")
    player_actors = [get_player(p, name=f"[{i}]{p}") for i, p in enumerate(players)]

    game = game_variant(player_actors, seed)
    loop = game.get_loop()

    await loop.run(
        turn_begin_callback=print_player_view_callback if pause else None,
        turn_end_callback=wait_input_callback if pause else None,
    )
    if log is not None:
        loop.save_logs(log)


def main():
    app()


if __name__ == "__main__":
    main()
