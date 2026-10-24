import pytest

from grok_hermes_webhook.validate import ValidationError, extract_task


def test_extract_task_ok():
    assert extract_task({"task": "  hello  "}) == "hello"


def test_alias_message():
    assert extract_task({"message": "via message"}) == "via message"


def test_empty_task():
    with pytest.raises(ValidationError, match="empty"):
        extract_task({"task": "  "})


def test_missing_task():
    with pytest.raises(ValidationError, match="missing"):
        extract_task({"source": "x"})


def test_non_object():
    with pytest.raises(ValidationError):
        extract_task(["not", "an", "object"])  # type: ignore[arg-type]
