"""Adversarial privacy and bounded-delivery logging contracts."""

import logging

import pytest

from voiage.logging import BoundedLogQueue, _redact_text


def test_redaction_removes_credentials_and_absolute_paths() -> None:
    text = "token=super-secret /Users/alice/private/patient.csv"
    scrubbed = _redact_text(text)
    assert "super-secret" not in scrubbed
    assert "/Users/alice/private" not in scrubbed


def test_bounded_queue_drops_low_severity_first() -> None:
    queue = BoundedLogQueue(capacity=2)
    queue.put(logging.INFO, "one")
    queue.put(logging.DEBUG, "two")
    queue.put(logging.ERROR, "three")
    assert queue.get() == (logging.DEBUG, "two")
    assert queue.get() == (logging.ERROR, "three")
    assert queue.dropped == 1


def test_bounded_queue_rejects_invalid_capacity() -> None:
    with pytest.raises(ValueError, match="capacity"):
        BoundedLogQueue(capacity=0)


def test_bounded_queue_rejects_low_priority_when_full() -> None:
    queue = BoundedLogQueue(capacity=1)
    queue.put(logging.ERROR, "critical")
    assert queue.put(logging.WARNING, "noise") is False
    assert queue.dropped == 1


def test_bounded_queue_scans_past_high_priority_entries() -> None:
    queue = BoundedLogQueue(capacity=2)
    queue.put(logging.ERROR, "critical")
    queue.put(logging.INFO, "detail")
    assert queue.put(logging.ERROR, "second-critical") is True
    assert queue.get() == (logging.ERROR, "critical")
    assert queue.get() == (logging.ERROR, "second-critical")
