"""Python-owned Workspace OS validator (WP-08/R13)."""

from __future__ import annotations

import os
from pathlib import Path

from .invariants import INVARIANTS, CheckResult
from .report import format_report
from .timeout import DEFAULT_CHECK_TIMEOUT, run_with_timeout

__all__ = ["run_validation", "emit_r14_preserve_markers"]


def emit_r14_preserve_markers(workspace: Path, raw_output: str) -> str:
    """Inject R14 PRESERVE markers into validator output for the 3 mandatory_drift categories.

    The validator emit chain (in invariants.py) does not emit the three
    mandatory_drift categories. This post-processing step detects the
    underlying conditions and appends ``drift: <key>`` markers to the
    validator output so the policy parser (in policy.py drift_categories)
    picks them up and the PRESERVE rule actually fires.

    Mandatory categories:
        - sprint_pattern_incomplete: any mission under .project-state/
          missing one of the 8 sprint pattern files
        - missing_security_audit_log: ARCHIVE/audits/IDENTITY-AUTHORITY-MAP-ARCHIVED-2026-06-27.md
          is missing (the canonical security-audit artifact)
        - missing_audit_json_key: CONTEXT/workspace-index.json is missing
          or unparseable
    """
    markers: list[str] = []
    # sprint_pattern_incomplete
    project_state = workspace / ".project-state"
    if project_state.is_dir():
        from .invariants import SPRINT_PATTERN_FILES_FOR_PRESERVE as _SPRINT_FILES

        for mission in project_state.iterdir():
            if not mission.is_dir():
                continue
            for required in _SPRINT_FILES:
                if not (mission / required).is_file():
                    markers.append("drift: sprint_pattern_incomplete")
                    break
            else:
                continue
            break
    # missing_security_audit_log
    if not (workspace / "ARCHIVE" / "audits" / "IDENTITY-AUTHORITY-MAP-ARCHIVED-2026-06-27.md").is_file():
        markers.append("drift: missing_security_audit_log")
    # missing_audit_json_key
    index = workspace / "CONTEXT" / "workspace-index.json"
    if not index.is_file():
        markers.append("drift: missing_audit_json_key")
    else:
        try:
            import json

            data = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            markers.append("drift: missing_audit_json_key")
        else:
            if not isinstance(data, dict) or not data:
                markers.append("drift: missing_audit_json_key")
    if not markers:
        return raw_output
    suffix = "\n".join(markers) + "\n"
    return raw_output + suffix


def run_validation(
    workspace_root: Path | str | None = None, *, check_timeout: float = DEFAULT_CHECK_TIMEOUT
) -> tuple[list[CheckResult], str, int]:
    workspace = Path(
        workspace_root
        or os.environ.get("WORKSPACE")
        or os.environ.get("WORKSPACE_OS_ROOT")
        or Path.cwd()
    ).resolve()
    if not workspace.is_dir():
        message = f"environment: workspace root does not exist: {workspace}"
        result = CheckResult("environment", "FAIL", message)
        return [result], format_report([result]), 2
    results: list[CheckResult] = []
    for check in INVARIANTS:
        try:
            value = run_with_timeout(check, workspace, timeout=check_timeout)
            results.extend(value if isinstance(value, list) else [value])
        except TimeoutError:
            results.append(
                CheckResult(
                    check.__name__, "FAIL", f"{check.__name__}: timed out after {check_timeout:g}s"
                )
            )
        except Exception as exc:  # one failed check must not suppress the report
            results.append(
                CheckResult(check.__name__, "FAIL", f"{check.__name__}: environment error: {exc}")
            )
    output = format_report(results)
    # C-1 fix: emit the R14 PRESERVE mandatory-drift markers so the
    # parser picks them up. This activates the previously-nominal PRESERVE
    # rule.
    output = emit_r14_preserve_markers(workspace, output)
    return results, output, 1 if any(not item.passed for item in results) else 0
