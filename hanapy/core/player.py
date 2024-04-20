from abc import ABC, abstractmethod
from typing import Callable, ClassVar, Counter, Dict, List, Set, Type, TypeVar, cast

from msgspec import Struct

from hanapy.core.action import Action, StateUpdate
from hanapy.core.card import Card, CardInfo
from hanapy.core.config import GameConfig, GameResult, GameState
from hanapy.types import EventHandlers, SeenCards
from hanapy.utils.ser import PolyStruct


class MemoCell(PolyStruct):
    __typename__: ClassVar = "memo_cell"
    __root__: ClassVar = True

    def __init_subclass__(cls):
        cls.__typename__ = f"{cls.__module__}.{cls.__name__}"
        super().__init_subclass__()


CT = TypeVar("CT", bound=MemoCell)


class PlayerMemo(Struct):
    cells: Dict[str, MemoCell]

    @classmethod
    def create(cls):
        return PlayerMemo(cells={})

    def get(self, cell_type: Type[CT]) -> CT:
        return cast(CT, self.cells[cell_type.__typename__])

    def add(self, cell: MemoCell):
        self.cells[cell.__typename__] = cell


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

    def get_all_seen_cards(self) -> SeenCards:
        result: Counter[Card] = self.state.played.get_all_cards(self.config.cards.colors)
        result.update(self.state.discarded.cards)
        for i, cards in enumerate(self.cards):
            if i == self.me:
                continue
            result.update(cards)
        result.update(c.as_card() for c in self.my_cards if c.is_known)
        return result

    def refresh_card_info(self):
        seen_cards = self.get_all_seen_cards()
        cant_have: Set[Card] = {
            card for card, count in seen_cards.items() if self.config.cards.counts[card.number] == count
        }
        for card_info in self.my_cards:
            if card_info.is_known:
                continue
            for color in list(card_info.colors):
                possible = {Card(color, num) for num in card_info.numbers}
                # if all impossible get clue
                if possible.intersection(cant_have) == possible:
                    card_info.colors.discard(color)
            for number in list(card_info.numbers):
                possible = {Card(color, number) for color in card_info.colors}
                # if all impossible get clue
                if possible.intersection(cant_have) == possible:
                    card_info.numbers.discard(number)


class PlayerActor(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
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

    def get_name(self) -> str:
        return self.name


Bot = Callable[[str], PlayerActor]


class PlayerState(Struct):
    name: str
    cards: List[Card]
    memo: PlayerMemo

    def loose_card(self, card_position: int) -> Card:
        card = self.cards[card_position]
        self.cards.pop(card_position)
        return card

    def gain_card(self, card: Card) -> None:
        self.cards.insert(0, card)
