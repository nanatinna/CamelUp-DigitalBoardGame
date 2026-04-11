from dataclasses import dataclass, field
from typing import Optional

# 5 normal racing camels
CAMEL_COLORS = ['green', 'purple', 'yellow', 'blue', 'red']

# 2 crazy camels — move backward, cannot be bet on
CRAZY_CAMEL_COLORS = ['black', 'white']

# All camel colours (racing + crazy)
ALL_CAMEL_COLORS = CAMEL_COLORS + CRAZY_CAMEL_COLORS

# 6 dice: one per racing camel + one grey die that moves a random crazy camel
DICE_COLORS = CAMEL_COLORS + ['grey']


@dataclass
class Camel:
    color: str
    position: int = 0        # 0 = not yet placed; 1–16 = tile; >16 = past finish
    stack_order: int = 0     # 0 = bottom; higher = further up the stack
    is_crazy: bool = False   # True for black/grey crazy camels (move backward)


@dataclass
class LegBetTile:
    camel_color: str
    value: int               # 5, 3, 2, or 1 (taken in decreasing order)


@dataclass
class RaceBet:
    camel_color: str
    bet_type: str            # 'winner' or 'loser'


@dataclass
class Player:
    name: str
    coins: int = 3
    leg_bets: list = field(default_factory=list)   # list[LegBetTile]
    race_bets: list = field(default_factory=list)  # list[RaceBet]
    desert_tile: Optional[dict] = None             # {'tile': int, 'type': str}
    desert_tile_placed: bool = False
    coin_log: list = field(default_factory=list)   # Track coin sources for results screen


@dataclass
class GameState:
    players: list
    camels: list
    current_player_idx: int = 0
    # 6 dice start available; leg ends when the 5 racing dice are exhausted
    dice_remaining: list = field(default_factory=lambda: list(DICE_COLORS))
    leg_number: int = 1
    turn_number: int = 0
    game_over: bool = False
    winner: Optional[str] = None
    # tile_num -> {'type': 'oasis'|'mirage', 'owner_idx': int}
    desert_tiles: dict = field(default_factory=dict)
    # Only racing camels have leg-bet tiles: {'blue': [5,3,2,1], ...}
    available_leg_bets: dict = field(default_factory=dict)
    event_log: list = field(default_factory=list)
