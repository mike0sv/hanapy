from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from hanapy.core.card import Card, Color
from hanapy.core.errors import InvalidUpdateError

if TYPE_CHECKING:
    from hanapy.core.state import GameState


@dataclass
class ActionResult:
    life_lost: bool
    clues_change: int = 0


@dataclass
class PlayerPos:
    player: int
    pos: int


@dataclass
class PlayerPosCard(PlayerPos):
    card: Card


@dataclass
class StateUpdate:
    lives: int = 0
    clues: int = 0
    discard: Optional[PlayerPosCard] = None
    play: Optional[PlayerPosCard] = None
    new_card: Optional[Card] = None
    clue: Optional["ClueAction"] = None

    def apply(self, state: "GameState") -> None:
        state.lives_left += self.lives
        state.clues_left += self.clues
        player: Optional[int] = None
        if self.discard is not None:
            player = self.discard.player
            del state.players[player].cards[self.discard.pos]
            state.discarded_cards.cards.append(self.discard.card)
        if self.play is not None:
            player = self.play.player
            del state.players[player].cards[self.play.pos]
            state.played_cards.play(self.play.card)
        if self.new_card is not None:
            # assert player is not None
            # assert new_card == self.new_card
            new_card = state.deck.draw()
            state.players[player].cards.append(new_card)

        if state.deck.is_empty():
            state.turns_left -= 1

    def validate(self, state: "GameState") -> None:
        new_clues = state.clues_left + self.clues
        if new_clues < 0 or (new_clues > state.config.max_clues and not state.config.unlimited_clues):
            raise InvalidUpdateError("clues")
        new_lives = state.lives_left + self.lives
        if new_lives < 0 or new_lives > state.config.max_lives:
            raise InvalidUpdateError("lives")

        if self.new_card is not None and self.new_card != state.deck.peek():
            raise InvalidUpdateError("newcard")

        if self.new_card is not None and self.play is None and self.discard is None:
            raise InvalidUpdateError("no play/discard")

        if self.play is not None and state.card_at(self.play) != self.play.card:
            raise InvalidUpdateError("play")

        if self.discard is not None and state.card_at(self.discard) != self.discard.card:
            raise InvalidUpdateError("discard")

        if self.clue is not None and self.clue.player == self.clue.to_player:
            raise InvalidUpdateError("self clue")
            # todo empty/wrong clues


@dataclass
class Action:
    player: int

    def to_update(self, state: "GameState") -> StateUpdate:
        raise NotImplementedError


@dataclass
class DiscardAction(Action):
    card: int

    def to_update(self, state: "GameState") -> StateUpdate:
        card = state.players[self.player].cards[self.card]
        return StateUpdate(clues=1, discard=(PlayerPosCard(self.player, self.card, card)), new_card=state.deck.peek())


class PlayAction(Action):
    card: int

    def to_update(self, state: "GameState") -> StateUpdate:
        card = state.players[self.player].cards[self.card]
        valid_play = state.played_cards.is_valid_play(card)
        return StateUpdate(
            lives=-1 if not valid_play else 0,
            clues=1 if valid_play and card.clues else 0,
            play=(PlayerPosCard(self.player, self.card, card)),
            new_card=state.deck.peek(),
        )


class ClueAction(Action):
    to_player: int
    color: Optional[Color]
    number: Optional[int]

    def to_update(self, state: "GameState") -> StateUpdate:
        return StateUpdate(clues=-1, clue=self)
