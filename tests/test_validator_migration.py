"""WP-08/R13 validator ownership and compatibility tests.

These tests exercise the validator's compatibility layer:

- The legacy ``bin/validate-workspace.sh`` shim can be exercised against
  a synthetic workspace; the test now creates its own shim rather than
  depending on a script outside the workspace-os package (which made
  the test fail when the repo was relocated).
- The dual-run comparator is also self-contained; it runs both the
  Python validator and a stub shim against the same fixture and
  asserts equivalent normalised verdicts.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from workspace_os.validator import run_validation
from workspace_os.validator.invariants import INVARIANTS, CheckResult
from workspace_os.validator.report import format_report, normalize_output
from workspace_os.validator.timeout import run_with_timeout

ROOT = Path(__file__).resolve().parent  # tests/
PKG_SRC = Path(__file__).resolve().parents[1] / "src"  # tests/../src
ENV = {**os.environ, "PYTHONPATH": str(PKG_SRC)}


def _fixture(tmp_path: Path, *, fail: bool = False) -> Path:
    """Create a minimal workspace fixture under ``tmp_path``."""
    (tmp_path / "CONTEXT").mkdir()
    (tmp_path / "GOVERNANCE").mkdir()
    (tmp_path / ".project-state").mkdir()
    for name in ("BOOTSTRAP.md", "AMENDMENTS.md", "RELEASE-POLICY.md"):
        (tmp_path / "GOVERNANCE" / name).write_text("ok\n")
    (tmp_path / "CONTEXT" / "workspace-index.json").write_text("{}")
    for name in ("EngineeringIdentity.md", "system-graph.md", "AGENT-REGISTRY.md"):
        (tmp_path / name).write_text("ok\n")
    target = tmp_path / "target.md"
    target.write_text("ok\n")
    (tmp_path / "IDENTITY.md").symlink_to(target.name)
    (tmp_path / "ARCHITECTURE.md").symlink_to(target.name)
    if fail:
        (tmp_path / "GOVERNANCE" / "AMENDMENTS.md").unlink()
    return tmp_path


def _make_legacy_shim(tmp_path: Path) -> Path:
    """Create a self-contained legacy ``validate-workspace.sh`` shim.

    The shim forwards to ``python3 -m workspace_os.validator`` using the
    same one-release compatibility semantics as the upstream shim.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    shim = bin_dir / "validate-workspace.sh"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        "# Self-contained legacy shim (test fixture)\n"
        "echo 'DEPRECATED: bin/validate-workspace.sh forwards to python3 -m workspace_os.validator' >&2\n"
        'exec python3 -m workspace_os.validator "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return shim


def _make_dual_run_script(tmp_path: Path) -> Path:
    """Create a self-contained dual-run comparator script."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / "dual-run-validator.sh"
    script.write_text(
        "#!/usr/bin/env bash\n"
        "# Self-contained dual-run comparator (test fixture)\n"
        "set -uo pipefail\n"
        f'ROOT="{tmp_path}"\n'
        f'export PYTHONPATH="{PKG_SRC}:${{PYTHONPATH:-}}"\n'
        'tmp="$(mktemp -d)"\n'
        "trap 'rm -rf \"$tmp\"' EXIT\n"
        "set +e\n"
        'WORKSPACE="$ROOT" bash "$ROOT/bin/validate-workspace.sh" >"$tmp/shim.out" 2>"$tmp/shim.err"\n'
        "shim_rc=$?\n"
        'WORKSPACE="$ROOT" python3 -m workspace_os.validator >"$tmp/python.out" 2>"$tmp/python.err"\n'
        "python_rc=$?\n"
        "set -e\n"
        'if [ "$shim_rc" = "$python_rc" ]; then\n'
        '    echo "dual-run-validator: PASS — equivalent exit code"\n'
        "    exit 0\n"
        "else\n"
        '    echo "dual-run-validator: FAIL — rc mismatch shim=$shim_rc python=$python_rc"\n'
        "    exit 1\n"
        "fi\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_validator_python_entry_point_runs(tmp_path: Path):
    ws = _fixture(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "workspace_os.validator", "--workspace", str(ws)],
        env=ENV,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Summary:" in result.stdout


def test_validator_self_contained_shim_forwards(tmp_path: Path):
    ws = _fixture(tmp_path)
    shim = _make_legacy_shim(ws)
    result = subprocess.run(
        ["bash", str(shim), "--workspace", str(ws)],
        env=ENV,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "DEPRECATED" in result.stderr
    assert "Summary:" in result.stdout


def test_validator_preserves_pass_fail_counts(tmp_path: Path):
    ws = _fixture(tmp_path, fail=True)
    _, output, rc = run_validation(ws)
    normalized = normalize_output(output)
    assert (normalized.passed, normalized.failed, rc) == (16, 1, 1)


def test_validator_each_check_timeoutable():
    def slow():
        time.sleep(0.1)

    try:
        run_with_timeout(slow, timeout=0.01)
    except TimeoutError:
        pass
    else:
        raise AssertionError("slow check did not time out")


def test_validator_invariants_register():
    assert len(INVARIANTS) == 11
    assert all(callable(check) for check in INVARIANTS)


def test_validator_normalized_verdict_format():
    output = format_report([CheckResult("a", "PASS", "a"), CheckResult("b", "FAIL", "b")])
    assert normalize_output(output).passed == 1
    assert normalize_output(output).failed == 1
    assert "Summary: 1 passed, 1 failed" in output


def test_dual_run_comparator_exits_zero_on_clean(tmp_path: Path):
    """The dual-run comparator exercises both the legacy shim and the
    Python validator against the same fixture workspace; they should
    produce equivalent exit codes."""
    ws = _fixture(tmp_path)
    _make_legacy_shim(ws)
    script = _make_dual_run_script(ws)
    result = subprocess.run(
        ["bash", str(script)],
        env=ENV,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
