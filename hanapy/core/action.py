from typing import TYPE_CHECKING, ClassVar, List, Optional

from msgspec import Struct

from hanapy.core.card import Card, Color
from hanapy.core.errors import InvalidUpdateError
from hanapy.utils.ser import PolyStruct

if TYPE_CHECKING:
    from hanapy.core.state import GameState


class ActionResult(Struct):
    life_lost: bool
    clues_change: int = 0


class PlayerPos(Struct):
    player: int
    pos: int


class PlayerPosCard(PlayerPos):
    card: Card


ClueTouched = List[int]


class StateUpdate(Struct):
    player: int
    lives: int = 0
    clues: int = 0
    discard: Optional[PlayerPosCard] = None
    play: Optional[PlayerPosCard] = None
    new_card: Optional[Card] = None
    clue: Optional["ClueAction"] = None
    clue_touched: Optional[ClueTouched] = None

    def apply(self, state: "GameState") -> None:
        state.public.lives_left += self.lives
        state.public.clues_left += self.clues
        player: Optional[int] = None
        if self.discard is not None:
            player = self.discard.player
            del state.players[player].cards[self.discard.pos]
            state.players[player].memo.info.pop_card(self.discard.pos)
            state.memo.pop_card(player, self.discard.pos)
            state.public.discarded_cards.cards.append(self.discard.card)
        if self.play is not None:
            player = self.play.player
            del state.players[player].cards[self.play.pos]
            state.players[player].memo.info.pop_card(self.play.pos)
            state.memo.pop_card(player, self.play.pos)
            state.public.played_cards.play(self.play.card)
        if self.new_card is not None:
            assert player is not None
            new_card = state.deck.draw()
            assert new_card == self.new_card
            state.players[player].gain_card(new_card)
        if self.clue is not None:
            clued = state.players[self.clue.to_player]
            clued.memo.info.apply_clue(self.clue, self.clue_touched)
            state.memo.touch(self.clue.to_player, self.clue_touched)

        if state.deck.is_empty():
            state.public.turns_left -= 1

    def validate(self, state: "GameState") -> None:
        new_clues = state.public.clues_left + self.clues
        if new_clues < 0 or (new_clues > state.public.config.max_clues and not state.public.config.unlimited_clues):
            raise InvalidUpdateError("clues")
        new_lives = state.public.lives_left + self.lives
        if new_lives < 0 or new_lives > state.public.config.max_lives:
            raise InvalidUpdateError("lives")

        if self.new_card is not None and self.new_card != state.deck.peek():
            raise InvalidUpdateError("newcard")

        if self.new_card is not None and self.play is None and self.discard is None:
            raise InvalidUpdateError("no play/discard")

        if self.play is not None and state.card_at(self.play) != self.play.card:
            raise InvalidUpdateError("play")

        if self.discard is not None and state.card_at(self.discard) != self.discard.card:
            raise InvalidUpdateError("discard")

        if self.clue is not None:
            if self.clue.player == self.clue.to_player:
                raise InvalidUpdateError("self clue")
            if self.clue_touched is None or len(self.clue_touched) == 0:
                raise InvalidUpdateError("empty clue")
            # todo empty/wrong clues


class Action(PolyStruct):
    __root__: ClassVar = True
    player: int

    def to_update(self, state: "GameState") -> StateUpdate:
        raise NotImplementedError(self.__class__.__name__)


class DiscardAction(Action):
    __typename__: ClassVar = "discard"

    card: int

    def to_update(self, state: "GameState") -> StateUpdate:
        card = state.players[self.player].cards[self.card]
        return StateUpdate(
            player=self.player,
            clues=1,
            discard=(PlayerPosCard(self.player, self.card, card)),
            new_card=state.deck.peek(),
        )


class PlayAction(Action):
    __typename__: ClassVar = "play"
    card: int

    def to_update(self, state: "GameState") -> StateUpdate:
        card = state.players[self.player].cards[self.card]
        valid_play = state.public.played_cards.is_valid_play(card)
        return StateUpdate(
            player=self.player,
            lives=-1 if not valid_play else 0,
            clues=1 if valid_play and card.clues else 0,
            play=(PlayerPosCard(self.player, self.card, card)),
            new_card=state.deck.peek(),
            discard=(PlayerPosCard(self.player, self.card, card)) if not valid_play else None,
        )


class ClueAction(Action):
    __typename__: ClassVar = "clue"

    to_player: int
    color: Optional[Color]
    number: Optional[int]

    def to_update(self, state: "GameState") -> StateUpdate:
        return StateUpdate(player=self.player, clues=-1, clue=self, clue_touched=self.get_touched(state))

    def get_touched(self, state: "GameState") -> ClueTouched:
        return [i for i, c in enumerate(state.players[self.to_player].cards) if self.touches(c)]

    def touches(self, card: Card) -> bool:
        if self.number is not None and card.number == self.number:
            return True
        if self.color is not None and card.color == self.color:
            return True
        return False
