"""SQLite state manager for ``<workspace_root>/.wsos/state.db``.

The state database lives at the workspace-local ``.wsos/state.db`` (per
`WorkspaceState.for_workspace(workspace_root)`). The
``DEFAULT_WSOS_ROOT`` module-level constant is a legacy default and is
NOT used by the CLI; every CLI command routes through ``for_workspace``
which writes to ``<workspace_root>/.wsos/state.db``.

The state database tracks:
    - workspaces (workspace_id, root_path, created_at, last_seen_at)
    - missions (mission_id, slug, status, created_at, closed_at, root_path)
    - mission_artifacts (mission_id, filename, exists, sha256, mtime)
    - validator_runs (run_id, ts, pass_count, fail_count, raw_output)
    - agent_runs (run_id, mission_id, ts, command, exit_code)

The schema is forward-compatible with the Phase 5+ Evidence Ledger (A-5).
Per Article VII (Sprint Pattern), the canonical filesystem is the source
of truth for mission identity; this DB is a derived cache.

HIGH-2 fix: ``init()`` and ``connect()`` use an advisory file lock
(``fcntl.flock`` on ``.wsos/.init.lock``) to serialise concurrent
bootstrap. SQLite ``PRAGMA busy_timeout=5000`` is set so concurrent
writers from already-locked processes wait up to 5s instead of
failing immediately with ``database is locked``.
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import os
import sqlite3
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from workspace_os._safe_io import (
    WSOS_DIR_MODE,
    WSOS_FILE_MODE,
    safe_mkdir,
    tighten_existing_file,
)

#: SQLite busy timeout (ms). Concurrent writers from already-locked
#: processes wait up to this duration before failing with
#: ``OperationalError: database is locked``.
BUSY_TIMEOUT_MS = 5000

#: Filename of the advisory process-level lock that serialises
#: ``WorkspaceState.init()`` and the first ``connect()`` against a
#: workspace. Lives inside ``.wsos/`` so it is hidden from the
#: filesystem view but always travels with the workspace.
_INIT_LOCK_NAME = ".init.lock"

__all__ = [
    "SCHEMA",
    "DEFAULT_WSOS_ROOT",
    "DEFAULT_DB_PATH",
    "WorkspaceState",
]

DEFAULT_WSOS_ROOT = Path.home() / ".wsos"  # legacy default; CLI uses for_workspace() instead
DEFAULT_DB_PATH = DEFAULT_WSOS_ROOT / "state.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS workspaces (
    workspace_id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_path TEXT NOT NULL UNIQUE,
    created_at REAL NOT NULL,
    last_seen_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS missions (
    mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    workspace_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at REAL NOT NULL,
    closed_at REAL,
    root_path TEXT NOT NULL,
    UNIQUE(workspace_id, slug),
    FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id)
);

CREATE TABLE IF NOT EXISTS mission_artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    "exists" INTEGER NOT NULL,
    sha256 TEXT,
    mtime REAL,
    UNIQUE(mission_id, filename),
    FOREIGN KEY(mission_id) REFERENCES missions(mission_id)
);

CREATE TABLE IF NOT EXISTS validator_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    ts REAL NOT NULL,
    pass_count INTEGER NOT NULL,
    fail_count INTEGER NOT NULL,
    raw_output_path TEXT,
    FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id)
);

CREATE TABLE IF NOT EXISTS agent_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER,
    ts REAL NOT NULL,
    command TEXT NOT NULL,
    exit_code INTEGER NOT NULL,
    output_path TEXT,
    FOREIGN KEY(mission_id) REFERENCES missions(mission_id)
);

CREATE INDEX IF NOT EXISTS idx_missions_workspace ON missions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);
CREATE INDEX IF NOT EXISTS idx_validator_runs_workspace ON validator_runs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_mission ON agent_runs(mission_id);
"""


@dataclass
class WorkspaceState:
    """A handle to the workspace-os SQLite state database.

    The DB is created lazily on first connect. Multiple instances pointing
    at the same path share a single SQLite file (WAL mode allows concurrent
    readers but only one writer).
    """

    db_path: Path = DEFAULT_DB_PATH
    wsos_root: Path = DEFAULT_WSOS_ROOT

    @classmethod
    def default(cls) -> WorkspaceState:
        return cls(db_path=DEFAULT_DB_PATH, wsos_root=DEFAULT_WSOS_ROOT)

    @classmethod
    def for_workspace(cls, workspace_root: Path) -> WorkspaceState:
        """Construct a state handle rooted at the given workspace.

        The DB path is the workspace-local ``.wsos/state.db`` so the
        state travels with the workspace on relocation.
        """
        wsos_root = workspace_root / ".wsos"
        return cls(db_path=wsos_root / "state.db", wsos_root=wsos_root)

    @contextlib.contextmanager
    def _init_lock(self) -> Iterator[None]:
        """Acquire an advisory file lock on ``.wsos/.init.lock``.

        HIGH-2 fix: serialises ``init()`` and the first ``connect()``
        against a workspace, so concurrent bootstrap from multiple
        processes does not race on directory creation or schema
        execution. The lock file is created lazily with mode 0o600 and
        released when the context manager exits.
        """
        lock_path = self.wsos_root / _INIT_LOCK_NAME
        # Ensure parent exists; safe_mkdir is symlink-safe.
        safe_mkdir(self.wsos_root, mode=WSOS_DIR_MODE)
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o600)
        try:
            # Block until we acquire the lock.
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def _bootstrap(self) -> None:
        """Create the SQLite schema and tighten permissions.

        This is the inner bootstrap routine called by ``init()`` under
        the ``_init_lock``. ``connect()`` must NOT call this — it would
        deadlock by re-acquiring the lock from the same thread.
        """
        safe_mkdir(self.wsos_root, mode=WSOS_DIR_MODE)
        conn = sqlite3.connect(str(self.db_path))
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()
        tighten_existing_file(self.db_path, mode=WSOS_FILE_MODE)

    def init(self) -> None:
        """Create the WSOS root directory and the SQLite schema.

        HIGH-2 fix: serialised with an advisory file lock so concurrent
        bootstrap from multiple processes does not race. ``safe_mkdir``
        is symlink-safe so a planted symlink at ``.wsos`` is refused.

        The directory is created with mode 0o700 (owner-only). After the
        SQLite database file is created by the connection, it is chmod'd
        to 0o600 to defend against other local users reading the audit
        trail on a shared host.
        """
        with self._init_lock():
            self._bootstrap()
            # Tighten any sidecars SQLite may have created.
            for sidecar in (
                self.db_path.with_suffix(self.db_path.suffix + "-wal"),
                self.db_path.with_suffix(self.db_path.suffix + "-shm"),
            ):
                if sidecar.exists():
                    tighten_existing_file(sidecar, mode=WSOS_FILE_MODE)

    def connect(self) -> sqlite3.Connection:
        """Open a connection. Caller is responsible for commit/close.

        HIGH-2 fix: ``PRAGMA busy_timeout`` is set so concurrent writers
        from already-locked processes wait up to 5s instead of failing
        with ``OperationalError: database is locked``.

        If the database file does not yet exist, the bootstrap routine
        is invoked under the ``_init_lock``. The connect call does not
        itself acquire the lock when ``_bootstrap`` is running (no
        recursive lock).

        MEDIUM-6 fix: refuse to open a symlinked state.db (defence
        against a TOCTOU attack where an attacker plants a symlink at
        ``state.db`` pointing to e.g. ``/etc/passwd``).
        """
        if not self.db_path.exists():
            # First-time bootstrap. Hold the init lock so concurrent
            # processes do not race on directory creation or schema
            # execution.
            with self._init_lock():
                self._bootstrap()
        # MEDIUM-6: refuse to follow a symlinked state.db. The file may
        # have been planted between the existence check and the open.
        # SymlinkRefusedError surfaces as a clean error to the operator.
        from workspace_os._safe_io import SymlinkRefusedError

        if self.db_path.is_symlink():
            raise SymlinkRefusedError(
                errno.EEXIST,
                f"refusing to operate on symbolic link at {self.db_path}",
            )
        conn = sqlite3.connect(str(self.db_path), timeout=BUSY_TIMEOUT_MS / 1000)
        conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        # Belt-and-braces: tighten any newly-created WAL/SHM sidecars too.
        tighten_existing_file(self.db_path, mode=WSOS_FILE_MODE)
        for sidecar in (
            self.db_path.with_suffix(self.db_path.suffix + "-wal"),
            self.db_path.with_suffix(self.db_path.suffix + "-shm"),
        ):
            if sidecar.exists():
                tighten_existing_file(sidecar, mode=WSOS_FILE_MODE)
        return conn

    def register_workspace(self, root_path: Path) -> int:
        """Register a workspace root; idempotent. Returns workspace_id.

        Concurrency-safe: uses ``ON CONFLICT`` so two simultaneous
        registrations of the same workspace produce exactly one row.
        """
        root_str = str(root_path.resolve())
        now = time.time()
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO workspaces(root_path, created_at, last_seen_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(root_path) DO UPDATE SET last_seen_at = excluded.last_seen_at
                   RETURNING workspace_id""",
                (root_str, now, now),
            )
            row = cur.fetchone()
            if row is None or row[0] is None:
                raise sqlite3.DatabaseError("register_workspace: no workspace_id returned")
            workspace_id = int(row[0])
            conn.commit()
            return workspace_id

    def register_mission(self, workspace_id: int, slug: str, root_path: Path) -> int:
        """Register a mission directory. Idempotent on (workspace_id, slug).

        Concurrency-safe: uses ``ON CONFLICT`` so two simultaneous
        registrations of the same slug produce exactly one row.
        """
        now = time.time()
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO missions(slug, workspace_id, status, created_at, root_path)
                   VALUES (?, ?, 'open', ?, ?)
                   ON CONFLICT(workspace_id, slug) DO NOTHING
                   RETURNING mission_id""",
                (slug, workspace_id, now, str(root_path.resolve())),
            )
            row = cur.fetchone()
            if row is not None:
                if row[0] is None:
                    raise sqlite3.DatabaseError("register_mission: no mission_id returned")
                mission_id = int(row[0])
                conn.commit()
                return mission_id
            # The row already existed; look it up.
            row = conn.execute(
                "SELECT mission_id FROM missions WHERE workspace_id = ? AND slug = ?",
                (workspace_id, slug),
            ).fetchone()
            conn.commit()
            if row is None or row[0] is None:
                raise sqlite3.DatabaseError(
                    "register_mission: SELECT after ON CONFLICT returned no mission_id"
                )
            return int(row[0])

    def close_mission(self, mission_id: int) -> str | None:
        """Mark a mission as closed. Idempotent: a second call is a no-op.

        Returns the mission's status after the operation (``'closed'`` whether
        this call performed the transition or it was already closed). Returns
        ``None`` if no mission with ``mission_id`` exists.

        Note: return type widened from ``None`` to ``Optional[str]`` in WP-02.
        Existing callers that ignore the return value are unaffected.
        """
        now = time.time()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status, closed_at FROM missions WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()
            if row is None:
                return None
            current_status = row[0]
            if current_status == "closed":
                # Idempotent no-op: do not overwrite the original closed_at.
                return "closed"
            conn.execute(
                "UPDATE missions SET status = 'closed', closed_at = ? WHERE mission_id = ?",
                (now, mission_id),
            )
            conn.commit()
            return "closed"

    def pause_mission(self, mission_id: int) -> str | None:
        """Mark a mission as 'paused'. Idempotent: a second call is a no-op.

        Added in AI OS v1.0 readiness certification (2026-08-04) to support
        deterministic recovery. Returns the new status, or ``None`` if no
        mission with ``mission_id`` exists.

        Allowed transitions: open/paused -> paused. Closed missions cannot
        be re-paused (use resume on a closed mission to record a re-open).
        """
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status FROM missions WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()
            if row is None:
                return None
            current_status = row[0]
            if current_status == "closed":
                # Closed missions cannot be paused. Re-open with resume() first.
                return "closed"
            if current_status == "paused":
                return "paused"  # Idempotent no-op.
            conn.execute(
                "UPDATE missions SET status = 'paused' WHERE mission_id = ?",
                (mission_id,),
            )
            conn.commit()
            return "paused"

    def resume_mission(self, mission_id: int) -> str | None:
        """Mark a paused mission as 'open' (in-progress). Idempotent: a no-op
        if already open.

        Added in AI OS v1.0 readiness certification (2026-08-04). Returns the
        new status, or ``None`` if no mission with ``mission_id`` exists.

        Allowed transitions: paused/closed -> open. Calling on a fresh
        'open' mission is a no-op.
        """
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status FROM missions WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()
            if row is None:
                return None
            current_status = row[0]
            if current_status == "open":
                return "open"  # Idempotent no-op.
            conn.execute(
                "UPDATE missions SET status = 'open', closed_at = NULL WHERE mission_id = ?",
                (mission_id,),
            )
            conn.commit()
            return "open"

    def fail_mission(self, mission_id: int) -> str | None:
        """Mark a mission as 'failed' (terminal, requires explicit re-open).

        Added in AI OS v1.0 readiness certification (2026-08-04). Returns
        the new status, or ``None`` if no mission with ``mission_id`` exists.

        Allowed transitions: open/paused -> failed. Once 'failed', use
        resume_mission() to re-open.
        """
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status FROM missions WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()
            if row is None:
                return None
            current_status = row[0]
            if current_status == "closed":
                return "closed"  # closed is terminal; do not overwrite.
            if current_status == "failed":
                return "failed"  # Idempotent no-op.
            conn.execute(
                "UPDATE missions SET status = 'failed' WHERE mission_id = ?",
                (mission_id,),
            )
            conn.commit()
            return "failed"

    def get_mission_status(self, mission_id: int) -> dict | None:
        """Return the full mission state for resume. Returns ``None`` if the
        mission does not exist.

        Added in AI OS v1.0 readiness certification (2026-08-04). Used by
        ``cli.py mission status`` to surface "where did I leave off?".

        Returns a dict with keys: status, slug, root_path, created_at,
        closed_at, last_artifact_mtime (filesystem mtime of newest state file).
        """
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status, slug, root_path, created_at, closed_at "
                "FROM missions WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()
        if row is None:
            return None
        status, slug, root_path, created_at, closed_at = row
        root = Path(root_path)
        # Find the most recent mtime among the 8 canonical state files.
        SPRINT_PATTERN = (
            "source-task.md", "progress.md", "decisions.md", "blockers.md",
            "artifacts.md", "environment.md", "execution-log.md", "final-report.md",
        )
        last_artifact_mtime = 0.0
        last_artifact_name = None
        for name in SPRINT_PATTERN:
            f = root / name
            if f.exists():
                mt = f.stat().st_mtime
                if mt > last_artifact_mtime:
                    last_artifact_mtime = mt
                    last_artifact_name = name
        return {
            "status": status,
            "slug": slug,
            "root_path": root_path,
            "created_at": created_at,
            "closed_at": closed_at,
            "last_artifact_mtime": last_artifact_mtime,
            "last_artifact_name": last_artifact_name,
        }

    def record_mission_artifact(
        self,
        mission_id: int,
        filename: str,
        exists: bool,
        sha256: str | None,
        mtime: float | None,
    ) -> None:
        with self.connect() as conn:
            # NEW-4 fix: atomic single-statement UPSERT. The previous
            # implementation used ON CONFLICT to upsert sha256/mtime,
            # then a separate UPDATE for the quoted ``"exists"`` column
            # because ON CONFLICT aliases interact poorly with quoted
            # column names. SQLite supports ``excluded."exists"`` if
            # the column reference is fully quoted in the UPDATE SET
            # clause too.
            conn.execute(
                """INSERT INTO mission_artifacts(mission_id, filename, "exists", sha256, mtime)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(mission_id, filename) DO UPDATE SET
                     "exists" = excluded."exists",
                     sha256 = excluded.sha256,
                     mtime = excluded.mtime""",
                (mission_id, filename, int(exists), sha256, mtime),
            )
            conn.commit()

    def record_validator_run(
        self,
        workspace_id: int,
        pass_count: int,
        fail_count: int,
        raw_output_path: Path | None,
    ) -> int:
        now = time.time()
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO validator_runs(workspace_id, ts, pass_count, fail_count, raw_output_path)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    workspace_id,
                    now,
                    pass_count,
                    fail_count,
                    str(raw_output_path) if raw_output_path else None,
                ),
            )
            conn.commit()
            # sqlite3 stubs type cur.lastrowid as int|None; the C API
            # always returns a valid rowid for INSERT. Cast through str
            # to avoid the type warning without an assertion (which is
            # stripped under -O and trips bandit B101).
            rowid = cur.lastrowid
            if rowid is None:
                raise sqlite3.DatabaseError("INSERT failed: no rowid returned")
            return int(rowid)

    def record_agent_run(
        self,
        mission_id: int | None,
        command: str,
        exit_code: int,
        output_path: Path | None = None,
    ) -> int:
        now = time.time()
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO agent_runs(mission_id, ts, command, exit_code, output_path)
                   VALUES (?, ?, ?, ?, ?)""",
                (mission_id, now, command, exit_code, str(output_path) if output_path else None),
            )
            conn.commit()
            rowid = cur.lastrowid
            if rowid is None:
                raise sqlite3.DatabaseError("INSERT failed: no rowid returned")
            return int(rowid)

    def list_missions(self, workspace_id: int | None = None) -> list[dict]:
        with self.connect() as conn:
            if workspace_id is None:
                cur = conn.execute(
                    """SELECT m.mission_id, m.slug, m.status, m.created_at, m.closed_at, m.root_path, w.root_path
                       FROM missions m JOIN workspaces w ON m.workspace_id = w.workspace_id
                       ORDER BY m.created_at DESC"""
                )
            else:
                cur = conn.execute(
                    """SELECT m.mission_id, m.slug, m.status, m.created_at, m.closed_at, m.root_path, w.root_path
                       FROM missions m JOIN workspaces w ON m.workspace_id = w.workspace_id
                       WHERE m.workspace_id = ?
                       ORDER BY m.created_at DESC""",
                    (workspace_id,),
                )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def latest_validator_run(self, workspace_id: int) -> dict | None:
        with self.connect() as conn:
            cur = conn.execute(
                """SELECT run_id, ts, pass_count, fail_count, raw_output_path
                   FROM validator_runs
                   WHERE workspace_id = ?
                   ORDER BY ts DESC LIMIT 1""",
                (workspace_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))

    def iter_workspaces(self) -> Iterator[dict]:
        with self.connect() as conn:
            cur = conn.execute(
                "SELECT workspace_id, root_path, created_at, last_seen_at FROM workspaces ORDER BY created_at"
            )
            cols = [d[0] for d in cur.description]
            for row in cur.fetchall():
                yield dict(zip(cols, row))
