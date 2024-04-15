from abc import ABC, abstractmethod
from typing import List

from hanapy.core.action import Action, StateUpdate
from hanapy.core.card import Card
from hanapy.core.config import PublicGameState
from hanapy.utils.ser import PolyStruct


class PlayerMemo(PolyStruct):
    pass


class PlayerView(PolyStruct):
    name: str
    me: int
    memo: PlayerMemo
    cards: List[List[Card]]
    state: PublicGameState


class PlayerActor(ABC):
    @abstractmethod
    def get_next_action(self, view: PlayerView) -> Action:
        raise NotImplementedError

    @abstractmethod
    def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        raise NotImplementedError


class PlayerState(PolyStruct):
    cards: List[Card]
    memo: PlayerMemo

    def loose_card(self, card_position: int) -> Card:
        card = self.cards[card_position]
        self.cards.pop(card_position)
        return card

    def gain_card(self, card: Card) -> None:
        self.cards.append(card)
