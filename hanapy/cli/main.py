import asyncio
import logging
from functools import wraps

from typer import Option, Typer

from hanapy.players.console.event_handlers import CONSOLE_EVENT_HANDLERS
from hanapy.players.console.player import ConsolePlayerActor
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


@app.command()
@run_async
async def run(
    name: str = Option(),
    serve: bool = Option(False),
    host: str = Option(DEFAULT_HOST),
    port: int = Option(DEFAULT_PORT),
    debug: bool = Option(False, "-d"),
):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    if serve:
        await AsyncServer(host, port).start(name)

    player = ConsolePlayerActor()
    client = AsyncClient(host, port)
    client.add_event_handlers(CONSOLE_EVENT_HANDLERS)
    player_proxy = ClientPlayerProxy(name, client, player)

    try:
        await player_proxy.run(is_host=serve)
    except EventWaitAborted:
        print("exiting")


def main():
    app()


if __name__ == "__main__":
    main()
