"""Stable text and normalized-verdict formatting."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .invariants import CheckResult

__all__ = [
    "DRIFT_ID_RE",
    "NormalizedVerdict",
    "SUMMARY_RE",
    "format_report",
    "normalize_output",
]

SUMMARY_RE = re.compile(r"Summary:\s*(\d+)\s*passed,\s*(\d+)\s*failed", re.I)
DRIFT_ID_RE = re.compile(r"drift_id[=:]\s*([0-9a-f]+)", re.I)


@dataclass(frozen=True)
class NormalizedVerdict:
    passed: int
    failed: int
    drift_id: str = ""


def format_report(results: Iterable[CheckResult], *, generated: str | None = None, drift_id: str = "") -> str:
    rows = list(results)
    passed = sum(result.passed for result in rows)
    failed = len(rows) - passed
    generated = generated or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = ["================================================", "Workspace OS v2 — Validation Report", f"Generated: {generated}", "================================================"]
    for result in rows:
        lines.append(f"{result.status:<6}{result.message}")
        lines.extend(f"        {detail}" for detail in result.details)
    lines.append("================================================")
    lines.append(f"Summary: {passed} passed, {failed} failed")
    if drift_id:
        lines.append(f"drift_id={drift_id}")
    lines.append("================================================")
    return "\n".join(lines) + "\n"


def normalize_output(output: str) -> NormalizedVerdict:
    summary = SUMMARY_RE.search(output)
    passed, failed = map(int, summary.groups()) if summary else (0, 0)
    drift = DRIFT_ID_RE.search(output)
    return NormalizedVerdict(passed, failed, drift.group(1) if drift else "")
