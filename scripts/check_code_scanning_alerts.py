#!/usr/bin/env python3
"""Fail closed when blocking code-scanning alerts exist for a commit.

The GitHub code-scanning API occasionally returns transient 5xx/429 responses
after SARIF upload.  Retries are limited to those responses; findings and all
other errors remain blocking.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import sys
import time
from typing import Any
import urllib.error
import urllib.request

DEFAULT_PER_PAGE = 100
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_RETRY_ATTEMPTS = 4
BLOCKING_SEVERITIES = {"high", "critical"}


@dataclass(frozen=True)
class AlertHit:
    """A blocking code-scanning alert."""

    number: int
    rule_id: str
    severity: str
    message: str
    html_url: str


def parse_args() -> argparse.Namespace:
    """Parse command-line options and GitHub defaults."""
    parser = argparse.ArgumentParser(
        description="Fail if the current commit has open high/critical alerts."
    )
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument(
        "--token", default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    )
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--retry-attempts", type=int, default=DEFAULT_RETRY_ATTEMPTS)
    parser.add_argument("--per-page", type=int, default=DEFAULT_PER_PAGE)
    return parser.parse_args()


def _http_get_json(url: str, token: str | None) -> Any:
    request = urllib.request.Request(  # noqa: S310
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _fetch_page(
    repository: str,
    token: str | None,
    page: int,
    per_page: int,
    *,
    deadline: float,
    retry_attempts: int,
) -> list[dict[str, Any]]:
    url = (
        f"https://api.github.com/repos/{repository}/code-scanning/alerts"
        f"?state=open&per_page={per_page}&page={page}"
    )
    for attempt in range(max(retry_attempts, 1)):
        try:
            payload = _http_get_json(url, token)
        except urllib.error.HTTPError as exc:
            transient = exc.code == 429 or 500 <= exc.code <= 599
            if (
                not transient
                or attempt + 1 >= retry_attempts
                or time.monotonic() >= deadline
            ):
                raise
            delay = min(30.0, 2.0**attempt * 5.0)
            time.sleep(min(delay, max(0.0, deadline - time.monotonic())))
            continue
        except urllib.error.URLError:
            if attempt + 1 >= retry_attempts or time.monotonic() >= deadline:
                raise
            delay = min(30.0, 2.0**attempt * 5.0)
            time.sleep(min(delay, max(0.0, deadline - time.monotonic())))
            continue
        if not isinstance(payload, list):
            raise TypeError(f"Unexpected API payload for {url}")
        return payload
    raise RuntimeError(f"Unable to query {url} before timeout")


def iter_open_alerts(
    repository: str,
    token: str | None,
    *,
    per_page: int = DEFAULT_PER_PAGE,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
) -> list[dict[str, Any]]:
    """Fetch all open alerts, retrying only transient API failures."""
    deadline = time.monotonic() + max(timeout_seconds, 0)
    alerts: list[dict[str, Any]] = []
    for page in range(1, 101):
        page_alerts = _fetch_page(
            repository,
            token,
            page,
            per_page,
            deadline=deadline,
            retry_attempts=retry_attempts,
        )
        alerts.extend(page_alerts)
        if len(page_alerts) < per_page:
            break
    return alerts


def alert_severity(alert: dict[str, Any]) -> str:
    """Return the normalized security severity for an alert."""
    rule = alert.get("rule") or {}
    severity = str(rule.get("security_severity_level") or "").lower()
    return severity or str(rule.get("severity") or "").lower()


def blocking_alerts(alerts: list[dict[str, Any]], *, commit_sha: str) -> list[AlertHit]:
    """Select high/critical alerts whose latest instance is on ``commit_sha``."""
    hits: list[AlertHit] = []
    for alert in alerts:
        recent = alert.get("most_recent_instance") or {}
        if str(recent.get("commit_sha") or "") != commit_sha:
            continue
        severity = alert_severity(alert)
        if severity not in BLOCKING_SEVERITIES:
            continue
        rule = alert.get("rule") or {}
        message = (recent.get("message") or {}).get("text") or ""
        hits.append(
            AlertHit(
                number=int(alert.get("number") or 0),
                rule_id=str(rule.get("id") or "unknown"),
                severity=severity,
                message=message,
                html_url=str(alert.get("html_url") or ""),
            )
        )
    return hits


def main() -> int:
    """Run the fail-closed alert check."""
    args = parse_args()
    if not args.repository or not args.commit_sha:
        print("repository and commit-sha are required", file=sys.stderr)
        return 2
    try:
        alerts = iter_open_alerts(
            args.repository,
            args.token,
            per_page=args.per_page,
            timeout_seconds=args.timeout_seconds,
            retry_attempts=args.retry_attempts,
        )
    except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as exc:
        print(
            f"Failed to query code-scanning alerts after bounded retries: {exc}",
            file=sys.stderr,
        )
        return 1

    hits = blocking_alerts(alerts, commit_sha=args.commit_sha)
    if hits:
        print("Blocking code-scanning alerts found:")
        for hit in hits:
            print(
                f"- #{hit.number} {hit.rule_id} [{hit.severity}] {hit.message} ({hit.html_url})"
            )
        return 1
    print("No open high/critical code-scanning alerts found for the current commit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
