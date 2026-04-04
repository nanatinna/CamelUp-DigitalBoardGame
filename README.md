# Camel Up — Python Desktop Game

A complete Python/pygame implementation of the board game **Camel Up** (Camel Cup), built as a university course project.

---

## How to Run

### Windows
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python camel_up\main.py
```

### Mac / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 camel_up/main.py
```

---

## How to Play

### Setup
- Choose 2–4 players and enter names on the Start Screen.
- Five camels (Blue, Green, Orange, Yellow, White) are placed randomly on tiles 1–3.

### On Your Turn, Choose One Action

| Action | Effect |
|--------|--------|
| **Roll Dice** | Pull a random unused pyramid die (1–3 steps). That camel moves. You gain **+1 coin**. When all 5 dice are used, the leg ends. |
| **Leg Bet** | Take a betting tile for which camel will finish the leg in 1st or 2nd place. Pays **5 / 3 / 2 / 1** coins if correct, **-1** if wrong. |
| **Race Bet** | Secretly predict the overall race **winner** or **loser**. First correct bet pays most. |
| **Place Desert Tile** | Put an **Oasis (+1)** or **Mirage (-1)** tile on any empty, unoccupied tile ≥ 2. When a camel lands on it, they bounce forward/back and you earn **+1 coin**. |

### Stacking
When a camel lands on a tile with others, it stacks **on top**. Moving a camel carries all camels above it as a piggyback stack.

### End of Leg
When all 5 dice are used, leg bets are scored and dice reset. Desert tiles are removed.

### End of Race
When any camel crosses tile 16, race bets are scored. The player with the most coins wins!

---

## Features

- Full Camel Up rule set including camel stacking, oasis/mirage desert tiles, leg bets, and race bets
- Desert warm visual theme — sand, wood panels, parchment cards
- Smooth camel movement animation (tweened over 20 frames)
- Animated dice pyramid showing used/remaining dice
- Scrollable event log tracking every action
- SQLite leaderboard of past games on the start screen
- Auto-save to `autosave.json` after every action — load it on next launch
- Fallback procedural asset generation (runs without any image files)
- All exceptions caught and logged to `errors.log` — game loop never crashes
- 41 unit tests covering all game logic

---

## File Structure

```
CamelUp/
├── requirements.txt
├── README.md
├── camel_up.db               ← auto-created on first run
├── autosave.json             ← auto-created during gameplay
└── camel_up/
    ├── main.py               ← entry point
    ├── assets/
    │   ├── theme.json        ← pygame_gui desert theme
    │   └── images/           ← optional image assets
    ├── game/
    │   ├── models.py         ← dataclasses: Camel, Player, GameState …
    │   ├── game_logic.py     ← CamelUpGame: all rules and stacking logic
    │   └── utils.py          ← logging, helpers
    ├── gui/
    │   ├── app.py            ← main pygame loop + screen manager
    │   ├── theme.py          ← colours, layout constants, fallback surfaces
    │   ├── components/
    │   │   ├── board.py      ← 16-tile oval track renderer
    │   │   ├── camel_sprite.py  ← animated camel token
    │   │   ├── bet_card.py   ← leg-bet tile display
    │   │   ├── dice_pyramid.py  ← pyramid with roll animation
    │   │   ├── player_hud.py ← left panel: players + action buttons
    │   │   └── event_log.py  ← scrollable bottom log strip
    │   └── screens/
    │       ├── start_screen.py
    │       ├── game_screen.py
    │       └── end_screen.py
    ├── storage/
    │   ├── database.py       ← SQLite schema + queries
    │   ├── save_manager.py   ← JSON autosave / load
    │   └── history.py        ← GameHistory wrapper
    └── tests/
        ├── test_models.py
        └── test_game_logic.py
```

---

## Running Tests

```bat
cd camel_up
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: **41 tests, 0 failures**
