# Support Policy

## Maintenance status

`workspace-os` 2.0.0 is the current bounded local-kernel **GA** release and is actively maintained.

The historical v1.1 LTS baseline remains governed by its existing bug-fix-only contract. This v2.0 release does not amend LTS governance.

## Supported versions

| Version | Phase | Status | Support window |
|---|---|---|---|
| 2.0.0 | GA (released) | active | ongoing 2.0.x maintenance |
| 2.0.0a1 | superseded candidate | unsupported | superseded by 2.0.0 |
| 1.1.0-LTS | historical LTS | frozen, bug fixes only | per existing LTS contract |

## Supported scope

We fix:

- security defects and unsafe filesystem behavior;
- correctness defects in the documented CLI, SQLite state, mission lifecycle, and validator;
- package build, install, and bundled-resource defects;
- committed quality-gate, CI, and release-tooling defects;
- documentation drift in maintained release surfaces.

We do not treat these post-GA ecosystem capabilities as v2.0 defects:

- daemon implementation;
- `kgctl approve-canonical` integration;
- GMR monorepo creation;
- four-service Compose deployment;
- distributed or hosted operation.

Changes to validator drift classification require an approved policy change and corresponding governance record.

## Reporting issues

Report package defects in the canonical repository issue tracker: https://github.com/taras-polishchuk/workspace-os/issues.

Include:

- `workspace-os --version` output;
- Python version and platform;
- exact command and exit code;
- minimal workspace fixture if applicable;
- output from `python scripts/release_verify.py` for build or gate failures.

## Deprecation policy

1. A deprecated function, flag, or behavior remains available for at least one minor release.
2. Use emits `DeprecationWarning` or a clear stderr warning.
3. The deprecation is recorded in `CHANGELOG.md`.
4. Removal occurs in the next major release unless security requires earlier action.

## Security policy

Report security issues via GitHub private vulnerability reporting on https://github.com/taras-polishchuk/workspace-os/security. Embargoed coordination is supported.

## Versioning

The project follows Semantic Versioning 2.0.0. The package version is `2.0.0`; `2.0.0` is the published GA release (annotated tag `v2.0.0`, peels to commit `97c3c49e5f54385256f7f52052e1a5eee012a6b4`). The earlier `v2.0-rc` release-phase string was retired at the GA commit.