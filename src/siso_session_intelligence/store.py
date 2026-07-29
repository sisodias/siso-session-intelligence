"""SQLite source of truth for privacy-reduced events and derived insights."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  session_hash TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  provider TEXT NOT NULL,
  role TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  summary TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS insights (
  insight_id TEXT PRIMARY KEY,
  dimension TEXT NOT NULL,
  dedup_key TEXT NOT NULL,
  title TEXT NOT NULL,
  evidence_excerpt TEXT NOT NULL,
  evidence_event_id TEXT NOT NULL REFERENCES events(event_id),
  recurrence INTEGER NOT NULL DEFAULT 1,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  importance REAL NOT NULL DEFAULT 0,
  UNIQUE(dimension, dedup_key)
);
CREATE INDEX IF NOT EXISTS idx_insights_rank ON insights(importance DESC, recurrence DESC);
"""


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def append_event(self, row: dict) -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO events VALUES (:event_id,:session_hash,:source_hash,:provider,:role,:observed_at,:summary)",
            row,
        )
        return cursor.rowcount == 1

    def upsert_insight(self, row: dict) -> None:
        self.connection.execute(
            """INSERT INTO insights
               (insight_id,dimension,dedup_key,title,evidence_excerpt,evidence_event_id,first_seen,last_seen)
               VALUES (:insight_id,:dimension,:dedup_key,:title,:evidence_excerpt,:evidence_event_id,:observed_at,:observed_at)
               ON CONFLICT(dimension,dedup_key) DO UPDATE SET
                 recurrence=insights.recurrence+1,
                 last_seen=excluded.last_seen,
                 evidence_excerpt=excluded.evidence_excerpt,
                 evidence_event_id=excluded.evidence_event_id""",
            row,
        )

    def rescore(self) -> None:
        from .scoring import importance
        rows = self.connection.execute(
            "SELECT insight_id,dimension,recurrence,last_seen FROM insights"
        ).fetchall()
        maximum = max((row["recurrence"] for row in rows), default=1)
        for row in rows:
            value = importance(row["dimension"], row["recurrence"], row["last_seen"], maximum)
            self.connection.execute(
                "UPDATE insights SET importance=? WHERE insight_id=?", (value, row["insight_id"])
            )
        self.connection.commit()

    def recall(self, query: str, limit: int = 10) -> list[dict]:
        pattern = f"%{query.lower()}%"
        rows = self.connection.execute(
            """SELECT dimension,title,evidence_excerpt,evidence_event_id,recurrence,importance,last_seen
               FROM insights
               WHERE lower(title) LIKE ? OR lower(evidence_excerpt) LIKE ? OR lower(dimension) LIKE ?
               ORDER BY importance DESC, recurrence DESC LIMIT ?""",
            (pattern, pattern, pattern, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> dict:
        events = self.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        insights = self.connection.execute("SELECT COUNT(*) FROM insights").fetchone()[0]
        dimensions = {
            row[0]: row[1]
            for row in self.connection.execute(
                "SELECT dimension,COUNT(*) FROM insights GROUP BY dimension ORDER BY dimension"
            )
        }
        return {"events": events, "insights": insights, "dimensions": dimensions}

    def export(self) -> list[dict]:
        rows = self.connection.execute(
            """SELECT insight_id,dimension,title,evidence_excerpt,evidence_event_id,
                      recurrence,importance,first_seen,last_seen
               FROM insights ORDER BY importance DESC, insight_id"""
        ).fetchall()
        return [dict(row) for row in rows]

    def export_json(self) -> str:
        return json.dumps({"schema_version": "1.0.0", "insights": self.export()}, indent=2) + "\n"
