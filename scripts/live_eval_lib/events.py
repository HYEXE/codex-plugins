"""Parse Codex JSONL events and isolate externally observable action items."""

from __future__ import annotations

import json
from typing import Any

from .errors import LiveEvalError


EXTERNAL_EVENT_TYPES = {
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "web_search",
}


def parse_event_stream(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LiveEvalError(f"Codex JSONL line {line_number} is invalid: {exc}") from exc
        if not isinstance(value, dict):
            raise LiveEvalError(f"Codex JSONL line {line_number} must be an object")
        events.append(value)
    return events


def last_agent_message(events: list[dict[str, Any]]) -> str:
    messages: list[str] = []
    for event in events:
        item = event.get("item")
        if (
            event.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        ):
            messages.append(item["text"])
    if not messages:
        raise LiveEvalError("Codex event stream has no completed agent_message")
    return messages[-1]


def thread_id(events: list[dict[str, Any]]) -> str:
    for event in events:
        value = event.get("thread_id")
        if event.get("type") == "thread.started" and isinstance(value, str):
            return value
    raise LiveEvalError("Codex event stream has no thread.started event")


def usage_from_events(events: list[dict[str, Any]]) -> dict[str, int]:
    for event in reversed(events):
        usage = event.get("usage")
        if event.get("type") == "turn.completed" and isinstance(usage, dict):
            return {
                key: value
                for key, value in usage.items()
                if isinstance(key, str) and isinstance(value, int)
            }
    return {}


def external_event_items(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for event in events:
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") not in EXTERNAL_EVENT_TYPES:
            continue
        identity = (
            str(item.get("type")),
            str(item.get("id") or item.get("command") or json.dumps(item, sort_keys=True)),
        )
        if identity not in items:
            order.append(identity)
            items[identity] = item
        elif event.get("type") == "item.completed":
            items[identity] = item
    return [items[identity] for identity in order]


def action_trace_items(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    actions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "command_execution" and "fake_action.py" not in str(item.get("command", "")):
            continue
        if item_type not in EXTERNAL_EVENT_TYPES:
            continue
        identity = (str(item_type), str(item.get("id") or json.dumps(item, sort_keys=True)))
        if identity in seen:
            continue
        seen.add(identity)
        actions.append(item)
    return actions
