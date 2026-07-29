"""Deterministic importance scoring; no model or network dependency."""

from __future__ import annotations

from datetime import datetime, timezone
import math

SOURCE_WEIGHTS = {
    "goals": 1.00,
    "decisions": 0.95,
    "wins": 0.85,
    "intentions": 0.80,
    "tasks": 0.75,
    "failures": 0.70,
    "friction": 0.70,
    "ideas": 0.55,
}


def importance(dimension: str, recurrence: int, last_seen: str,
               max_recurrence: int, decay: float = 0.005) -> float:
    try:
        observed = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        age_hours = max(0.0, (datetime.now(timezone.utc) - observed).total_seconds() / 3600)
    except (TypeError, ValueError):
        age_hours = 24.0
    recency = math.exp(-decay * age_hours)
    frequency = math.log1p(max(1, recurrence)) / math.log1p(max(1, max_recurrence))
    source = SOURCE_WEIGHTS.get(dimension, 0.5)
    return round(0.4 * recency + 0.3 * frequency + 0.3 * source, 6)
