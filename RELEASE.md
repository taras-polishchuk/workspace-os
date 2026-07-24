# Release Notes

This document is the canonical release narrative for `workspace-os`.
For the structured changelog, see [`CHANGELOG.md`](CHANGELOG.md).
For the operator-facing runbook, see [`runbook.md`](runbook.md).

## Latest release: 2.0.0a1 (v0.5-rc)

**Release date:** 2026-07-22
**Phase:** v0.5 release candidate (post-blueprint, pre-LTS)
**Compatibility:** v1.1 LTS governance preserved via
`bin/validate-workspace.sh` shim; canonical CLI is `workspace-os` and
`validator`.

### What this release delivers

1. **Post-blueprint state-management kernel.** CLI + SQLite state store +
   mission lifecycle + Python validator, replacing the legacy
   `bin/validate-workspace.sh` shell implementation. The legacy script
   remains as a forwarding shim for one release cycle.
2. **Hardened security baseline.** 5 HIGH-severity defects closed:
   symlink-write attacks (NEW-1/2/3, HIGH-1), concurrent-init races
   (HIGH-2), unsafe shell-script execution (MEDIUM-3).
3. **109-test regression suite.** Covers CLI, mission lifecycle, SQLite
   state, validator, daemon stub, and 22 dedicated safety tests
   (`tests/test_safety.py`).
4. **Clean static analysis.** `ruff`, `mypy`, and `bandit` all return
   zero issues at this release.

### What is NOT in this release

These were deliberately deferred (per `README.md` "v0.5-rc scope"):

- Daemon process (`daemon.py` is a documented stub).
- Integration with `kgctl approve-canonical`.
- GMR monorepo creation.
- 4-service compose.

### Upgrade from v1.1-LTS

No migration is required for the v1.1 LTS governance layer; the
validator produces the same `drift_id` and the same 5 PASS / 12 FAIL
canonical baseline.

For projects that call `bin/validate-workspace.sh` directly, see
[`docs/validator-callers.md`](docs/validator-callers.md) for the
dual-run / compatibility plan.

### Verify this release

```bash
# Editable install
pip install -e ".[test]"

# Run tests
PYTHONPATH=src python3 -m pytest tests/ -q

# Smoke
workspace-os --workspace /tmp/lts-smoke init
workspace-os --workspace /tmp/lts-smoke mission new lts-test
workspace-os --workspace /tmp/lts-smoke validate
workspace-os --workspace /tmp/lts-smoke mission close lts-test

# Cleanup
rm -rf /tmp/lts-smoke
```

Expected: `109 passed`, validator returns
`drift_id=33c96175219bdd00cc3798a2090362bffdc2a56f021b29ac95b6afa9aaa3c7d4`.

### Known limitations

- The `validator` entry point depends on the canonical Workspace OS
  layout (bootstrap files, governance structure). Running it against a
  non-canonical workspace will return FAIL verdicts by design.
- The daemon is a documented stub. Any future daemon work is gated on
  the IPC test suite described in `runbook.md` §6.

---

## Release history

| Version | Date | Phase | Status |
|---|---|---|---|
| 2.0.0a1 | 2026-07-22 | v0.5-rc | Current |
| 1.1.0-LTS | 2026-06-28 | LTS | Frozen (bug-fix only) |

The v1.1.0-LTS baseline is governed by
`/home/taras/projects/GOVERNANCE/FREEZE-NOTICE.md`. The v2.x series is
the post-blueprint evolution under the V2 Implementation Program
ratified in `FINAL-IMPLEMENTATION-PROGRAM.md` 2026-07-22.
