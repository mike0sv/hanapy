# ruff: noqa: A003
from typing import List, Optional, Any
from msgspec import Struct


class HLModel(Struct):
    pass


class CommandData(HLModel):
    tableID: Optional[int] = None
    databaseID: Optional[int] = None
    setting: Optional[str] = None
    msg: Optional[str] = None
    room: Optional[str] = None
    recipient: Optional[str] = None
    name: Optional[str] = None
    options: Optional["Options"] = None
    password: Optional[str] = None
    maxPlayers: Optional[int] = None
    intendedPlayers: Optional[List[str]] = None
    type: Optional[int] = None
    target: Optional[int] = None
    value: Optional[int] = None
    votes: Optional[List[int]] = None
    note: Optional[str] = None
    order: Optional[int] = None
    shadowingPlayerIndex: Optional[int] = None
    source: Optional[str] = None
    gameJSON: Optional["GameJSON"] = None
    visibility: Optional[str] = None
    segment: Optional[int] = None
    rank: Optional[int] = None
    suit: Optional[int] = None
    sound: Optional[str] = None
    offset: Optional[int] = None
    amount: Optional[int] = None
    seed: Optional[str] = None
    friends: Optional[bool] = None
    actionJSON: Optional[str] = None
    inactive: Optional[bool] = None
    hidePregame: Optional[bool] = None


class Spectator(HLModel):
    name: Optional[str] = None
    shadowingPlayerIndex: Optional[int] = None
    shadowingPlayerUsername: Optional[str] = None


class Options(HLModel):
    numPlayers: Optional[int] = None
    startingPlayer: Optional[int] = None
    variantID: Optional[int] = None
    variantName: Optional[str] = None
    timed: Optional[bool] = None
    timeBase: Optional[int] = None
    timePerTurn: Optional[int] = None
    speedrun: Optional[bool] = None
    cardCycle: Optional[bool] = None
    deckPlays: Optional[bool] = None
    emptyClues: Optional[bool] = None
    oneExtraCard: Optional[bool] = None
    oneLessCard: Optional[bool] = None
    allOrNothing: Optional[bool] = None
    detrimentalCharacters: Optional[bool] = None
    tableName: Optional[str] = None
    maxPlayers: Optional[int] = None


class OptionsJSON(HLModel):
    startingPlayer: Optional[int] = None
    variant: Optional[str] = None
    timed: Optional[bool] = None
    timeBase: Optional[int] = None
    timePerTurn: Optional[int] = None
    speedrun: Optional[bool] = None
    cardCycle: Optional[bool] = None
    deckPlays: Optional[bool] = None
    emptyClues: Optional[bool] = None
    oneExtraCard: Optional[bool] = None
    oneLessCard: Optional[bool] = None
    allOrNothing: Optional[bool] = None
    detrimentalCharacters: Optional[bool] = None


class CardIdentity(HLModel):
    suitIndex: Optional[int] = None
    rank: Optional[int] = None


class TableMessage(HLModel):
    id: Optional[int] = None
    name: Optional[str] = None
    passwordProtected: Optional[bool] = None
    joined: Optional[bool] = None
    numPlayers: Optional[int] = None
    owned: Optional[bool] = None
    running: Optional[bool] = None
    variant: Optional[str] = None
    options: Optional["Options"] = None
    timed: Optional[bool] = None
    timeBase: Optional[int] = None
    timePerTurn: Optional[int] = None
    sharedReplay: Optional[bool] = None
    progress: Optional[int] = None
    players: Optional[List[str]] = None
    spectators: Optional[List["Spectator"]] = None
    maxPlayers: Optional[int] = None


class GameJSON(HLModel):
    id: Optional[int] = None
    players: Optional[List[str]] = None
    deck: Optional[List["CardIdentity"]] = None
    actions: Optional[List["GameAction"]] = None
    options: Optional["OptionsJSON"] = None
    notes: Optional[List[str]] = None
    characters: Optional[List["CharacterAssignment"]] = None
    seed: Optional[str] = None


class CharacterAssignment(HLModel):
    name: Optional[str] = None
    metadata: Optional[int] = None


class GameAction(HLModel):
    type: Optional[int] = None
    target: Optional[int] = None
    value: Optional[int] = None


class GameActionListMessage(HLModel):
    tableID: Optional[int] = None
    list: Optional[List[Any]] = None
