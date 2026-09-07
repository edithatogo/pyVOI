"""Adversarial privacy and bounded-delivery logging contracts."""

import logging

import pytest

import voiage.logging as logging_module


def test_redaction_removes_credentials_and_absolute_paths() -> None:
    text = "token=super-secret /Users/alice/private/patient.csv"
    scrubbed = logging_module._redact_text(text)
    assert "super-secret" not in scrubbed
    assert "/Users/alice/private" not in scrubbed


def test_bounded_queue_drops_low_severity_first() -> None:
    queue = logging_module.BoundedLogQueue(capacity=2)
    queue.put(logging.INFO, "one")
    queue.put(logging.DEBUG, "two")
    queue.put(logging.ERROR, "three")
    assert queue.get() == (logging.INFO, "one")
    assert queue.get() == (logging.ERROR, "three")
    assert queue.dropped == 1


def test_bounded_queue_rejects_invalid_capacity() -> None:
    with pytest.raises(ValueError, match="capacity"):
        logging_module.BoundedLogQueue(capacity=0)


def test_bounded_queue_rejects_low_priority_when_full() -> None:
    queue = logging_module.BoundedLogQueue(capacity=1)
    queue.put(logging.ERROR, "critical")
    assert queue.put(logging.WARNING, "noise") is False
    assert queue.dropped == 1


def test_bounded_queue_scans_past_high_priority_entries() -> None:
    queue = logging_module.BoundedLogQueue(capacity=2)
    queue.put(logging.ERROR, "critical")
    queue.put(logging.INFO, "detail")
    assert queue.put(logging.ERROR, "second-critical") is True
    assert queue.get() == (logging.ERROR, "critical")
    assert queue.get() == (logging.ERROR, "second-critical")


def test_bounded_queue_rejects_when_all_entries_are_high_priority() -> None:
    queue = logging_module.BoundedLogQueue(capacity=2)
    queue.put(logging.ERROR, "first")
    queue.put(logging.CRITICAL, "second")
    assert queue.put(logging.ERROR, "third") is False
