"""Policy-driven wrapper around the Python-owned validator."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from workspace_os._safe_io import (
    SymlinkRefusedError,
    atomic_write_text,
    safe_mkdir,
)
from workspace_os.policy import compute_drift_id, drift_categories, load_policy

__all__ = [
    "DEFAULT_POLICY_PATH",
    "SUMMARY_RE",
    "ValidatorVerdict",
    "run_validator",
]

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[2] / "policy.yaml"
SUMMARY_RE = re.compile(r"Summary:\s*(\d+)\s*passed,\s*(\d+)\s*failed", re.IGNORECASE)


def _shim_is_safe(shim_path: Path) -> bool:
    """Verify the legacy shim is safe to execute.

    MEDIUM-3 fix: the shim itself must be a regular file (not a
    symlink), must be owned by the current UID, must not be
    group/world-writable, and must not have setuid/setgid/sticky bits.
    Also rejects symlinks at any path level (defence against
    `bin/`-as-symlink attacks).

    Returns True iff the shim is owned by the current user and has a
    strict permission mode and no special bits. Otherwise False.
    """
    # MEDIUM-3: refuse if the shim path itself is a symlink (TOCTOU
    # window between check and subprocess.run) or any parent is a
    # symlink. ``os.lstat`` does not follow symlinks.
    try:
        st = os.lstat(shim_path)
    except OSError:
        return False
    # Refuse if the leaf is a symlink or any special file.
    import stat as stat_mod
    if not stat_mod.S_ISREG(st.st_mode):
        return False
    if st.st_uid != os.getuid():
        return False
    # Reject if group- or world-writable.
    if st.st_mode & 0o022:
        return False
    # Reject if setuid, setgid, or sticky bit is set (defence in depth).
    if st.st_mode & 0o7000:
        return False
    # MEDIUM-3: also refuse if any parent component is a symlink. An
    # attacker who can plant a symlink at `bin/` can swap the shim
    # even if the target file is safe.
    parent = shim_path.parent
    while parent != parent.parent:
        try:
            if parent.is_symlink():
                return False
        except OSError:
            return False
        parent = parent.parent
    return True


@dataclass
class ValidatorVerdict:
    pass_count: int
    fail_count: int
    raw_output: str
    raw_output_path: Optional[Path]
    exit_code: int
    drift_id: str = ""
    drift_categories: list[str] = field(default_factory=list)
    accepted: bool = False
    accept_rationale: str = ""
    policy_ok: bool = True

    @property
    def total(self) -> int:
        return self.pass_count + self.fail_count

    @property
    def ok(self) -> bool:
        # The frozen shell validator returns nonzero for the canonical 14/78
        # baseline; policy classification, not that legacy status, is authoritative.
        return self.policy_ok

    def __str__(self) -> str:
        accepted = " accepted" if self.accepted else ""
        return (f"{self.pass_count} PASS / {self.fail_count} FAIL (exit {self.exit_code}); "
                f"drift_id={self.drift_id}{accepted}")


def run_validator(
    workspace_root: Path,
    *,
    output_path: Optional[Path] = None,
    timeout: Optional[int] = None,
    policy_path: Optional[Path] = None,
    accept_drift: bool = False,
    accept_rationale: str = "",
    mission_id: Optional[int] = None,
    strict: bool = False,  # R14: --strict opt-in for hard-fail on any drift
) -> ValidatorVerdict:
    """Run the Python validator and classify its normalized drift.

    R14: ``strict=True`` flips the WARN-only default and treats any
    unexpected drift (categories not in ``known_drift``) as a hard fail.
    PRESERVE rule: categories in ``mandatory_drift`` are always hard fails,
    regardless of ``accept_drift`` or ``strict`` setting (defense-in-depth
    for security/audit JSON keys).
    """
    if accept_drift and not accept_rationale.strip():
        raise ValueError("--accept-drift requires a non-empty --accept-rationale")
    policy = load_policy(policy_path or DEFAULT_POLICY_PATH)
    # H-6 fix: the legacy "bin/validate-workspace.sh" fixture is no longer
    # required for the canonical workspace; the Python validator runs for
    # all workspaces. A workspace-local "bin/validate-workspace.sh" shim is
    # still honored if present (preserves WP-13 compat for non-canonical
    # workspaces), but the default is the Python engine.
    legacy_fixture = workspace_root / "bin" / "validate-workspace.sh"
    # Caller may tighten the limit, but may never exceed policy's 60s bound.
    effective_timeout = min(timeout or policy.invariants.max_runtime_seconds,
                            policy.invariants.max_runtime_seconds)
    if legacy_fixture.exists():
        # Compatibility path: workspace-local shim is present.
        # Defence-in-depth: only execute the shim if it is owned by the
        # current user and not group/world-writable. Otherwise fall back
        # to the Python peer validator rather than running attacker code.
        if _shim_is_safe(legacy_fixture):
            completed = subprocess.run(["bash", str(legacy_fixture)], cwd=str(workspace_root),
                                       capture_output=True, text=True, timeout=effective_timeout)
            raw_output = completed.stdout + completed.stderr
            returncode = completed.returncode
        else:
            # Fall back to the Python-owned validator. We deliberately do
            # NOT raise here: the operator may not have created the shim
            # and an unprivileged actor may have. Returning a verdict
            # from the Python engine is the safer outcome than refusing
            # the entire validation run.
            from workspace_os.validator import run_validation
            _, raw_output, returncode = run_validation(
                workspace_root, check_timeout=effective_timeout
            )
    else:
        # Default path: Python-owned validator peer.
        from workspace_os.validator import run_validation
        _, raw_output, returncode = run_validation(workspace_root, check_timeout=effective_timeout)
    if output_path is not None:
        # Atomic, symlink-safe write.
        try:
            atomic_write_text(output_path, raw_output)
        except SymlinkRefusedError as e:
            raise ValueError(
                f"refusing to write validator output to symlink: {output_path}"
            ) from e
    match = SUMMARY_RE.search(raw_output)
    passed, failed = (map(int, match.groups()) if match else (0, 0))
    categories = drift_categories(policy, raw_output)
    drift_id = compute_drift_id(policy, raw_output)
    forbidden = sorted(set(categories) & set(policy.forbidden_drift))
    unexpected = sorted(set(categories) - set(policy.known_drift))
    mandatory_hit = sorted(set(categories) & set(policy.mandatory_drift))  # R14 PRESERVE
    # Forbidden + mandatory drift can never be waived. Other unexpected
    # drift requires an explicit one-run acceptance; in --strict mode
    # even accepted drift fails.
    policy_ok = (
        not forbidden
        and not mandatory_hit
        and (not unexpected or (accept_drift and not strict))
    )
    accepted = bool(accept_drift and unexpected and not forbidden and not mandatory_hit and not strict)
    verdict = ValidatorVerdict(passed, failed, raw_output, output_path,
                               returncode, drift_id, categories,
                               accepted, accept_rationale.strip(), policy_ok)
    if accepted:
        audit_path = workspace_root / ".wsos" / "drift-acceptance.jsonl"
        # Defend against symlink attacks: refuse if the audit path or
        # any of its parent components is a symlink.
        safe_mkdir(audit_path.parent, mode=0o700)
        if audit_path.is_symlink():
            raise ValueError(
                f"refusing to append to symlink at {audit_path}"
            )
        record = {"ts": time.time(), "drift_id": drift_id,
                  "categories": unexpected, "rationale": accept_rationale.strip(),
                  "mission_id": mission_id}
        # Append atomically: write the full new contents to a tempfile
        # and replace. (jsonl files are append-only but we read-modify-write
        # to keep the operation atomic and symlink-safe.)
        existing = ""
        if audit_path.exists() and not audit_path.is_symlink():
            existing = audit_path.read_text(encoding="utf-8")
        atomic_write_text(audit_path, existing + json.dumps(record, sort_keys=True) + "\n")
    return verdict
