"""Tests for workspace_os.state.WorkspaceState."""

from __future__ import annotations

import time
from pathlib import Path

from workspace_os.state import WorkspaceState


def test_init_creates_directory_and_db(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    assert not state.db_path.exists()
    state.init()
    assert state.wsos_root.exists()
    assert state.db_path.exists()


def test_init_is_idempotent(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    state.init()
    assert state.db_path.exists()


def test_schema_tables_present(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    with state.connect() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    names = {r[0] for r in rows}
    assert {
        "workspaces",
        "missions",
        "mission_artifacts",
        "validator_runs",
        "agent_runs",
    } <= names


def test_register_workspace_creates_row(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    assert isinstance(wid, int)
    with state.connect() as conn:
        row = conn.execute(
            "SELECT root_path FROM workspaces WHERE workspace_id = ?", (wid,)
        ).fetchone()
    assert row[0] == str(tmp_path.resolve())


def test_register_workspace_idempotent(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid1 = state.register_workspace(tmp_path)
    wid2 = state.register_workspace(tmp_path)
    assert wid1 == wid2


def test_register_mission(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    mid = state.register_mission(wid, "test-slug", tmp_path / ".project-state" / "test-slug")
    assert isinstance(mid, int)


def test_register_mission_idempotent_on_slug(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    m1 = state.register_mission(wid, "alpha", tmp_path / ".project-state" / "alpha")
    m2 = state.register_mission(wid, "alpha", tmp_path / ".project-state" / "alpha")
    assert m1 == m2


def test_close_mission(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    mid = state.register_mission(wid, "x", tmp_path / ".project-state" / "x")
    state.close_mission(mid)
    with state.connect() as conn:
        status = conn.execute(
            "SELECT status FROM missions WHERE mission_id = ?", (mid,)
        ).fetchone()[0]
    assert status == "closed"


def test_close_mission_idempotent(tmp_path: Path):
    """Second close is a true no-op: status stays 'closed', closed_at is NOT
    overwritten, and close_mission still returns 'closed' on both calls."""
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    mid = state.register_mission(wid, "alpha-idemp", tmp_path / ".project-state" / "alpha-idemp")
    # First close — performs the transition.
    assert state.close_mission(mid) == "closed"
    with state.connect() as conn:
        first_closed_at, first_status = conn.execute(
            "SELECT closed_at, status FROM missions WHERE mission_id = ?",
            (mid,),
        ).fetchone()
    assert first_status == "closed"
    assert first_closed_at is not None and first_closed_at > 0
    # Sleep so a regression that overwrites closed_at would be detectable.
    time.sleep(0.05)
    # Second close — must be a no-op.
    assert state.close_mission(mid) == "closed"
    with state.connect() as conn:
        second_closed_at, second_status = conn.execute(
            "SELECT closed_at, status FROM missions WHERE mission_id = ?",
            (mid,),
        ).fetchone()
    assert second_status == "closed"
    assert second_closed_at == first_closed_at, (
        f"closed_at was overwritten on idempotent re-close: "
        f"first={first_closed_at}, second={second_closed_at}"
    )


def test_close_mission_returns_status(tmp_path: Path):
    """close_mission returns 'closed' on first and second calls; returns None
    for an unknown mission_id."""
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    mid = state.register_mission(wid, "alpha-rs", tmp_path / ".project-state" / "alpha-rs")
    # First close — returns 'closed'.
    assert state.close_mission(mid) == "closed"
    # Second close — returns 'closed' (no-op path).
    assert state.close_mission(mid) == "closed"
    # Unknown mission_id — returns None.
    assert state.close_mission(99999) is None


def test_record_mission_artifact(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    mid = state.register_mission(wid, "a", tmp_path / ".project-state" / "a")
    state.record_mission_artifact(mid, "progress.md", True, "deadbeef", time.time())
    with state.connect() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM mission_artifacts WHERE mission_id = ?", (mid,)
        ).fetchone()[0]
    assert n == 1


def test_record_mission_artifact_upsert(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    mid = state.register_mission(wid, "a", tmp_path / ".project-state" / "a")
    state.record_mission_artifact(mid, "progress.md", False, None, None)
    state.record_mission_artifact(mid, "progress.md", True, "abc", time.time())
    with state.connect() as conn:
        row = conn.execute(
            'SELECT "exists", sha256 FROM mission_artifacts WHERE mission_id = ? AND filename = ?',
            (mid, "progress.md"),
        ).fetchone()
    assert row[0] == 1
    assert row[1] == "abc"


def test_record_validator_run(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    rid = state.record_validator_run(wid, 14, 78, tmp_path / "out.txt")
    assert isinstance(rid, int)


def test_latest_validator_run(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    assert state.latest_validator_run(wid) is None
    state.record_validator_run(wid, 14, 78, None)
    state.record_validator_run(wid, 15, 77, None)
    latest = state.latest_validator_run(wid)
    assert latest is not None
    assert latest["pass_count"] == 15


def test_record_agent_run(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    mid = state.register_mission(wid, "a", tmp_path / ".project-state" / "a")
    rid = state.record_agent_run(mid, "echo hello", 0, None)
    assert isinstance(rid, int)


def test_list_missions(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    state.register_mission(wid, "m1", tmp_path / ".project-state" / "m1")
    state.register_mission(wid, "m2", tmp_path / ".project-state" / "m2")
    missions = state.list_missions(workspace_id=wid)
    slugs = {m["slug"] for m in missions}
    assert slugs == {"m1", "m2"}


def test_list_missions_empty(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    wid = state.register_workspace(tmp_path)
    assert state.list_missions(workspace_id=wid) == []


def test_iter_workspaces(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    state.register_workspace(tmp_path)
    state.register_workspace(tmp_path / "sub")
    workspaces = list(state.iter_workspaces())
    assert len(workspaces) >= 1


def test_default_state_root():
    state = WorkspaceState.default()
    assert state.wsos_root == Path.home() / ".wsos"


def test_foreign_keys_enabled(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    with state.connect() as conn:
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1


def test_wal_mode(tmp_path: Path):
    state = WorkspaceState.for_workspace(tmp_path)
    state.init()
    with state.connect() as conn:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"
