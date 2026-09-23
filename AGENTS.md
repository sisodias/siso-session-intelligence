# SISO Session Intelligence

**In one line:** Tool that turns explicitly supplied Claude or Codex session files into redacted, classified insights stored in a local recall database. District: `SISO_Agents` (`~/SISO_Workspace/SISO_Agents/siso-session-intelligence`).

## Purpose

Turn explicitly supplied Claude or Codex JSONL sessions into privacy-reduced,
traceable insights and recall. This repository never owns raw transcripts.

## First reads

- Product contract and commands: `README.md`
- System and data boundary: `docs/ARCHITECTURE.html`
- Warehouse-to-public decisions: `MIGRATION-MAP.json`
- Verification: `script/test`

## Invariants

- Never auto-discover a user's session directories.
- Never copy raw transcripts into this repository or its database.
- Redact before persistence; keep bounded evidence and hashed source locators.
- Ingest is idempotent by stable event identity.
- Provider adapters normalize into one contract; analysis never depends on a provider envelope.
- No network call is required or performed by the core pipeline.

## Operations

```sh
./script/bootstrap
./script/test
./bin/siso-session-intelligence --help
```
