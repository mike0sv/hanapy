from hanapy.players.dummy import DiscardingPlayer
from hanapy.variants.classic import ClassicGame


def test_classic_game():
    players = [DiscardingPlayer(), DiscardingPlayer()]
    game = ClassicGame(players)
    loop = game.get_loop()
    loop.state.config.unlimited_clues = True
    loop.run()

    assert loop.state.deck.is_empty()
