from hanapy.players.dummy import DiscardingPlayer
from hanapy.variants.classic import ClassicGame


async def test_classic_game():
    players = [DiscardingPlayer("1"), DiscardingPlayer("1")]
    game = ClassicGame(players)
    loop = game.get_loop()
    loop.data.config.unlimited_clues = True
    await loop.run()

    assert loop.data.deck.is_empty()
