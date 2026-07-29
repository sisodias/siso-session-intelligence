"""Command-line surface over the stable local contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import ingest
from .store import Store


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="siso-session-intelligence")
    root.add_argument("--db", type=Path, default=Path("session-intelligence.db"))
    commands = root.add_subparsers(dest="command", required=True)
    ingest_command = commands.add_parser("ingest", help="ingest one explicit JSONL file")
    ingest_command.add_argument("--provider", choices=("claude", "codex"), required=True)
    ingest_command.add_argument("--input", type=Path, required=True)
    recall = commands.add_parser("recall", help="search ranked privacy-reduced insights")
    recall.add_argument("query")
    recall.add_argument("--limit", type=int, default=10)
    commands.add_parser("stats", help="show database counts")
    export = commands.add_parser("export", help="write the privacy-reduced registry")
    export.add_argument("--output", type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    args.db.parent.mkdir(parents=True, exist_ok=True)
    store = Store(args.db)
    try:
        if args.command == "ingest":
            if not args.input.is_file():
                raise SystemExit(f"input does not exist: {args.input}")
            print(json.dumps(ingest(args.input, args.provider, store), indent=2))
        elif args.command == "recall":
            print(json.dumps({"query": args.query, "results": store.recall(args.query, args.limit)}, indent=2))
        elif args.command == "stats":
            print(json.dumps(store.stats(), indent=2))
        elif args.command == "export":
            payload = store.export_json()
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(payload, encoding="utf-8")
                print(args.output)
            else:
                print(payload, end="")
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
