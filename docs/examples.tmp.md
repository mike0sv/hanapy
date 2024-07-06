# Ok move

1. Send action to do the move
action {"tableID":9,"type":0,"target":7}
2. Move info
gameAction {"tableID":9,"action":{"type":"play","playerIndex":1,"order":7,"suitIndex":4,"rank":1}}
3. Table progress update
tableProgress {"tableID":9,"progress":4}
4. Draw a new card
gameAction {"tableID":9,"action":{"type":"draw","playerIndex":1,"order":11,"suitIndex":-1,"rank":-1}}
5. Update clues / score
gameAction {"tableID":9,"action":{"type":"status","clues":8,"score":1,"maxScore":25}}
6. Pass the turn to the next player
gameAction {"tableID":9,"action":{"type":"turn","num":2,"currentPlayerIndex":0}}

# Failed move

1. strike update
gameAction {"tableID":9,"action":{"type":"strike","num":1,"turn":0,"order":0}}
2. discard failed card
gameAction {"tableID":9,"action":{"type":"discard","playerIndex":0,"order":0,"suitIndex":0,"rank":3,"failed":true}}
3. draw a new card to the hand
gameAction {"tableID":9,"action":{"type":"draw","playerIndex":0,"order":10,"suitIndex":3,"rank":3}}
4. update clues / score info
gameAction {"tableID":9,"action":{"type":"status","clues":8,"score":0,"maxScore":25}}
5. pass the turn to the next player
gameAction {"tableID":9,"action":{"type":"turn","num":1,"currentPlayerIndex":1}}

# Clue

1. Send action to clue (cluing by yellow color, cards in first and last slots)
action {"tableID":9,"type":2,"target":1,"value":1}
2. Move info
gameAction {"tableID":9,"action":{"type":"clue","clue":{"type":0,"value":1},"giver":0,"list":[5,11],"target":1,"turn":2}}
3. Game status
gameAction {"tableID":9,"action":{"type":"status","clues":7,"score":1,"maxScore":25}}
4. Pass turn to next player
gameAction {"tableID":9,"action":{"type":"turn","num":3,"currentPlayerIndex":1}}

# Discard

1. Send action to discard from slot 4
action {"tableID":9,"type":1,"target":6}
2. Move info
gameAction {"tableID":9,"action":{"type":"discard","playerIndex":1,"order":6,"suitIndex":0,"rank":3,"failed":false}}
3. Draw info
gameAction {"tableID":9,"action":{"type":"draw","playerIndex":1,"order":12,"suitIndex":-1,"rank":-1}}
4. Status update
gameAction {"tableID":9,"action":{"type":"status","clues":8,"score":1,"maxScore":22}}
5. Pass turn to next player
gameAction {"tableID":9,"action":{"type":"turn","num":4,"currentPlayerIndex":0}}