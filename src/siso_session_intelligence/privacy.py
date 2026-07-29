"""Redaction happens before any session-derived text reaches persistence."""

from __future__ import annotations

import re

MAX_SUMMARY_CHARS = 480

_RULES = (
    (re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[^\s,;]+"), "<credential>"),
    (re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+[^\s,;]+"), "Authorization: <credential>"),
    (re.compile(r"\b(?:sk|gh[opsu])[-_][A-Za-z0-9_-]{12,}\b"), "<credential>"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "<credential>"),
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "<email>"),
    (re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/[^\s/]+"), "<home>"),
    (re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+"), "<home>"),
    (re.compile(r"https?://[^\s/]+\.ts\.net(?::\d+)?"), "<private-host>"),
)


def redact(text: str, limit: int = MAX_SUMMARY_CHARS) -> str:
    """Return a whitespace-normalized, bounded, privacy-reduced excerpt."""
    value = str(text or "")
    for pattern, replacement in _RULES:
        value = pattern.sub(replacement, value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > limit:
        return value[: max(0, limit - 1)].rstrip() + "…"
    return value
