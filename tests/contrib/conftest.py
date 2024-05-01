from typing import List, Tuple, Union

from hanapy.core.card import Card, CardInfo, Clue, Color
from hanapy.core.config import CardConfig, GameConfig, GameState
from hanapy.core.player import PlayerMemo, PlayerView
from hanapy.players.dummy import DiscardingPlayer
from hanapy.variants.classic import ClassicGame


class Cards:
    @classmethod
    def parse_card(cls, card: str, colors: List[Color]) -> Card:
        number_str, color = list(card)
        return Card(number=int(number_str), color=Color.parse(color, colors))

    @classmethod
    def hand(
        cls, cards: Union[str, List[str]], clues: List[Clue], card_config: CardConfig
    ) -> Tuple[List[Card], List[CardInfo]]:
        if isinstance(cards, str):
            cards = cards.split(",")
        card_res: List[Card] = [cls.parse_card(card, card_config.colors) for card in cards]
        info_res: List[CardInfo] = [CardInfo.create(card_config) for _ in cards]

        for card, info in zip(card_res, info_res):
            for clue in clues:
                if clue.touches(card):
                    info.touch(clue)
                else:
                    info.not_touch(clue)
        return card_res, info_res


class Players:
    @classmethod
    def discarding(cls, count: int):
        return [DiscardingPlayer("")] * count


class Games:
    @classmethod
    def classic(cls, players: int, seed: int = 0):
        return ClassicGame(players=Players.discarding(players), random_seed=seed)


class Views:
    @classmethod
    def create(cls, config: GameConfig, me: int = 0):
        return PlayerView(
            name="",
            me=me,
            memo=PlayerMemo.create(),
            cards=[[] for _ in range(config.player_count)],
            state=GameState.create(config, 0),
            config=config,
        )
