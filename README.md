# SISO Session Intelligence

Evidence-backed learning from agent sessions, without publishing the sessions.

The tool reads a Claude or Codex JSONL file only when you name it explicitly. It
normalizes the provider envelope, redacts sensitive material before persistence,
classifies useful moments into durable dimensions, scores importance, and exposes
local recall. It is offline and dependency-free.

## Quick start

```sh
./script/bootstrap
./bin/siso-session-intelligence --db ./session-intelligence.db ingest \
  --provider claude --input /path/to/session.jsonl
./bin/siso-session-intelligence --db ./session-intelligence.db stats
./bin/siso-session-intelligence --db ./session-intelligence.db recall "architecture"
```

Codex sessions use `--provider codex`. Re-running the same file is idempotent.

## What is stored

- Stable hashes for the source and session, never their absolute paths.
- Provider, role, timestamp, and a bounded redacted summary.
- Typed insights such as goals, decisions, failures, wins, intentions, tasks,
  friction, and ideas.
- A redacted evidence excerpt, recurrence count, and deterministic importance.

Raw transcript records, tool payloads, credentials, email addresses, and personal
home paths are not persisted. The SQLite database and exports are ignored by Git.

## Commands

```text
ingest   Normalize, redact, classify, and append one JSONL session
recall   Search ranked insights with their evidence references
stats    Show event and insight counts
export   Emit the privacy-reduced insight registry as JSON
```

Architecture and extraction reasoning are in
[`docs/ARCHITECTURE.html`](docs/ARCHITECTURE.html). The machine-readable source
disposition is [`MIGRATION-MAP.json`](MIGRATION-MAP.json).

## License

MIT. See [`LICENSE`](LICENSE).
