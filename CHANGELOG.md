# Changelog

All notable changes to `workspace-os` are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No changes yet.

## [2.0.0] - 2026-07-25

### Added

- Packaged `workspace_os/policy.yaml` resource in wheel and sdist.
- Regression coverage for packaged-policy availability, repository/package policy equality, release tooling, CI wiring, version, and phase metadata.
- Canonical `scripts/release_verify.py` gate for local and clean-clone release verification.
- GitHub Actions CI on Python 3.11 and 3.12 using the canonical verifier.
- Committed development dependencies for `types-PyYAML` and package builds.

### Changed

- Version finalized as `2.0.0`; GA release (`v2.0.0` tag, peels to commit `97c3c49e5f54385256f7f52052e1a5eee012a6b4`).
- Default policy loading now uses `importlib.resources`, so installed wheels do not depend on the repository root.
- Source and tests are Ruff-formatted under committed Ruff configuration.
- Mypy and Bandit release policies are committed in `pyproject.toml`.
- README, RELEASE, and SUPPORT now describe the bounded local-kernel GA scope consistently.

### Fixed

- Wheel and sdist no longer omit the runtime drift policy.
- Installed validation no longer exits because `policy.yaml` is absent.
- Static-analysis and formatting gates are reproducible in a fresh environment.

### Security

- Bandit continues to fail on non-excluded findings. The only exclusions are B404, B603, and B607 for reviewed, shell-free subprocess boundaries: operator-provided `agent run`, the owner/mode-validated compatibility shim, and bounded subprocess helpers.

## [2.0.0a1] - 2026-07-22

Superseded post-blueprint pre-GA artifact under the V2 Implementation Program.

### Added

- Local CLI, SQLite state, mission lifecycle, Python validator, and daemon-unavailable contract stub.
- `_safe_io.py` with atomic writes, safe directory creation, and symlink refusal.
- Security and concurrency regression coverage.

### Security

- `.wsos/` mode 0o700 and `state.db` mode 0o600.
- Concurrent registration and initialization defenses.

## [1.1.0-LTS] - 2026-06-28

Historical v1.1 LTS baseline under its existing governance contract.

[Unreleased]: https://github.com/taras-polishchuk/workspace-os/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0
[2.0.0a1]: https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0a1
[1.1.0-LTS]: https://github.com/taras-polishchuk/workspace-os/releases/tag/v1.1.0-LTS
