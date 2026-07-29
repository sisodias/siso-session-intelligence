"""Normalize → redact → classify → aggregate → score."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re

from .adapters import SessionEvent, read_session
from .privacy import redact
from .store import Store

_DIMENSIONS = (
    ("failures", re.compile(r"\b(fail(?:ed|ure)?|error|broken|doesn['’]?t work|bug)\b", re.I)),
    ("decisions", re.compile(r"\b(decid(?:e|ed)|choos(?:e|ing)|going with|decision)\b", re.I)),
    ("wins", re.compile(r"\b(pass(?:ed|es)?|working|fixed|complete(?:d)?|done|shipped)\b", re.I)),
    ("goals", re.compile(r"\b(goal|need to|want to|objective|must)\b", re.I)),
    ("intentions", re.compile(r"\b(next|will|plan(?:ning)?|intend)\b", re.I)),
    ("tasks", re.compile(r"\b(build|implement|create|add|update|extract|publish|deploy)\b", re.I)),
    ("friction", re.compile(r"\b(confus(?:ed|ing)|unclear|annoy(?:ed|ing)?|hard|friction)\b", re.I)),
    ("ideas", re.compile(r"\b(idea|could|what if|perhaps|maybe we)\b", re.I)),
)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _dedup_key(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return " ".join(words[:32])


def classify(summary: str) -> list[str]:
    return [name for name, pattern in _DIMENSIONS if pattern.search(summary)]


def _insight(event: SessionEvent, summary: str, dimension: str) -> dict:
    key = _dedup_key(summary)
    observed = event.timestamp or "1970-01-01T00:00:00+00:00"
    return {
        "insight_id": _hash(f"{dimension}\0{key}"),
        "dimension": dimension,
        "dedup_key": key,
        "title": summary[:120],
        "evidence_excerpt": summary,
        "evidence_event_id": event.event_id,
        "observed_at": observed,
    }


def ingest(path: Path, provider: str, store: Store) -> dict:
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    events = read_session(path, provider)
    inserted, insights = 0, 0
    for event in events:
        summary = redact(event.text)
        if not summary:
            continue
        row = {
            "event_id": event.event_id,
            "session_hash": _hash(event.session_id),
            "source_hash": source_hash,
            "provider": event.provider,
            "role": event.role,
            "observed_at": event.timestamp or "1970-01-01T00:00:00+00:00",
            "summary": summary,
        }
        if not store.append_event(row):
            continue
        inserted += 1
        for dimension in classify(summary):
            store.upsert_insight(_insight(event, summary, dimension))
            insights += 1
    store.rescore()
    return {"provider": provider, "events_read": len(events), "events_inserted": inserted,
            "insight_observations": insights, "source_hash": source_hash}
