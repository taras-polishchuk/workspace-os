"""CLI entry point for workspace-os.

Commands:
    init              Initialize <workspace>/.wsos/ and register the workspace root
    mission new       Create a mission under .project-state/
    mission list      List missions registered to the workspace
    mission close     Close a mission by id or slug (idempotent, WP-02/R5)
    validate          Run the Python validator peer entry and parse the verdict
    agent run         Run a shell command, record it in agent_runs, return exit code

Usage examples:
    workspace-os --workspace /path init
    workspace-os --workspace /path mission new my-slug
    workspace-os --workspace /path mission list
    workspace-os --workspace /path mission close my-slug
    workspace-os --workspace /path validate
    workspace-os --workspace /path agent run -- echo hello

Implementation note: workspace_root defaults to the current working directory.
Override with ``--workspace /path`` (accepted either before or after the
verb) or the ``WORKSPACE_OS_ROOT`` env var.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sqlite3
import subprocess
import sys
import time
from datetime import UTC
from pathlib import Path

from workspace_os import __version__
from workspace_os._safe_io import (
    WSOS_DIR_MODE,
    SymlinkRefusedError,
    atomic_write_text,
    safe_mkdir,
)
from workspace_os.mission import SPRINT_PATTERN_FILES, InvalidSlugError, Mission
from workspace_os.state import WorkspaceState
from workspace_os.validate import run_validator

__all__ = [
    "DEFAULT_WORKSPACE_ROOT",
    "build_parser",
    "cmd_agent_run",
    "cmd_init",
    "cmd_mission_close",
    "cmd_mission_list",
    "cmd_mission_new",
    "cmd_validate",
    "main",
]

DEFAULT_WORKSPACE_ROOT = Path.cwd()


def _resolve_workspace(args: argparse.Namespace) -> Path:
    """Resolve the workspace root from args, env, or default.

    H-4 fix: explicit empty string for ``--workspace`` is rejected (the
    prior behavior of silently falling back to DEFAULT_WORKSPACE_ROOT
    is now an error). ``--workspace /nonexistent`` is also rejected
    unless ``--yes`` is passed (H-5 fix).
    """
    explicit = getattr(args, "workspace", None)
    if explicit is not None:
        if explicit == "":
            raise ValueError("--workspace '' is not allowed (empty string)")
        path = Path(explicit).resolve()
        if not path.exists() and not getattr(args, "yes", False):
            raise FileNotFoundError(
                f"--workspace {explicit!r} does not exist; pass --yes to create it"
            )
        return path
    env = os.environ.get("WORKSPACE_OS_ROOT")
    if env:
        return Path(env).resolve()
    return DEFAULT_WORKSPACE_ROOT


# Backward-compat alias for any external callers
_workspace_root = _resolve_workspace


def _init_workspace_state(ws_root: Path) -> tuple[WorkspaceState, int]:
    """Initialise the WorkspaceState and register the workspace.

    Returns ``(state, workspace_id)``. Prints a clean error and raises
    :class:`SystemExit` via :class:`click`-style helper on filesystem errors
    so callers don't have to handle PermissionError/FileNotFoundError
    separately.
    """
    state = WorkspaceState.for_workspace(ws_root)
    state.init()
    workspace_id = state.register_workspace(ws_root)
    return state, workspace_id


class WorkspaceStateInitError(Exception):
    """Raised when the workspace state cannot be initialised cleanly."""

    def __init__(self, message: str, exit_code: int = 5) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


def _safe_init_workspace_state(ws_root: Path) -> tuple[WorkspaceState, int]:
    """Like :func:`_init_workspace_state` but catches filesystem errors."""
    try:
        return _init_workspace_state(ws_root)
    except PermissionError as e:
        raise WorkspaceStateInitError(
            f"error: workspace root not writable: {ws_root} ({e})", exit_code=5
        ) from e
    except FileNotFoundError as e:
        raise WorkspaceStateInitError(
            f"error: cannot create workspace state: {e}", exit_code=5
        ) from e
    except OSError as e:
        raise WorkspaceStateInitError(
            f"error: cannot initialize workspace-os at {ws_root}: {e}", exit_code=5
        ) from e


def cmd_init(args: argparse.Namespace) -> int:
    ws_root = _resolve_workspace(args)
    try:
        state, workspace_id = _safe_init_workspace_state(ws_root)
    except WorkspaceStateInitError as e:
        print(e.message, file=sys.stderr)
        return e.exit_code
    print(f"Initialized workspace-os at {state.wsos_root}")
    print(f"Workspace registered: id={workspace_id} root={ws_root}")
    return 0


def cmd_mission_new(args: argparse.Namespace) -> int:
    ws_root = _resolve_workspace(args)
    try:
        state, workspace_id = _safe_init_workspace_state(ws_root)
        mission = Mission.create(
            slug=args.slug,
            workspace_root=ws_root,
            state_root=args.state_root,
            overwrite=args.overwrite,
        )
    except WorkspaceStateInitError as e:
        print(e.message, file=sys.stderr)
        return e.exit_code
    except InvalidSlugError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except FileExistsError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    except PermissionError as e:
        print(f"error: cannot create mission directory: {e}", file=sys.stderr)
        return 5
    except OSError as e:
        print(f"error: cannot create mission directory: {e}", file=sys.stderr)
        return 5
    mission_id = state.register_mission(workspace_id, args.slug, mission.root_path)
    print(f"Created mission {args.slug} at {mission.root_path} (id={mission_id})")
    for filename in SPRINT_PATTERN_FILES:
        state.record_mission_artifact(
            mission_id=mission_id,
            filename=filename,
            exists=True,
            sha256=None,
            mtime=None,
        )
    return 0


def cmd_mission_list(args: argparse.Namespace) -> int:
    ws_root = _resolve_workspace(args)
    try:
        state, workspace_id = _safe_init_workspace_state(ws_root)
    except WorkspaceStateInitError as e:
        print(e.message, file=sys.stderr)
        return e.exit_code
    missions = state.list_missions(workspace_id=workspace_id)
    if not missions:
        print("No missions found.")
        return 0
    print(f"{'mission_id':<10} {'slug':<40} {'status':<10} {'created_at':<20}")
    print("-" * 80)
    for m in missions:
        ts = m["created_at"]
        from datetime import datetime

        ts_str = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M")
        print(f"{m['mission_id']:<10} {m['slug']:<40} {m['status']:<10} {ts_str:<20}")
    return 0


def cmd_mission_close(args: argparse.Namespace) -> int:
    """Close a mission by integer id or slug. Idempotent (WP-02 / R5).

    Exit codes:
        0 — success (including no-op when already closed)
        4 — mission not found (unknown id or slug)
        5 — DB error (sqlite3)
    """
    import sqlite3
    from datetime import datetime

    ws_root = _resolve_workspace(args)
    try:
        state, workspace_id = _safe_init_workspace_state(ws_root)
    except WorkspaceStateInitError as e:
        print(e.message, file=sys.stderr)
        return e.exit_code
    identifier: str = args.identifier

    try:
        if identifier.isdigit():
            mission_id = int(identifier)
            matches = [
                m
                for m in state.list_missions(workspace_id=workspace_id)
                if m["mission_id"] == mission_id
            ]
            if not matches:
                print(f"error: mission {identifier!r} not found.", file=sys.stderr)
                return 4
            mission = matches[0]
        else:
            matches = [
                m for m in state.list_missions(workspace_id=workspace_id) if m["slug"] == identifier
            ]
            if not matches:
                print(f"error: mission {identifier!r} not found.", file=sys.stderr)
                return 4
            mission = matches[0]
            mission_id = mission["mission_id"]

        if mission["status"] == "closed":
            closed_at = mission.get("closed_at")
            if closed_at is None:
                ts_str = "unknown"
            else:
                ts_str = datetime.fromtimestamp(closed_at, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"Mission {mission['slug']} (id={mission_id}) was already closed at {ts_str}")
            return 0

        new_status = state.close_mission(mission_id)
        if new_status is None:
            print(f"error: mission {identifier!r} not found.", file=sys.stderr)
            return 4
        closed_row = [
            m
            for m in state.list_missions(workspace_id=workspace_id)
            if m["mission_id"] == mission_id
        ][0]
        closed_at = closed_row.get("closed_at")
        ts_str = (
            datetime.fromtimestamp(closed_at, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            if closed_at is not None
            else "unknown"
        )
        print(f"Closed mission {mission['slug']} (id={mission_id}, closed_at={ts_str})")
        return 0
    except sqlite3.Error as e:
        print(f"error: database error: {e}", file=sys.stderr)
        return 5


def cmd_validate(args: argparse.Namespace) -> int:
    """Run the Python validator and persist the result as one validator_run row.

    R6 acceptance: every ``workspace-os validate`` invocation creates exactly one
    ``validator_runs`` row regardless of pass/fail outcome (including the
    FileNotFoundError path on a non-canonical workspace — H-8 fix).
    """
    ws_root = _resolve_workspace(args)
    try:
        state, workspace_id = _safe_init_workspace_state(ws_root)
    except WorkspaceStateInitError as e:
        print(e.message, file=sys.stderr)
        return e.exit_code
    mission_id = None
    if getattr(args, "mission", None):
        matches = [m for m in state.list_missions(workspace_id) if m["slug"] == args.mission]
        if not matches:
            print(f"error: mission {args.mission!r} not found.", file=sys.stderr)
            return 4
        mission_id = matches[0]["mission_id"]
    output_path: Path | None = Path(args.output) if getattr(args, "output", None) else None

    # H-8 fix: record validator_runs even on FileNotFoundError so the audit
    # trail captures every invocation. Use (0, 0) when the validator
    # never produced a verdict.
    try:
        verdict = run_validator(
            ws_root,
            output_path=output_path,
            timeout=30,
            policy_path=Path(args.policy) if getattr(args, "policy", None) else None,
            accept_drift=getattr(args, "accept_drift", False),
            accept_rationale=getattr(args, "accept_rationale", "") or "",
            mission_id=mission_id,
            strict=getattr(args, "strict", False),
        )
        pass_count = verdict.pass_count
        fail_count = verdict.fail_count
        drift_id = verdict.drift_id
        rc = 0 if verdict.ok else 1
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        pass_count, fail_count, drift_id = 0, 0, ""
        rc = 5
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired as e:
        print(f"error: validator timeout after {e.timeout}s", file=sys.stderr)
        pass_count, fail_count, drift_id = 0, 0, ""
        rc = 6
    except PermissionError as e:
        print(f"error: cannot write validator output: {e}", file=sys.stderr)
        return 5
    # Persist exactly one validator_run row per invocation. Both pass and
    # fail paths must record (so the audit trail shows failed validations
    # too).
    state.record_validator_run(
        workspace_id=workspace_id,
        pass_count=pass_count,
        fail_count=fail_count,
        raw_output_path=output_path,
    )
    if mission_id is not None and drift_id:
        state.record_mission_artifact(mission_id, "validator-drift-id", True, drift_id, time.time())
    if rc != 5 and rc != 6:
        # We have a verdict to display.
        print(f"Validator verdict: {verdict}")
        if output_path is not None:
            print(f"Raw output written to {output_path}")
    return rc


def cmd_agent_run(args: argparse.Namespace) -> int:
    ws_root = _resolve_workspace(args)
    try:
        state, workspace_id = _safe_init_workspace_state(ws_root)
    except WorkspaceStateInitError as e:
        print(e.message, file=sys.stderr)
        return e.exit_code
    mission_id = None
    if getattr(args, "mission", None):
        missions = [
            m for m in state.list_missions(workspace_id=workspace_id) if m["slug"] == args.mission
        ]
        if not missions:
            print(f"error: mission {args.mission!r} not found.", file=sys.stderr)
            return 4
        mission_id = missions[0]["mission_id"]
    # Filter out the argparse REMAINDER "--" separator. If nothing remains,
    # the operator forgot to provide a command — clean error rather than
    # a Python traceback (HIGH-2 fix).
    filtered = [c for c in args.command if c != "--"]
    if not filtered:
        print("error: agent run requires a command after --", file=sys.stderr)
        return 2
    command_str = " ".join(shlex.quote(c) for c in filtered)
    print(f"$ {command_str}")
    completed = subprocess.run(filtered, cwd=str(ws_root))
    # Atomic, symlink-safe write of the agent-run log. Filename uses ms
    # precision + PID to reduce collision probability (LOW-8) and makes
    # symlink-swap attacks harder (HIGH-4). The destination is rejected
    # if it or any parent is a symlink.
    log_dir = ws_root / ".wsos" / "agent-runs"
    safe_mkdir(log_dir, mode=WSOS_DIR_MODE)
    log_name = f"run-{workspace_id}-{int(time.time() * 1000)}-{os.getpid()}.log"
    log_path = log_dir / log_name
    log_content = f"command: {command_str}\nexit_code: {completed.returncode}\n"
    try:
        atomic_write_text(log_path, log_content)
    except SymlinkRefusedError as e:
        print(f"error: refusing to write agent-run log through symlink: {e}", file=sys.stderr)
        return 5
    run_id = state.record_agent_run(
        mission_id=mission_id,
        command=command_str,
        exit_code=completed.returncode,
        output_path=log_path,
    )
    print(f"agent_runs row id={run_id}")
    return completed.returncode


# Top-level options (--workspace, --yes) — single source of truth.
# We use argparse.REMAINDER-style handling: --workspace and --yes are
# captured by the top-level parser, then propagated to subparser args
# in `main()`.


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workspace-os",
        description="Workspace OS v2 local validator + CLI",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        help="Workspace root path (default: $WORKSPACE_OS_ROOT or the current directory)",
        default=None,
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Allow creating the workspace root directory if it does not exist",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"workspace-os {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    p_init = sub.add_parser("init", help="Initialize workspace-os state", add_help=True)
    p_init.add_argument("--workspace", "-w", default=None, help=argparse.SUPPRESS)
    p_init.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    p_init.set_defaults(func=cmd_init)

    p_mission = sub.add_parser("mission", help="Mission operations", add_help=True)
    p_mission.add_argument("--workspace", "-w", default=None, help=argparse.SUPPRESS)
    p_mission.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    msub = p_mission.add_subparsers(dest="mission_command", required=True)

    p_mission_new = msub.add_parser("new", help="Create a new mission directory", add_help=True)
    p_mission_new.add_argument("--workspace", "-w", default=None, help=argparse.SUPPRESS)
    p_mission_new.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    p_mission_new.add_argument("slug", help="Mission slug (lowercase, hyphens)")
    p_mission_new.add_argument(
        "--state-root", type=Path, default=None, help="Override .project-state parent"
    )
    p_mission_new.add_argument(
        "--overwrite", action="store_true", help="Replace existing mission directory"
    )
    p_mission_new.set_defaults(func=cmd_mission_new)

    p_mission_list = msub.add_parser("list", help="List missions for this workspace", add_help=True)
    p_mission_list.add_argument("--workspace", "-w", default=None, help=argparse.SUPPRESS)
    p_mission_list.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    p_mission_list.set_defaults(func=cmd_mission_list)

    p_mission_close = msub.add_parser(
        "close", help="Close a mission by id or slug (idempotent)", add_help=True
    )
    p_mission_close.add_argument("--workspace", "-w", default=None, help=argparse.SUPPRESS)
    p_mission_close.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    p_mission_close.add_argument("identifier", help="Mission ID (integer) or slug")
    p_mission_close.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt (no prompt currently; reserved for future use)",
    )
    p_mission_close.set_defaults(func=cmd_mission_close)

    p_validate = sub.add_parser(
        "validate", help="Run the Python validator and parse verdict", add_help=True
    )
    p_validate.add_argument("--workspace", "-w", default=None, help=argparse.SUPPRESS)
    p_validate.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    p_validate.add_argument("--output", default=None, help="Path to write raw validator output")
    p_validate.add_argument("--policy", default=None, help="Drift policy YAML")
    p_validate.add_argument(
        "--accept-drift", action="store_true", help="Accept non-forbidden drift for this run"
    )
    p_validate.add_argument(
        "--accept-rationale", default=None, help="Required rationale with --accept-drift"
    )
    p_validate.add_argument(
        "--mission", default=None, help="Record drift ID against this mission slug"
    )
    p_validate.add_argument(
        "--strict",
        action="store_true",
        help="R14: hard-fail on any unexpected drift (overrides --accept-drift for non-mandatory categories). Mandatory drift categories are ALWAYS hard-fail regardless.",
    )
    p_validate.set_defaults(func=cmd_validate)

    p_agent = sub.add_parser("agent", help="Agent operations", add_help=True)
    p_agent.add_argument("--workspace", "-w", default=None, help=argparse.SUPPRESS)
    p_agent.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    asub = p_agent.add_subparsers(dest="agent_command", required=True)
    p_agent_run = asub.add_parser("run", help="Run a shell command and record it", add_help=True)
    p_agent_run.add_argument("--workspace", "-w", default=None, help=argparse.SUPPRESS)
    p_agent_run.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    p_agent_run.add_argument(
        "command", nargs=argparse.REMAINDER, help="Command to run (everything after --)"
    )
    p_agent_run.add_argument("--mission", default=None, help="Associate with a mission slug")
    p_agent_run.set_defaults(func=cmd_agent_run)

    return parser


def _propagate_top_level_options(
    top: argparse.Namespace, sub: argparse.Namespace
) -> argparse.Namespace:
    """Copy top-level --workspace and --yes to a subparser namespace."""
    if getattr(sub, "workspace", None) is None and getattr(top, "workspace", None) is not None:
        sub.workspace = top.workspace
    if getattr(sub, "yes", False) is False and getattr(top, "yes", False):
        sub.yes = top.yes
    return sub


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    # Split argv at the first non-option token: everything before is
    # top-level options, everything after belongs to the subparser. This
    # lets `--workspace /path init` set top-level options while
    # `init --workspace /path` works via subparser.
    if argv is None:
        argv = sys.argv[1:]
    split_at = None
    for i, arg in enumerate(argv):
        if not arg.startswith("-") and arg in {
            "init",
            "mission",
            "validate",
            "agent",
            "-h",
            "--help",
        }:
            split_at = i
            break
    if split_at is None:
        args = parser.parse_args(argv)
    else:
        # Two-pass parse: top-level options first, then full parse
        # with the subparser-aware parser.
        top_args = parser.parse_args(argv[:split_at])
        full_parser = build_parser()
        sub_args = full_parser.parse_args(argv[split_at:])
        args = _propagate_top_level_options(top_args, sub_args)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    try:
        return int(args.func(args))
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 5
    except PermissionError as e:
        print(f"error: permission denied: {e}", file=sys.stderr)
        return 5
    except SymlinkRefusedError as e:
        print(f"error: refusing to operate through symlink: {e}", file=sys.stderr)
        return 5
    except subprocess.TimeoutExpired as e:
        print(f"error: validator timeout after {e.timeout}s", file=sys.stderr)
        return 6
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: filesystem error: {e}", file=sys.stderr)
        return 5
    except KeyboardInterrupt:
        # MEDIUM-5 fix: clean message instead of default Python traceback.
        print("interrupted", file=sys.stderr)
        return 130
    except sqlite3.DatabaseError as e:
        # MEDIUM-5 fix: corrupt or unreadable DB surfaces as a clean
        # error rather than a traceback. Generic OSError handler
        # above does not catch DatabaseError (subclass of Exception).
        print(f"error: database error: {e}", file=sys.stderr)
        return 5
    except Exception as e:
        # MEDIUM-5 fix: catch-all so any unexpected internal exception
        # becomes a clean rc=5 instead of a Python traceback.
        # Operators see the error message; full traceback goes to the
        # log if needed (we don't have a logger here, so we print
        # the exception type for debugging).
        print(f"error: internal {type(e).__name__}: {e}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
