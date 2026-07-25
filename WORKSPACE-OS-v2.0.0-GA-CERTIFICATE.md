# Workspace OS v2.0.0 GA Certificate

> **Status:** Canonical historical certificate of the Workspace OS v2.0.0 GA release.
> **Issued:** 2026-07-25
> **Released commit:** `97c3c49e5f54385256f7f52052e1a5eee012a6b4`
> **Tag:** annotated `v2.0.0` (object `ccec833929b5f81716fe3e3d880047440493270d`, peels to `97c3c49`)
> **Status:** GA RELEASED

This document is the immutable historical record of the Workspace OS v2.0.0 GA release. Future changes to the package MUST cut a new release tag (e.g. `v2.0.1`, `v2.0.0-LTS`) following the constitutional amendment procedure. The annotated tag `v2.0.0` and the released commit `97c3c49e5f54385256f7f52052e1a5eee012a6b4` remain the historical baseline.

## 1. Release identity

| Item | Value |
|---|---|
| Product | `workspace-os` (PyPI name) / `workspace_os` (Python import) |
| Version | `2.0.0` |
| Phase at GA | GA (the historical `v2.0-rc` release-phase string was retired at the GA commit) |
| Released commit (HEAD at GA) | `97c3c49e5f54385256f7f52052e1a5eee012a6b4` |
| Tag | annotated `v2.0.0`, tag object `ccec833929b5f81716fe3e3d880047440493270d` |
| Canonical remote | https://github.com/taras-polishchuk/workspace-os |
| GitHub Release | https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0 |
| GitHub Release publishedAt | `2026-07-25T15:38:29Z` |
| License | MIT, © 2026 Taras Polishchuk |
| Python | `>=3.11` (verified on 3.11 and 3.12 in CI) |
| Runtime dependency | `PyYAML >= 6.0` (single runtime dependency) |

## 2. Quality gate evidence

The release verifier (`scripts/release_verify.py --clean-clone`) reports `RELEASE VERIFY PASS` against the released commit. CI run `30163934239` ran the same verifier on Python 3.11 and 3.12 with `conclusion: success` against HEAD `97c3c49`.

| Gate | Tool | Result |
|---|---|---|
| Ruff check | `ruff check src tests` | PASS |
| Ruff format | `ruff format --check src tests` | PASS |
| Mypy | `mypy src` | PASS, 14 source files |
| Bandit | `bandit -q -c pyproject.toml -r src` | PASS (committed policy: B404, B603, B607 documented as intentional) |
| Pytest | `pytest -q` | PASS, 114 tests |
| pip-audit | `pip-audit -r <runtime requirements>` | PASS, no known vulnerabilities |
| Build | `python -m build` | PASS, wheel + sdist produced |
| Archive contents | wheel and sdist must include `workspace_os/policy.yaml` and LICENSE | PASS |
| Installed smoke | install wheel in isolated venv; verify CLI and validator entry points; load packaged policy via `importlib.resources` | PASS |
| CI | GitHub Actions run `30163934239` on Python 3.11 + 3.12 | PASS |

GitHub Actions URL: https://github.com/taras-polishchuk/workspace-os/actions/runs/30163934239

## 3. Distribution artifacts

The artifacts below were uploaded to the GitHub Release `v2.0.0` on 2026-07-25 and are reachable at the URLs shown.

| Artifact | Download URL | SHA-256 | Size (bytes) |
|---|---|---|---|
| Wheel | https://github.com/taras-polishchuk/workspace-os/releases/download/v2.0.0/workspace_os-2.0.0-py3-none-any.whl | `82da84b8f4a99afb83bb4b2b6e845d25e5b46d96a4e200c7db94450aca24bd17` | 39168 |
| Sdist | https://github.com/taras-polishchuk/workspace-os/releases/download/v2.0.0/workspace_os-2.0.0.tar.gz | `23118bbd00a4fc5a3b1fefb74869b4a5c847197f896430c9847e90e9c85004ea` | 46942 |

PyPI publication was intentionally deferred at GA. `python3 -m pip index versions workspace-os` reports no distribution; the GitHub Release is the canonical download surface until the operator authorizes a PyPI upload.

## 4. Implementation history (canonical, between audited RC and GA)

The v2.0.0 GA commit `97c3c49` differs from the certified audit-time commit `b08ec5d` by three release-blocking portability fixes. All three are the smallest possible fix to make the repository portable in CI; no architecture change.

| Commit | Subject | Purpose |
|---|---|---|
| `6c8c711` | `fix(ci): make CLI tests repository-portable` | Replace hardcoded `cwd="/home/taras/projects/workspace-os"` in `tests/test_cli.py` and `tests/test_safety.py` with a repo-relative `REPO_ROOT` constant. |
| `19f392f` | `fix(ci): preserve CLI tests' WORKSPACE_OS_ROOT` | Preserve `WORKSPACE_OS_ROOT` across `_run` invocations in two CLI safety tests so they target `tmp_path` consistently. |
| `97c3c49` | `fix(cli): default workspace root to current directory for portability` | Change `DEFAULT_WORKSPACE_ROOT` from the host-specific `/home/taras/projects` to `Path.cwd()`; update CLI help, `README.md`, and `mission.py` docstring. |

The earlier implementation commits remain the architectural backbone of the release:

| Commit | Subject | Purpose |
|---|---|---|
| `53567df` | release: harden Workspace OS v2.0.0 candidate | Packaging, resource loading, quality policy, CI, release tooling, metadata, documentation, initial artifacts |
| `cfdb134` | test: harden release metadata verification | Harden CI workflow metadata regression test |

## 5. Tag and remote state

```
git ls-remote --tags origin
ccec833929b5f81716fe3e3d880047440493270d    refs/tags/v2.0.0
97c3c49e5f54385256f7f52052e1a5eee012a6b4    refs/tags/v2.0.0^{}
```

The annotated tag `v2.0.0` peels to the released commit `97c3c49`. The internal backup tag `backup/pre-author-fix-20260723T225000Z` was NOT pushed. The `refs/original/*` recovery references were NOT pushed. No pre-author-fix branches were published.

## 6. Compatibility and known intentional limitations

Compatibility:

- Python `>=3.11` (CI verified on 3.11 and 3.12).
- Linux and macOS supported (CI runs on ubuntu-latest).
- License: MIT.

Known intentional limitations (NOT shipped in v2.0.0):

- No long-running daemon. `daemon.py` is an honest unavailable contract stub; `is_daemon_available()` returns `False`; the `workspace-os daemon` subparser is not exposed.
- No `kgctl` command-line surface in the kernel.
- No Git-managed Repository (GMR) subsystem.
- No four-service Compose deployment stack.
- No PyPI publication at GA (deferred).
- No distributed or hosted operation.
- No SDK, HTTP API, dashboard, telemetry, auto-update, marketplace, or multi-tenant SaaS.

## 7. Stability guarantees

For the lifetime of this certificate:

- The released commit `97c3c49e5f54385256f7f52052e1a5eee012a6b4` is immutable. Its tree hash is the historical GA baseline.
- The annotated tag `v2.0.0` peels to that commit.
- The GitHub Release at https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0 carries the canonical artifacts and SHA-256s.
- Future work that affects the package MUST be cut as a new release tag (e.g. `v2.0.1` for bug fixes, `v2.0.0-LTS` for the LTS amendment). The existing `v2.0.0` tag is never overwritten, moved, or deleted.

## 8. Cross-references

- Canonical Context: `WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md` (in this repository)
- Mission state: `/home/taras/projects/.project-state/workspace-os-v2-ga-hardening-2026-07-25/`
  - `final-report.md` — pre-publication final report (LOCAL RELEASE CANDIDATE READY)
  - `PUBLICATION-REPORT.md` — full publication report including the 3 portability commits and CI failures
- README, CHANGELOG, RELEASE, SUPPORT in this repository reflect the GA state.
- Workspace OS authority plane: `/home/taras/projects/GOVERNANCE/`, `/home/taras/projects/WORKSPACE-OS-CANONICAL-MODEL.md`, `/home/taras/projects/FINAL-IMPLEMENTATION-PROGRAM.md`.

## 9. Sign-off

This certificate is self-issued by the post-GA baseline freeze mission on 2026-07-25. It is a record of what was released, not a claim about future releases. The verdict is `GA RELEASED`.

```
Repository:    https://github.com/taras-polishchuk/workspace-os
Commit SHA:    97c3c49e5f54385256f7f52052e1a5eee012a6b4
Tag:           v2.0.0 (annotated, peels to 97c3c49)
Release URL:   https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0
Workflow URL:  https://github.com/taras-polishchuk/workspace-os/actions/runs/30163934239
Verdict:       GA RELEASED
```