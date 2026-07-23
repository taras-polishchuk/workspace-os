# Validator callers — WP-08 / R13

## One-release overlap manifest

| Caller | Before | After | Dual-run / compatibility plan |
|---|---|---|---|
| `scripts/verify/release-gate.sh:138` | `bash bin/validate-workspace.sh` | `PYTHONPATH=workspace-os/src python3 -m workspace_os.validator` | `dual-run-validator.sh`; old path remains forwarding shim. |
| `scripts/verify/deployment-static.sh:389` | Indirect only (release/cold-boot) | Explicit Python validator runtime check | Exit 1 means findings and remains non-environmental; shim can be substituted unchanged. |
| `scripts/deploy/build-bundle.sh:86,110` | Bundled `workspace-os/`, but not shim/comparator | Bundles package, shim, comparator | Validate both bundled entry points before promotion. |
| `scripts/deploy/cold-boot-recovery.sh:74` | Indirect through deployment-static/release-gate | Explicit Python preflight, then existing gates | Exit 1 findings preserve historical non-blocking drift; rc >1 blocks boot. |

The compatibility shim exports the package source path, forwards all arguments,
stdout/stderr and process status. Rollback is therefore exercised by replacing a
caller's direct Python command with `bash bin/validate-workspace.sh`; no caller
contract changes.

## Check migration

The Python registry ports the shell checks: path integrity; four bootstrap
entries; three authority sources; two symlinks; identity drift; amendments;
release policy; governance references; Git identity override scan; canonical
project-state root; and mission-state structural integrity. These expand into
multiple result rows exactly as the shell did. Every registered invariant runs
under an individual timeout. The R7 classifier remains in `policy.py` and is
re-exported under `validator/drift.py` without modification.

## Retirement

Keep the shim and comparator for one release. After stored dual-run evidence has
no unexplained normalized count/status delta and caller census is clean, remove
the shim in a separate work package. Rollback restores direct shim commands;
never discard captured drift/audit history.
