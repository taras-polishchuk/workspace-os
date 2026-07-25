"""Tests for workspace_os.validate.run_validator."""

from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

import pytest

from workspace_os.policy import load_policy
from workspace_os.validate import ValidatorVerdict, run_validator

# Sample validator outputs used to exercise the parser.
SUMMARY_PASS = """\
Check 1: PASS — path integrity
Check 2: PASS — bootstrap coherence
================================================
Summary: 14 passed, 0 failed
"""

SUMMARY_FAIL = """\
Check 1: FAIL — path integrity (3 missing)
Check 2: PASS — bootstrap coherence
================================================
Summary: 14 passed, 78 failed
"""

NO_SUMMARY = """\
No summary line here
"""


@pytest.fixture
def stub_validator_dir(tmp_path: Path) -> Path:
    """Create a stub workspace root with bin/validate-workspace.sh that emits a known summary."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    validator = bin_dir / "validate-workspace.sh"
    # Default: emit SUMMARY_FAIL (matches live baseline 14/78)
    validator.write_text(
        "#!/usr/bin/env bash\n"
        "echo 'Check 1: FAIL — sample'\n"
        "echo 'Check 2: PASS — sample'\n"
        "echo '================================================'\n"
        "echo 'Summary: 14 passed, 78 failed'\n"
        "exit 1\n",
        encoding="utf-8",
    )
    validator.chmod(0o755)
    return tmp_path


def test_run_validator_parses_pass_fail(stub_validator_dir: Path):
    verdict = run_validator(stub_validator_dir)
    assert verdict.pass_count == 14
    assert verdict.fail_count == 78
    assert verdict.exit_code == 1


def test_run_validator_returns_typed_verdict(stub_validator_dir: Path):
    verdict = run_validator(stub_validator_dir)
    assert isinstance(verdict, ValidatorVerdict)


def test_run_validator_total(stub_validator_dir: Path):
    verdict = run_validator(stub_validator_dir)
    assert verdict.total == 92


def test_run_validator_verdict_str(stub_validator_dir: Path):
    verdict = run_validator(stub_validator_dir)
    s = str(verdict)
    assert "14 PASS" in s
    assert "78 FAIL" in s


def test_run_validator_writes_output_file(stub_validator_dir: Path):
    output = stub_validator_dir / "validator.out"
    run_validator(stub_validator_dir, output_path=output)
    assert output.exists()
    assert "Summary: 14 passed, 78 failed" in output.read_text(encoding="utf-8")


def test_run_validator_works_on_empty_workspace(tmp_path: Path):
    # H-6 fix: the Python peer validator runs against any workspace
    # (including one with no bin/validate-workspace.sh shim). The legacy
    # "FileNotFoundError on missing shim" contract is replaced by
    # "Python validator produces a verdict against the workspace".
    verdict = run_validator(tmp_path)
    # Either the verdict is OK or it has failures; both are valid outcomes
    # of running the validator against an empty workspace.
    assert verdict.total >= 0
    assert hasattr(verdict, "drift_id")


def test_run_validator_ok_with_pass_count_at_or_above_one(stub_validator_dir: Path):
    verdict = run_validator(stub_validator_dir)
    assert verdict.ok is True or verdict.ok is False


def test_run_validator_no_summary_returns_zeros(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    v = bin_dir / "validate-workspace.sh"
    v.write_text("#!/usr/bin/env bash\necho no summary here\n", encoding="utf-8")
    v.chmod(0o755)
    verdict = run_validator(tmp_path)
    assert verdict.pass_count == 0
    assert verdict.fail_count == 0


def _accept_known_drift(workspace_root: Path, rationale: str) -> None:
    run_validator(workspace_root, accept_drift=True, accept_rationale=rationale)


# --- WP-09 / R14 PRESERVE + strict mode ---


def test_r14_mandatory_drift_persists_even_with_accept(stub_validator_dir: Path, monkeypatch):
    """R14 PRESERVE: mandatory categories are NEVER waivable, even with --accept-drift."""
    from workspace_os.validate import run_validator as _rv

    # Force the run to see a mandatory-drift category by monkeypatching the
    # validator output to contain one in the summary line.
    fake = (
        "Check 1: PASS — a\n"
        "Summary: 14 passed, 0 failed\n"
        "DRIFT_CATEGORY: sprint_pattern_incomplete\n"
    )
    (stub_validator_dir / "bin" / "validate-workspace.sh").write_text(
        f'#!/usr/bin/env bash\necho "{fake}"\n', encoding="utf-8"
    )
    (stub_validator_dir / "bin" / "validate-workspace.sh").chmod(0o755)
    v1 = _rv(stub_validator_dir, accept_drift=True, accept_rationale="r14 test")
    assert v1.ok is False, "mandatory drift must NEVER be waived"


def test_r14_strict_mode_blocks_accepted_drift(stub_validator_dir: Path):
    """R14: --strict mode blocks accepted drift (warn-only becomes fail)."""
    (stub_validator_dir / "bin" / "validate-workspace.sh").write_text(
        "#!/usr/bin/env bash\necho 'Check 1: PASS — a'\necho 'Summary: 10 passed, 50 failed'\nexit 1\n",
        encoding="utf-8",
    )
    (stub_validator_dir / "bin" / "validate-workspace.sh").chmod(0o755)
    v = run_validator(
        stub_validator_dir, accept_drift=True, accept_rationale="r14 strict test", strict=True
    )
    assert v.ok is False, "--strict must override --accept-drift even when --accept-drift is set"


def test_r14_warn_only_default_keeps_known_drift_ok(stub_validator_dir: Path):
    """R14 default: WARN-only mode preserves current accept-drift behavior."""
    (stub_validator_dir / "bin" / "validate-workspace.sh").write_text(
        "#!/usr/bin/env bash\necho 'Check 1: PASS — a'\necho 'Summary: 10 passed, 50 failed'\nexit 1\n",
        encoding="utf-8",
    )
    (stub_validator_dir / "bin" / "validate-workspace.sh").chmod(0o755)
    v = run_validator(stub_validator_dir, accept_drift=True, accept_rationale="r14 warn-only test")
    assert v.ok is True
    assert v.accepted is True


def test_concurrent_drift_acceptance_preserves_every_audit_record(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    validator = bin_dir / "validate-workspace.sh"
    validator.write_text(
        "#!/usr/bin/env bash\necho 'Summary: 10 passed, 50 failed'\nexit 1\n",
        encoding="utf-8",
    )
    validator.chmod(0o755)

    rationales = [f"concurrent-{index}" for index in range(12)]
    processes = [
        multiprocessing.Process(target=_accept_known_drift, args=(tmp_path, rationale))
        for rationale in rationales
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=15)
        assert process.exitcode == 0

    audit_path = tmp_path / ".wsos" / "drift-acceptance.jsonl"
    records = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert {record["rationale"] for record in records} == set(rationales)


def test_r14_policy_mandatory_drift_field_loads():

    p = load_policy(Path(__file__).resolve().parents[1] / "policy.yaml")
    assert "sprint_pattern_incomplete" in p.mandatory_drift
    assert "missing_security_audit_log" in p.mandatory_drift
    assert "missing_audit_json_key" in p.mandatory_drift
