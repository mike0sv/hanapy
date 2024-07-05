# ruff: noqa: A003
from typing import List

from msgspec import Struct


class HLModel(Struct):
    pass


class Spectator(HLModel):
    name: str
    shadowingPlayerIndex: int
    shadowingPlayerUsername: str


class Options(HLModel):
    numPlayers: int
    startingPlayer: int
    variantID: int
    variantName: str
    timed: bool
    timeBase: int
    timePerTurn: int
    speedrun: bool
    cardCycle: bool
    deckPlays: bool
    emptyClues: bool
    oneExtraCard: bool
    oneLessCard: bool
    allOrNothing: bool
    detrimentalCharacters: bool
    tableName: str
    maxPlayers: int


class TableMessage(HLModel):
    id: int
    name: str
    passwordProtected: bool
    joined: bool
    numPlayers: int
    owned: bool
    running: bool
    variant: str
    options: Options
    timed: bool
    timeBase: int
    timePerTurn: int
    sharedReplay: bool
    progress: int
    players: List[str]
    spectators: List[Spectator]
    maxPlayers: int
