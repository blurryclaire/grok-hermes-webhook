"""Payload validation: require a non-empty task (with aliases)."""

from __future__ import annotations

from typing import Any

TASK_ALIASES = ("task", "message", "prompt", "instruction")
MAX_TASK_LEN = 8000
MAX_BODY_BYTES = 1 * 1024 * 1024  # 1 MiB


class ValidationError(ValueError):
    """Invalid webhook payload."""


def extract_task(payload: dict[str, Any]) -> str:
    """Return stripped task text from payload or raise ValidationError."""
    if not isinstance(payload, dict):
        raise ValidationError("payload must be a JSON object")

    raw: Any = None
    for key in TASK_ALIASES:
        if key in payload and payload[key] is not None:
            raw = payload[key]
            break

    if raw is None:
        raise ValidationError("missing task (accepted keys: task|message|prompt|instruction)")

    if not isinstance(raw, str):
        raise ValidationError("task must be a string")

    task = raw.strip()
    if not task:
        raise ValidationError("empty task")
    if len(task) > MAX_TASK_LEN:
        raise ValidationError(f"task exceeds {MAX_TASK_LEN} characters")
    return task
