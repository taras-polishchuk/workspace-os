# Workspace OS v2.0 GA Release Readiness Audit

**Date:** 2026-07-25
**Repository:** `/home/taras/projects/workspace-os`
**Audited commit:** `746c9b49390cb953a7c565c5b581b8a36a3421fd`
**Current tag:** `v2.0.0a1`
**Mode:** Read-only implementation audit. No architecture, source code, tests, release metadata, Git refs, or remote state were modified.

## Executive Verdict

# DELAY RELEASE FOR SPECIFIC MANDATORY FIXES

Workspace OS v2.0 does **not** need a production daemon, `kgctl approve-canonical` integration, a GMR monorepo, or a four-service Compose topology before GA of the **local single-host Python kernel**. Those capabilities belong to the wider 38-61 week AI Ecosystem migration and are suitable for post-GA delivery.

The current commit is nevertheless not an honest `v2.0.0` GA candidate yet. Release must be delayed for a small bounded remediation pass because:

1. the built wheel omits `policy.yaml`, so the advertised `workspace-os ... validate` command fails after normal wheel installation;
2. the five requested quality gates are not reproducibly green from a clean environment under their literal default commands;
3. version, phase, changelog, release notes, support policy, and tag still describe `2.0.0a1` / `v0.5-rc`;
4. no CI workflow exists to prove clean-environment reproducibility;
5. no Git remote, GitHub repository, or PyPI distribution currently exists despite public URLs and installation language in the docs.

These are release-engineering and documentation fixes. None requires architecture redesign or deferred-feature implementation.

## 1. Evidence Boundaries

| Boundary | Verified state | Verdict |
|---|---|---|
| Current working tree | Source tree was clean before this audit; the audit report is now the only untracked non-ignored file. Ignored caches, build outputs, local venv, and `.wsos/` state also exist | RC source unchanged; audit artifact untracked |
| Committed `HEAD` | `746c9b4`, tagged `v2.0.0a1`; 48 tracked files | Reproducible source commit |
| Clean clone | Editable install and 109 tests pass | Source development path works |
| Built wheel/sdist | Build and `twine check` pass, but wheel omits `policy.yaml` | Distribution blocker |
| External publication | No Git remote; GitHub repo lookup fails; PyPI lookup finds no distribution | Not published |

Historical release reports were treated as orientation only. Current source and executable behavior override their verdicts.

## 2. Minimum Honest v2.0.0 GA Scope

The minimum honest GA contract is:

> Workspace OS v2.0.0 is a local, single-host Python package providing the `workspace-os` CLI, SQLite-backed workspace and mission state, the eight-artifact mission lifecycle, agent-run audit recording, and the Python validator entry point. It does not promise a long-running daemon, Knowledge OS promotion integration, an ecosystem monorepo, or a multi-service deployment.

This scope is already consistent with the implemented public API:

- `README.md:3-10` defines a local Python validator, CLI, SQLite state store, and mission lifecycle.
- `src/workspace_os/__init__.py:5-12` exposes the same kernel boundary.
- `README.md:73-82` explicitly lists daemon, `kgctl`, GMR, and Compose as limitations/deferred work.
- `SUPPORT.md:33-42` excludes new external integrations from the supported current surface.

No architecture amendment is required to release this bounded package. GA must not be described as completion of the entire Workspace OS v2 ecosystem migration.

## 3. GA Blocker Classification

| Candidate blocker | Classification | Evidence | Canonical disposition |
|---|---|---|---|
| Production daemon | **Optional, post-GA** | `FINAL-RELEASE-PLAN.md:53-72` requires an honest unavailable-daemon assertion for beta; `IMPLEMENTATION-EVIDENCE-MATRIX.md:140-143` accepts `is_daemon_available() -> False`; `README.md:75-76` documents the stub | Keep stub and limitation. Do not implement for GA. |
| `kgctl approve-canonical` integration | **Optional, post-GA** | `README.md:80`; `SUPPORT.md:37-40`; transition blueprint `:52-62` and `:159-161` treat promotion as a later ecosystem migration safeguard, not Python-kernel functionality | Move to post-GA ecosystem roadmap. |
| GMR monorepo creation | **Optional, post-GA** | Transition architecture `:48-50` defines a 38-61 week migration; `:62` places runtime expansion after earlier phases | Do not block kernel GA. |
| Four-service Compose | **Optional, post-GA** | Transition architecture `:62` says three services are preserved through Phases 0-3 and four services arrive in Phase 4 | Do not block kernel GA. |
| R9 / R11 | **Optional, gated post-GA** | `FINAL-IMPLEMENTATION-PROGRAM.md:87-92`; `FINAL-RELEASE-PLAN.md:119-127` explicitly mark them DEFER pending ADR/Article XIII gates | Preserve defer status. |
| R29 / R30 | **Scope-dependent, not package blockers** | `FINAL-IMPLEMENTATION-PROGRAM.md:103-108`; `FINAL-RELEASE-PLAN.md:96-114` attach them to file-bridge and bridge DoS surfaces outside this package | Block ecosystem production claims, not local package GA. |
| Wheel missing `policy.yaml` | **Mandatory before GA** | Wheel inventory contains package modules and metadata but no `policy.yaml`; installed `workspace-os --workspace <dir> validate` exits 5 with missing `.../venv/lib/python3.12/policy.yaml`; source uses `DEFAULT_POLICY_PATH` at `validate.py:27` | Package policy as package data and resolve it through package resources or equivalent frozen-compatible path. Add installed-wheel regression test. |
| Existing `dist/` artifacts stale and missing LICENSE | **Mandatory before distribution** | The pre-existing wheel and sdist under `dist/` contain neither `LICENSE` nor `policy.yaml`; fresh build from HEAD includes LICENSE but still omits policy | Delete/rebuild artifacts from the final GA commit; verify inventories before upload. |
| Literal five-gate reproducibility | **Mandatory before GA** | Clean clone: pytest 0, ruff 1, mypy 1, bandit 1, pip-audit 0 | Define exact canonical commands/configuration and make all five exit 0. |
| GA metadata/tag | **Mandatory before GA** | `pyproject.toml:7`, `__init__.py:21-22`, `CHANGELOG.md:31`, `RELEASE.md:7-10`, `SUPPORT.md:17,80-82`, and tag all remain alpha/RC | Cut a reviewed GA commit with synchronized `2.0.0` metadata and annotated `v2.0.0` tag. |
| CI reproducibility | **Mandatory before public GA** | No `.github/` directory or CI workflow exists | Add minimal CI for clean install, five gates, build, artifact install, and smoke. This is release engineering, not architecture. |
| Remote/publication | **Mandatory only for public release** | `git remote -v` empty; `gh repo view taras-polishchuk/workspace-os` fails; PyPI has no `workspace-os` distribution | For local GA tag only, non-blocking. For GitHub/PyPI GA, create/push/publish after operator authorization. |
| Security disclosure route | **Mandatory before public GA** | `SUPPORT.md:61-66` points security reports to a nonexistent public issue tracker and offers no private route; `SECURITY.md` absent | Add an actionable disclosure route before public publication. |
| Root Workspace validator red | **Not a package-code blocker; ecosystem release-gate blocker** | Fresh root validator result: 13 PASS / 111 FAIL and `drift: sprint_pattern_incomplete`; failures are historical Mission State at `/home/taras/projects/.project-state`, not this repo | Do not claim full Workspace OS root compliance. Classify/remediate separately if ecosystem release is intended. |
| Ecosystem release gate timeout | **Not enough evidence for package failure; ecosystem process risk** | `scripts/verify/release-gate.sh` timed out at the 180-second audit bound; it tests Knowledge OS, Factory, CCP, ecosystem deployment, not only this package | Run in a dedicated ecosystem certification mission before ecosystem production claims. |

## 4. Scope Contradictions

### 4.1 Deferred features are both outside scope and GA blockers

The contradiction exists in three surfaces:

1. `README.md:73-82` says daemon, `kgctl`, GMR, and Compose are deferred limitations.
2. `RELEASE.md:30-37` says the same features are deliberately not in the release.
3. `SUPPORT.md:33-40` says these integrations are not supported and are deferred.
4. But `SUPPORT.md:80-82` says GA follows only when there are "no deferred items remaining".
5. `.project-state/workspace-os-lts-transition-2026-07-23/FINAL-LTS-TRANSITION-REPORT.md:299-329` elevates the four deferred items into GA blockers.

### 4.2 Canonical recommendation

Replace the ambiguous rule "no deferred items remaining" with:

> v2.0.0 GA requires closure of every blocker inside the declared local Python kernel scope. Deferred ecosystem migration capabilities remain explicit post-GA work and do not block package GA. Any feature still documented as part of the v2.0.0 public contract must either be implemented or removed from that contract before tagging.

This resolves the contradiction without changing architecture. It narrows the release contract to the code that exists.

### 4.3 A second naming contradiction

The frozen implementation program uses `v2.0-prod` as an ecosystem production gate:

- `FINAL-IMPLEMENTATION-PROGRAM.md:30-45` reserves v2.0-prod for R9/R11 re-evaluation and R29/R30.
- `FINAL-RELEASE-PLAN.md:96-115` requires ecosystem cold boot, Article XIII evidence, canary traffic, and Tailscale evidence.

That milestone is not equivalent to a GA release of the standalone `workspace-os` Python package. The documents currently overload "v2.0" for two boundaries:

1. package GA;
2. full AI Ecosystem production transition.

Canonical treatment: release `workspace-os` package v2.0.0 with the bounded local-kernel contract, while retaining the ecosystem milestone under an explicitly different label such as "Workspace OS v2 ecosystem production gate". This is editorial boundary clarification, not architecture redesign.

## 5. Release Engineering Audit

### 5.1 Versioning

| Surface | Current | Required for GA |
|---|---|---|
| `pyproject.toml:7` | `2.0.0a1` | `2.0.0` |
| `src/workspace_os/__init__.py:21` | `2.0.0a1` | `2.0.0` |
| `src/workspace_os/__init__.py:22` | `v0.5-rc` | A truthful GA phase, or remove phase if redundant |
| `tests/test_package.py:13-15` | Hardcodes `v0.5-rc` | Update to GA contract |
| Git tag | `v2.0.0a1` | Annotated `v2.0.0` on final reviewed commit |

### 5.2 CHANGELOG

Current blockers:

- `CHANGELOG.md:10-29` still has an Unreleased section containing packaging work already present in the RC commit.
- There is no `[2.0.0]` entry.
- Link targets at `:75-77` point to a GitHub repository that does not exist.
- `CHANGELOG.md:61-62` references `FINAL-LTS-TRANSITION-REPORT.md` as if it were in the repository root, but that file lives under `.project-state/workspace-os-lts-transition-2026-07-23/`.

Required: cut a dated `[2.0.0]` entry, preserve historical alpha entry, fix links only after the actual remote exists, and correct the LTS-report path or describe it as external mission evidence.

### 5.3 RELEASE notes

`RELEASE.md` is internally consistent for the alpha RC but not suitable for GA. It must be rewritten for the bounded GA contract and must stop saying the four deferred ecosystem features block GA.

It also claims `ruff`, `mypy`, and `bandit` all return zero issues (`RELEASE.md:27-28`). Fresh default commands contradict that claim.

### 5.4 SUPPORT policy

`SUPPORT.md` correctly scopes supported functionality at `:20-42`, but contradicts itself at `:80-82` with the no-deferred-items condition. Public security reporting is not actionable because there is no issue tracker and no private disclosure channel.

### 5.5 README

README accurately describes the implemented local kernel and explicitly labels PyPI installation as future (`README.md:14-17`). Required GA edits:

- change RC terminology and version references;
- distinguish standalone package GA from ecosystem migration completion;
- document exact reproducible quality-gate commands;
- document the installed validator behavior after policy packaging is fixed;
- avoid implying publication until GitHub/PyPI actually exist.

### 5.6 Packaging metadata and artifacts

Verified:

- clean build produces wheel and sdist;
- `twine check dist/*` passes;
- wheel installs in a clean runtime venv;
- `workspace-os --version` and `validator --help` work;
- init, mission new/list/close, and agent run work from the installed package;
- a fresh build from audited HEAD contains LICENSE and passes `twine check`.

Blocking defect:

- `policy.yaml` is not in wheel or sdist.
- the pre-existing ignored artifacts currently in `dist/` are older than the LICENSE commit and contain neither LICENSE nor policy. They must not be uploaded.
- The library resolves it from `Path(__file__).resolve().parents[2] / "policy.yaml"`, which points outside the installed package.
- Installed `workspace-os validate` is broken.
- Tests run from an installed sdist fail 13 cases for the same missing file.

Non-blocking packaging warning:

- setuptools reports `project.license = {text = "MIT"}` is deprecated and should become an SPDX string before 2027-02-18.

### 5.7 Git tags and remote state

- Working tree clean.
- `v2.0.0a1` is annotated and points to HEAD.
- The tag message contains a stale sentence saying it was re-pointed after commit `9abc...`; actual HEAD is `746c9b4`.
- An internal backup tag `backup/pre-author-fix-20260723T225000Z` and `refs/original/*` rewrite refs remain locally. Do not use `git push --tags`; prune or explicitly exclude internal refs before public publication.
- `.git/packed-refs` contains a stale packed `main` value (`d084cb7`) shadowed by the correct loose ref (`746c9b4`). Git resolves correctly, but refs should be normalized before publication.
- No `origin` or any remote exists.
- GitHub repository lookup for `taras-polishchuk/workspace-os` fails.
- PyPI has no matching distribution.

The project is local-release-ready only after mandatory fixes. It is not currently publicly released.

### 5.8 CI reproducibility

No CI configuration exists in the repository. Prior reports describe manually installed global tools and commands, not a committed reproducibility contract.

Minimum CI matrix:

1. Python 3.11 and 3.12.
2. `pip install -e '.[dev]'` or equivalent locked bootstrap.
3. canonical pytest, ruff, mypy, bandit, and pip-audit commands.
4. build wheel/sdist and `twine check`.
5. install wheel into a second clean venv.
6. run installed CLI smoke including `workspace-os validate`.
7. verify wheel contains `policy.yaml`.

## 6. Reproducible Quality Gates

Fresh clean clone, clean Python 3.12 venv, `pip install -e '.[dev]'`:

| Gate | Command audited | Exit | Result | Exact issue |
|---|---|---:|---|---|
| pytest | `python -m pytest tests/ -q` | 0 | PASS | 109 tests pass |
| ruff | `python -m ruff check src tests` | 1 | FAIL | 81 findings under freshly installed Ruff 0.15.7; no Ruff version pin or rule configuration exists |
| ruff format | `python -m ruff format --check src tests` | 1 | FAIL | 19 files would be reformatted |
| mypy | `python -m mypy src` | 1 | FAIL | Missing `types-PyYAML`; `mypy --ignore-missing-imports src` passes |
| bandit | `python -m bandit -r src -q` | 1 | FAIL | 7 accepted LOW findings; `bandit -r src -lll` passes with zero Medium/High |
| pip-audit | `python -m pip_audit` | 0 | PASS with caveat | No known dependency vulnerabilities; local package skipped because not on PyPI |

### Required gate corrections

1. **mypy:** add `types-PyYAML` to dev dependencies, or commit an explicit `ignore_missing_imports` override for `yaml`. Adding the stubs is the more honest default because the brief requires literal `mypy` success.
2. **ruff:** pin a supported Ruff range and commit `[tool.ruff]` configuration defining target version, selected rules, and justified ignores. Then fix all findings selected by that policy. Do not claim "ruff clean" without recording the command and tool version.
3. **bandit:** define the release policy explicitly. Either:
   - make literal `bandit -r src` pass by justified inline suppressions/config exclusions for the seven reviewed subprocess findings; or
   - make the canonical release gate `bandit -r src -lll`, which fails only on High severity. If the success criterion literally requires default Bandit exit 0, use the first option.
4. **pip-audit:** audit an explicit dependency input or installed environment and record that the local package itself is skipped because it is unpublished. Current runtime dependency `PyYAML>=6.0` has no known vulnerabilities.
5. **build tooling:** `build`, `twine`, and `types-PyYAML` are absent from `[project.optional-dependencies].dev`; add them if they are part of the documented release workflow.

## 7. Mandatory GA Fixes

### P0 - distribution correctness

1. Package `policy.yaml` inside the wheel and sdist.
2. Resolve the default policy with an installed-package-safe mechanism.
3. Add clean-wheel tests proving:
   - `workspace-os ... validate` does not fail due to missing policy;
   - `run_validator()` works from a normal installed package;
   - wheel/sdist inventories include the policy.

### P0 - release truth

4. Synchronize all version and phase fields to `2.0.0` only after P0 fixes pass.
5. Add a dated `CHANGELOG.md` 2.0.0 entry.
6. Rewrite `RELEASE.md`, `SUPPORT.md`, and README around the bounded local-kernel GA scope.
7. Remove the false rule that every deferred ecosystem feature must be complete before package GA.

### P1 - reproducibility

8. Commit exact Ruff, mypy, Bandit, and pip-audit policies and versions.
9. Add missing dev/release dependencies.
10. Make the full five-gate clean-clone run exit 0.
11. Add CI reproducing those gates and the built-wheel smoke.
12. Rebuild and inspect `dist/`; reject the existing stale artifacts.

### P1 - public release safety

13. Add a real private security disclosure route.
14. Normalize/prune internal Git refs before any public tag push.
15. Create/configure the remote only with operator authorization.
16. Verify the final clean clone from the remote commit, not only from the local filesystem.

## 8. Non-Blockers

The following do not block a bounded v2.0.0 package GA:

- daemon remains an honest stub;
- no `kgctl approve-canonical` integration;
- no GMR monorepo;
- no four-service Compose topology;
- accepted LOW Bandit findings, once the gate policy is explicit;
- deprecated `project.license` table warning, provided it is placed on a near-term maintenance list;
- no public remote when the operator intends only a local GA tag;
- historical root Mission State failures, provided no ecosystem-wide compliance claim is made;
- absence of LTS promotion. GA and LTS are separate transitions.

## 9. Release Checklist

### Scope and documentation

- [ ] Adopt the bounded local-kernel GA contract from Section 2.
- [ ] Reclassify daemon, `kgctl`, GMR, and Compose as post-GA.
- [ ] Remove "no deferred items remaining" from GA criteria.
- [ ] Separate package GA terminology from ecosystem production-gate terminology.

### Distribution

- [ ] Include `policy.yaml` in wheel and sdist.
- [ ] Installed `workspace-os validate` smoke passes.
- [ ] Installed `validator` entry point smoke passes.
- [ ] `python -m build` passes.
- [ ] `twine check dist/*` passes.
- [ ] Wheel/sdist contents inspected.
- [ ] Existing stale `dist/` artifacts deleted and rebuilt from the final commit.

### Quality

- [ ] pytest exits 0 in a clean venv.
- [ ] ruff exits 0 under committed policy.
- [ ] mypy exits 0 without an undocumented local-only workaround.
- [ ] bandit exits 0 under committed policy.
- [ ] pip-audit exits 0 under committed policy.
- [ ] CI reproduces all five gates on Python 3.11 and 3.12.
- [ ] Ruff format check exits 0 under committed policy.

### Release metadata

- [ ] `pyproject.toml` version is `2.0.0`.
- [ ] `workspace_os.__version__` is `2.0.0`.
- [ ] phase is GA-accurate or removed.
- [ ] CHANGELOG has `[2.0.0]` with date.
- [ ] RELEASE describes actual GA scope.
- [ ] SUPPORT lists 2.0.0 accurately.
- [ ] README counts, commands, links, and publication status match reality.

### Git and publication

- [ ] Final GA commit has a clean tree.
- [ ] Clean clone from final commit passes all gates.
- [ ] Annotated `v2.0.0` tag points to that commit.
- [ ] Internal backup tags and `refs/original/*` are not pushed publicly.
- [ ] Packed and loose branch refs are normalized.
- [ ] Remote exists and links resolve, if public release is intended.
- [ ] GitHub release created, if public release is intended.
- [ ] PyPI upload and external install smoke verified, if package publication is intended.
- [ ] Security disclosure route is actionable.

## 10. Recommended Release Order

1. **Ratify scope editorially:** local single-host kernel is v2.0.0; ecosystem migration stays post-GA.
2. **Fix distribution correctness:** package policy and add installed-wheel regressions.
3. **Freeze quality commands:** pin/configure Ruff, mypy, Bandit, pip-audit; add missing dependencies.
4. **Run clean gates:** all five tools, build, twine check, wheel/sdist inventory, installed CLI smoke.
5. **Add CI:** rerun on Python 3.11 and 3.12 from a clean checkout.
6. **Cut GA metadata:** versions, phase, changelog, release notes, support policy, README.
7. **Create final GA commit:** verify clean tree and rerun the full pipeline.
8. **Tag `v2.0.0`:** annotated tag at the verified commit.
9. **Publish externally only if intended:** configure remote, push commit/tag, create GitHub release, publish to PyPI, test installation from PyPI.
10. **Consider LTS separately:** only after a defined stabilization/support decision. Do not automatically equate GA with LTS.

## 11. Risks After Release

| Risk | Impact | Mitigation |
|---|---|---|
| Local-only default workspace path | Commands without `--workspace` target `/home/taras/projects` | Keep explicit `--workspace` in public examples; consider post-GA default-policy review |
| Validator requires canonical Workspace OS structure | Ordinary directories produce expected FAIL verdicts | Document clearly; distinguish execution failure from validation findings |
| No daemon | No long-running IPC service | Keep honest stub and unavailable assertion |
| No external integrations | Package does not complete ecosystem migration | State package boundary prominently |
| Security reports currently lack private path | Public disclosures may leak | Add SECURITY.md/private contact before public publication |
| Unpinned lower-bound dev tools | Future installs can change lint outcomes | Pin compatible ranges and run CI |
| Root Workspace validator red | Full ecosystem cannot claim clean Workspace OS compliance | Separate Mission State remediation mission |
| No remote/backup publication | Local repository durability risk | Push verified GA commit/tag after operator authorization |

## 12. Recommended Post-GA Roadmap

### v2.0.x maintenance

- migrate license metadata to SPDX string;
- remove hardcoded test CWDs;
- keep release tool versions current within pinned compatible ranges;
- improve security disclosure and contributor/public governance files;
- retire the legacy validator shim only after documented one-release overlap evidence.

### v2.1 - optional local runtime expansion

- decide whether a daemon is still justified;
- if yes, implement only against the already-defined IPC contract and preflight tests;
- do not make daemon availability a retroactive v2.0 promise.

### Ecosystem migration program

- Knowledge OS promotion integration;
- real GMR merge and durable adapters;
- Factory cutover;
- four-service Compose topology;
- file-bridge tampering and DoS controls;
- cold-boot, canary, Article XIII, and ecosystem release-gate evidence.

These remain governed by the frozen transition architecture and its phase ordering. They must not be pulled into the package GA patch opportunistically.

## 13. Final Operator Decision

**Do not release `v2.0.0` immediately from commit `746c9b4`.**

Delay only for the mandatory bounded fixes in Sections 7 and 9. Do not delay for daemon, `kgctl`, GMR, or Compose implementation. Once distribution correctness, reproducible gates, GA metadata, and CI are green, release the local Python kernel as v2.0.0 and move the ecosystem work to the post-GA roadmap.

## 14. Verification Record

Fresh evidence collected during this audit:

- clean source clone created from local Git commit;
- clean Python 3.12 venv created;
- editable dev install succeeded;
- pytest: 109 passed;
- Ruff default clean-clone run: 81 findings;
- Ruff format check: 19 files would be reformatted;
- mypy default run: one missing `types-PyYAML` error;
- mypy with `--ignore-missing-imports`: success on 14 source files;
- Bandit default: seven LOW findings, exit 1;
- Bandit High-only threshold: zero findings, exit 0;
- pip-audit: no known dependency vulnerabilities; unpublished local package skipped;
- wheel and sdist built successfully;
- `twine check` passed;
- existing ignored `dist/` artifacts contain neither LICENSE nor policy and are stale;
- fresh build from audited HEAD contains LICENSE but still omits policy;
- wheel installed in a second clean venv;
- installed init, mission new/list/close, and agent run smoke passed;
- installed `workspace-os validate` failed due to missing packaged policy;
- installed-sdist test run: 13 failures caused by missing `policy.yaml`;
- root validator: 13 PASS / 111 FAIL, `sprint_pattern_incomplete`;
- ecosystem release gate exceeded the audit's 180-second bound;
- internal backup/rewrite refs and a stale packed `main` ref remain locally;
- no Git remote, GitHub repository, CI workflow, or PyPI distribution found.

No production or architecture files were modified by this audit.
