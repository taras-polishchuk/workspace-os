# workspace-os — Operator Runbook

This runbook covers Workspace OS V2 (Phase 1 through v0.5-rc). Architecture
is frozen per `/home/taras/projects/.project-state/workspace-os-v2-implementation-2026-07-22/FINAL-WORK-PACKAGES.md`.
All changes must be authorized by ratification per
`/home/taras/projects/GOVERNANCE/WORKSPACE-CONSTITUTION.md` Article X (Amendment).

For the higher-level operator runbook (covers all Workspace OS V2
subsystems: bridge, validator, daemon, release), see
`/home/taras/projects/OPERATOROS.md`.

**Audience:** Taras (operator), AI agents operating on his behalf.

---

## 1. Quick start

```bash
cd /home/taras/projects/workspace-os
pip install -e .
workspace-os --workspace /home/taras/projects init
workspace-os --workspace /home/taras/projects mission new my-first-mission
workspace-os --workspace /home/taras/projects mission list
workspace-os --workspace /home/taras/projects validate
```

> The CLI accepts `--workspace` both before and after the verb. If
> omitted, the default is `/home/taras/projects` (or `WORKSPACE_OS_ROOT`).
> Running bare `workspace-os init` in a non-canonical directory is a
> common operator mistake; pass `--workspace` explicitly.

Expected `workspace-os validate` output on a live workspace:

```
Validator verdict: 14 PASS / 78 FAIL (exit 1)
```

The 14 PASS / 78 FAIL pattern matches the canonical R7 freeze baseline.
The 78 FAILs are the mission-state-integrity noise from older or
in-progress `.project-state/<slug>/` directories that have not been
retroactively populated with the 8-artifact Sprint Pattern. The baseline
drifts as new missions are added; treat the absolute number as
informational.

The 14/66 figure appearing in any prior doc is **explicitly obsolete**
(see `policy.yaml:3`); the live count may also differ from 14/78 as
missions accumulate. The 13/90 / 14/78 / 14/66 trio is collapsed to
**14/78 (canonical R7 freeze) + live count** in this runbook.

---

## 2. Mission lifecycle (R5)

1. **Create**: `workspace-os --workspace /path mission new <slug>` creates
   `.project-state/<slug>/` with the 8-artifact Sprint Pattern
   (source-task.md, progress.md, decisions.md, blockers.md, artifacts.md,
   environment.md, execution-log.md, final-report.md).

---

## 3. Validator (R7, R13, R14)

### R7 (drift classification)
- Policy at `policy.yaml` declares canonical 14/78 baseline
- 14/66 figure is **explicitly obsolete** (line 3 of policy.yaml)
- `drift_id` is stable across runs that produce the same drift categories

### R13 (validator under workspace-os)
- Python validator at `workspace-os/src/workspace_os/validator/__main__.py`
- `/home/taras/projects/bin/validate-workspace.sh` is a shim that
  forwards to Python (legacy; new code should use the `validator` peer
  CLI directly: `validator --workspace /path`)
- Default invocation: `PYTHONPATH=src python3 -m workspace_os.validator`
- Verdict is informational; release-gate forces `rc=0` with `; true`

### R14 (8-file WARN-only + `--strict` + PRESERVE rule)
- Default behavior: WARN-only (`--accept-drift` waives non-mandatory drift)
- `--strict` mode: any drift becomes hard fail
- PRESERVE rule: `mandatory_drift` categories (`missing_security_audit_log`,
  `missing_audit_json_key`, `sprint_pattern_incomplete`) are ALWAYS
  blocking, even with `--accept-drift`
- v0.5-rc release-candidate tags: `RELEASE_CANDIDATE=1 bash release-gate.sh`
  triggers strict mode automatically

> **Note on R14 implementation:** the validator emit chain (per
> `invariants.py`) was extended in v0.5-rc to actually emit
> `drift: missing_security_audit_log`, `drift: missing_audit_json_key`,
> and `drift: sprint_pattern_incomplete` markers when the underlying
> conditions are detected. Prior implementations declared the
> categories in `policy.yaml` but no validator check ever emitted the
> matching markers, so PRESERVE was de-facto inactive.

## 4. Audit trail (R6)

Every validator run is recorded in `validator_runs` table, including
failures (R6 contract):

```sql
-- The drift_id is computed by run_validator() and printed to stdout but is NOT
-- persisted to validator_runs. To inspect the persisted audit trail:
SELECT run_id, ts, pass_count, fail_count, raw_output_path FROM validator_runs ORDER BY ts DESC LIMIT 5;
```

`cmd_validate` calls `record_validator_run()` after parsing the verdict,
even when the validator exits with a non-zero status (e.g.
FileNotFoundError on a non-canonical workspace).

## 5. Bridge integration (R4, R23)

The Kanban bridge is at `/home/taras/projects/scripts/kanban-bridge/`.
See `scripts/kanban-bridge/README.md` for full operator setup. Workspace
OS uses the bridge as its sole path to the Factory runtime.

Key constraints (R4 mandate):
- Split tokens required (`bridge-read-token` + `bridge-write-token`).
  `start.sh` reads `WSOS_KANBAN_READ_TOKEN_FILE` and
  `WSOS_KANBAN_WRITE_TOKEN_FILE` env vars and passes them via
  `--read-token-file` / `--write-token-file` CLI flags.
- Legacy single bearer `bridge-token` is REFUSED at startup (rc=6) when
  used as the sole token. The launcher's `start.sh` issues rc=6 when
  no split tokens are configured.
- A configuration with `read + legacy, no write` is also REFUSED at
  startup (rc=6) — the original audit found a parallel bypass that
  granted legacy `ROLE_WRITE` when read+legacy coexisted without
  write; this is now closed.
- Bridge MUST bind to `100.97.71.14` (canonical Tailnet IP) — NOT
  `0.0.0.0`. The bind check refuses to start with rc=4 on the wrong
  IP.

## 6. Daemon (R26)

The daemon is **honestly stubbed** in v0.5-rc.

```python
from workspace_os.daemon import is_daemon_available, ipc_request
print(is_daemon_available())  # False
ipc_request({"op": "ping"})   # raises DaemonNotAvailableError
```

When `is_daemon_available() == True` is reached, it requires the
full IPC test suite (lifecycle, concurrency, timeout, malformed input)
+ release-gate preflight passes.

> The `workspace-os daemon` subparser is NOT exposed in CLI. References
> to `daemon` in module docstrings are forward-looking.

## 7. Commit identity (R28)

`/home/taras/projects/bin/commit.sh` enforces commit identity. Tests at
`scripts/verify/test-commit-identity-preflight.sh` cover reject paths.

## 8. Common operations

### Reset SQLite state

```bash
rm -rf /home/taras/projects/.wsos
workspace-os --workspace /home/taras/projects init
```

### List missions for a workspace

```bash
workspace-os --workspace /path mission list
```

### Run a shell command and record it

```bash
workspace-os --workspace /path agent run --mission my-slug -- make build
```

### Inspect the SQLite database directly

```bash
sqlite3 /home/taras/projects/.wsos/state.db
> .tables
> SELECT * FROM missions;
> SELECT * FROM validator_runs ORDER BY ts DESC LIMIT 5;
```

## 9. Troubleshooting

### `Workspace root not writable`

Cause: `.wsos/` cannot be created because the parent directory is read-only
or owned by another user.
Fix: ensure the workspace root is writable by the current user.

### `Invalid mission slug`

Cause: slug contains uppercase letters, underscores, leading/trailing
hyphens, or is longer than 64 characters.
Fix: use a lowercase alphanumeric slug with hyphens, e.g. `phase-1-init`.

### `Mission directory already exists`

Cause: the same slug was used previously.
Fix: pass `--overwrite` to replace, or use a new slug.

### Validator returns `Summary: 0 passed, 0 failed`

Cause: the validator's output format changed and the regex no longer matches.
Fix: check `/home/taras/projects/bin/validate-workspace.sh` output format;
the regex expects `Summary: <N> passed, <M> failed`.

### Live validator reports <N> PASS / <M> FAIL (vs canonical 14/78)

Cause: live workspace has accumulated mission directories.
Fix: informational. The R7 canonical baseline is 14/78; the live count
is whatever it is. To clean up historical noise:
`find .project-state/ -type d -name '<slug>' -exec rm -rf {} +` for any
obsolete historical mission. **DO NOT** delete current missions without
confirming.

### `workspace-os validate` against a non-canonical workspace

Cause: a workspace other than `/home/taras/projects` requires either
the peer `validator` CLI or a `bin/validate-workspace.sh` shim at
`/home/taras/projects/bin/validate-workspace.sh`.
Fix: use the peer `validator --workspace /path` for non-canonical
workspaces; the legacy shim is no longer required.

## 10. What's implemented (v0.5-rc scope)

| Capability | Rec | Status |
|---|---|---|
| `workspace-os init` | (kernel capability) | ✅ |
| `workspace-os mission new/list/close` | WP-02 / R5 | ✅ |
| `record_validator_run` on every validate | WP-03 / R6 | ✅ |
| Drift classification (policy.yaml + drift_id) | WP-04 / R7 | ✅ |
| KGOS → knowledge-os rename | WP-05 / R8 | ✅ + shims |
| `operatoros-platform-import-baseline` tag | WP-06 / R10 | ✅ |
| Constitution/topology banner | WP-07 / R12 | ✅ (banner-only) |
| Validator under workspace-os | WP-08 / R13 | ✅ |
| 8-file WARN-only + PRESERVE + `--strict` (emit chain fixed) | WP-09 / R14 | ✅ |
| Atomic replace `*-e2e.sh` → `ws-e2e.sh` | WP-10 / R15 | ✅ |
| DB-header census (4 UNKNOWN DBs classified) | WP-11 / R17 | ✅ |
| Adapter policy (factory/policy.yaml) | WP-12 / R18 | ✅ |
| Multi-host decision record (NO verdict) | WP-13 / R19 | ✅ |
| 5-target E2E (`ws-e2e.sh`) | WP-14 / R22 | ✅ |
| Tailnet ACL + rotation runbook | WP-15 / R23 | ✅ |
| DB-separation guard | WP-16 / R24 | ✅ |
| Daemon IPC preflight + tests | WP-17 / R26 | ✅ (stub) |
| Reference integrity check | WP-18 / R27 | ✅ |
| `bin/commit.sh` identity preflight | WP-19 / R28 | ✅ |

> WP-01 in the prior runbook was misattributed to `init`; per the
> canonical `FINAL-WORK-PACKAGES.md`, WP-01 is R4 Bridge Hardening.
> `init` is a kernel capability, not a numbered work package.

## 11. Authority

- `WORKSPACE-CONSTITUTION.md` Article VII (Sprint Pattern) — R12 banner applied
- `WORKSPACE-CONSTITUTION.md` Article X (Amendment procedure)
- `Final-Implementation-Program.md` 2026-07-22 (program ratification)
- `GOVERNANCE/AMENDMENTS.md` 2026-07-22 (operator disposition)
- Canonical implementation package: `/home/taras/projects/.project-state/workspace-os-v2-implementation-2026-07-22/`
- Production acceptance audit: `/home/taras/projects/.project-state/workspace-os-v2-production-acceptance-2026-07-22/`
- Independent audit + verification:
  `/home/taras/projects/.project-state/workspace-os-v2-independent-audit-2026-07-23/` and
  `/home/taras/projects/.project-state/workspace-os-v2-findings-verification-2026-07-23/`
- The blueprint file referenced in prior runs of this runbook
  (`WORKSPACE-OS-V2-IMPLEMENTATION-BLUEPRINT.md`) is archived at
  `/home/taras/projects/.project-state/archive/workspace-os-v2-implementation-blueprint-2026-07-22/`
  and is **not** a production-path document. Implementation authority
  flows from `Final-Implementation-Program.md` instead.
