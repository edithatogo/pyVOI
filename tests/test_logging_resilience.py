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
