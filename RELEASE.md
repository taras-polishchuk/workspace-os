# Release Notes

Canonical release narrative for `workspace-os`. See [`CHANGELOG.md`](CHANGELOG.md) for structured changes and [`runbook.md`](runbook.md) for operator procedures.

## Released: 2.0.0

**Release date:** 2026-07-25
**Released commit:** `97c3c49e5f54385256f7f52052e1a5eee012a6b4`
**Tag:** annotated `v2.0.0` (tag object `ccec833929b5f81716fe3e3d880047440493270d`)
**GitHub Release:** https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0
**CI:** https://github.com/taras-polishchuk/workspace-os/actions/runs/30163934239 (success on Python 3.11 and 3.12)
**Scope:** bounded local, single-host Python kernel

The canonical historical certificate is [`WORKSPACE-OS-v2.0.0-GA-CERTIFICATE.md`](WORKSPACE-OS-v2.0.0-GA-CERTIFICATE.md). The long-term canonical context is [`WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md`](WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md).

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

### Verify the release

```bash
python -m pip install -e ".[dev]"
python scripts/release_verify.py
python scripts/release_verify.py --clean-clone
```

A successful run ends with `RELEASE VERIFY PASS` and names the wheel and sdist. The script validates that both archives contain `workspace_os/policy.yaml`, installs the wheel in an isolated environment, loads the policy without repository access, and exercises both console entry points.

### Publication state

The release is published. The GitHub Release `v2.0.0` carries the canonical wheel and sdist artifacts at the URLs shown in the GA Certificate. PyPI publication is intentionally deferred at GA; `pip install workspace-os==2.0.0` from PyPI is not available until the operator authorizes an upload. Until then, install from the GitHub Release:

```bash
python -m pip install \
  https://github.com/taras-polishchuk/workspace-os/releases/download/v2.0.0/workspace_os-2.0.0-py3-none-any.whl
```

### Known limitations

- Validator results are relative to the Workspace OS layout and committed drift policy.
- The default workspace root is the current working directory (`Path.cwd()`); portable callers should pass `--workspace` or set `WORKSPACE_OS_ROOT`.
- The package is local and single-host. It does not expose a daemon or distributed deployment surface.

## Release history

| Version | Date | Phase | Status |
|---|---|---|---|
| 2.0.0 | 2026-07-25 | GA | Released |
| 2.0.0a1 | 2026-07-22 | v0.5-rc | Superseded candidate |
| 1.1.0-LTS | 2026-06-28 | LTS | Historical frozen baseline |
