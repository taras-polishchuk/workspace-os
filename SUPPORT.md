# Support Policy

## Maintenance status

`workspace-os` v2.0.0a1 is the current release and is **actively
maintained** as the post-blueprint state-management kernel for
Workspace OS V2.

The v1.1 LTS baseline (`v1.1.0-LTS`, frozen 2026-06-28) remains under
the v1.1 LTS governance contract: bug fixes only, no architectural
changes. See `/home/taras/projects/GOVERNANCE/FREEZE-NOTICE.md`.

## Supported versions

| Version | Phase | Status | Support window |
|---|---|---|---|
| v2.0.0a1 (v0.5-rc) | release candidate | active | until v2.0.0 GA |
| v1.1.0-LTS | LTS | frozen (bug fixes only) | per LTS contract |

## What we fix

For the current release (`v2.0.0a1`):

- **Security defects** — CVE-class issues, race conditions, unsafe
  filesystem operations. Same-day response during work hours.
- **Correctness defects** — bugs in the documented CLI surface,
  SQLite state semantics, or validator verdict parsing.
- **Documentation drift** — stale references, broken links, version
  mismatches between docs and code.
- **Build / install** — wheel build failures, dependency conflicts,
  metadata errors.

## What we DO NOT fix

- New features not present in the documented CLI surface.
- Architectural redesign of the state-management kernel.
- Integration with external systems beyond the documented peer
  interfaces (`kgctl approve-canonical` integration, GMR monorepo
  creation, 4-service compose) — these are deferred per
  `README.md` "v0.5-rc scope".
- Behavior changes in the validator's drift classification without an
  amendment to `policy.yaml` and a corresponding governance entry.

## Reporting issues

For workspace-os itself, file an issue in this repository.

For governance, validator-policy, or cross-cutting Workspace OS
concerns, see `/home/taras/projects/GOVERNANCE/AMENDMENTS.md`.

## Deprecation policy

When a function, CLI flag, or behaviour is deprecated:

1. It continues to work unchanged for at least one minor release.
2. A `DeprecationWarning` is emitted (Python ≥3.7) or a stderr
   warning is printed on use.
3. The deprecation is documented in `CHANGELOG.md` under "Deprecated".
4. The deprecation is removed in the next major release.

## Security policy

Security defects should be reported via the same issue tracker with
the `security` label. There is no separate embargo process for the
v2.0.0a1 release candidate; LTS releases will follow a separate
disclosure policy when announced.

## Versioning

This project follows Semantic Versioning 2.0.0:

- **MAJOR** — incompatible API changes.
- **MINOR** — backwards-compatible functionality additions.
- **PATCH** — backwards-compatible bug fixes.

Pre-1.0 versions (a, b, rc) are not covered by the strict SemVer
contract; their API may evolve between minor versions within the same
release candidate phase.

The current `v2.0.0a1` is a **release candidate** for `v2.0.0`. The
first GA release will follow after the v0.5-rc scope is closed (no
deferred items remaining).
