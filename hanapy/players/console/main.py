import asyncio

from hanapy.players.console.player import ConsolePlayerActor
from hanapy.variants.classic import ClassicGame


def main():
    players = [ConsolePlayerActor(), ConsolePlayerActor()]
    game = ClassicGame(players)
    loop = game.get_loop()
    asyncio.run(loop.run())


if __name__ == "__main__":
    main()
