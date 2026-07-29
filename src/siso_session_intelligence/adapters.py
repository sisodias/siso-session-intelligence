"""Provider envelopes normalized into one small event contract."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SessionEvent:
    event_id: str
    session_id: str
    provider: str
    role: str
    timestamp: str
    text: str
    cwd: str


def _text(content: object) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind in {"text", "input_text", "output_text"} or (
            "text" in block and kind not in {"tool_use", "tool_result"}
        ):
            parts.append(str(block.get("text", "")))
    return "\n".join(part for part in parts if part)


def _stable_id(provider: str, session_id: str, line_number: int, role: str, text: str) -> str:
    value = f"{provider}\0{session_id}\0{line_number}\0{role}\0{text}".encode()
    return hashlib.sha256(value).hexdigest()


def _records(path: Path) -> Iterable[tuple[int, dict]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(value, dict):
                yield line_number, value


def read_claude(path: Path) -> list[SessionEvent]:
    events: list[SessionEvent] = []
    fallback_session = hashlib.sha256(path.read_bytes()).hexdigest()[:24]
    for line_number, record in _records(path):
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or record.get("type") or "")
        if role not in {"user", "assistant"}:
            continue
        content = _text(message.get("content")).strip()
        if not content:
            continue
        session_id = str(record.get("sessionId") or fallback_session)
        event_id = str(record.get("uuid") or _stable_id("claude", session_id, line_number, role, content))
        events.append(SessionEvent(event_id, session_id, "claude", role,
                                   str(record.get("timestamp") or ""), content,
                                   str(record.get("cwd") or "")))
    return events


def read_codex(path: Path) -> list[SessionEvent]:
    events: list[SessionEvent] = []
    fallback_session = hashlib.sha256(path.read_bytes()).hexdigest()[:24]
    session_id, cwd = fallback_session, ""
    for line_number, record in _records(path):
        envelope_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        payload_type = payload.get("type")
        if envelope_type == "session_meta" or payload_type == "session_meta":
            session_id = str(payload.get("id") or session_id)
            cwd = str(payload.get("cwd") or cwd)
            continue
        role, content = "", ""
        if envelope_type == "response_item" or payload_type == "response_item":
            role = str(payload.get("role") or "")
            content = _text(payload.get("content")).strip()
        elif payload_type in {"agent_message", "user_message"}:
            role = "assistant" if payload_type == "agent_message" else "user"
            content = str(payload.get("message") or payload.get("text") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        event_id = _stable_id("codex", session_id, line_number, role, content)
        events.append(SessionEvent(event_id, session_id, "codex", role,
                                   str(record.get("timestamp") or ""), content, cwd))
    return events


def read_session(path: Path, provider: str) -> list[SessionEvent]:
    if provider == "claude":
        return read_claude(path)
    if provider == "codex":
        return read_codex(path)
    raise ValueError(f"unsupported provider: {provider}")
