# Changelog

All notable changes to `workspace-os` are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html),
with the v1.x series having served as the LTS baseline and v2.x as the
post-blueprint evolution.

## [Unreleased]

### Added
- LTS packaging metadata (CHANGELOG.md, RELEASE.md, SUPPORT.md).
- `pyproject.toml` `optional-dependencies` for `test` and `dev` extras.

### Changed
- README: install + CLI examples generalised to portable paths.
- `docs/README.md`: now lists `validator-callers.md` (was incorrectly
  marked "Currently empty" in the prior docs/ README).
- `tests/README.md`: test count 85 → 109 (was stale).
- `pyproject.toml`: `chmod 644` permissions restored for distribution.

### Fixed
- README references to `Final-Implementation-Program.md` (mixed case) →
  `FINAL-IMPLEMENTATION-PROGRAM.md` (uppercase, actual canonical filename).
- `runbook.md` audit-trail SQL example: removed `drift_id` from column list
  (column is not persisted to `validator_runs`).
- `src/workspace_os/__init__.py` Authority section: same filename
  correction.

## [2.0.0a1] — 2026-07-22 (v0.5-rc)

Initial post-blueprint release under the V2 Implementation Program.

### Added
- `_safe_io.py`: `atomic_write_text`, `safe_mkdir`, `SymlinkRefusedError`
  with leaf-and-ancestor symlink refusal.
- 5 HIGH-severity security fixes: NEW-1/2/3 (Mission.create symlink
  safety), HIGH-1 (safe_mkdir parent check), HIGH-2 (concurrent init
  file lock + busy_timeout).
- 4 MEDIUM-severity fixes: NEW-4 (atomic mission_artifact upsert),
  MEDIUM-3 (shim safety), MEDIUM-5 (cli.main() catch-all), MEDIUM-6
  (state.db symlink refusal).
- 22 regression tests in `tests/test_safety.py` (was 0).
- `bin/validate-workspace.sh` shim forwards to canonical Python validator.

### Changed
- Static analysis: ruff 11 errors → 0, mypy 22 errors → 0.
- Test suite: 85 tests → 109 tests.
- Validator drift_id: stable at
  `33c96175219bdd00cc3798a2090362bffdc2a56f021b29ac95b6afa9aaa3c7d4`
  (canonical 5 PASS / 12 FAIL baseline).

### Security
- World-readable `.wsos/` → 0o700; world-readable `state.db` → 0o600.
- Race conditions in `register_workspace`/`register_mission` resolved via
  `ON CONFLICT ... RETURNING` and SQLite `busy_timeout=5000`.
- Concurrent `init()` from multiple processes: serialised via
  `fcntl.flock` on `.wsos/.init.lock`.

See `FINAL-PRODUCTION-REPORT.md`, `FINAL-RELEASE-CERTIFICATION.md`,
and `FINAL-LTS-TRANSITION-REPORT.md` for the complete audit trail.

## [1.1.0-LTS] — 2026-06-28

LTS baseline under v1.1 governance. Frozen per
`GOVERNANCE/FREEZE-NOTICE.md`. Bug-fix only; no architectural changes
permitted.

See `/home/taras/projects/GOVERNANCE/AMENDMENTS.md` 2026-06-28 entry for
the canonical LTS freeze notice.

---

[Unreleased]: https://github.com/taras-polishchuk/workspace-os/compare/v2.0.0a1...HEAD
[2.0.0a1]: https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0a1
[1.1.0-LTS]: https://github.com/taras-polishchuk/workspace-os/releases/tag/v1.1.0-LTS
