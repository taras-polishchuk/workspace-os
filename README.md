# workspace-os

**Workspace OS v2.0 - bounded local Python kernel for workspace missions.**

GA release (`v2.0.0`, tag peeled at `97c3c49e5f54385256f7f52052e1a5eee012a6b4`). See [`WORKSPACE-OS-v2.0.0-GA-CERTIFICATE.md`](WORKSPACE-OS-v2.0.0-GA-CERTIFICATE.md) for the immutable historical certificate and [`WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md`](WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md) for the long-term canonical context.

## What this is

`workspace-os` provides a local CLI, SQLite-backed state, the eight-artifact mission lifecycle, agent-run audit recording, and a Python validator. It targets a single host and preserves the approved post-blueprint architecture.

## Installation

```bash
# Development checkout
python -m pip install -e ".[dev]"

# Built release artifact
python -m pip install dist/workspace_os-2.0.0-py3-none-any.whl

# PyPI, after publication
python -m pip install workspace-os
```

Python 3.11+ is required. The only runtime dependency is PyYAML>=6.0.

## CLI

```bash
workspace-os --workspace /path/to/workspace init
workspace-os --workspace /path/to/workspace mission new my-slug
workspace-os --workspace /path/to/workspace mission list
workspace-os --workspace /path/to/workspace validate
workspace-os --workspace /path/to/workspace agent run -- echo hello
```

`--workspace` is accepted before or after the verb. The default root is the current directory; override it with `--workspace` or `WORKSPACE_OS_ROOT`.

## Library API

```python
from pathlib import Path
from workspace_os import Mission, SPRINT_PATTERN_FILES, WorkspaceState, run_validator

root = Path("/path/to/workspace")
state = WorkspaceState.for_workspace(root)
state.init()
state.register_workspace(root)

mission = Mission.create("my-slug", workspace_root=root)
ok, missing = mission.all_artifacts_present()
assert ok and missing == []

verdict = run_validator(root)
print(f"{verdict.pass_count} PASS / {verdict.fail_count} FAIL")
```

## Development and release verification

```bash
python -m pip install -e ".[dev]"
python scripts/release_verify.py
python scripts/release_verify.py --clean-clone
```

The verifier runs Ruff check and format, mypy, Bandit under the committed release policy, pytest, pip-audit, package build, archive-content checks, and installed-package smoke tests. CI invokes the same script on Python 3.11 and 3.12.

## Documentation

For the runtime bootstrap procedure that any conforming AI runtime implements in service of the Workspace OS workspace, see [`docs/BOOTSTRAP-PROCEDURE.md`](docs/BOOTSTRAP-PROCEDURE.md). The procedure canonical owner is `/home/taras/projects/GOVERNANCE/BOOTSTRAP.md`; the kernel's `docs/` file does not redefine it.

For the validator caller contract, see [`docs/validator-callers.md`](docs/validator-callers.md).

For the operator-facing runbook, see [`runbook.md`](runbook.md).

## Authority

The authoritative governance and implementation program live in the parent Workspace OS workspace, outside this distribution repository:

- `/home/taras/projects/GOVERNANCE/WORKSPACE-CONSTITUTION.md` Articles VII and X.
- `/home/taras/projects/.project-state/workspace-os-v2-implementation-2026-07-22/FINAL-IMPLEMENTATION-PROGRAM.md`.
- `/home/taras/projects/GOVERNANCE/AMENDMENTS.md` 2026-07-22.

These host paths document release provenance and are not required at package runtime.

## v2.0.0 scope and limitations

Included:

- local CLI and SQLite state store;
- mission create, list, and close lifecycle;
- eight-artifact Sprint Pattern;
- agent-run recording and validator entry points;
- symlink and concurrent-init defenses;
- packaged drift policy loaded from installed distributions.

Not included:

- daemon process (`daemon.py` remains an unavailable contract stub);
- `kgctl approve-canonical` integration;
- GMR monorepo creation;
- four-service Compose topology.

These are post-GA ecosystem work, not missing local-kernel functionality.
