from typing import List

from rich import print

from hanapy.core.action import StateUpdate
from hanapy.core.card import Card, CardInfo
from hanapy.core.player import PlayerView


def print_cards(pos: int, cards: List[Card], infos: List[CardInfo]):
    print(f"[{pos}]", " ".join(c.to_str(infos[i].is_touched) for i, c in enumerate(cards)))


def print_my_cards(view: PlayerView):
    print(f"[{view.me}]", " ".join(ci.to_str() for ci in view.state.clued[view.me]))


def print_players_cards(view: PlayerView):
    print_my_cards(view)

    player_count = view.config.player_count
    me = view.me
    for i in range(player_count):
        pos = (i + me) % player_count
        if pos == me:
            continue
        print_cards(pos, view.cards[pos], view.state.clued.cards[pos])


def print_played_cards(view: PlayerView):
    print("played cards")
    for c in view.config.cards.colors:
        print(c.paint(f"{view.state.played.cards.get(c.char, 0)}{c.char}"), end=" ")
    print()


def print_discarded_cards(view: PlayerView):
    print("discarded cards")
    for c in view.config.cards.colors:
        cards = [str(card.number) for card in view.state.discarded.cards if card.color == c]
        if len(cards) > 0:
            print(f"[{c.value}]{c.char}: " + ", ".join(sorted(cards)))


def print_update(update: StateUpdate):
    clue = update.clue
    if clue is not None:
        clued_cards = " ".join(str(c + 1) for c in clue.touched)
        print(f"player {update.player} clues {clue.value} to player {clue.to_player} and touches {clued_cards}")
    if update.clues != 0:
        print(f"Clues {update.clues}")

    play = update.play
    if play is not None:
        print(f"player {play.player} plays {play.card.to_str(False)} from {play.pos + 1}")
    if update.lives != 0:
        print(f"Lives {update.lives}")
    discard = update.discard
    if discard is not None:
        print(f"player {discard.player} discards {discard.card.to_str(False)} from {discard.pos + 1}")


def print_player_view(view: PlayerView):
    print_played_cards(view)
    print_discarded_cards(view)
    print("player cards: ")
    print_players_cards(view)
    print(f"Lives: {view.state.lives_left}, Clues: {view.state.clues_left}, Cards left: {view.state.cards_left}")
    if view.state.cards_left == 0:
        print("Turns left:", view.state.turns_left)


def print_game_end(view: PlayerView, is_win: bool):
    print_player_view(view)
    if is_win:
        print("[green]YOU WON")
    else:
        print("[red]YOU LOOSE")


def print_invalid_action(msg: str):
    print(f"[red]Invalid action: {msg}")
