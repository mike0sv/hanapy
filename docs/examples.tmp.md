# Ok move

1. Send action to do the move
   `action {"tableID":9,"type":0,"target":7}`
2. Move info
   `gameAction {"tableID":9,"action":{"type":"play","playerIndex":1,"order":7,"suitIndex":4,"rank":1}}`
3. Table progress update
   `tableProgress {"tableID":9,"progress":4}`
4. Draw a new card
   `gameAction {"tableID":9,"action":{"type":"draw","playerIndex":1,"order":11,"suitIndex":-1,"rank":-1}}`
5. Update clues / score
   `gameAction {"tableID":9,"action":{"type":"status","clues":8,"score":1,"maxScore":25}}`
6. Pass the turn to the next player
   `gameAction {"tableID":9,"action":{"type":"turn","num":2,"currentPlayerIndex":0}}`

# Failed move

1. strike update
   `gameAction {"tableID":9,"action":{"type":"strike","num":1,"turn":0,"order":0}}`
2. discard failed card
   `gameAction {"tableID":9,"action":{"type":"discard","playerIndex":0,"order":0,"suitIndex":0,"rank":3,"failed":true}}`
3. draw a new card to the hand
   `gameAction {"tableID":9,"action":{"type":"draw","playerIndex":0,"order":10,"suitIndex":3,"rank":3}}`
4. update clues / score info
   `gameAction {"tableID":9,"action":{"type":"status","clues":8,"score":0,"maxScore":25}}`
5. pass the turn to the next player
   `gameAction {"tableID":9,"action":{"type":"turn","num":1,"currentPlayerIndex":1}}`

# Clue

1. Send action to clue (cluing by yellow color, cards in first and last slots)
   `action {"tableID":9,"type":2,"target":1,"value":1}`
2. Move info
   `gameAction {"tableID":9,"action":{"type":"clue","clue":{"type":0,"value":1},"giver":0,"list":[5,11],"target":1,"turn":2}}`
3. Game status
   `gameAction {"tableID":9,"action":{"type":"status","clues":7,"score":1,"maxScore":25}}`
4. Pass turn to next player
   `gameAction {"tableID":9,"action":{"type":"turn","num":3,"currentPlayerIndex":1}}`

# Discard

1. Send action to discard from slot 4
   `action {"tableID":9,"type":1,"target":6}`
2. Move info
   `gameAction {"tableID":9,"action":{"type":"discard","playerIndex":1,"order":6,"suitIndex":0,"rank":3,"failed":false}}`
3. Draw info
   `gameAction {"tableID":9,"action":{"type":"draw","playerIndex":1,"order":12,"suitIndex":-1,"rank":-1}}`
4. Status update
   `gameAction {"tableID":9,"action":{"type":"status","clues":8,"score":1,"maxScore":22}}`
5. Pass turn to next player
   `gameAction {"tableID":9,"action":{"type":"turn","num":4,"currentPlayerIndex":0}}`

# Game start as host

```
_tableCreate {"name":"stamper tweaks spooning","options":{"variantName":"No Variant","timed":false,"timeBase":0,"timePerTurn":0,"speedrun":false,"cardCycle":false,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false,"detrimentalCharacters":false},"password":"","maxPlayers":5}	321
table {"id":97,"name":"stamper tweaks spooning","passwordProtected":false,"joined":true,"numPlayers":1,"owned":true,"running":false,"variant":"No Variant","options":{"numPlayers":0,"startingPlayer":0,"variantID":0,"variantName":"No Variant","timed":false,"timeBase":0,"timePerTurn":0,"speedrun":false,"cardCycle":false,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false,"detrimentalCharacters":false},"timed":false,"timeBase":0,"timePerTurn":0,"sharedReplay":false,"progress":0,"players":["123"],"spectators":[],"maxPlayers":5}	575
game {"tableID":97,"name":"stamper tweaks spooning","owner":1,"players":[{"index":0,"name":"123","you":true,"present":true,"stats":{"numGames":1,"variant":{"numGames":10,"bestScores":[{"numPlayers":2,"score":25,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":3,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":4,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":5,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":6,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false}],"averageScore":25,"numStrikeouts":9}}}],"options":{"numPlayers":0,"startingPlayer":0,"variantID":0,"variantName":"No Variant","timed":false,"timeBase":0,"timePerTurn":0,"speedrun":false,"cardCycle":false,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false,"detrimentalCharacters":false},"passwordProtected":false,"maxPlayers":5}	1256
user {"userID":1,"name":"123","status":1,"tableID":97,"hyphenated":false,"inactive":false}	90
joined {"tableID":97}	21
chatList {"list":[{"msg":"\u003cstrong\u003e123\u003c/strong\u003e created the table.","who":"","discord":false,"server":true,"datetime":"2024-07-06T18:42:29.253193+04:00","room":"table97","recipient":""}],"unread":1}	217
pregameSpectators {"tableID":97,"spectators":[]}	48
userInactive {"userID":2,"inactive":false}	42
table {"id":97,"name":"stamper tweaks spooning","passwordProtected":false,"joined":true,"numPlayers":2,"owned":true,"running":false,"variant":"No Variant","options":{"numPlayers":0,"startingPlayer":0,"variantID":0,"variantName":"No Variant","timed":false,"timeBase":0,"timePerTurn":0,"speedrun":false,"cardCycle":false,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false,"detrimentalCharacters":false},"timed":false,"timeBase":0,"timePerTurn":0,"sharedReplay":false,"progress":0,"players":["123","321"],"spectators":[],"maxPlayers":5}	581
game {"tableID":97,"name":"stamper tweaks spooning","owner":1,"players":[{"index":0,"name":"123","you":true,"present":true,"stats":{"numGames":1,"variant":{"numGames":10,"bestScores":[{"numPlayers":2,"score":25,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":3,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":4,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":5,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":6,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false}],"averageScore":25,"numStrikeouts":9}}},{"index":1,"name":"321","you":false,"present":true,"stats":{"numGames":1,"variant":{"numGames":4,"bestScores":[{"numPlayers":2,"score":25,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":3,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":4,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":5,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false},{"numPlayers":6,"score":0,"modifier":0,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false}],"averageScore":25,"numStrikeouts":3}}}],"options":{"numPlayers":0,"startingPlayer":0,"variantID":0,"variantName":"No Variant","timed":false,"timeBase":0,"timePerTurn":0,"speedrun":false,"cardCycle":false,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false,"detrimentalCharacters":false},"passwordProtected":false,"maxPlayers":5}	2103
user {"userID":2,"name":"321","status":1,"tableID":97,"hyphenated":false,"inactive":false}	90
chat {"msg":"321 joined the game.","who":"","discord":false,"server":true,"datetime":"2024-07-06T18:42:36.007446+04:00","room":"table97","recipient":""}	152
_chatRead {"tableID":97}	23
pregameSpectators {"tableID":97,"spectators":[]}	48
_tableStart {"tableID":97,"intendedPlayers":["123","321"]}	57
tableStart {"tableID":97,"replay":false}	40
_getGameInfo1 {"tableID":97}	27
table {"id":97,"name":"stamper tweaks spooning","passwordProtected":false,"joined":true,"numPlayers":2,"owned":true,"running":true,"variant":"No Variant","options":{"numPlayers":2,"startingPlayer":0,"variantID":0,"variantName":"No Variant","timed":false,"timeBase":0,"timePerTurn":0,"speedrun":false,"cardCycle":false,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false,"detrimentalCharacters":false},"timed":false,"timeBase":0,"timePerTurn":0,"sharedReplay":false,"progress":0,"players":["123","321"],"spectators":[],"maxPlayers":5}	580
user {"userID":1,"name":"123","status":2,"tableID":97,"hyphenated":false,"inactive":false}	90
user {"userID":2,"name":"321","status":2,"tableID":97,"hyphenated":false,"inactive":false}	90
init {"tableID":97,"playerNames":["123","321"],"ourPlayerIndex":0,"spectating":false,"shadowing":false,"replay":false,"databaseID":-1,"hasCustomSeed":false,"seed":"p2v0s5","datetimeStarted":"2024-07-06T18:42:40.098588+04:00","datetimeFinished":"0001-01-01T00:00:00Z","options":{"numPlayers":2,"startingPlayer":0,"variantID":0,"variantName":"No Variant","timed":false,"timeBase":0,"timePerTurn":0,"speedrun":false,"cardCycle":false,"deckPlays":false,"emptyClues":false,"oneExtraCard":false,"oneLessCard":false,"allOrNothing":false,"detrimentalCharacters":false},"characterAssignments":[],"characterMetadata":[],"sharedReplay":false,"sharedReplayLeader":"123","sharedReplaySegment":0,"sharedReplayEffMod":0,"paused":false,"pausePlayerIndex":-1,"pauseQueued":false}	762
_getGameInfo2 {"tableID":97}	27
gameActionList {"tableID":97,"list":[{"type":"draw","playerIndex":0,"order":0,"suitIndex":-1,"rank":-1},{"type":"draw","playerIndex":0,"order":1,"suitIndex":-1,"rank":-1},{"type":"draw","playerIndex":0,"order":2,"suitIndex":-1,"rank":-1},{"type":"draw","playerIndex":0,"order":3,"suitIndex":-1,"rank":-1},{"type":"draw","playerIndex":0,"order":4,"suitIndex":-1,"rank":-1},{"type":"draw","playerIndex":1,"order":5,"suitIndex":1,"rank":5},{"type":"draw","playerIndex":1,"order":6,"suitIndex":0,"rank":3},{"type":"draw","playerIndex":1,"order":7,"suitIndex":4,"rank":1},{"type":"draw","playerIndex":1,"order":8,"suitIndex":0,"rank":4},{"type":"draw","playerIndex":1,"order":9,"suitIndex":4,"rank":3}]}	698
_loaded {"tableID":97}	21
connected {"tableID":97,"list":[false,false]}	45
clock {"tableID":97,"times":[-126,0],"activePlayerIndex":0,"timeTaken":126}	75
noteListPlayer {"tableID":97,"notes":["","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""]}	204
voteChange {"vote":false}	25
spectators {"tableID":97,"spectators":[]}	41
chatList {"list":[{"msg":"\u003cstrong\u003e123\u003c/strong\u003e created the table.","who":"","discord":false,"server":true,"datetime":"2024-07-06T18:42:29.253193+04:00","room":"table97","recipient":""},{"msg":"321 joined the game.","who":"","discord":false,"server":true,"datetime":"2024-07-06T18:42:36.007446+04:00","room":"table97","recipient":""}],"unread":0}	365
connected {"tableID":97,"list":[true,false]}	44
clock {"tableID":97,"times":[0,0],"activePlayerIndex":0,"timeTaken":0}	70
connected {"tableID":97,"list":[true,true]}
```
