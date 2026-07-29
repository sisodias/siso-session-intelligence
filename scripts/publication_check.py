#!/usr/bin/env python3
"""Fail closed on private warehouse material and credential-shaped strings."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", "__pycache__"}
FORBIDDEN_TEXT = (
    "shaan" + "sisodia",
    "tail100d11" + ".ts.net",
    "SISO_Workspace/" + ".SystemDB",
    "OPENROUTER_" + "API_KEY=",
)
CREDENTIAL = re.compile(r"\b(?:sk|gh[opsu])[-_][A-Za-z0-9_-]{16,}\b")

checked = 0
for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in EXCLUDED for part in path.parts):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    checked += 1
    for forbidden in FORBIDDEN_TEXT:
        if forbidden in text:
            raise SystemExit(f"publication check failed: {path.relative_to(ROOT)} contains forbidden private material")
    if CREDENTIAL.search(text):
        raise SystemExit(f"publication check failed: {path.relative_to(ROOT)} contains a credential-shaped value")

print(f"SESSION_INTELLIGENCE_PUBLICATION_OK ({checked} text files)")
