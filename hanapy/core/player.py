from abc import ABC, abstractmethod
from typing import Callable, List

from msgspec import Struct

from hanapy.core.action import Action, StateUpdate
from hanapy.core.card import Card, CardInfo
from hanapy.core.config import GameConfig, GameResult, GameState
from hanapy.types import EventHandlers


class PlayerMemo(Struct):
    @classmethod
    def create(cls):
        return PlayerMemo()


class PlayerView(Struct):
    name: str
    me: int
    memo: PlayerMemo
    cards: List[List[Card]]
    state: GameState
    config: GameConfig

    @property
    def my_cards(self) -> List[CardInfo]:
        return self.state.clued[self.me]


class PlayerActor(ABC):
    @abstractmethod
    async def on_game_start(self, view: PlayerView):
        raise NotImplementedError

    @abstractmethod
    async def get_next_action(self, view: PlayerView) -> Action:
        raise NotImplementedError

    @abstractmethod
    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        raise NotImplementedError

    @abstractmethod
    async def on_game_end(self, view: PlayerView, game_result: GameResult):
        raise NotImplementedError

    async def on_valid_action(self):
        return

    async def on_invalid_action(self, msg: str):
        return

    def get_event_handlers(self) -> EventHandlers:
        return {}


Bot = Callable[[], PlayerActor]


class PlayerState(Struct):
    cards: List[Card]
    memo: PlayerMemo

    def loose_card(self, card_position: int) -> Card:
        card = self.cards[card_position]
        self.cards.pop(card_position)
        return card

    def gain_card(self, card: Card) -> None:
        self.cards.insert(0, card)
