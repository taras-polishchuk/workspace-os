# tests/

Pytest suite for `workspace_os`. Run with:

```bash
cd /home/taras/projects/workspace-os
PYTHONPATH=src python3 -m pytest -q
```

Current state: 85 tests, all passing.

The tests cover:
- CLI argument parsing and exit codes
- Validator behavior (pass/fail classification, drift_id, mandatory drift)
- Mission lifecycle (create, list, close, idempotency)
- SQLite state manager (schema, register, record, list)
- Validator migration (Python-owned validator peer entry)
- Package metadata (version, phase, public API)
- Daemon IPC stub (raises DaemonNotAvailableError)
