from typing import List

from rich import print

from hanapy.core.action import StateUpdate
from hanapy.core.card import Card, CardInfo
from hanapy.core.config import CardConfig, GameResult
from hanapy.core.player import PlayerView


def print_cards(pos: int, cards: List[Card], infos: List[CardInfo]):
    print(f"[{pos}]", " ".join(c.to_str(infos[i].is_touched) for i, c in enumerate(cards)))


def print_my_cards(view: PlayerView):
    print_card_clues(view.me, view.my_cards)


def print_card_clues(player_num: int, cards: List[CardInfo]):
    print(f"[{player_num}]", " ".join(ci.to_str() for ci in cards))


def print_card_clues_detailed(cards: List[CardInfo], config: CardConfig):
    for i, card in enumerate(cards):
        numbers = "".join(str(n) for n in card.numbers)
        colors = "".join(c.char_painted for c in card.colors)
        print(f"card {i + 1}: {numbers} {colors}")


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


def print_player_view(view: PlayerView, detailed=False):
    print_played_cards(view)
    print_discarded_cards(view)
    print("player cards: ")
    print_players_cards(view)
    print(f"Lives: {view.state.lives_left}, Clues: {view.state.clues_left}, Cards left: {view.state.cards_left}")
    if view.state.cards_left == 0:
        print("Turns left:", view.state.turns_left)
    if detailed:
        for i, cards in enumerate(view.state.clued.cards):
            print_card_clues(i, cards)
            print_card_clues_detailed(cards, view.config.cards)


def print_game_end(view: PlayerView, game_result: GameResult):
    print_player_view(view)
    if game_result.is_win:
        print("[green]YOU WON")
    else:
        print(f"[red]YOU LOOSE {game_result.score}/{game_result.max_score}")


def print_invalid_action(msg: str):
    print(f"[red]Invalid action: {msg}")
