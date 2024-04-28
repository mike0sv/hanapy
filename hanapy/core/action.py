from typing import TYPE_CHECKING, ClassVar, List, Optional

from msgspec import Struct

from hanapy.core.card import Card, CardInfo, Clue
from hanapy.core.errors import InvalidUpdateError
from hanapy.utils.ser import PolyStruct

if TYPE_CHECKING:
    from hanapy.core.state import GameData


class ActionResult(Struct):
    life_lost: bool
    clues_change: int = 0


class PlayerPos(Struct):
    player: int
    pos: int


class PlayerPosCard(PlayerPos):
    card: Card


ClueTouched = List[int]


class ClueResult(Clue):
    touched: ClueTouched

    @classmethod
    def from_clue(cls, clue: Clue, cards: List[Card]):
        return ClueResult(
            to_player=clue.to_player, number=clue.number, color=clue.color, touched=clue.get_touched(cards)
        )


class StateUpdate(Struct):
    player: int
    lives: int = 0
    clues: int = 0
    discard: Optional[PlayerPosCard] = None
    play: Optional[PlayerPosCard] = None
    new_card: Optional[Card] = None
    clue: Optional[ClueResult] = None

    def apply(self, game_data: "GameData") -> None:
        game_data.state.lives_left += self.lives
        game_data.state.clues_left = min(game_data.state.clues_left + self.clues, game_data.config.max_clues)
        player: Optional[int] = None
        new_card_dealed = self.new_card is not None
        if self.discard is not None:
            player = self.discard.player
            del game_data.players[player].cards[self.discard.pos]
            game_data.state.clued.pop_card(
                player, self.discard.pos, CardInfo.create(game_data.config.cards) if new_card_dealed else None
            )
            game_data.state.discarded.cards.append(self.discard.card)
        if self.play is not None:
            player = self.play.player
            if not self.discard:
                del game_data.players[player].cards[self.play.pos]
                game_data.state.clued.pop_card(
                    player, self.play.pos, CardInfo.create(game_data.config.cards) if new_card_dealed else None
                )
            game_data.state.played.play(self.play.card)
        if new_card_dealed:
            assert player is not None
            new_card = game_data.deck.draw()
            assert new_card == self.new_card
            game_data.players[player].gain_card(new_card)
            game_data.state.cards_left -= 1
        if self.clue is not None:
            game_data.state.clued.apply_clue(self.clue.to_player, self.clue, self.clue.touched)

        if game_data.deck.is_empty():
            game_data.state.turns_left -= 1

    def validate(self, game_data: "GameData") -> None:
        new_clues = game_data.state.clues_left + self.clues
        if new_clues < 0 or (
            self.play is None and new_clues > game_data.config.max_clues and not game_data.config.unlimited_clues
        ):
            raise InvalidUpdateError("clues")
        new_lives = game_data.state.lives_left + self.lives
        if new_lives < 0 or new_lives > game_data.config.max_lives:
            raise InvalidUpdateError("lives")

        if self.new_card is not None and self.new_card != game_data.deck.peek():
            raise InvalidUpdateError("newcard")

        if self.new_card is not None and self.play is None and self.discard is None:
            raise InvalidUpdateError("no play/discard")

        if self.play is not None and game_data.card_at(self.play) != self.play.card:
            raise InvalidUpdateError("play")

        if self.discard is not None and game_data.card_at(self.discard) != self.discard.card:
            raise InvalidUpdateError("discard")

        if self.clue is not None:
            if self.player == self.clue.to_player:
                raise InvalidUpdateError("self clue")
            if len(self.clue.touched) == 0:
                raise InvalidUpdateError("empty clue")
            # todo empty/wrong clues


class Action(PolyStruct):
    __root__: ClassVar = True
    player: int

    def to_update(self, game_data: "GameData") -> StateUpdate:
        raise NotImplementedError(self.__class__.__name__)


class DiscardAction(Action):
    __typename__: ClassVar = "discard"

    card: int

    def to_update(self, game_data: "GameData") -> StateUpdate:
        card = game_data.players[self.player].cards[self.card]
        return StateUpdate(
            player=self.player,
            clues=1,
            discard=(PlayerPosCard(self.player, self.card, card)),
            new_card=game_data.deck.peek(),
        )

    def __str__(self):
        return f"ActionDiscard[{self.card}]"


class PlayAction(Action):
    __typename__: ClassVar = "play"
    card: int

    def to_update(self, game_data: "GameData") -> StateUpdate:
        card = game_data.players[self.player].cards[self.card]
        valid_play = game_data.state.played.is_valid_play(card)
        return StateUpdate(
            player=self.player,
            lives=-1 if not valid_play else 0,
            clues=1 if valid_play and card.clues else 0,
            play=(PlayerPosCard(self.player, self.card, card)),
            new_card=game_data.deck.peek(),
            discard=(PlayerPosCard(self.player, self.card, card)) if not valid_play else None,
        )

    def __str__(self):
        return f"ActionPlay[{self.card}]"


class ClueAction(Action):
    __typename__: ClassVar = "clue"

    clue: Clue

    def to_update(self, game_data: "GameData") -> StateUpdate:
        return StateUpdate(
            player=self.player,
            clues=-1,
            clue=ClueResult.from_clue(self.clue, game_data.players[self.clue.to_player].cards),
        )

    def __str__(self):
        return f"Action{self.clue}"
