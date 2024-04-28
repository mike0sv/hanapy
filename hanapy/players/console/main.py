import asyncio

from hanapy.players.console.player import ConsolePlayerActor
from hanapy.variants.classic import ClassicGame


def main():
    players = [ConsolePlayerActor("0"), ConsolePlayerActor("1")]
    game = ClassicGame(players, random_seed=0)
    loop = game.get_loop()
    asyncio.run(loop.run())


if __name__ == "__main__":
    main()
