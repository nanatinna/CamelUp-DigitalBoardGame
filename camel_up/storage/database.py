"""
database.py — SQLite persistence layer for Camel Up.

Stores completed game records, per-player results, and turn-by-turn events.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'camel_up.db')


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_GAMES = """
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    num_players INTEGER,
    winner_name TEXT,
    winner_score INTEGER,
    total_legs INTEGER,
    duration_seconds INTEGER
);
"""

_CREATE_GAME_PLAYERS = """
CREATE TABLE IF NOT EXISTS game_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER REFERENCES games(id),
    player_name TEXT,
    final_score INTEGER,
    placement INTEGER
);
"""

_CREATE_GAME_EVENTS = """
CREATE TABLE IF NOT EXISTS game_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER REFERENCES games(id),
    leg_number INTEGER,
    turn_number INTEGER,
    player_name TEXT,
    action_type TEXT,
    action_detail TEXT,
    timestamp TEXT
);
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create database tables if they don't already exist."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(_CREATE_GAMES)
            conn.execute(_CREATE_GAME_PLAYERS)
            conn.execute(_CREATE_GAME_EVENTS)
            conn.commit()
        logger.debug("Database initialised at %s", DB_PATH)
    except sqlite3.Error as exc:
        logger.error("init_db failed: %s", exc)


def save_game(state, duration_seconds: int) -> int:
    """
    Persist a completed game from a GameState object.

    Parameters
    ----------
    state:
        A GameState instance.  Expects ``state.players`` (list of Player with
        ``.name`` and ``.coins``) and ``state.leg_number``.
    duration_seconds:
        Wall-clock length of the game in seconds.

    Returns
    -------
    int
        The ``id`` of the newly inserted row in ``games``, or -1 on failure.
    """
    try:
        # Rank players by coins descending; ties share the same placement.
        sorted_players = sorted(state.players, key=lambda p: p.coins, reverse=True)
        winner = sorted_players[0]

        date_str = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                """
                INSERT INTO games
                    (date, num_players, winner_name, winner_score,
                     total_legs, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    date_str,
                    len(state.players),
                    winner.name,
                    winner.coins,
                    state.leg_number,
                    duration_seconds,
                ),
            )
            game_id = cur.lastrowid

            # Determine placements (1-based, ties share the same rank).
            placement = 1
            prev_coins: Optional[int] = None
            for rank_offset, player in enumerate(sorted_players):
                if prev_coins is not None and player.coins < prev_coins:
                    placement = rank_offset + 1
                conn.execute(
                    """
                    INSERT INTO game_players
                        (game_id, player_name, final_score, placement)
                    VALUES (?, ?, ?, ?)
                    """,
                    (game_id, player.name, player.coins, placement),
                )
                prev_coins = player.coins

            conn.commit()

        logger.info("Game saved with id=%d", game_id)
        return game_id

    except sqlite3.Error as exc:
        logger.error("save_game failed: %s", exc)
        return -1


def get_leaderboard(limit: int = 10) -> list[dict]:
    """
    Return the top players ordered by win count.

    Each entry contains: ``player_name``, ``wins``, ``avg_score``.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    player_name,
                    COUNT(*) AS wins,
                    AVG(final_score) AS avg_score
                FROM game_players
                WHERE placement = 1
                GROUP BY player_name
                ORDER BY wins DESC, avg_score DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("get_leaderboard failed: %s", exc)
        return []


def get_player_stats(name: str) -> dict:
    """
    Return statistics for a single player.

    Returned dict keys: ``player_name``, ``games_played``, ``wins``,
    ``avg_score``, ``best_score``.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT
                    player_name,
                    COUNT(*) AS games_played,
                    SUM(CASE WHEN placement = 1 THEN 1 ELSE 0 END) AS wins,
                    AVG(final_score) AS avg_score,
                    MAX(final_score) AS best_score
                FROM game_players
                WHERE player_name = ?
                GROUP BY player_name
                """,
                (name,),
            ).fetchone()

        if row is None:
            return {
                'player_name': name,
                'games_played': 0,
                'wins': 0,
                'avg_score': 0.0,
                'best_score': 0,
            }
        return dict(row)
    except sqlite3.Error as exc:
        logger.error("get_player_stats failed for %r: %s", name, exc)
        return {}


def get_all_games(limit: int = 20) -> list[dict]:
    """
    Return the most recent completed games.

    Each entry contains: ``id``, ``date``, ``winner_name``, ``winner_score``,
    ``num_players``, ``total_legs``, ``duration_seconds``.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    id,
                    date,
                    winner_name,
                    winner_score,
                    num_players,
                    total_legs,
                    duration_seconds
                FROM games
                ORDER BY date DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("get_all_games failed: %s", exc)
        return []
