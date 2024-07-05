# ruff: noqa: A003
from typing import List

from msgspec import Struct


class Spectator(Struct):
    name: str
    shadowingPlayerIndex: int
    shadowingPlayerUsername: str


class Options(Struct):
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


class TableMessage(Struct):
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
