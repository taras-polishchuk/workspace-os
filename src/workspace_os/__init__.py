"""Workspace OS v2 — local Python validator + CLI + SQLite state store.

v0.5-rc scope per Workspace OS V2 Implementation Program.

The workspace-os kernel implements the post-blueprint state management
kernel: validator, CLI, mission lifecycle, and SQLite state store.

Public API:
    - ``workspace_os.cli.main`` — CLI entry point (init, mission new/list/close, validate, agent run)
    - ``workspace_os.state.WorkspaceState`` — SQLite manager at ``<workspace>/.wsos/state.db``
    - ``workspace_os.mission.Mission`` — 8-artifact Sprint Pattern directory creator
    - ``workspace_os.validate.run_validator`` — Python-owned validator wrapper

Authority:
    - Constitution Article VII (Sprint Pattern)
    - Constitution Article X (Amendment)
    - Final-Implementation-Program.md 2026-07-22 (program ratification)
    - AMENDMENTS.md 2026-07-22 (operator disposition ratifying program)
"""

__version__ = "2.0.0a1"  # PEP 440 canonical; setuptools normalizes 2.0.0-a.1 → 2.0.0a1
__phase__ = "v0.5-rc"

from workspace_os.state import WorkspaceState
from workspace_os.mission import Mission, SPRINT_PATTERN_FILES
from workspace_os.validate import run_validator, ValidatorVerdict

__all__ = [
    "__version__",
    "__phase__",
    "WorkspaceState",
    "Mission",
    "SPRINT_PATTERN_FILES",
    "run_validator",
    "ValidatorVerdict",
]
