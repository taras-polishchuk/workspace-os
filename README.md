# workspace-os

**Workspace OS v2 — local Python validator + CLI + SQLite state store.**

v0.5-rc scope per Workspace OS V2 Implementation Program (19 shippable work packages, 213.25h).

## What this is

The `workspace-os` package implements the post-blueprint state management
kernel: validator, CLI, mission lifecycle, and SQLite state store.

## Installation

```bash
cd /home/taras/projects/workspace-os
pip install -e .
```

## CLI

```bash
workspace-os --workspace /path init                            # initialize /path/.wsos/state.db
workspace-os --workspace /path mission new my-slug             # create .project-state/my-slug/ with 8 artifacts
workspace-os --workspace /path mission list                    # list missions
workspace-os --workspace /path validate                        # run peer validator and report
workspace-os --workspace /path agent run -- echo hello         # run a shell command, record in agent_runs
```

`--workspace` is accepted both before and after the verb. Default
workspace root is `/home/taras/projects`; override via `--workspace
/path` or `WORKSPACE_OS_ROOT` env var.

## Library API

```python
from workspace_os import WorkspaceState, Mission, run_validator, SPRINT_PATTERN_FILES

# Create SQLite state for a workspace
state = WorkspaceState.for_workspace(Path("/home/taras/projects"))
state.init()
wid = state.register_workspace(Path("/home/taras/projects"))

# Create a mission directory per Article VII Sprint Pattern
m = Mission.create("my-slug", workspace_root=Path("/home/taras/projects"))
ok, missing = m.all_artifacts_present()
assert ok and missing == []

# Run the workspace validator and parse the verdict
verdict = run_validator(Path("/home/taras/projects"))
print(f"{verdict.pass_count} PASS / {verdict.fail_count} FAIL")
```

## Tests

```bash
cd /home/taras/projects/workspace-os
pip install pytest
PYTHONPATH=src python3 -m pytest tests/ -q
```

Target: ≥50 tests (current: 85).

## Authority

- `GOVERNANCE/WORKSPACE-CONSTITUTION.md` Articles VII (Sprint Pattern),
  X (Amendment). See `runbook.md` for the canonical amendment procedure.
- `FINAL-IMPLEMENTATION-PROGRAM.md` 2026-07-22 (program ratification).
- `GOVERNANCE/AMENDMENTS.md` 2026-07-22 (operator disposition ratifying program).

## v0.5-rc scope and limitations

- Daemon process is not yet shipped (`daemon.py` is a documented stub;
  `workspace-os daemon` returns `invalid choice`; CLI only).
- Peer `validator` entry point implements the post-blueprint validation
  kernel; the legacy `bin/validate-workspace.sh` shim is no longer
  required for non-canonical workspaces.
- No integration with `kgctl approve-canonical` (deferred).
- No GMR monorepo creation (deferred).
- No 4-service compose (deferred).
