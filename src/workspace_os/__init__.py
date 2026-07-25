"""Workspace OS v2 — local Python validator + CLI + SQLite state store.

v2.0-rc scope per Workspace OS V2 Implementation Program.

The workspace-os kernel implements the post-blueprint state management
kernel: validator, CLI, mission lifecycle, and SQLite state store.

Public API:
    - ``workspace_os.cli.main`` — CLI entry point (init, mission new/list/close, validate, agent run)
    - ``workspace_os.state.WorkspaceState`` — SQLite manager at ``<workspace>/.wsos/state.db``
    - ``workspace_os.mission.Mission`` — 8-artifact Sprint Pattern directory creator
    - ``workspace_os.validate.run_validator`` — Python-owned validator wrapper

Authority (external to this distribution repository):
    - /home/taras/projects/GOVERNANCE/WORKSPACE-CONSTITUTION.md Articles VII and X
    - /home/taras/projects/.project-state/workspace-os-v2-implementation-2026-07-22/FINAL-IMPLEMENTATION-PROGRAM.md
    - /home/taras/projects/GOVERNANCE/AMENDMENTS.md (2026-07-22 ratification)
"""

__version__ = "2.0.0"
__phase__ = "v2.0-rc"

from workspace_os.mission import SPRINT_PATTERN_FILES, Mission
from workspace_os.state import WorkspaceState
from workspace_os.validate import ValidatorVerdict, run_validator

__all__ = [
    "__version__",
    "__phase__",
    "WorkspaceState",
    "Mission",
    "SPRINT_PATTERN_FILES",
    "run_validator",
    "ValidatorVerdict",
]
