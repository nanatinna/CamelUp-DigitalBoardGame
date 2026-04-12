# Camel Up — Python Desktop Game

A complete Python/Pygame implementation of **Camel Up 2.0**, built as a university course project.

The game features 5 racing camels and 2 crazy camels that move backward, camel stacking, oasis/mirage desert tiles, leg bets, race bets, and a full GUI with animations.

---

## Requirements

- Python 3.10+
- `pygame-ce >= 2.5.0`
- `pygame_gui >= 0.6.0`
- `Pillow >= 10.0.0`

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
- Enter 2–4 player names on the Start Screen.
- **5 racing camels** (Green, Purple, Yellow, Blue, Red) are placed randomly on tiles 1–3.
- **2 crazy camels** (Black, White) are placed randomly on tiles 14–16 — they move **backward**.

### On Your Turn, Choose One Action

| Action | Effect |
|--------|--------|
| **Roll Dice** | Pull a random unused die from the pyramid (1–3 steps). The camel moves. You earn **+1 coin**. The grey die moves a random crazy camel backward. A leg lasts exactly **5 dice rolls**. |
| **Leg Bet** | Take a tile predicting which camel finishes the leg in **1st or 2nd**. Pays **5 / 3 / 2 / 1** coins if 1st, **1** coin if 2nd, **−1** if wrong. |
| **Race Bet** | Secretly predict the overall race **winner** or **loser**. Earlier correct bets pay more (8 / 5 / 3 / 2 / 1). |
| **Desert Tile** | Place an **Oasis (+1)** or **Mirage (−1)** tile on any empty tile ≥ 2. When a camel lands on it you earn **+1 coin**, and the camel is nudged forward/backward. |

### Camel Stacking
When a racing camel lands on an occupied tile it stacks **on top**. Crazy camels slide **under** the existing stack. Moving a camel carries its entire piggyback stack.

### Desert Tiles and Crazy Camels
Desert tiles push a camel one extra step in the direction it is already travelling:
- **Racing camel on Oasis** → +1 forward
- **Racing camel on Mirage** → −1 backward
- **Crazy camel on Oasis** → −1 (further backward)
- **Crazy camel on Mirage** → +1 (back toward higher tiles)

### End of Leg
After 5 dice are rolled, a **Leg Summary popup** appears showing standings, bet payouts, coin changes per player, and a recap of every die rolled that leg. Click **NEXT LEG** to continue. Dice and desert tiles reset; leg bets clear.

### End of Race
When any racing camel crosses tile 16, race bets are scored and the **Results Screen** shows a full breakdown per player. The player with the most coins wins!

---

## Features

- Full Camel Up 2.0 rule set: 5 racing + 2 crazy camels, stacking rules, desert tiles, leg bets, and race bets
- Desert warm visual theme — sand, wood panels, parchment cards
- Smooth camel movement animation with speed proportional to steps rolled
- Dice Tracker panel showing rolled values and a Last Roll banner each leg
- Animated dice roll overlay when a die is pulled
- Leg Summary popup at the end of every leg
- Scrollable event log tracking every action
- SQLite leaderboard of past completed games on the start screen
- Auto-save to `autosave.json` after every action — resumes on next launch
- Results screen with per-player coin breakdown at game end
- All exceptions logged to `errors.log` — the game loop never crashes

---

## File Structure

```
CamelUp-DigitalBoardGame/
├── requirements.txt
├── README.md
└── camel_up/
    ├── main.py                      ← entry point
    ├── assets/
    │   ├── fonts/
    │   │   └── Cinzel-Bold.otf
    │   ├── images/
    │   │   ├── game_background.png
    │   │   └── logo.png
    │   └── theme.json               ← pygame_gui desert theme
    ├── game/
    │   ├── models.py                ← dataclasses: Camel, Player, GameState …
    │   ├── game_logic.py            ← CamelUpGame: all rules and stacking logic
    │   └── utils.py                 ← logging helpers
    ├── gui/
    │   ├── app.py                   ← pygame loop + screen manager
    │   ├── theme.py                 ← colours, layout constants
    │   ├── components/
    │   │   ├── bet_card.py          ← leg-bet tile panel
    │   │   ├── board.py             ← 16-tile track renderer
    │   │   ├── camel_sprite.py      ← animated camel token
    │   │   ├── dice_pyramid.py      ← dice tracker with roll animation
    │   │   ├── event_log.py         ← scrollable event log strip
    │   │   ├── leg_summary_popup.py ← end-of-leg summary overlay
    │   │   └── player_hud.py        ← left panel: players + action buttons
    │   └── screens/
    │       ├── start_screen.py      ← player setup + leaderboard
    │       ├── game_screen.py       ← main game view
    │       ├── results_screen.py    ← per-player coin breakdown
    │       └── end_screen.py        ← winner announcement
    ├── storage/
    │   ├── database.py              ← SQLite schema + queries
    │   ├── save_manager.py          ← JSON autosave / load
    │   └── history.py               ← GameHistory wrapper
    └── tests/
        ├── test_models.py
        └── test_game_logic.py
```

> `autosave.json`, `camel_up.db`, and `errors.log` are created automatically at runtime and are excluded from version control via `.gitignore`.

---

## Running Tests

```bash
cd camel_up
python -m unittest discover -s tests -p "test_*.py" -v
```
