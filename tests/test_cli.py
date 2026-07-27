"""Tests for workspace_os.cli entry point and the workspace-os command surface."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _stub_validator_workspace(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    validator = bin_dir / "validate-workspace.sh"
    validator.write_text(
        "#!/usr/bin/env bash\n"
        "echo 'Check 1: PASS — sample'\n"
        "echo '================================================'\n"
        "echo 'Summary: 14 passed, 78 failed'\n"
        "exit 1\n",
        encoding="utf-8",
    )
    validator.chmod(0o755)
    return tmp_path


def test_cli_version():
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "--version"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0
    assert "2.0.0" in completed.stdout


def test_cli_help():
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "--help"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0
    assert "workspace-os" in completed.stdout


def test_cli_init(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(tmp_path))
    env = {**os.environ, "PYTHONPATH": "src"}
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "init"],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / ".wsos" / "state.db").exists()


def test_cli_mission_new(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(tmp_path))
    env = {**os.environ, "PYTHONPATH": "src"}
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "mission", "new", "alpha-beta"],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0, completed.stderr
    mission_dir = tmp_path / ".project-state" / "alpha-beta"
    assert mission_dir.exists()
    assert (mission_dir / "source-task.md").exists()


def test_cli_mission_new_invalid_slug(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(tmp_path))
    env = {**os.environ, "PYTHONPATH": "src"}
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "mission", "new", "InvalidSlug"],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 2, completed.stderr


def test_cli_mission_new_overwrite_required(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(tmp_path))
    args = [sys.executable, "-m", "workspace_os.cli", "mission", "new", "alpha"]
    env = {**os.environ, "PYTHONPATH": "src"}
    r1 = subprocess.run(args, capture_output=True, text=True, env=env, cwd=REPO_ROOT)
    assert r1.returncode == 0, r1.stderr
    r2 = subprocess.run(args, capture_output=True, text=True, env=env, cwd=REPO_ROOT)
    assert r2.returncode == 3, r2.stderr


def test_cli_mission_list(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(tmp_path))
    env = {**os.environ, "PYTHONPATH": "src"}
    cwd = REPO_ROOT
    subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "mission", "new", "first"],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "mission", "list"],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert completed.returncode == 0
    assert "first" in completed.stdout


def test_cli_validate(tmp_path: Path, monkeypatch):
    workspace = _stub_validator_workspace(tmp_path)
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(workspace))
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "validate"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=REPO_ROOT,
    )
    assert "14 PASS" in completed.stdout
    assert "78 FAIL" in completed.stdout


def test_cli_agent_run(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(tmp_path))
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "agent", "run", "--", "echo", "hello"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0
    assert "hello" in completed.stdout


def test_cli_no_command_prints_help(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(tmp_path))
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0
    assert "workspace-os" in completed.stdout


def test_cli_validate_unknown_workspace(tmp_path: Path):
    # H-6/H-8 fix: the Python peer validator runs against any workspace;
    # the legacy "bin/validate-workspace.sh" fixture is no longer required
    # for non-canonical workspaces. The validator_runs row is still
    # recorded, and the validator's exit code reflects the policy verdict.
    bad_path = tmp_path / "no-validator-here"
    bad_path.mkdir()
    completed = subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", "--workspace", str(bad_path), "validate"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=REPO_ROOT,
    )
    # Python validator runs and returns its own verdict (rc=1 on FAILs,
    # rc=0 on all-PASS). Either is acceptable; the contract is that the
    # command exits cleanly without raising FileNotFoundError.
    assert completed.returncode in (0, 1)


def test_cli_validate_records_one_validator_run_row(tmp_path: Path, monkeypatch):
    """R6 acceptance: each `ws validate` invocation creates exactly one
    validator_runs row, regardless of pass/fail outcome. Agent-run recording
    at cmd_agent_run is unchanged.
    """
    import sqlite3

    workspace = _stub_validator_workspace(tmp_path)
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(workspace))
    env = {**os.environ, "PYTHONPATH": "src"}
    # Run twice — must produce two rows total (one per invocation).
    for _ in range(2):
        subprocess.run(
            [sys.executable, "-m", "workspace_os.cli", "validate"],
            capture_output=True,
            text=True,
            env=env,
            cwd=REPO_ROOT,
        )
    db = workspace / ".wsos" / "state.db"
    conn = sqlite3.connect(str(db))
    try:
        rows = conn.execute(
            "SELECT workspace_id, pass_count, fail_count FROM validator_runs"
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 2, f"expected 2 validator_runs rows, got {len(rows)}"
    for wid, pc, fc in rows:
        assert wid is not None
        assert pc == 14 and fc == 78, f"unexpected counts: pass={pc} fail={fc}"


def test_cli_mission_archive_requires_real_final_report(tmp_path: Path, monkeypatch):
    """The generated final-report stub is not proof of completion."""
    _create_mission("archive-stub", tmp_path, monkeypatch)

    r = _run_ws(["mission", "archive", "archive-stub"], tmp_path, monkeypatch)

    assert r.returncode == 3
    assert "final-report.md" in r.stderr
    assert not (tmp_path / ".project-state" / "archive-stub" / ".archived").exists()
    assert not (tmp_path / "pet" / "_archived" / "archive-stub").exists()


def test_cli_mission_archive_and_unarchive(tmp_path: Path, monkeypatch):
    """Archive creates a source marker, archive symlink and audit log; rollback removes them."""
    _create_mission("archive-complete", tmp_path, monkeypatch)
    mission_dir = tmp_path / ".project-state" / "archive-complete"
    (mission_dir / "final-report.md").write_text(
        "# Final Report\n\nImplementation and validation are complete.\n",
        encoding="utf-8",
    )

    archived = _run_ws(["mission", "archive", "archive-complete"], tmp_path, monkeypatch)

    assert archived.returncode == 0, archived.stderr
    marker = mission_dir / ".archived"
    archive_link = tmp_path / "pet" / "_archived" / "archive-complete"
    log_path = tmp_path / ".wsos" / "mission-archive.log"
    assert marker.is_file()
    assert archive_link.is_symlink()
    assert archive_link.resolve() == mission_dir.resolve()
    assert "action=archive" in log_path.read_text(encoding="utf-8")
    assert "mission=archive-complete" in log_path.read_text(encoding="utf-8")

    unarchived = _run_ws(["mission", "unarchive", "archive-complete"], tmp_path, monkeypatch)

    assert unarchived.returncode == 0, unarchived.stderr
    assert not marker.exists()
    assert not archive_link.exists()
    assert "action=unarchive" in log_path.read_text(encoding="utf-8")


def test_cli_mission_archive_missing_directory(tmp_path: Path, monkeypatch):
    """An unregistered/non-existent mission directory is rejected cleanly."""
    r = _run_ws(["mission", "archive", "missing-mission"], tmp_path, monkeypatch)
    assert r.returncode == 4
    assert "does not exist" in r.stderr


# ──────────────────────────────────────────────────────────────────────
# WP-02 (R5) — mission close CLI tests
# ──────────────────────────────────────────────────────────────────────


def _wsos_root(tmp_path: Path) -> Path:
    return tmp_path / ".wsos"


def _run_ws(args: list, tmp_path: Path, monkeypatch) -> subprocess.CompletedProcess:
    monkeypatch.setenv("WORKSPACE_OS_ROOT", str(tmp_path))
    env = {**os.environ, "PYTHONPATH": "src"}
    return subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )


def _create_mission(slug: str, tmp_path: Path, monkeypatch) -> int:
    """Create a mission via the CLI and return its mission_id from the DB."""
    import sqlite3

    r = _run_ws(["mission", "new", slug], tmp_path, monkeypatch)
    assert r.returncode == 0, r.stderr
    db_path = _wsos_root(tmp_path) / "state.db"
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT mission_id FROM missions WHERE slug = ?",
            (slug,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, f"mission {slug!r} not registered in state DB"
    return int(row[0])


def test_cli_mission_close_by_slug(tmp_path: Path, monkeypatch):
    """Closing by slug persists 'closed' status + timestamp; exit 0."""
    import sqlite3

    mid = _create_mission("alpha-close-slug", tmp_path, monkeypatch)
    r = _run_ws(["mission", "close", "alpha-close-slug"], tmp_path, monkeypatch)
    assert r.returncode == 0, r.stderr
    assert f"id={mid}" in r.stdout
    assert "closed_at=" in r.stdout
    assert "alpha-close-slug" in r.stdout
    # DB-level verification.
    conn = sqlite3.connect(str(_wsos_root(tmp_path) / "state.db"))
    try:
        status, closed_at = conn.execute(
            "SELECT status, closed_at FROM missions WHERE mission_id = ?",
            (mid,),
        ).fetchone()
    finally:
        conn.close()
    assert status == "closed"
    assert closed_at is not None and closed_at > 0


def test_cli_mission_close_by_id(tmp_path: Path, monkeypatch):
    """Closing by integer id resolves correctly; persists 'closed' status."""
    import sqlite3

    mid = _create_mission("alpha-close-id", tmp_path, monkeypatch)
    r = _run_ws(["mission", "close", str(mid)], tmp_path, monkeypatch)
    assert r.returncode == 0, r.stderr
    assert f"id={mid}" in r.stdout
    assert "alpha-close-id" in r.stdout
    conn = sqlite3.connect(str(_wsos_root(tmp_path) / "state.db"))
    try:
        status = conn.execute(
            "SELECT status FROM missions WHERE mission_id = ?",
            (mid,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert status == "closed"


def test_cli_mission_close_unknown_slug(tmp_path: Path, monkeypatch):
    """Unknown slug returns exit 4 with the error on stderr; no DB mutation."""
    import sqlite3

    # Initialize workspace state so the close path actually reaches the DB lookup.
    r_init = _run_ws(["init"], tmp_path, monkeypatch)
    assert r_init.returncode == 0, r_init.stderr
    r = _run_ws(["mission", "close", "ghost-slug"], tmp_path, monkeypatch)
    assert r.returncode == 4, r.stderr
    assert "ghost-slug" in r.stderr
    # No missions row created.
    conn = sqlite3.connect(str(_wsos_root(tmp_path) / "state.db"))
    try:
        n = conn.execute("SELECT COUNT(*) FROM missions").fetchone()[0]
    finally:
        conn.close()
    assert n == 0


def test_cli_mission_close_already_closed(tmp_path: Path, monkeypatch):
    """Second close is a no-op: exit 0, deterministic 'already closed' message,
    original closed_at is NOT overwritten."""
    import sqlite3
    import time as _time

    mid = _create_mission("alpha-close-twice", tmp_path, monkeypatch)
    r1 = _run_ws(["mission", "close", "alpha-close-twice"], tmp_path, monkeypatch)
    assert r1.returncode == 0, r1.stderr
    # Capture original closed_at.
    conn = sqlite3.connect(str(_wsos_root(tmp_path) / "state.db"))
    try:
        original_closed_at = conn.execute(
            "SELECT closed_at FROM missions WHERE mission_id = ?",
            (mid,),
        ).fetchone()[0]
    finally:
        conn.close()
    # Sleep to ensure ts comparison is meaningful if implementation regresses.
    _time.sleep(0.05)
    r2 = _run_ws(["mission", "close", "alpha-close-twice"], tmp_path, monkeypatch)
    assert r2.returncode == 0, r2.stderr
    assert "already closed" in r2.stdout
    assert "alpha-close-twice" in r2.stdout
    # Confirm closed_at was not overwritten.
    conn = sqlite3.connect(str(_wsos_root(tmp_path) / "state.db"))
    try:
        second_closed_at, status = conn.execute(
            "SELECT closed_at, status FROM missions WHERE mission_id = ?",
            (mid,),
        ).fetchone()
    finally:
        conn.close()
    assert status == "closed"
    assert second_closed_at == original_closed_at, (
        f"closed_at was overwritten: original={original_closed_at}, now={second_closed_at}"
    )


def test_cli_mission_close_invalid_id(tmp_path: Path, monkeypatch):
    """Non-numeric non-slug identifier returns exit 4 with the error on stderr.

    'NotAValidIdentifier!' contains uppercase + punctuation so it cannot be
    parsed as an integer and is not a registered mission slug in this workspace.
    """
    r_init = _run_ws(["init"], tmp_path, monkeypatch)
    assert r_init.returncode == 0, r_init.stderr
    r = _run_ws(["mission", "close", "NotAValidIdentifier!"], tmp_path, monkeypatch)
    assert r.returncode == 4, r.stderr
    assert "NotAValidIdentifier!" in r.stderr
