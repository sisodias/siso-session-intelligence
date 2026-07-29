from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from siso_session_intelligence.pipeline import ingest
from siso_session_intelligence.store import Store

ROOT = Path(__file__).resolve().parents[1]


class SessionIntelligenceSystemTest(unittest.TestCase):
    def test_two_providers_privacy_idempotence_and_recall(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "state.db"
            store = Store(database)
            try:
                claude = ingest(ROOT / "fixtures" / "claude.jsonl", "claude", store)
                codex = ingest(ROOT / "fixtures" / "codex.jsonl", "codex", store)
                again = ingest(ROOT / "fixtures" / "claude.jsonl", "claude", store)
                self.assertEqual(2, claude["events_inserted"])
                self.assertEqual(2, codex["events_inserted"])
                self.assertEqual(0, again["events_inserted"])
                stats = store.stats()
                self.assertEqual(4, stats["events"])
                self.assertGreaterEqual(stats["insights"], 5)
                self.assertTrue(store.recall("architecture"))
                payload = json.loads(store.export_json())
                self.assertEqual("1.0.0", payload["schema_version"])
            finally:
                store.close()
            raw_database = database.read_bytes()
            self.assertNotIn(b"fixture-sensitive-value", raw_database)
            self.assertNotIn(b"fixture@example.test", raw_database)
            self.assertNotIn(b"/home/fixture-person", raw_database)
            self.assertIn(b"<credential>", raw_database)
            with sqlite3.connect(database) as connection:
                self.assertEqual(4, connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
