import asyncio

from hanapy.runtime.console.player import ConsolePlayerActor
from hanapy.variants.classic import ClassicGame


def main():
    players = [ConsolePlayerActor(), ConsolePlayerActor()]
    game = ClassicGame(players)
    loop = game.get_loop()
    asyncio.run(loop.run())


if __name__ == "__main__":
    main()
