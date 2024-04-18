from typing import List

from rich import print

from hanapy.core.action import StateUpdate
from hanapy.core.card import Card
from hanapy.core.config import DiscardPile, GameConfig, PlayedCards
from hanapy.core.player import PlayerMemo, PlayerView


def print_cards(pos: int, cards: List[Card], touched: List[bool]):
    print(f"[{pos}]", " ".join(c.to_str(touched[i]) for i, c in enumerate(cards)))


def print_my_cards(me: int, memo: PlayerMemo):
    print(f"[{me}]", " ".join(ci.to_str() for ci in memo.info.cards))


def print_players_cards(me: int, max_cards: int, cards: List[List[Card]], memo: PlayerMemo, touched: List[List[bool]]):
    print_my_cards(me, memo)
    players = len(cards)
    for i in range(players):
        pos = (i + me) % players
        if pos == me:
            continue
        print_cards(pos, cards[pos], touched[pos])


def print_played_cards(config: GameConfig, cards: PlayedCards):
    print("played cards")
    for c in config.colors:
        print(c.paint(f"{cards.cards.get(c.char, 0)}{c.char}"), end=" ")
    print()


def print_discarded_cards(config: GameConfig, pile: DiscardPile):
    print("discarded cards")
    for c in config.colors:
        cards = [str(card.number) for card in pile.cards if card.color == c]
        if len(cards) > 0:
            print(f"[{c.value}]{c.char}: " + ", ".join(sorted(cards)))


def print_update(update: StateUpdate):
    clue = update.clue
    if clue is not None:
        clue_value = clue.number or clue.color.paint(clue.color.value)
        clued_cards = " ".join(str(c + 1) for c in update.clue_touched)
        print(f"player {clue.player} clues {clue_value} to player {clue.to_player} and touches {clued_cards}")
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
    print_played_cards(view.state.config, view.state.played_cards)
    print_discarded_cards(view.state.config, view.state.discarded_cards)
    print("player cards: ")
    print_players_cards(view.me, view.state.config.max_cards, view.cards, view.memo, view.common_memo.touched)
    print(f"Lives: {view.state.lives_left}, Clues: {view.state.clues_left}, Cards left: {view.state.cards_left}")
    if view.state.cards_left == 0:
        print("Turns left:", view.state.turns_left)


def print_game_end(view: PlayerView, is_win: bool):
    print_player_view(view)
    if is_win:
        print("[green]YOU WON")
    else:
        print("[red]YOU LOOSE")
