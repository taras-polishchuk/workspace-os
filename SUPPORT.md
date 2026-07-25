# Support Policy

## Maintenance status

`workspace-os` 2.0.0 is the current bounded local-kernel release candidate and is actively maintained.

The historical v1.1 LTS baseline remains governed by its existing bug-fix-only contract. This v2.0 release does not amend LTS governance.

## Supported versions

| Version | Phase | Status | Support window |
|---|---|---|---|
| 2.0.0 (`v2.0-rc`) | release candidate | active | through GA publication and subsequent 2.0.x maintenance |
| 2.0.0a1 | superseded candidate | unsupported | superseded by 2.0.0 candidate |
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

Report package defects in the canonical repository issue tracker once the repository is published. Until then, report them to the repository owner with:

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

Security reports currently use the same owner channel as correctness defects. A separate private disclosure channel must be established before public publication if embargoed reports are required.

## Versioning

The project follows Semantic Versioning 2.0.0. The package version is `2.0.0`; `v2.0-rc` describes release-candidate lifecycle state, not a different Python package version. GA is reached only when the candidate commit is published, remote CI is green, and the `v2.0.0` tag identifies that commit.
