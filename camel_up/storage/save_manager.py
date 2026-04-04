"""
save_manager.py — JSON autosave / load for Camel Up game state.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import os
from typing import Optional

from game.models import (GameState, Player, Camel, LegBetTile, RaceBet,
                          CAMEL_COLORS, CRAZY_CAMEL_COLORS, ALL_CAMEL_COLORS, DICE_COLORS)

logger = logging.getLogger(__name__)

SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'autosave.json')


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

class _Encoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        return super().default(obj)


# ---------------------------------------------------------------------------
# Decoding
# ---------------------------------------------------------------------------

def _decode_leg_bet(d: dict) -> LegBetTile:
    return LegBetTile(camel_color=d['camel_color'], value=d['value'])


def _decode_race_bet(d: dict) -> RaceBet:
    return RaceBet(camel_color=d['camel_color'], bet_type=d['bet_type'])


def _decode_player(d: dict) -> Player:
    return Player(
        name=d['name'],
        coins=d['coins'],
        leg_bets=[_decode_leg_bet(b) for b in d.get('leg_bets', [])],
        race_bets=[_decode_race_bet(b) for b in d.get('race_bets', [])],
        desert_tile=d.get('desert_tile'),
        desert_tile_placed=d.get('desert_tile_placed', False),
    )


def _decode_camel(d: dict) -> Camel:
    return Camel(
        color=d['color'],
        position=d['position'],
        stack_order=d['stack_order'],
        is_crazy=d.get('is_crazy', d['color'] in CRAZY_CAMEL_COLORS),
    )


def _decode_state(d: dict) -> GameState:
    # desert_tiles keys are strings after JSON round-trip → restore ints
    raw_dt = d.get('desert_tiles', {})
    desert_tiles = {int(k): v for k, v in raw_dt.items()}

    raw_alb = d.get('available_leg_bets', {})
    available_leg_bets = {str(k): list(v) for k, v in raw_alb.items()}

    return GameState(
        players=[_decode_player(p) for p in d['players']],
        camels=[_decode_camel(c) for c in d['camels']],
        current_player_idx=d.get('current_player_idx', 0),
        dice_remaining=d.get('dice_remaining', list(DICE_COLORS)),
        leg_number=d.get('leg_number', 1),
        turn_number=d.get('turn_number', 0),
        game_over=d.get('game_over', False),
        winner=d.get('winner'),
        desert_tiles=desert_tiles,
        available_leg_bets=available_leg_bets,
        event_log=d.get('event_log', []),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def has_save() -> bool:
    if not os.path.isfile(SAVE_PATH):
        return False
    try:
        with open(SAVE_PATH, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return {'players', 'camels', 'leg_number'}.issubset(data.keys())
    except Exception as exc:
        logger.warning("has_save: corrupt save — %s", exc)
        return False


def save_game(state: GameState) -> bool:
    try:
        with open(SAVE_PATH, 'w', encoding='utf-8') as fh:
            json.dump(dataclasses.asdict(state), fh, cls=_Encoder, indent=2)
        return True
    except Exception as exc:
        logger.error("save_game failed: %s", exc)
        return False


def load_game() -> Optional[GameState]:
    if not os.path.isfile(SAVE_PATH):
        return None
    try:
        with open(SAVE_PATH, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return _decode_state(data)
    except Exception as exc:
        logger.error("load_game failed: %s", exc)
        return None


def delete_save() -> None:
    try:
        if os.path.isfile(SAVE_PATH):
            os.remove(SAVE_PATH)
    except OSError as exc:
        logger.error("delete_save failed: %s", exc)
