"""
history.py — High-level interface to game history and statistics.

Wraps the low-level database functions with a clean, presentation-friendly
API.  All methods are safe to call even when the database is unavailable.
"""
from __future__ import annotations

import logging
from datetime import datetime

from storage import database

logger = logging.getLogger(__name__)


class GameHistory:
    """Provides a clean interface over the stored game history."""

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_recent_games(self, limit: int = 10) -> list[dict]:
        """
        Return up to *limit* recently completed games, newest first.

        Each dict contains: ``id``, ``date``, ``winner_name``,
        ``winner_score``, ``num_players``, ``total_legs``,
        ``duration_seconds``.
        """
        try:
            return database.get_all_games(limit=limit)
        except Exception as exc:
            logger.error("get_recent_games failed: %s", exc)
            return []

    def get_top_players(self, limit: int = 10) -> list[dict]:
        """
        Return up to *limit* players ranked by win count.

        Each dict contains: ``player_name``, ``wins``, ``avg_score``.
        """
        try:
            return database.get_leaderboard(limit=limit)
        except Exception as exc:
            logger.error("get_top_players failed: %s", exc)
            return []

    def record_game(self, state, duration_seconds: int) -> int:
        """
        Persist a completed game.

        Parameters
        ----------
        state:
            A ``GameState`` object with ``players`` and ``leg_number``.
        duration_seconds:
            Wall-clock length of the game in whole seconds.

        Returns
        -------
        int
            The new ``game_id`` (≥ 1), or -1 on failure.
        """
        try:
            return database.save_game(state, duration_seconds)
        except Exception as exc:
            logger.error("record_game failed: %s", exc)
            return -1

    # ------------------------------------------------------------------
    # Formatting utilities
    # ------------------------------------------------------------------

    @staticmethod
    def format_duration(seconds: int) -> str:
        """
        Convert a duration in seconds to a human-readable string.

        Examples
        --------
        >>> GameHistory.format_duration(125)
        '2m 5s'
        >>> GameHistory.format_duration(45)
        '0m 45s'
        """
        try:
            seconds = max(0, int(seconds))
            minutes, secs = divmod(seconds, 60)
            return f"{minutes}m {secs}s"
        except Exception as exc:
            logger.error("format_duration failed: %s", exc)
            return "0m 0s"

    @staticmethod
    def format_date(date_str: str) -> str:
        """
        Convert an ISO 8601 date/datetime string to a readable label.

        Examples
        --------
        >>> GameHistory.format_date('2026-03-24T14:05:00+00:00')
        'Mar 24, 2026'
        >>> GameHistory.format_date('2026-03-24')
        'Mar 24, 2026'
        """
        if not date_str:
            return ''
        # Try progressively simpler formats.
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',   # with timezone offset
            '%Y-%m-%dT%H:%M:%S',     # without timezone
            '%Y-%m-%d %H:%M:%S',     # space-separated datetime
            '%Y-%m-%d',              # date only
        ]
        # Strip trailing fractional seconds and Z before attempting parse.
        cleaned = date_str.split('.')[0].rstrip('Z')
        # Re-attach timezone offset if it was present after the fractional part.
        if '+' in date_str:
            tz_part = '+' + date_str.split('+', 1)[1]
            cleaned = cleaned + tz_part

        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.strftime('%b %d, %Y').replace(' 0', ' ')
            except ValueError:
                continue

        # Last resort: return the raw string.
        logger.warning("format_date: could not parse %r", date_str)
        return date_str
