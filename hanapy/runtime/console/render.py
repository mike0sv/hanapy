from typing import List

from hanapy.core.action import StateUpdate
from hanapy.core.card import Card
from hanapy.core.config import DiscardPile, GameConfig, PlayedCards


def print_cards(pos: int, cards: List[Card]):
    print(f"[{pos}]", " ".join(f"{c.number}{c.color.char}" for c in cards))


def print_players_cards(me: int, max_cards: int, cards: List[List[Card]]):
    print(f"[{me}]", "?? " * max_cards)
    players = len(cards)
    for i in range(players):
        pos = (i + me) % players
        if pos == me:
            continue
        print_cards(pos, cards[pos])


def print_played_cards(config: GameConfig, cards: PlayedCards):
    print("played cards")
    for c in config.colors:
        print(f"{c.char}{cards.cards.get(c.char, 0)}", end=" ")
    print()


def print_discarded_cards(config: GameConfig, pile: DiscardPile):
    print("discarded cards")
    for c in config.colors:
        cards = [str(card.number) for card in pile.cards if card.color == c]
        if len(cards) > 0:
            print(f"{c.char}: " + ", ".join(sorted(cards)))


def print_update(update: StateUpdate):
    clue = update.clue
    if clue is not None:
        print(f"player {clue.player} clues {clue.number or clue.color} to player {clue.to_player}")
    if update.clues != 0:
        print(f"Clues {update.clues}")

    play = update.play
    if play is not None:
        print(f"player {play.player} plays {play.card} from {play.pos}")
    if update.lives != 0:
        print(f"Lives {update.lives}")
    discard = update.discard
    if discard is not None:
        print(f"player {discard.player} discards {discard.card} from {discard.pos}")
