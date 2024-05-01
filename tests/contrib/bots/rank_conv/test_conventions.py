from hanapy.contrib.bots.ranking_conventions.conventions import PlayClueOnlyConnected, RankingConventionsView
from hanapy.conventions.cells import ClueTypeCell
from hanapy.core.card import Clue
from tests.contrib.conftest import Cards, Games, Views


def test_no_connecting_through_self():
    conv = PlayClueOnlyConnected()

    game = Games.classic(3)
    config = game.get_game_config()
    p1cards, p1infos = Cards.hand(
        "2y,1y,5r,3r,2r", [Clue.from_string(1, "r", config.cards), Clue.from_string(1, "y", config.cards)], config.cards
    )
    view = Views.create(config)
    cell = ClueTypeCell.create(config)
    cell.set_play(1, 1)
    view.memo.add(cell)
    view.cards[1] = p1cards
    view.state.clued.cards[1] = p1infos
    view.state.played.play(Cards.parse_card("1r", config.cards.colors))
    conview = RankingConventionsView(view, [], False)

    clue = Clue(to_player=1, number=3, color=None)
    assert conv.score_clue(conview, clue) == -500
