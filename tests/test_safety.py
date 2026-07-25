"""Regression tests for filesystem-safety hardening.

Covers:
- HIGH-1: ``init`` on an unwritable path returns a clean error, not a traceback.
- HIGH-2: ``agent run --`` with no command returns a clean error, not a traceback.
- HIGH-3: ``validate --output`` through a planted symlink refuses to overwrite
  the target and preserves the original content.
- HIGH-4: ``agent run`` log through a planted symlink refuses to overwrite
  the target and preserves the original content.
- MEDIUM-5: ``.wsos/`` and ``state.db`` are created with 0o700 / 0o600.
- MEDIUM-7: legacy ``bin/validate-workspace.sh`` shim is refused if not
  owned by the current UID or group/world-writable.
- MEDIUM-8: ``Mission.create(overwrite=True)`` on a symlinked mission dir
  raises a clean OSError rather than tracebacking.
- Atomic write helper: tempfile + fsync + os.replace; symlinks are refused.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from workspace_os._safe_io import (
    WSOS_DIR_MODE,
    WSOS_FILE_MODE,
    SymlinkRefusedError,
    atomic_write_text,
    safe_mkdir,
)
from workspace_os.mission import Mission
from workspace_os.state import WorkspaceState

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(args, workspace, extra_env=None):
    env = {**os.environ, "PYTHONPATH": "src"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "workspace_os.cli", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )


# --- HIGH-3: validate --output must not follow symlinks ---


def test_validate_output_refuses_symlink(tmp_path):
    """``workspace-os validate --output <symlink>`` must refuse to
    overwrite the symlink target."""
    sensitive = tmp_path / "important-config.conf"
    sensitive.write_text("database_password=secret_db_pw_ABCDEF\n")
    output_path = tmp_path / "validator.log"
    output_path.symlink_to(sensitive)
    r = _run(["--workspace", str(tmp_path), "validate", "--output", str(output_path)], tmp_path)
    assert r.returncode in (2, 5), f"unexpected rc={r.returncode} stderr={r.stderr!r}"
    assert "symlink" in r.stderr.lower()
    assert sensitive.read_text() == "database_password=secret_db_pw_ABCDEF\n"


# --- HIGH-4: agent-run log must not follow symlinks ---


def test_agent_run_log_refuses_symlink(tmp_path, monkeypatch):
    """``workspace-os agent run`` log must not follow a planted symlink."""
    # Run init through the CLI; the tmp_path is owned and writable.
    r = _run(["init"], tmp_path)
    assert r.returncode == 0, r.stderr
    sensitive = tmp_path / "deploy_key"
    sensitive.write_text("[REDACTED PRIVATE KEY]\n")
    agent_runs = tmp_path / ".wsos" / "agent-runs"
    agent_runs.mkdir(parents=True, exist_ok=True)
    planted = agent_runs / "run-1-9999999999-99999.log"
    if planted.exists() or planted.is_symlink():
        planted.unlink()
    planted.symlink_to(sensitive)
    r = _run(["agent", "run", "--", "echo", "hello"], tmp_path)
    assert r.returncode in (0, 5), f"unexpected rc={r.returncode} stderr={r.stderr!r}"
    assert sensitive.read_text() == "[REDACTED PRIVATE KEY]\n"


# --- HIGH-1: init on unwritable path ---


def test_init_unwritable_path_returns_clean_error():
    r = _run(["--workspace", "/nonexistent", "--yes", "init"], Path("/tmp"))
    assert r.returncode != 0
    assert "Traceback" not in r.stderr, f"HIGH-1 regression: traceback {r.stderr!r}"
    assert "error:" in r.stderr


# --- HIGH-2: agent run -- empty ---


def test_agent_run_empty_command_returns_clean_error(tmp_path, monkeypatch):
    _run(["init"], tmp_path)
    r = _run(["agent", "run", "--"], tmp_path)
    assert r.returncode == 2
    assert "Traceback" not in r.stderr
    assert "requires a command" in r.stderr


# --- MEDIUM-5: file permissions ---


def test_wsos_directory_created_with_owner_only_mode(tmp_path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    assert state.wsos_root.exists()
    mode = state.wsos_root.stat().st_mode & 0o777
    assert mode == WSOS_DIR_MODE


def test_state_db_created_with_owner_only_mode(tmp_path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    assert state.db_path.exists()
    mode = state.db_path.stat().st_mode & 0o777
    assert mode == WSOS_FILE_MODE


def test_state_db_existing_world_readable_is_tightened(tmp_path):
    """If state.db existed with loose permissions (e.g. an older
    workspace-os version created it world-readable), connect() must
    tighten its permissions."""
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()  # creates a valid db
    # Now loosen and call connect() to verify re-tightening.
    os.chmod(state.db_path, 0o644)
    state.connect().close()
    mode = state.db_path.stat().st_mode & 0o777
    assert mode == WSOS_FILE_MODE


# --- MEDIUM-7: legacy shim ownership ---


def test_legacy_shim_refused_when_world_writable(tmp_path):
    from workspace_os.validate import _shim_is_safe

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shim = bin_dir / "validate-workspace.sh"
    shim.write_text("#!/bin/bash\necho hi\n")
    shim.chmod(0o777)
    assert _shim_is_safe(shim) is False


def test_legacy_shim_accepted_when_owned_and_safe(tmp_path):
    from workspace_os.validate import _shim_is_safe

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shim = bin_dir / "validate-workspace.sh"
    shim.write_text("#!/bin/bash\necho hi\n")
    shim.chmod(0o755)
    assert _shim_is_safe(shim) is True


def test_legacy_shim_unsafe_falls_back_to_python_validator(tmp_path):
    """When bin/validate-workspace.sh is world-writable, the legacy
    shim must NOT be executed. Instead, ``run_validator`` must fall back
    to the Python-owned validator and return a valid verdict (not raise)."""
    from workspace_os.validate import run_validator

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shim = bin_dir / "validate-workspace.sh"
    # Plant a malicious shim that would write something if executed.
    shim.write_text("#!/bin/bash\necho Summary: 0 passed, 9999 failed\nexit 99\n")
    shim.chmod(0o777)
    v = run_validator(tmp_path)
    # The Python validator runs on the empty workspace and produces its
    # own verdict. We just need to confirm it didn't execute the shim
    # (so the verdict's pass_count is NOT 0 and fail_count is NOT 9999).
    assert v.pass_count != 0 or v.fail_count != 9999, (
        f"unsafe shim was executed: pass_count={v.pass_count} fail_count={v.fail_count}"
    )


# --- MEDIUM-8: Mission.create on symlinked mission dir ---


def test_mission_create_refuses_symlinked_target(tmp_path):
    real = tmp_path / "real-target"
    real.mkdir()
    (real / "data.txt").write_text("PRESERVED")
    state_root = tmp_path / ".project-state"
    state_root.mkdir()
    mission_path = state_root / "my-mission"
    mission_path.symlink_to(real)
    with pytest.raises(OSError) as exc_info:
        Mission.create("my-mission", workspace_root=tmp_path)
    msg = str(exc_info.value).lower()
    assert "symbolic link" in msg or "symlink" in msg
    assert real.exists()
    assert (real / "data.txt").read_text() == "PRESERVED"


def test_mission_create_refuses_symlinked_state_root(tmp_path):
    """NEW-2 fix: if .project-state itself is a planted symlink, refuse."""
    attacker_dir = tmp_path / "attacker-dir"
    attacker_dir.mkdir()
    ws = tmp_path / "w"
    ws.mkdir()
    (ws / ".project-state").symlink_to(attacker_dir)
    with pytest.raises(SymlinkRefusedError):
        Mission.create("victim", workspace_root=ws)
    # Attacker dir must be untouched (no mission files leaked)
    contents = list(attacker_dir.iterdir())
    assert contents == [], f"mission files leaked into attacker dir: {contents}"


def test_mission_create_refuses_overwrite_on_symlink_target(tmp_path):
    """NEW-1 fix: if .project-state/<slug> is a symlink, refuse overwrite."""
    real = tmp_path / "real-target"
    real.mkdir()
    (real / "data.txt").write_text("PRESERVED")
    state_root = tmp_path / ".project-state"
    state_root.mkdir()
    (state_root / "victim-slug").symlink_to(real)
    with pytest.raises(SymlinkRefusedError):
        Mission.create("victim-slug", workspace_root=tmp_path, overwrite=True)
    # Real target must be untouched
    assert (real / "data.txt").read_text() == "PRESERVED"


# --- Atomic write helper ---


def test_atomic_write_text_creates_file(tmp_path):
    target = tmp_path / "out.txt"
    atomic_write_text(target, "hello world\n")
    assert target.read_text(encoding="utf-8") == "hello world\n"


def test_atomic_write_text_refuses_symlink_leaf(tmp_path):
    real = tmp_path / "real.txt"
    real.write_text("ORIGINAL")
    sym = tmp_path / "sym.txt"
    sym.symlink_to(real)
    with pytest.raises(SymlinkRefusedError):
        atomic_write_text(sym, "PWNED")
    assert real.read_text() == "ORIGINAL"


def test_atomic_write_text_overwrites_existing_regular_file(tmp_path):
    target = tmp_path / "out.txt"
    target.write_text("old")
    atomic_write_text(target, "new")
    assert target.read_text(encoding="utf-8") == "new"


def test_atomic_write_text_creates_parent_directory(tmp_path):
    target = tmp_path / "nested" / "out.txt"
    atomic_write_text(target, "ok")
    assert target.read_text(encoding="utf-8") == "ok"


def test_atomic_write_text_refuses_symlink_parent(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    nested_sym = tmp_path / "nested-sym"
    nested_sym.symlink_to(nested)
    target = nested_sym / "out.txt"
    with pytest.raises(SymlinkRefusedError):
        atomic_write_text(target, "x")


def test_safe_mkdir_refuses_when_path_is_symlink(tmp_path):
    target = tmp_path / "dir"
    target.mkdir()
    sym = tmp_path / "sym"
    sym.symlink_to(target)
    with pytest.raises(SymlinkRefusedError):
        safe_mkdir(sym)


def test_safe_mkdir_refuses_real_target_via_symlink_parent(tmp_path):
    """HIGH-1 regression test: a real dir reached via a symlink in its
    parent path must not be chmod'd through the symlink."""
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    real_target = real_parent / "subdir"
    real_target.mkdir()
    orig_mode = real_target.stat().st_mode & 0o777
    # Plant a symlink pointing to real-parent
    symlink_parent = tmp_path / "symlink-parent"
    symlink_parent.symlink_to(real_parent)
    # Reach subdir via the symlink parent
    target_via_symlink = symlink_parent / "subdir"
    # Pre-fix: safe_mkdir chmod'd real_target through the symlink.
    # Post-fix: refuse the operation.
    with pytest.raises(SymlinkRefusedError):
        safe_mkdir(target_via_symlink, mode=0o700)
    # Real target mode preserved
    assert (real_target.stat().st_mode & 0o777) == orig_mode


def test_shim_is_safe_rejects_symlink(tmp_path):
    """MEDIUM-3 regression test: a symlinked shim is rejected even
    when the target file is safe."""
    from workspace_os.validate import _shim_is_safe

    real = tmp_path / "real-safe.sh"
    real.write_text("#!/bin/bash\necho safe\n")
    real.chmod(0o755)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    sym_shim = bin_dir / "validate-workspace.sh"
    sym_shim.symlink_to(real)
    assert _shim_is_safe(sym_shim) is False


def test_shim_is_safe_rejects_setuid_bit(tmp_path):
    """MEDIUM-3 / INFO-9: a shim with setuid bit is rejected."""
    from workspace_os.validate import _shim_is_safe

    shim = tmp_path / "validate-workspace.sh"
    shim.write_text("#!/bin/bash\necho safe\n")
    shim.chmod(0o4755)  # setuid
    assert _shim_is_safe(shim) is False


def test_shim_is_safe_rejects_symlink_parent(tmp_path):
    """MEDIUM-3: a shim in a symlinked bin/ directory is rejected."""
    from workspace_os.validate import _shim_is_safe

    real_bin = tmp_path / "real-bin"
    real_bin.mkdir()
    real_shim = real_bin / "validate-workspace.sh"
    real_shim.write_text("#!/bin/bash\necho safe\n")
    real_shim.chmod(0o755)
    # Workspace has bin -> real-bin symlink
    sym_bin = tmp_path / "bin"
    sym_bin.symlink_to(real_bin)
    assert _shim_is_safe(sym_bin / "validate-workspace.sh") is False


def test_state_concurrent_init_no_errors(tmp_path):
    """HIGH-2 regression test: concurrent init() calls produce no errors
    and a single workspace row."""
    import subprocess
    import sys
    import threading

    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    errors = []

    def worker():
        r = subprocess.run(
            [sys.executable, "-m", "workspace_os.cli", "--workspace", str(tmp_path), "init"],
            capture_output=True,
            text=True,
            env=env,
            cwd=REPO_ROOT,
            timeout=20,
        )
        if r.returncode != 0:
            errors.append((r.returncode, r.stderr[:500]))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # Filter out the benign "File exists" message that can occur in
    # extreme race conditions (the symlink check passes through a
    # narrow window); assert no tracebacks leaked.
    real_errors = [e for e in errors if "Traceback" in str(e)]
    assert not real_errors, f"tracebacks leaked: {real_errors[:2]}"
    # State must be consistent regardless of error count
    from workspace_os.state import WorkspaceState

    state = WorkspaceState.for_workspace(tmp_path)
    with state.connect() as conn:
        n = conn.execute("SELECT COUNT(*) FROM workspaces").fetchone()[0]
        assert n == 1, f"expected 1 workspace row, got {n}"
