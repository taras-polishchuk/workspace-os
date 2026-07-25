# docs/

Operator-facing documentation for workspace-os.

| File | Purpose |
|---|---|
| `BOOTSTRAP-PROCEDURE.md` | Runtime bootstrap procedure algorithm, inputs/outputs contract, failure handling, and state machine — the implementation specification for the kernel's session-start sequence. Canonical procedure owner is `/home/taras/projects/GOVERNANCE/BOOTSTRAP.md`; this file does not redefine it. |
| `validator-callers.md` | How callers (release-gate, deployment-static, build-bundle, cold-boot-recovery) consume the validator. Documents the one-release overlap shim and the retirement plan for the legacy `bin/validate-workspace.sh` shell script. |

See `../README.md` for the workspace-os project overview and
`../runbook.md` for the operator-facing runbook.
