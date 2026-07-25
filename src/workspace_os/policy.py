"""Versioned drift-classification policy and deterministic drift identifiers."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import BinaryIO, cast

import yaml

__all__ = [
    "Invariants",
    "Policy",
    "compute_drift_id",
    "drift_categories",
    "load_policy",
    "validate_policy",
]


@dataclass(frozen=True)
class Invariants:
    min_pass_count: int
    max_fail_count: int
    max_runtime_seconds: int


@dataclass(frozen=True)
class Policy:
    schema_version: int
    invariants: Invariants
    known_drift: tuple[str, ...]
    forbidden_drift: tuple[str, ...]
    baseline_pass_count: int
    baseline_fail_count: int
    mandatory_drift: tuple[str, ...] = ()  # R14 PRESERVE rule
    source_bytes: bytes = b""


def load_policy(path: Path | str | Traversable) -> Policy:
    if isinstance(path, (Path, str)):
        raw = Path(path).read_bytes()
    else:
        with cast(BinaryIO, path.open("rb")) as stream:
            raw = stream.read()
    data = yaml.safe_load(raw) or {}
    inv = data.get("invariants") or {}
    baseline = data.get("baseline") or {}
    policy = Policy(
        schema_version=data.get("schema_version") or 0,
        invariants=Invariants(
            inv.get("min_pass_count") or 0,
            inv.get("max_fail_count") or 0,
            inv.get("max_runtime_seconds") or 0,
        ),
        known_drift=tuple(data.get("known_drift") or ()),
        forbidden_drift=tuple(data.get("forbidden_drift") or ()),
        mandatory_drift=tuple(data.get("mandatory_drift") or ()),
        baseline_pass_count=baseline.get("pass_count") or 0,
        baseline_fail_count=baseline.get("fail_count") or 0,
        source_bytes=raw,
    )
    errors = validate_policy(policy)
    if errors:
        raise ValueError("invalid policy: " + "; ".join(errors))
    return policy


def validate_policy(policy: Policy) -> list[str]:
    errors: list[str] = []
    if policy.schema_version != 1:
        errors.append("schema_version must be 1")
    values = {
        "invariants.min_pass_count": policy.invariants.min_pass_count,
        "invariants.max_fail_count": policy.invariants.max_fail_count,
        "invariants.max_runtime_seconds": policy.invariants.max_runtime_seconds,
        "baseline.pass_count": policy.baseline_pass_count,
        "baseline.fail_count": policy.baseline_fail_count,
    }
    for name, value in values.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{name} must be a non-negative integer")
    if (
        isinstance(policy.invariants.max_runtime_seconds, int)
        and not 1 <= policy.invariants.max_runtime_seconds <= 60
    ):
        errors.append("invariants.max_runtime_seconds must be between 1 and 60")
    if policy.baseline_pass_count != policy.invariants.min_pass_count:
        errors.append("baseline.pass_count must equal invariants.min_pass_count")
    if policy.baseline_fail_count != policy.invariants.max_fail_count:
        errors.append("baseline.fail_count must equal invariants.max_fail_count")
    for name, items in (
        ("known_drift", policy.known_drift),
        ("forbidden_drift", policy.forbidden_drift),
        ("mandatory_drift", policy.mandatory_drift),
    ):
        if not all(isinstance(item, str) and item.strip() for item in items):
            errors.append(f"{name} entries must be non-empty strings")
    return errors


def drift_categories(policy: Policy, validator_output: str) -> list[str]:
    """Extract actual categories, independent of volatile ordering/noise."""
    categories: set[str] = set()
    summary = re.search(r"Summary:\s*(\d+)\s*passed,\s*(\d+)\s*failed", validator_output, re.I)
    if not summary:
        categories.add("missing_summary")
    else:
        passed, failed = map(int, summary.groups())
        if passed < policy.invariants.min_pass_count:
            categories.add("pass_count_below_minimum")
        if failed > policy.invariants.max_fail_count:
            categories.add("fail_count_above_maximum")
        if (passed, failed) != (policy.baseline_pass_count, policy.baseline_fail_count):
            categories.add(f"baseline_count:{passed}/{failed}")
    # Explicit machine-readable categories emitted by validators/fixtures.
    categories.update(
        re.findall(r"(?:DRIFT(?:_CATEGORY)?|drift)\s*[:=]\s*([a-zA-Z0-9_.-]+)", validator_output)
    )
    return sorted(categories)


def compute_drift_id(policy: Policy, validator_output: str) -> str:
    """SHA-256(policy bytes + canonical actual category list)."""
    policy_hash = hashlib.sha256(policy.source_bytes).hexdigest()
    canonical = json.dumps(
        {"policy_sha256": policy_hash, "categories": drift_categories(policy, validator_output)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(canonical).hexdigest()
