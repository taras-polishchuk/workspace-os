# Release Notes

Canonical release narrative for `workspace-os`. See [`CHANGELOG.md`](CHANGELOG.md) for structured changes and [`runbook.md`](runbook.md) for operator procedures.

## Release candidate: 2.0.0

**Candidate date:** 2026-07-25

**Phase:** v2.0-rc

**Scope:** bounded local, single-host Python kernel

### Delivered

1. Local CLI, SQLite-backed workspace and mission state, mission create/list/close, agent-run recording, and Python validator.
2. Eight-artifact Sprint Pattern with symlink-safe writes and concurrent-init defenses.
3. Runtime drift policy included in wheel and sdist and loaded through `importlib.resources`.
4. Reproducible release gate covering Ruff, Ruff format, mypy, Bandit, pytest, pip-audit, build, archive contents, and installed-package smoke checks.
5. CI definition for Python 3.11 and 3.12 that invokes the same release verifier.

### Deliberately outside v2.0.0

- production daemon;
- `kgctl approve-canonical` integration;
- GMR monorepo creation;
- four-service Compose topology.

The daemon module remains an explicit unavailable contract stub. These ecosystem capabilities are post-GA work and are not represented as shipped.

### Verify the candidate

```bash
python -m pip install -e ".[dev]"
python scripts/release_verify.py
python scripts/release_verify.py --clean-clone
```

A successful run ends with `RELEASE VERIFY PASS` and names the wheel and sdist. The script validates that both archives contain `workspace_os/policy.yaml`, installs the wheel in an isolated environment, loads the policy without repository access, and exercises both console entry points.

### Publication state

The release candidate can be certified locally and committed independently of publication. A public GA release additionally requires:

- a configured canonical Git remote;
- the committed candidate pushed to that remote;
- remote CI green for the pushed commit;
- an annotated `v2.0.0` tag on that commit;
- optional PyPI publication if the package is intended for `pip install workspace-os`.

No public release, remote CI, tag, or PyPI state should be inferred from local verification alone.

### Known limitations

- Validator results are relative to the Workspace OS layout and committed drift policy.
- The default workspace root remains `/home/taras/projects`; portable callers should pass `--workspace` or set `WORKSPACE_OS_ROOT`.
- The package is local and single-host. It does not expose a daemon or distributed deployment surface.

## Release history

| Version | Date | Phase | Status |
|---|---|---|---|
| 2.0.0 | 2026-07-25 | v2.0-rc | Local release candidate |
| 2.0.0a1 | 2026-07-22 | v0.5-rc | Superseded candidate |
| 1.1.0-LTS | 2026-06-28 | LTS | Historical frozen baseline |
