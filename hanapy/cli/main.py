import asyncio
from functools import wraps

from typer import Option, Typer

from hanapy.runtime.asyncio import AsyncClient, AsyncServer
from hanapy.runtime.base import DEFAULT_HOST, DEFAULT_PORT
from hanapy.runtime.console.player import ConsolePlayerActor
from hanapy.runtime.players import ClientPlayerProxy

app = Typer(pretty_exceptions_enable=False)

# logging.basicConfig(level=logging.DEBUG)


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
):
    if serve:
        await AsyncServer(host, port).start(name)

    player = ConsolePlayerActor()
    client = ClientPlayerProxy(name, AsyncClient(host, port), player)

    await client.run(is_host=serve)


def main():
    app()


if __name__ == "__main__":
    main()
