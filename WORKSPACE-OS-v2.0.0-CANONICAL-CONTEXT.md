# Workspace OS v2.0.0 — Canonical Context

> **Purpose.** This document is the single long-term reference for understanding Workspace OS v2.0.0. It is optimized for future AI agents (or future humans) that have never seen the repository. Every claim is evidence-backed from the released source. Nothing here is aspirational; nothing is invented.
>
> **Authority precedence.** When this document and any other source disagree, the **released source** (HEAD `97c3c49e5f54385256f7f52052e1a5eee012a6b4`, annotated tag `v2.0.0`) wins for implementation details. When the released source and the constitutional authorities (`GOVERNANCE/WORKSPACE-CONSTITUTION.md`, `RATIFICATION.md`) disagree, **the constitutional authorities win** for governance and authority questions. The v1.1 zero-based audit (`workspace-os-v1-deliverables/independent-architecture-review-v1.1.md`) is retained as historical evidence; the post-blueprint v2.0 program is the production path.
>
> **Version of record.** `2.0.0` (released `2026-07-25`, MIT license). Repository: <https://github.com/taras-polishchuk/workspace-os>. GitHub Release: <https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0> (publishedAt `2026-07-25T15:38:29Z`). HEAD `97c3c49e5f54385256f7f52052e1a5eee012a6b4`, annotated tag `v2.0.0`. `v2.0.0a1` is a superseded candidate; `v2.0.0-LTS` is a future governance amendment, not created at GA.

---

## 1. Executive Summary

Workspace OS is a **distributed, local-first, filesystem-level operating environment** for a single human operator and the AI runtimes that act on their behalf. It governs how identity, authority, missions, knowledge, validation, and evidence are organized and recovered. The current v2.0.0 release is the **bounded local Python kernel** for that environment — a single-host, single-operator, single-process state manager with a CLI, a SQLite store, an 8-artifact mission lifecycle, and a Python validator.

Workspace OS is **not** a product, a workflow engine, a SaaS, or a single repository. It is a **maintained discipline and contract over a filesystem**. The `/home/taras/projects/workspace-os/` Python package is one (important) implementable piece of that discipline; the broader system is articulated by `WORKSPACE-OS-CANONICAL-MODEL.md` and the seven constitutional authorities in `GOVERNANCE/`.

A senior engineer should think of it as: a **single-host, single-process, single-operator state kernel** that enforces the eight-artifact Sprint Pattern, persists its audit trail in SQLite, refuses symlinks at the boundary, classifies drift against a versioned policy, and exposes a CLI and a Python peer validator — all with **one runtime dependency** (PyYAML ≥ 6.0) and **no daemon, no network, no hosted service**.

The canonical local-first entry point is the CLI:

```bash
python -m pip install -e ".[dev]"
workspace-os --workspace /home/taras/projects init
workspace-os --workspace /home/taras/projects mission new phase-1-init
workspace-os --workspace /home/taras/projects mission list
workspace-os --workspace /home/taras/projects validate
```

The `validate` step reports a verdict against the canonical 14/78 freeze baseline; every validator run is recorded in the audit table; drift is classified as known, forbidden, or mandatory-preserve.
Canonical evidence of the GA release: GitHub Release <https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0>, GitHub Actions run id `30163934239` (success on Python 3.11 and 3.12 against HEAD `97c3c49e5f54385256f7f52052e1a5eee012a6b4`), wheel SHA-256 `82da84b8f4a99afb83bb4b2b6e845d25e5b46d96a4e200c7db94450aca24bd17`, sdist SHA-256 `23118bbd00a4fc5a3b1fefb74869b4a5c847197f896430c9847e90e9c85004ea`. PyPI publication is intentionally deferred.

---

## 2. Why Workspace OS Exists

### Motivation

Workspace OS exists because **operating a serious engineering practice over a plain filesystem does not scale without governance**. Three forces drove its creation:

- **The context problem.** AI agents and humans both waste tokens and time when the same engineering identity, architecture, and operational rules are duplicated across 100+ files, each at a different revision. Workspace OS consolidates these to a single canonical set.
- **The authority problem.** A serious workspace must answer "who said this is the truth?" — for identity, architecture, amendment procedure, agent registration, and validation. Without explicit authority, drift is inevitable.
- **The recovery problem.** When an AI session is interrupted, when a tool fails, when a CI gate fails, when a mission is half-done — the operator must be able to recover the state from the filesystem without trusting any one runtime's memory. The 8-artifact Sprint Pattern is the answer for missions; the SQLite audit trail is the answer for validator runs; the versioned drift policy is the answer for evidence.

### Design goals (Constitution Article I–X, plus Operating Principles)

| Layer | Source | Goal |
| --- | --- | --- |
| Constitutional | `GOVERNANCE/WORKSPACE-CONSTITUTION.md` | One authority per concept; identity immutability; evidence over opinion; human authority; amendment procedure (Article X). |
| Operating | `WORKSPACE-MANIFEST.md` | One source per concept; identity changes slowly, projects cheaply; load only needed context; reference rather than copy; durable over transient; evidence over opinion. |
| Methodology | OperatorOS six principles (reusable extraction) | Single Authority, Everything Replaceable, Typed Substrate, Composable, Evidence-Based, Local-First. |
| Local kernel | v2.0.0 README, runbook | Bounded, single-host, single-process Python kernel; CLI + SQLite + 8-artifact mission + Python validator; no daemon; no hosted service. |

### Problems solved

- **Identity authority at scale.** Workspace OS makes engineering identity live in one file (`career-operating-system/EngineeringIdentity.md`) and the rest of the system must reference it. The first v1.1 refactor collapsed 24 legacy identity redefinitions to 0 (workspace-os-v1-deliverables/authority-map.md §Identity Drift Status).
- **Sprint pattern enforcement.** A mission is eight files (Constitution Article VII). `Mission.create()` makes that reproducible; `Mission.all_artifacts_present()` checks it; the `sprint_pattern_incomplete` drift category is a hard fail under R14 PRESERVE.
- **Symlink-rejection at the boundary.** Workspace files can be planted as symlinks to attacker-controlled paths. `_safe_io.py` refuses symlinks at every level; `state.py` refuses a symlinked `state.db`; `mission.py` refuses a symlinked mission leaf or any ancestor. The whole boundary is one consistent posture.
- **Drift classification as a contract.** Validator output is classified against a versioned YAML policy. The `drift_id` is `SHA-256(policy_bytes + canonical_categories)`. Forbidden and mandatory categories are un-waivable. This is a contract, not a runtime hope.
- **Audit trail in SQLite.** Every `validate` invocation produces exactly one `validator_runs` row, even on error paths. Every `agent run` produces one `agent_runs` row with the command string and exit code. The filesystem is the source of truth; SQLite is a derived cache (state.py §Per Article VII).
- **Concurrent-init defense.** `WorkspaceState.init()` and the first `connect()` share an advisory file lock on `.wsos/.init.lock`. `PRAGMA busy_timeout = 5000` is set so concurrent writers wait up to 5 s. This closes the race where two processes bootstrap a workspace simultaneously.

### Non-goals (explicit, from `README.md`, `RELEASE.md`, `SUPPORT.md`, `WORKSPACE-OS-CANONICAL-MODEL.md`)

- **No daemon process.** `daemon.py` is an honest unavailable contract stub. `is_daemon_available()` returns `False`. `ipc_request()` raises `DaemonNotAvailableError`. The CLI is the only surface.
- **No distributed / multi-host deployment.** Single-host, single-process. The `daemon.py` stub is the placeholder for a future process that would own the SQLite write lock and expose a unix-socket API, but it is not a v2.0 deliverable.
- **No hosted service or SaaS.** The kernel is local and single-host. There is no network authority.
- **No `kgctl approve-canonical` integration, GMR monorepo creation, four-service Compose deployment.** These are post-GA ecosystem work; explicitly listed as "not included" in `RELEASE.md` §"Deliberately outside v2.0.0".
- **No marketplace, no auto-update, no schema-less configuration, no multi-tenant SaaS.** Consistent with the broader Workspace OS boundary.
- **No promotion of an LLM to authority.** The CLI is operator-driven. The validator is policy-driven. AI is never the authority for identity, amendment, or mission state.
- **No history deletion.** Per Constitution Article X (amendment procedure), governance changes are recorded, not rewritten.

---

## 3. Position Inside the Ecosystem

Workspace OS sits at the top of an authority hierarchy. Each of these is distinct; confusing them is the most common error.

| System | Role | Relationship to Workspace OS |
| --- | --- | --- |
| **Workspace OS (this product)** | A **filesystem-level operating discipline and a local Python kernel** (`workspace-os` v2.0.0). | The authority plane. Seven constitutional primitives (Identity, Principle, Authority, Knowledge, Mission, Subsystem, Specialization). Defines the contract; provides a bounded kernel implementation. |
| **OperatorOS Platform** (separate product, v1.0.0) | A local-first TypeScript platform for executing Missions as durable Runs with an evidence ledger. | **Shared S4 infrastructure, not a 7th Workspace OS Subsystem.** It implements Workspace OS Missions as durable Runs; references Workspace OS primitives; never redefines them. |
| **OperatorOS v0.8** | The prior, frozen release line. | A reusable methodology/CLI extracted from Workspace OS. Optional to Workspace OS. Migration is one-way via `v08-importer` in OperatorOS Platform. |
| **Knowledge OS** | A parallel durable knowledge substrate and governed product. | Not the authority over Workspace OS. `workspace-knowledge-vault/` is its generated/imported production corpus, not a second authority. |
| **AI Factory** | A higher-level product composition that runs OperatorOS. | A consumer of Workspace OS identity, mission, and authority. Not a Workspace OS authority. |
| **Hermes** | A runtime AI orchestrator. | The current runtime orchestrator, not a Workspace OS primitive. `~/.hermes/` is its config. |
| **Other top-level projects** (taras-polishchuk.github.io, the career-operating-system, the AI ecosystem documentation, etc.) | Concrete products and reference corpora. | They participate through context, Mission State, runtime adapters, evidence, and validators. They do not become constitutional authorities merely by living under `/home/taras/projects`. |

### Distinguishing architecture from implementation

The **Workspace OS architecture** is a **frozen discipline over a filesystem**, articulated by `WORKSPACE-OS-CANONICAL-MODEL.md`, `GOVERNANCE/WORKSPACE-CONSTITUTION.md`, `RATIFICATION.md`, and the `OPERATOROS-AND-WORKSPACE-OS-HOWTO.md` guide. It defines four planes (authority, control, execution, evidence) and seven primitives. It is not a single file.

The **Workspace OS v2.0.0 kernel implementation** is a **Python package** (`workspace-os`) at `/home/taras/projects/workspace-os/`, distributed via wheel and sdist. It implements the local-kernel portion of the broader architecture. The CLI, the SQLite store, the 8-artifact mission lifecycle, and the Python validator are the kernel.

The **v1.1 zero-based architecture review** (`workspace-os-v1-deliverables/independent-architecture-review-v1.1.md`) is **historical evidence**, not a current governance document. It is preserved because the post-blueprint v2.0 program explicitly chose the production path through the Implementation Program and the Amendment procedure (see §6.2 and §9), not through the v1.1 deliverables.

---

## 4. Core Concepts

These are the concepts a future agent must keep straight. Each is independent. The canonical glossary is `WORKSPACE-OS-CANONICAL-MODEL.md` and the seven constitutional authorities.

**Workspace.** A single operator-controlled directory tree. The canonical example is `/home/taras/projects`. The kernel's runtime state lives in `<workspace>/.wsos/`.

**Workspace OS Constitution.** The `GOVERNANCE/WORKSPACE-CONSTITUTION.md` file. Defines Articles I through X (and subsequent amendments). Article VII is the 8-artifact Sprint Pattern. Article X is the amendment procedure. New Articles are added by amendment, not by edit.

**Sprint Pattern (Constitution Article VII).** The canonical 8-file mission directory layout. Every mission under `.project-state/<slug>/` must contain all eight:

```
source-task.md     what + why
progress.md        current state
decisions.md       key choices with rationale
blockers.md        open issues
artifacts.md       produced files
environment.md     system snapshot
execution-log.md   timestamped actions
final-report.md    closure
```

The v2.0.0 kernel implements this in `workspace_os.mission.SPRINT_PATTERN_FILES` (a tuple of 8 strings). `Mission.create()` populates the directory with templated headers. `Mission.all_artifacts_present()` returns `(ok, missing)`. The Python validator emits a `sprint_pattern_incomplete` drift category if a directory is missing files; this category is in `mandatory_drift` (R14 PRESERVE), so it is un-waivable.

**Identity.** A single canonical engineering-identity file (`career-operating-system/EngineeringIdentity.md`). Referenced by symlink (`IDENTITY.md`). The v1.1 refactor collapsed 24 legacy identity redefinitions to 0. Future agents must read this file, not invent their own.

**Mission.** A mission is the *de facto* filesystem pattern of a `.project-state/<slug>/` directory. `Mission.create()` materializes the 8 files with templated headers; `Mission.exists()` and `Mission.all_artifacts_present()` check the structure. The SQLite `missions` table is a derived cache, not the source of truth.

**Mission slug.** Lowercase alphanumeric with hyphens, must start and end with an alphanumeric character, length 2..64. Validated by `SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")`. Invalid slugs raise `InvalidSlugError`.

**WorkspaceState.** A handle to the SQLite state at `<workspace>/.wsos/state.db`. Methods: `init()`, `connect()`, `register_workspace()`, `register_mission()`, `close_mission()`, `record_mission_artifact()`, `record_validator_run()`, `record_agent_run()`, `list_missions()`, `latest_validator_run()`, `iter_workspaces()`.

**Validator verdict.** A `ValidatorVerdict` dataclass: `pass_count`, `fail_count`, `raw_output`, `raw_output_path`, `exit_code`, `drift_id`, `drift_categories`, `accepted`, `accept_rationale`, `policy_ok`. The `ok` property returns `policy_ok` (NOT the legacy shell exit code), because the frozen shell validator returns nonzero for the canonical 14/78 baseline; policy classification is authoritative.

**Drift.** A category of deviation from the canonical Workspace OS layout. Three classes: `known_drift` (waivable with `--accept-drift --accept-rationale` and not in strict mode), `forbidden_drift` (never waivable — currently `unexpected_db_writer`, `missing_validator_script`), `mandatory_drift` (R14 PRESERVE — always hard-fail regardless of any flag — currently `missing_security_audit_log`, `missing_audit_json_key`, `sprint_pattern_incomplete`).

**Drift ID.** `SHA-256(policy_source_bytes + canonical_actual_category_list)`. Stable across runs that produce the same drift categories under the same policy. Stored in `mission_artifacts` as a sidecar (`validator-drift-id` row).

**Policy.** A versioned YAML document at `policy.yaml` (in-repo, also packaged via `importlib.resources`). Schema_version is 1. Contains `invariants` (min_pass_count, max_fail_count, max_runtime_seconds), `known_drift`, `forbidden_drift`, `mandatory_drift`, and `baseline` (pass_count, fail_count). The freeze baseline is **14 PASS / 78 FAIL** (R7). The historical 14/66 figure is explicitly obsolete (`policy.yaml:3`).

**Validator.** A peer CLI entry point (`validator`) registered in `pyproject.toml` as `validator = "workspace_os.validator.__main__:main"`. The default is the Python peer; the legacy `bin/validate-workspace.sh` shim is honored only if present AND safe (owned by current UID, not group/world-writable, no special bits, no symlink at any parent). Otherwise, the Python peer runs and the shim is ignored.

**Validator run.** A single invocation of `workspace-os validate`. Always recorded in `validator_runs` (R6 acceptance), including on `FileNotFoundError` and `subprocess.TimeoutExpired` paths (H-8 fix). Schema: `run_id, workspace_id, ts, pass_count, fail_count, raw_output_path`.

**Agent run.** A single invocation of `workspace-os agent run -- <command>`. Recorded in `agent_runs` with the command string, exit code, and a per-run log file at `<workspace>/.wsos/agent-runs/run-<workspace_id>-<ms_timestamp>-<pid>.log`. The command is executed via `subprocess.run` with `cwd=<workspace_root>` and no `shell=True`.

**Safe I/O boundary.** `_safe_io.py` provides the safety primitives the kernel relies on: `safe_mkdir` (refuses symlinks at any level), `atomic_write_text` (write-temp-then-rename), `tighten_existing_file` (chmod 0o600), `SymlinkRefusedError`, `WSOS_DIR_MODE = 0o700`, `WSOS_FILE_MODE = 0o600`. The whole kernel is one consistent posture: refuse symlinks, atomic writes, owner-only.

**Daemon (intentionally unavailable).** The kernel exposes `IPC_CONTRACT_VERSION = "0-stub"`, `is_daemon_available()` (always False), `ipc_request()` (always raises `DaemonNotAvailableError`), and `daemon_main()` (prints informational message and returns 0). The `workspace-os daemon` subparser is NOT exposed. References to "daemon" in module docstrings are forward-looking.

**Operator.** The single human responsible for the workspace. AI is never the operator. The CLI accepts the operator's input; the validator returns a verdict the operator reads; the operator decides what to fix.

**Drift-acceptance audit log.** An append-only JSONL at `<workspace>/.wsos/drift-acceptance.jsonl`. Each accepted-drift run appends one record: `ts, drift_id, categories, rationale, mission_id`. Atomic write; refuses symlinks.

**Frozen authority documents.** Seven documents that constitute the Workspace OS governance plane, per `WORKSPACE-OS-CANONICAL-MODEL.md` and the v1.1 `authority-map.md` (the v1.1 deliverable counts 16 documents, but the seven constitutional primitives are the canonical set):

1. `career-operating-system/EngineeringIdentity.md` — Engineering Identity
2. `system-graph.md` — Workspace Architecture
3. `GOVERNANCE/WORKSPACE-CONSTITUTION.md` — Constitution
4. `GOVERNANCE/AUTHORITY-MODEL.md` — Authority Model
5. `GOVERNANCE/CONTEXT-ROUTING.md` — Context Routing
6. `GOVERNANCE/DOCUMENT-LIFECYCLE.md` — Document Lifecycle
7. `GOVERNANCE/VALIDATION-CHECKLIST.md` — Validation Checklist

Plus operational documents (`RATIFICATION.md`, `AMENDMENTS.md`, `BOOTSTRAP.md`, `HUMAN-INSTRUCTIONS.md`, `IDENTITY-AUTHORITY-MAP.md`, `AGENT-REGISTRY.md`, `CONTEXT/operator-profile.md`, `CONTEXT/state-summary.md`, `CONTEXT/high-leverage-assets.md`, `CONTEXT/workspace-index.json`, `INSTRUCTIONS/*.md`).

**Top-level symlinks.** `IDENTITY.md` resolves to `career-operating-system/EngineeringIdentity.md`; `ARCHITECTURE.md` resolves to `system-graph.md`. They are the canonical entry points for "where do I start?" — agents can hard-code these paths.

**Eight-artifact Sprint Pattern invariant.** The 8-file mission directory is enforced at three levels: filesystem (Mission.create populates and Mission.all_artifacts_present checks), policy (mandatory_drift includes sprint_pattern_incomplete), audit (drift-acceptance.jsonl records any acceptance, and PRESERVE means this acceptance is impossible).

---

## 5. Internal Architecture

### 5.1 The four-plane model (Workspace OS authority)

From `WORKSPACE-OS-CANONICAL-MODEL.md` §1:

| Plane | What lives here | Concrete artifacts |
| --- | --- | --- |
| **Authority plane** | Identity, Constitution, architecture, authority classes, lifecycle, context-routing, ratification, amendments, human final authority. | The 7 constitutional primitives + `RATIFICATION.md` + `AMENDMENTS.md` + the 25 instruction symlinks. |
| **Control plane** | Four-file bootstrap, progressive context loading, Mission State, Kanban, agent/skill routing, validation, recovery policy. | `GOVERNANCE/BOOTSTRAP.md` + `.project-state/` + `kanban.db` (external) + `workspace-os` Python kernel + `bin/validate-workspace.sh` legacy shim. |
| **Execution plane** | Hermes + optional implementations (OperatorOS v0.8, OperatorOS Platform) + product runtimes (Knowledge OS, CCP/Content OS, AI Factory, deployed products). | `~/.hermes/`, `operatoros-platform/`, `operatoros/`, `workspace-knowledge-vault/`. |
| **Evidence plane** | Workspace files + git history, Mission State, `kanban.db`, `state.db`, Knowledge OS entities, audit logs, validator output, release gates, backups, historical records. | Every file under `/home/taras/projects/`, including `<workspace>/.wsos/state.db` and `<workspace>/.wsos/agent-runs/`. |

### 5.2 The Workspace OS v2.0.0 kernel (the Python package)

The v2.0.0 kernel is the bounded local implementation of the control plane. It is **one** Python package with seven first-class modules:

| Module | File | Role |
| --- | --- | --- |
| `workspace_os.__init__` | `__init__.py` (36 lines) | Public API surface, `__version__ = "2.0.0"`. (The historical `__phase__ = "v2.0-rc"` constant was retired at the GA commit; the kernel is past the release-candidate phase.) Exports `SPRINT_PATTERN_FILES`, `Mission`, `WorkspaceState`, `run_validator`, `ValidatorVerdict`. |
| `workspace_os.mission` | `mission.py` (282 lines) | `Mission` dataclass + `Mission.create()` (the 8-artifact Sprint Pattern enforcer) + `SLUG_RE` + `_validate_slug` + `_format_utc_timestamp` + `_format_utc_date`. |
| `workspace_os.state` | `state.py` (461 lines) | `WorkspaceState` dataclass + `SCHEMA` (5 tables) + `WorkspaceState.init/connect/register_workspace/register_mission/close_mission/record_mission_artifact/record_validator_run/record_agent_run/list_missions/latest_validator_run/iter_workspaces` + `_init_lock` (advisory file lock) + `_bootstrap`. |
| `workspace_os.policy` | `policy.py` (135 lines) | `Policy` + `Invariants` dataclasses + `load_policy` + `validate_policy` + `drift_categories` + `compute_drift_id` (SHA-256 of policy bytes + canonical categories). |
| `workspace_os.validate` | `validate.py` (228 lines) | `run_validator()` (Python peer) + `ValidatorVerdict` + `DEFAULT_POLICY_RESOURCE` (`importlib.resources`) + `_shim_is_safe` (defence-in-depth for legacy shim) + summary regex `Summary:\s*(\d+)\s*passed,\s*(\d+)\s*failed`. |
| `workspace_os.daemon` | `daemon.py` (83 lines) | Honest unavailable contract stub. `IPC_CONTRACT_VERSION = "0-stub"`, `is_daemon_available()` (False), `DaemonNotAvailableError`, `ipc_request()` (raises), `daemon_main()` (informational). |
| `workspace_os.cli` | `cli.py` (590 lines) | `argparse` subparser tree. Subcommands: `init`, `mission new/list/close`, `validate`, `agent run`. Top-level options: `--workspace`, `--yes`, `--version`. |
| `workspace_os._safe_io` | `_safe_io.py` (233 lines) | Safety primitives. `safe_mkdir` (refuses symlinks), `atomic_write_text` (write-temp-then-rename), `tighten_existing_file`, `SymlinkRefusedError`, `WSOS_DIR_MODE = 0o700`, `WSOS_FILE_MODE = 0o600`. |
| `workspace_os.validator.__init__` | `validator/__init__.py` (104 lines) | Re-exports + the `run_validation` peer. |
| `workspace_os.validator.__main__` | `validator/__main__.py` (37 lines) | `validator` peer CLI entry. |
| `workspace_os.validator.drift` | `validator/drift.py` (9 lines) | Re-export shim — `Policy`/`drift_categories`/`compute_drift_id` come from `policy.py`. |
| `workspace_os.validator.invariants` | `validator/invariants.py` (433 lines) | The Python ports of the shell validator checks. |
| `workspace_os.validator.report` | `validator/report.py` (59 lines) | Report formatting. |
| `workspace_os.validator.timeout` | `validator/timeout.py` (37 lines) | Per-check timeout. |

Total: ~2,727 lines of Python source.

The package layout is conventional `src/workspace_os/`. `src/workspace_os.egg-info/` is auto-generated by setuptools (git-ignored). `policy.yaml` is the in-repo source policy; it is also packaged as a wheel/sdist resource and loaded via `importlib.resources.files("workspace_os").joinpath("policy.yaml")` (so installed wheels do not depend on the repository root).

### 5.3 The SQLite schema (5 tables)

| Table | Columns | Source of truth |
| --- | --- | --- |
| `workspaces` | `workspace_id`, `root_path` (UNIQUE), `created_at`, `last_seen_at` | The filesystem (root_path) is source of truth; this table is the cache. |
| `missions` | `mission_id`, `slug`, `workspace_id` (FK), `status` (`'open'`/`'closed'`), `created_at`, `closed_at`, `root_path`, UNIQUE(workspace_id, slug) | The `.project-state/<slug>/` directory is source of truth; this table is the cache. |
| `mission_artifacts` | `artifact_id`, `mission_id` (FK), `filename`, `"exists"`, `sha256`, `mtime`, UNIQUE(mission_id, filename) | Per-article existence check + sidecar (e.g. `validator-drift-id`). |
| `validator_runs` | `run_id`, `workspace_id` (FK), `ts`, `pass_count`, `fail_count`, `raw_output_path` | The audit trail. Always one row per `validate` invocation. |
| `agent_runs` | `run_id`, `mission_id` (FK, nullable), `ts`, `command`, `exit_code`, `output_path` | The agent-run audit trail. |

Indexes: `idx_missions_workspace`, `idx_missions_status`, `idx_validator_runs_workspace`, `idx_agent_runs_mission`.

PRAGMAs at every `connect()`: `PRAGMA busy_timeout = 5000`, `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`. Sidecars (WAL/SHM) are tightened to mode 0o600 on every bootstrap.

### 5.4 The drift policy (R7 + R14)

`policy.yaml` is a versioned YAML document. The current freeze baseline is `baseline: { pass_count: 14, fail_count: 78 }`. The invariants are `min_pass_count: 14`, `max_fail_count: 78`, `max_runtime_seconds: 60`. Three drift classes:

- **`known_drift`**: empty in v2.0.0. Drift categories the operator accepts as legitimate.
- **`forbidden_drift`**: `unexpected_db_writer`, `missing_validator_script`. Always hard-fail.
- **`mandatory_drift`** (R14 PRESERVE): `missing_security_audit_log`, `missing_audit_json_key`, `sprint_pattern_incomplete`. Always hard-fail regardless of `--accept-drift` or `--strict`.

The validator computes a `drift_id` as `SHA-256(policy.source_bytes + JSON({"policy_sha256": ..., "categories": sorted(actual_categories)}))`. This is stable across runs that produce the same drift under the same policy. The drift ID is recorded as a sidecar in `mission_artifacts` (filename `validator-drift-id`) when the run is bound to a mission via `--mission <slug>`.

### 5.5 The CLI surface

`workspace-os` is a single multi-level argparse subparser tree:

```
workspace-os
├── init
├── mission
│   ├── new <slug> [--state-root <path>] [--overwrite]
│   ├── list
│   └── close <id-or-slug> [--force]
├── validate [--output <path>] [--policy <path>] [--accept-drift] [--accept-rationale <text>] [--mission <slug>] [--strict]
└── agent
    └── run -- <command> [--mission <slug>]
```

Top-level options: `--workspace <path>` (or `-w`), `--yes` (allow creating the workspace root if it does not exist), `--version`. The workspace root default is the current working directory (`Path.cwd()`); override with `--workspace` or `$WORKSPACE_OS_ROOT`. The historical hard-coded `/home/taras/projects` default was replaced at the GA commit for portability.

The peer CLI `validator` is registered separately as `validator = "workspace_os.validator.__main__:main"`. It is the Python validator exposed for callers that bypass the `workspace-os validate` subcommand.

### 5.6 Runtime model

- **Process model.** Single Python process per workspace. The kernel does not fork, daemonize, or open sockets. `daemon.py` is a stub.
- **Concurrency model.** The advisory file lock on `.wsos/.init.lock` (created with mode 0o600) serialises `init()` and the first `connect()`. `PRAGMA busy_timeout = 5000` lets concurrent writers wait. WAL mode allows concurrent readers.
- **Network model.** None. The kernel does not open sockets, talk to the network, or call external services. The only external process invocation is `bash bin/validate-workspace.sh` (the legacy shim, defended with `_shim_is_safe`).
- **State recovery model.** The filesystem is the source of truth. SQLite is a derived cache. Mission identity lives in `.project-state/<slug>/`; validator runs live in `validator_runs`; agent runs live in `agent_runs` + `<workspace>/.wsos/agent-runs/`. The drift policy is a package resource that ships in the wheel.

---

## 6. Repository Structure

A future agent that has only this document needs to know where to look. The repository top level is:

| Path | Role |
| --- | --- |
| `README.md` | Public overview (91 lines). Bounded local-kernel scope, four-step install + golden path. |
| `CHANGELOG.md` | `[Unreleased]`, `[2.0.0] - 2026-07-25`, `[2.0.0a1] - 2026-07-22`, `[1.1.0-LTS] - 2026-06-28`. |
| `RELEASE.md` | Canonical release narrative. v2.0.0 is the published GA release. Lists what is in / out, verification command, publication state. |
| `SUPPORT.md` | Supported versions table; the "We fix / We do not treat" boundary; deprecation policy; security channel caveat. |
| `LICENSE` | MIT, © 2026 Taras Polishchuk. |
| `pyproject.toml` | Build (setuptools ≥ 68), `name = "workspace-os"`, `version = "2.0.0"`, `requires-python = ">=3.11"`, runtime deps `["PyYAML>=6.0"]`, dev extras, console scripts `workspace-os` and `validator`, Ruff/mypy/bandit config. |
| `policy.yaml` | The versioned drift-classification policy. Freeze baseline 14/78. |
| `runbook.md` | Operator-facing runbook. Quick start, mission lifecycle, validator, audit trail, bridge integration, daemon, commit identity, troubleshooting, what's implemented. |
| `src/workspace_os/` | The Python package source (~2,727 lines, 14 files). |
| `src/workspace_os.egg-info/` | Setuptools-generated metadata (git-ignored). |
| `tests/` | Pytest test suite (114 tests, 8 files). |
| `docs/validator-callers.md` | WP-08 / R13 documentation: how release-gate, deployment-static, build-bundle, and cold-boot-recovery consume the validator; the one-release overlap shim; the retirement plan. |
| `scripts/release_verify.py` | The canonical release verifier (Ruff check, Ruff format, mypy, Bandit, pytest, pip-audit, build, archive contents, installed-package smoke). Supports `--clean-clone`. |
| `examples/` | Example usage. |
| `dist/` | Built wheel and sdist (git-ignored; produced by `python -m build`). |
| `.github/` | CI workflows. |
| `.wsos/` | Created at runtime (mode 0o700). The kernel's local state. |
| `venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/` | Local runtime caches (git-ignored). |
| `.gitignore` | Standard Python ignores; `.wsos` is NOT ignored because it is operator state. |

### 6.1 The `src/workspace_os/` package

```
src/workspace_os/
├── __init__.py            # 36 lines. Public API, version, phase, exports
├── __pycache__/           # git-ignored
├── _safe_io.py            # 233 lines. safe_mkdir, atomic_write_text, tighten_existing_file, SymlinkRefusedError
├── cli.py                 # 590 lines. argparse subparser tree
├── daemon.py              # 83 lines. Honest unavailable contract stub
├── mission.py             # 282 lines. SPRINT_PATTERN_FILES, Mission, SLUG_RE
├── policy.py              # 135 lines. Policy, Invariants, compute_drift_id, drift_categories
├── policy.yaml            # The versioned drift-classification policy
├── state.py               # 461 lines. WorkspaceState, SCHEMA, init, connect, register_*
├── validate.py            # 228 lines. run_validator, ValidatorVerdict, DEFAULT_POLICY_RESOURCE
└── validator/
    ├── __init__.py        # 104 lines. Re-exports + run_validation peer
    ├── __main__.py        # 37 lines. validator peer CLI entry
    ├── drift.py           # 9 lines. Re-export shim from policy.py
    ├── invariants.py      # 433 lines. Python ports of the shell validator checks
    ├── report.py          # 59 lines. Report formatting
    └── timeout.py         # 37 lines. Per-check timeout
```

### 6.2 The Workspace OS authority documents (the broader filesystem, not the v2.0.0 kernel)

The kernel does not contain the constitutional authorities — those live in the broader `/home/taras/projects/` filesystem. A future agent must distinguish between:

- **The kernel repository** at `/home/taras/projects/workspace-os/` — the v2.0.0 Python implementation.
- **The Workspace OS authority plane** at `/home/taras/projects/GOVERNANCE/`, `/home/taras/projects/CONTEXT/`, `/home/taras/projects/RATIFICATION.md`, `/home/taras/projects/AMENDMENTS.md`, `/home/taras/projects/IDENTITY.md` (symlink to `career-operating-system/EngineeringIdentity.md`), `/home/taras/projects/ARCHITECTURE.md` (symlink to `system-graph.md`).
- **The Workspace OS canonical model** at `/home/taras/projects/WORKSPACE-OS-CANONICAL-MODEL.md` (reconstructed 2026-07-20, 57 KB, 773 lines). This is the post-v1.1 reconstruction; treat it as the operating reference for the broader system.
- **The post-blueprint program** at `/home/taras/projects/FINAL-IMPLEMENTATION-PROGRAM.md` (2026-07-22). The v2.0 program ratification record.
- **The v1.1 zero-based architecture review** at `/home/taras/projects/workspace-os-v1-deliverables/independent-architecture-review-v1.1.md` (2026-06-28). Historical evidence; the production path is the v2.0 program, not the v1.1 deliverables.
- **The v1 deliverables bundle** at `/home/taras/projects/workspace-os-v1-deliverables/` (20 files: authority-map, validation reports, technical-debt register, rollback instructions, etc.). Retained per Constitution's amendment and audit retention principles.

---

## 7. Runtime Flow

A canonical Workspace OS v2.0.0 session walks through these steps. The numbers reference the source files where the work happens.

### 7.1 Workspace initialization

1. **Operator chooses a workspace root.** The default is the current working directory (`Path.cwd()`); override with `--workspace <path>` or `$WORKSPACE_OS_ROOT`. The directory must exist; pass `--yes` to allow creation. (The historical hard-coded `/home/taras/projects` default was replaced at the GA commit for portability.)
2. **Operator invokes `init`.** `workspace-os --workspace <root> init` runs `cmd_init` (`cli.py`). It calls `WorkspaceState.for_workspace(root)`, which sets `db_path = <root>/.wsos/state.db` and `wsos_root = <root>/.wsos`. It then calls `state.init()`.
3. **`init()` acquires the advisory file lock on `.wsos/.init.lock`.** This serialises `init()` and the first `connect()` against the same workspace. Concurrent processes wait.
4. **Bootstrap creates `.wsos/` with mode 0o700.** `safe_mkdir` refuses any symlink at any level.
5. **The schema is created.** `conn.executescript(SCHEMA)` runs the 5 CREATE TABLE / 4 CREATE INDEX statements.
6. **The database file is chmod'd to 0o600.** `tighten_existing_file` is called on `state.db` and on the WAL/SHM sidecars.
7. **`register_workspace(root)` is called.** `INSERT ... ON CONFLICT(root_path) DO UPDATE SET last_seen_at = excluded.last_seen_at` is idempotent — concurrent registrations produce exactly one row. Returns the `workspace_id`.
8. **CLI prints confirmation.** `Initialized workspace-os at <wsos_root>` and `Workspace registered: id=<id> root=<root>`. Returns 0.

### 7.2 Mission creation

1. **Operator invokes `mission new <slug>`.** Example: `workspace-os --workspace /home/taras/projects mission new phase-1-init`.
2. **Slug validation.** `SLUG_RE.match(slug)` checks the regex; on failure raises `InvalidSlugError`, CLI returns exit code 2.
3. **Mission directory creation.** `Mission.create(slug, workspace_root, state_root=None, *, overwrite=False)` runs in `mission.py`:
   - Validates the slug.
   - Resolves `state_root` (defaults to `<workspace>/.project-state/`).
   - **Refuses symlinks** at the mission leaf, at the `state_root`, and at any ancestor of `state_root` inside the workspace. This is the symlink-rejection boundary.
   - If the mission directory exists and `overwrite=False`, raises `FileExistsError` (CLI returns 3). With `overwrite=True`, `shutil.rmtree` removes it.
   - `safe_mkdir(state_root, mode=0o700)` and `safe_mkdir(mission_dir, mode=0o700)` create the directory tree.
4. **The 8 Sprint Pattern files are populated** with templated headers (`_populate()` in `mission.py`):
   - `source-task.md`, `progress.md`, `decisions.md`, `blockers.md`, `artifacts.md`, `environment.md`, `execution-log.md`, `final-report.md`.
   - Each file is created with `O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600` — no-follow means a planted symlink at the file path is refused by the kernel itself.
5. **The mission is registered in SQLite.** `state.register_mission(workspace_id, slug, mission.root_path)` is idempotent on `(workspace_id, slug)`. Returns the `mission_id`.
6. **All 8 artifacts are recorded in `mission_artifacts`.** `state.record_mission_artifact(...)` is called for each file with `exists=True, sha256=None, mtime=None`.
7. **CLI prints** `Created mission <slug> at <path> (id=<id>)`. Returns 0.

### 7.3 Validator invocation

1. **Operator invokes `validate`** with optional flags: `--output`, `--policy`, `--accept-drift`, `--accept-rationale`, `--mission <slug>`, `--strict`.
2. **CLI ensures the workspace state is initialised.** If `state.init()` fails (e.g. permission error), `WorkspaceStateInitError` is raised and the CLI returns exit code 5.
3. **Mission lookup** (if `--mission` is set): the slug is resolved to `mission_id` via `state.list_missions(workspace_id)`. If not found, exit code 4.
4. **`run_validator()` is called** with the effective timeout (`min(timeout, policy.invariants.max_runtime_seconds)`) and the strict flag.
5. **Policy is loaded.** Default is `importlib.resources.files("workspace_os").joinpath("policy.yaml")`; override with `--policy`.
6. **Validator path is chosen** (`validate.py`):
   - If `<workspace>/bin/validate-workspace.sh` exists AND `_shim_is_safe(...)` (owned by current UID, not group/world-writable, no setuid/setgid/sticky bits, no symlink at any parent), the shim is executed via `subprocess.run(["bash", str(shim)])`.
   - Otherwise (default), the Python peer `run_validation(workspace_root, check_timeout=...)` is called.
7. **Verdict is computed.** `drift_categories(policy, raw_output)` extracts the actual categories. `compute_drift_id(policy, raw_output)` produces the SHA-256-based drift ID. `policy_ok = not forbidden and not mandatory_hit and (not unexpected or (accept_drift and not strict))`.
8. **If accepted, the audit record is appended** to `<workspace>/.wsos/drift-acceptance.jsonl` via atomic write (refuses symlinks).
9. **Validator run is recorded.** `state.record_validator_run(workspace_id, pass_count, fail_count, raw_output_path)` always creates one row, even on error paths (`FileNotFoundError` → exit code 5; `subprocess.TimeoutExpired` → exit code 6).
10. **CLI prints the verdict** and returns the appropriate exit code.

### 7.4 Agent run

1. **Operator invokes `agent run -- <command>`** with optional `--mission <slug>`.
2. **The `--` separator is filtered out.** If nothing remains, the CLI returns exit code 2 (HIGH-2 fix).
3. **The command is executed** via `subprocess.run(filtered, cwd=str(workspace_root))`. No `shell=True`.
4. **A per-run log is written** to `<workspace>/.wsos/agent-runs/run-<workspace_id>-<ms_timestamp>-<pid>.log` via `atomic_write_text` (refuses symlinks at any level).
5. **`agent_runs` row is recorded** with `mission_id`, the quoted command string, the exit code, and the log path.
6. **CLI prints** `agent_runs row id=<id>` and returns the command's exit code.

### 7.5 Persistence

- **Local default.** SQLite at `<workspace>/.wsos/state.db`. Mode 0o600. WAL mode. `PRAGMA busy_timeout = 5000`. `PRAGMA foreign_keys = ON`.
- **Sidecar tightening.** `.db-wal` and `.db-shm` are chmod'd to 0o600 on every bootstrap.
- **No host store.** No cloud authority, no marketplace, no auto-update. The workspace and its evidence are operator-controlled.

### 7.6 Evidence generation

- **Mission files.** The 8 Sprint Pattern files are the operator-facing evidence surface. `Mission.all_artifacts_present()` checks existence and non-empty.
- **Validator runs.** Every invocation records a `validator_runs` row with `pass_count`, `fail_count`, `raw_output_path`. The drift ID is recorded as a sidecar in `mission_artifacts` when bound to a mission.
- **Agent runs.** Every `agent run` records an `agent_runs` row with the quoted command, exit code, and a per-run log file. The log file is symlink-rejected.
- **Drift acceptance audit.** When `--accept-drift` is used, one JSONL record is appended with `ts, drift_id, categories, rationale, mission_id`. Atomic write; refuses symlinks.

### 7.7 Recovery

The kernel is **state-recoverable** because state is durable and the safe-I/O boundary is consistent:

- **State database corruption.** The filesystem (`.project-state/<slug>/`) is the source of truth. SQLite is a derived cache. If the DB is corrupted, the missions can be reconstructed from filesystem walks; the audit trail is lost but the canonical mission state survives.
- **Concurrent bootstrap.** The advisory file lock on `.wsos/.init.lock` serialises `init()` and the first `connect()`. PRAGMA `busy_timeout` lets writers wait.
- **Symlink-rejection.** Every boundary refuses symlinks. A planted symlink is detected by `safe_mkdir` or `_shim_is_safe`; the operation fails with `SymlinkRefusedError` rather than writing through it.
- **Atomic writes.** `atomic_write_text` writes to a tempfile, then renames. A partial write never replaces an existing file.
- **Mission close is idempotent.** `state.close_mission(mission_id)` returns `'closed'` whether it performed the transition or the mission was already closed. It does not overwrite `closed_at` on a second call.

### 7.8 Shutdown

There is no daemon and no formal shutdown. Each CLI invocation runs to completion and exits. The kernel holds no in-memory state across invocations. The next `workspace-os` invocation reconstructs state from the filesystem and the SQLite cache. The drift-acceptance audit log and the validator-runs audit trail are append-only; nothing is rewritten on shutdown.

---

## 8. CLI

`workspace-os` is the only public CLI surface shipped in v2.0.0. The peer CLI `validator` is registered for callers that bypass the `validate` subcommand.

### 8.1 Subcommands

| Subcommand | Purpose | Exit codes |
| --- | --- | --- |
| `init` | Initialize `<workspace>/.wsos/` and register the workspace root. | 0 success; 5 on filesystem error. |
| `mission new <slug>` | Create a mission under `.project-state/`. | 0 success; 2 invalid slug; 3 directory exists; 5 filesystem error. |
| `mission list` | List missions registered to the workspace. | 0 success; 5 on filesystem error. |
| `mission close <id-or-slug>` | Close a mission by id or slug. Idempotent. | 0 success (including no-op); 4 not found; 5 DB error. |
| `validate` | Run the Python validator and parse the verdict. | 0 if policy_ok; 1 if policy violation; 2 invalid input; 4 not found; 5 filesystem/perms; 6 timeout. |
| `agent run -- <command>` | Run a shell command and record it. | The command's exit code; 2 if no command after `--`; 4 mission not found; 5 filesystem error. |

### 8.2 Output conventions

- The CLI prints human-readable summaries to stdout. Errors go to stderr.
- The validator verdict is printed as `Validator verdict: <N> PASS / <M> FAIL (exit <code>); drift_id=<hash>`.
- Agent-run output is `agent_runs row id=<id>` followed by the command's exit code.
- Mission-list output is a columnar table with `mission_id`, `slug`, `status`, `created_at`.
- The `--output <path>` flag for `validate` writes raw output to a file via `atomic_write_text` (refuses symlinks).

### 8.3 Top-level options

- `--workspace <path>` / `-w` — the workspace root. Default: `$WORKSPACE_OS_ROOT`, or the current working directory (`Path.cwd()`) when the env var is unset.
- `--yes` — allow creating the workspace root directory if it does not exist.
- `--version` — print `workspace-os 2.0.0` and exit.

### 8.4 Validator flags (R6, R7, R13, R14)

| Flag | Effect |
| --- | --- |
| `--output <path>` | Write raw validator output to `<path>` atomically. |
| `--policy <path>` | Override the default `policy.yaml`. |
| `--accept-drift` | Waive non-forbidden, non-mandatory drift for one run. **Requires** `--accept-rationale`. |
| `--accept-rationale <text>` | The rationale (must be non-empty when using `--accept-drift`). |
| `--mission <slug>` | Bind the run to a mission; the drift ID is recorded as a `mission_artifacts` sidecar. |
| `--strict` | R14: hard-fail on any unexpected drift. PRESERVE categories are still always hard-fail. |

### 8.5 Intended usage

A canonical session is:

```bash
# 1. Install
python -m pip install -e ".[dev]"

# 2. Verify the installation
python scripts/release_verify.py

# 3. Initialize a workspace
workspace-os --workspace /home/taras/projects init

# 4. Create a mission
workspace-os --workspace /home/taras/projects mission new phase-1-init

# 5. Run a shell command and record it under the mission
workspace-os --workspace /home/taras/projects agent run --mission phase-1-init -- ls -la

# 6. Validate
workspace-os --workspace /home/taras/projects validate

# 7. Close the mission
workspace-os --workspace /home/taras/projects mission close phase-1-init
```

`README.md` and `runbook.md` are the full operator-facing references. The canonical release verification is `python scripts/release_verify.py` (with `--clean-clone` for the same evidence from a fresh checkout).

---

## 9. Release Model

### 9.1 Versioning

Semantic Versioning 2.0.0 (per `SUPPORT.md` §Versioning). The package version is `2.0.0`; the historical `v2.0-rc` release-phase string was retired at the GA commit and is no longer the canonical phase label. The kernel is past the release-candidate lifecycle.

- `2.0.0` is the published GA release (annotated tag at `97c3c49e5f54385256f7f52052e1a5eee012a6b4`).
- `2.0.0a1` is a superseded candidate (phase `v0.5-rc`).
- `1.1.0-LTS` is the historical LTS baseline, frozen, bug-fix-only.
- `v2.0-rc` was the release phase string in the package; it was retired at the GA commit.

GA is reached only when **all** of:

- The committed candidate is pushed to the canonical remote.
- Remote CI is green.
- An annotated `v2.0.0` tag identifies that commit.
- Optional PyPI publication occurs only if the package is intended for `pip install workspace-os`.

The `v2.0.0` tag was created at the GA commit (`97c3c49e5f54385256f7f52052e1a5eee012a6b4`, `fix(cli): default workspace root to current directory for portability`); later commits `3ab758a` and `f18b984` (post-release docs) sit on `main` but are not part of the tag.

### 9.2 Frozen authority documents

The v2.0.0 kernel does not pin a `authority-lock.json`-style file in the repository. The frozen authorities are the **seven Workspace OS constitutional documents** + the implementation program + the operator disposition. They live in the broader `/home/taras/projects/` filesystem, not in the kernel repository:

| Authority | File | Program / disposition |
| --- | --- | --- |
| Workspace OS Constitution | `GOVERNANCE/WORKSPACE-CONSTITUTION.md` | Articles I–X. Article X is the amendment procedure. |
| Authority Model | `GOVERNANCE/AUTHORITY-MODEL.md` | Defines authority classes. |
| Context Routing | `GOVERNANCE/CONTEXT-ROUTING.md` | Progressive context loading. |
| Document Lifecycle | `GOVERNANCE/DOCUMENT-LIFECYCLE.md` | draft / active / legacy / archived. |
| Validation Checklist | `GOVERNANCE/VALIDATION-CHECKLIST.md` | The shell validator fixture contract. |
| Bootstrap Procedure | `GOVERNANCE/BOOTSTRAP.md` | Four-file bootstrap contract. |
| Human Instructions | `GOVERNANCE/HUMAN-INSTRUCTIONS.md` | Operator conventions. |
| Agent Registry | `GOVERNANCE/AGENT-REGISTRY.md` | One authority per agent. |
| Identity Authority Map | `GOVERNANCE/IDENTITY-AUTHORITY-MAP.md` | The audit document — see §12 misconception 4. |
| Engineering Identity | `career-operating-system/EngineeringIdentity.md` | The single canonical identity file. |
| Workspace Architecture | `system-graph.md` | The architecture. |
| Ratification | `RATIFICATION.md` | Records what is ratified. |
| Amendments | `AMENDMENTS.md` (referenced by Article X) | The amendments log. |
| Implementation Program | `FINAL-IMPLEMENTATION-PROGRAM.md` (2026-07-22) | The v2.0 program ratification. |
| Canonical Model | `WORKSPACE-OS-CANONICAL-MODEL.md` (2026-07-20) | The post-v1.1 reconstruction. |
| Operator Disposition | `GOVERNANCE/AMENDMENTS.md` (2026-07-22) | The operator's disposition ratifying the program. |

For the v2.0.0 kernel release, the canonical acceptance command is `python scripts/release_verify.py` (with `--clean-clone` for the same evidence from a fresh checkout). It runs:

1. Ruff check
2. Ruff format check
3. Mypy (per `[tool.mypy]` in `pyproject.toml`)
4. Bandit (per `[tool.bandit]`, with the three reviewed exclusions: B404, B603, B607)
5. Pytest (114 tests, 8 files)
6. pip-audit
7. `python -m build` (wheel + sdist)
8. Archive-content checks (the wheel and sdist must include `workspace_os/policy.yaml`)
9. Installed-package smoke (the wheel installs in an isolated env, the policy loads without repository access, both console entry points are exercised)

CI invokes the same script on Python 3.11 and 3.12 (per `SUPPORT.md` and `pyproject.toml`'s `requires-python = ">=3.11"`).

### 9.3 Architecture lock

The Workspace OS **architecture** is not byte-locked in the kernel repository; it is governed by **Article X of the Constitution** and the post-blueprint program record (`FINAL-IMPLEMENTATION-PROGRAM.md`, 2026-07-22). Any change to a constitutional authority requires the formal amendment procedure (Article X), refreshed verification, and operator disposition (`AMENDMENTS.md`).

The kernel's `policy.yaml` is **versioned** (`schema_version: 1`) and **byte-pinned indirectly** via the wheel/sdist packaging. A change to `policy.yaml` requires a version bump and a migration of the drift-id contract.

The kernel's `pyproject.toml` is **byte-locked** by the test `tests/test_package.py` (the release metadata verification test, originally `cfdb134`; the GA commits extended the contract with `test_version_is_2_0_0` and `test_phase_is_v2_0_rc`).

### 9.4 Release process

The v2.0.0 release process is:

1. The kernel repository is a Python package at `workspace-os/`.
2. `python -m build` produces `dist/workspace_os-2.0.0-py3-none-any.whl` and `dist/workspace_os-2.0.0-*.tar.gz` (with `policy.yaml` packaged as a resource).
3. The release verifier (`python scripts/release_verify.py`) runs the full quality gate locally.
4. The committed candidate is pushed to the canonical remote (`github.com/taras-polishchuk/workspace-os`).
5. Remote CI green for the pushed commit (Python 3.11 and 3.12).
6. An annotated `v2.0.0` tag is created on that commit.
7. PyPI publication was intentionally deferred at GA. The release is reachable via GitHub Release; PyPI upload is a future owner-gated step.

The GitHub Actions CI definition is at `.github/workflows/` (not in scope for this document; see the repository).

### 9.5 Release philosophy

- **The filesystem is the source of truth.** SQLite is a derived cache. The Mission State directories are the canonical mission state. Validator runs and agent runs are recorded in SQLite for query convenience, but the audit trail is reproducible from the filesystem and the SQLite file.
- **Bounded local kernel.** Single host, single process, single operator. The kernel does not pretend to be a distributed system; the daemon is a stub; the v2.0 program ratification explicitly defers hosted and multi-host capabilities.
- **Evidence over opinion.** Drift is classified against a versioned policy. The drift ID is `SHA-256(policy_bytes + canonical_categories)`. Accepted drift is recorded in JSONL with a rationale. PRESERVE categories are un-waivable.
- **One runtime dependency.** `PyYAML >= 6.0`. The kernel does not grow dependencies without a versioned policy + dependency review.
- **Refuse symlinks at every boundary.** `_safe_io.py` enforces this consistently. The validator shim is also checked.
- **Operator-gated publication.** Git push, tag creation, GitHub Release, and PyPI publication are owner-authorized. The kernel state was committed-and-staged before those gates at GA; the GitHub Release was published by the operator on 2026-07-25. PyPI upload remains the only outstanding owner-gated step (deferred) (per `RELEASE.md` §Publication state).
- **No marketing over statement.** The README, CHANGELOG, RELEASE, SUPPORT, and runbook are aligned: "no daemon", "no hosted service", "no multi-host deployment". The v1.1 deliverable bundle is preserved as historical evidence, not as a current product surface.

---

## 10. Engineering Principles (extracted from the source)

These are not aspirations. They are the principles the v2.0.0 kernel *demonstrates*, derived from the source code and the Workspace OS constitution.

1. **Authority over convenience.** Workspace OS names seven constitutional primitives. The v1.1 refactor collapsed 24 legacy identity redefinitions to 0 (workspace-os-v1-deliverables/authority-map.md §Identity Drift Status). Authority is a property of the system, not a convention.

2. **One source per concept.** The eight-artifact Sprint Pattern is defined once (`workspace_os.mission.SPRINT_PATTERN_FILES`) and referenced everywhere. The drift policy is defined once (`policy.yaml`, also packaged) and loaded via `importlib.resources`. The single runtime dependency (PyYAML) is named once in `pyproject.toml`.

3. **Reference rather than copy.** The Workspace OS identity is one file, symlinked from `IDENTITY.md`. The 25 instruction de-duplication symlinks (5 instructions × 5 source directories) all point to the same 5 canonical files in `INSTRUCTIONS/`.

4. **Identity changes slowly, projects cheaply.** Identity is referenced by every other document; mission slugs are validated by a regex and live in the filesystem. Adding a new mission is a CLI call; changing identity requires an amendment.

5. **Durable over transient.** The Mission State lives in the filesystem, survives the process, and is the source of truth. The validator runs are recorded in SQLite with `ts`, `pass_count`, `fail_count`, `raw_output_path`. Agent runs are recorded with the command, exit code, and a per-run log file.

6. **Evidence over opinion.** Drift is classified against a versioned policy. The drift ID is a hash. The validator output is parsed by a regex; the categories are extracted by a deterministic function. Accepted drift is recorded in JSONL with a rationale.

7. **Bounded, single-process, single-host.** The kernel is a Python module that runs as a CLI. There is no daemon, no network, no hosted service. `daemon.py` is an honest unavailable contract stub.

8. **Refuse symlinks at every boundary.** `safe_mkdir`, `atomic_write_text`, the shim check, the mission creation path, the state database open — all reject symlinks. This is a consistent posture, not a per-feature check.

9. **Concurrent-init defense is built in.** The advisory file lock on `.wsos/.init.lock` serialises bootstrap. `PRAGMA busy_timeout = 5000` lets writers wait. WAL mode allows concurrent readers.

10. **Idempotent operations.** `register_workspace` is idempotent on `root_path`. `register_mission` is idempotent on `(workspace_id, slug)`. `close_mission` is idempotent (returns `'closed'` whether it performed the transition or the mission was already closed; does not overwrite `closed_at`).

11. **Atomic writes.** `atomic_write_text` writes to a tempfile, then renames. A partial write never replaces an existing file. The drift-acceptance JSONL is written atomically (read-modify-write to keep append-only semantics).

12. **Permissions as a contract.** `.wsos/` is mode 0o700. `state.db` and its WAL/SHM sidecars are mode 0o600. Mission directories are mode 0o700. Mission files are mode 0o600. The operator is the only user; other local users on a shared host cannot read the audit trail.

13. **PRESERVE is un-waivable.** The R14 PRESERVE rule makes `missing_security_audit_log`, `missing_audit_json_key`, and `sprint_pattern_incomplete` always hard-fail, regardless of `--accept-drift` or `--strict`. This is defence-in-depth for the categories that the policy author refuses to accept as drift.

14. **The CLI is the only public surface.** No SDK, no HTTP API, no RPC, no hosted service. The peer `validator` CLI is the one exception, and it is registered explicitly in `pyproject.toml`.

15. **The kernel does not promote LLM output to authority.** The CLI accepts operator input; the validator returns a verdict the operator reads; the operator decides. AI is never the authority for identity, amendment, or mission state.

---

## 11. Current Capabilities (v2.0.0)

This section enumerates what the released kernel does. It is split into three categories by the brief: implemented, intentionally deferred, future backlog.

### 11.1 Implemented in v2.0.0 (verified at the GA release commit `97c3c49e5f54385256f7f52052e1a5eee012a6b4`)

**Local kernel.**

- Single-host, single-process Python kernel at `/home/taras/projects/workspace-os/`.
- SQLite WAL at `<workspace>/.wsos/state.db`, mode 0o600.
- One runtime dependency: PyYAML ≥ 6.0.
- Python 3.11+ (tested on 3.11 and 3.12 in CI).

**Workspace initialization.**

- `workspace-os init` — bootstrap `<workspace>/.wsos/` with the 5-table schema.
- `WorkspaceState.init()` is serialised with an advisory file lock.
- `WorkspaceState.register_workspace()` is idempotent on `root_path`.

**Mission lifecycle.**

- `Mission.create(slug, workspace_root, state_root, *, overwrite)` — creates the 8-artifact Sprint Pattern directory.
- `Mission.exists()`, `Mission.all_artifacts_present()` — checks the 8 files.
- `workspace-os mission new <slug>`, `mission list`, `mission close <id-or-slug>` (idempotent).
- Slug validation: `^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$`.
- 8 Sprint Pattern files: `source-task.md`, `progress.md`, `decisions.md`, `blockers.md`, `artifacts.md`, `environment.md`, `execution-log.md`, `final-report.md`.
- Mission files created with `O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600`.

**Validator.**

- `workspace-os validate` — runs the Python peer by default, or the legacy `bin/validate-workspace.sh` shim if present AND safe.
- `validator` peer CLI — registered as `validator = "workspace_os.validator.__main__:main"`.
- Drift classification: `known_drift`, `forbidden_drift`, `mandatory_drift`.
- Drift ID: `SHA-256(policy.source_bytes + canonical_categories)`.
- R14 PRESERVE: `mandatory_drift` always hard-fails.
- R14 strict: `--strict` opt-in for hard-fail on any unexpected drift.
- Acceptance audit: `<workspace>/.wsos/drift-acceptance.jsonl` (atomic write, refuses symlinks).
- Validator run is always recorded in `validator_runs`, including on error paths.

**Agent run.**

- `workspace-os agent run -- <command> [--mission <slug>]` — executes a shell command and records it.
- Per-run log: `<workspace>/.wsos/agent-runs/run-<workspace_id>-<ms_timestamp>-<pid>.log`.
- `agent_runs` row recorded with command, exit code, log path.
- `subprocess.run(filtered, cwd=<workspace_root>)` — no `shell=True`.

**Safe I/O boundary.**

- `safe_mkdir(path, mode=0o700)` — refuses symlinks at any level.
- `atomic_write_text(path, content)` — write-temp-then-rename.
- `tighten_existing_file(path, mode=0o600)` — chmod existing files.
- `SymlinkRefusedError` — the error class for all boundary rejections.

**CLI surface (v2.0.0).**

- Subcommands: `init`, `mission new/list/close`, `validate`, `agent run`.
- Top-level options: `--workspace`, `--yes`, `--version`.
- Exit codes: 0 success; 2 invalid input; 3 file exists; 4 not found; 5 filesystem/DB error; 6 timeout.

**Quality gate (v2.0.0).**

- `python scripts/release_verify.py` runs: Ruff check, Ruff format, mypy, Bandit, pytest (114 tests, 8 files), pip-audit, build, archive-content checks, installed-package smoke.
- CI on Python 3.11 and 3.12.
- Bandit exclusions: B404, B603, B607 (reviewed, shell-free subprocess boundaries).
- Build produces `dist/workspace_os-2.0.0-py3-none-any.whl` and `dist/workspace_os-2.0.0.tar.gz`.
- Wheel and sdist include `workspace_os/policy.yaml` (packaged via `setuptools.package-data`).
- Installed wheels load the policy via `importlib.resources` without repository access.

**Database state.**

- 5 tables: `workspaces`, `missions`, `mission_artifacts`, `validator_runs`, `agent_runs`.
- 4 indexes: `idx_missions_workspace`, `idx_missions_status`, `idx_validator_runs_workspace`, `idx_agent_runs_mission`.
- PRAGMAs at every `connect()`: `busy_timeout = 5000`, `foreign_keys = ON`, `journal_mode = WAL`.
- Sidecar tightening: `.db-wal` and `.db-shm` chmod'd to 0o600 on every bootstrap.

### 11.2 Intentionally deferred in v2.0.0 (deferred, not abandoned)

These are explicitly listed in `README.md` §"Not included", `RELEASE.md` §"Deliberately outside v2.0.0", and `SUPPORT.md` §"We do not treat these post-GA ecosystem capabilities as v2.0 defects":

- **Daemon implementation.** `daemon.py` is an honest unavailable contract stub. `is_daemon_available()` returns False. `ipc_request()` raises `DaemonNotAvailableError`. The `workspace-os daemon` subparser is not exposed.
- **`kgctl approve-canonical` integration.** External integration with the Knowledge OS canonicalization CLI. Post-GA ecosystem work.
- **GMR monorepo creation.** A higher-level monorepo that would compose Workspace OS + OperatorOS + Knowledge OS + AI Factory. Post-GA.
- **Four-service Compose topology.** A deployment topology that would distribute the kernel across services. Post-GA.
- **Distributed or hosted operation.** Single-host, single-process is the v2.0 contract. Multi-host or hosted deployment requires a successor architecture.

### 11.3 Future backlog (from `workspace-os-v1-deliverables/future-recommendations.md` and `technical-debt-register-v1.1.md`)

The v1.1 deliverables bundle includes a `future-recommendations.md` and a `technical-debt-register-v1.1.md`. These are historical documents; a future agent should consult them directly for the current backlog. The categories are: validator migration, knowledge substrate, multi-host coordination, hosted operation, tooling, documentation. The v2.0 program (`FINAL-IMPLEMENTATION-PROGRAM.md`, 2026-07-22) and the operator disposition (`AMENDMENTS.md`, 2026-07-22) are the source of truth for the current roadmap.

---

## 12. Known Limitations (current boundaries)

These are the boundaries the v2.0.0 kernel *acknowledges* explicitly. None of them is a defect; each is a deliberate scope decision backed by the architecture or the constitution.

**Single host, single process.** No distributed, no multi-host, no hosted. The daemon is a stub. There is no RPC, no unix socket, no network endpoint.

**No daemon.** `is_daemon_available()` is hard-coded to False. Any caller that hits daemon IPC must catch `DaemonNotAvailableError` and either fall back to CLI or fail loud — never silently succeed (R26 acceptance).

**The default workspace root is the current working directory (`Path.cwd()`).** The historical `/home/taras/projects` default was replaced at the GA commit (HEAD `97c3c49e5f54385256f7f52052e1a5eee012a6b4`, `fix(cli): default workspace root to current directory for portability`). Portable callers should pass `--workspace <path>` or set `$WORKSPACE_OS_ROOT`.

**No CLI, no SDK, no HTTP API, no Dashboard, no telemetry, no auto-update, no marketplace, no multi-tenant SaaS.** The kernel ships one CLI; nothing else.

**PyPI publication is intentionally deferred at GA.** The wheel and sdist are published on the GitHub Release (`https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0`); PyPI upload is the only remaining publication surface and is owner-gated. The package does not claim PyPI availability in the v2.0.0 release.

**The drift policy is versioned but the schema is schema_version = 1.** A future change to the policy schema requires a migration of the drift-id contract and a version bump. The validator rejects any non-1 schema version with `validate_policy` errors.

**The 14/78 freeze baseline is a contract, not a recommendation.** The validator reports the actual `pass_count` / `fail_count`. The drift categories are emitted against the freeze baseline. The historical 14/66 figure is explicitly obsolete (per `policy.yaml:3`); any document still referencing 14/66 is historical evidence, not current state.

**The 8-artifact Sprint Pattern is the only mission shape.** The kernel does not support alternative mission layouts, partial missions, or mission overrides. The drift category `sprint_pattern_incomplete` is mandatory-preserve; the validator will hard-fail on any missing file.

**The 3 mandatory-preserve drift categories are un-waivable.** `missing_security_audit_log`, `missing_audit_json_key`, `sprint_pattern_incomplete`. No flag, no rationale, no override. The R14 PRESERVE rule is the contract.

**The legacy `bin/validate-workspace.sh` shim is honored only if present AND safe.** The check (`_shim_is_safe`) verifies ownership, mode, special bits, and parent symlinks. An unsafe shim is silently ignored; the Python peer runs. This is deliberate defence-in-depth; the operator may not have created the shim, and an unprivileged actor may have.

**The Workspace OS v1.1 zero-based architecture review is historical evidence, not a current governance document.** The architecture score of 5/10 is a v1.1 review. The post-blueprint v2.0 program explicitly chose the production path through `FINAL-IMPLEMENTATION-PROGRAM.md` and the operator disposition, not through the v1.1 deliverables. Future agents should treat the v1.1 review as a record of what was fixed, not as a current critique.

**`IDENTITY-AUTHORITY-MAP.md` is a 47 KB audit document with 26 `(typo)` annotations.** The v1.1 review observed that the document "is the type of 'evidence over opinion' that Article VI demands, but the *evidence* is '26 broken paths in 1 file'." A future agent reading this document should not treat it as a current source of truth; it is an audit document retained per the amendment retention principle. The canonical identity is `career-operating-system/EngineeringIdentity.md`; the canonical authority is `GOVERNANCE/AUTHORITY-MODEL.md`.

**The `/home/taras/` path typo is in 3 governance documents.** This is the v1.1 review's primary criticism. The v2.0 kernel does not depend on the typo (the kernel does not read those governance documents). Future agents reading the broader Workspace OS governance plane should be aware of this historical typo.

**The `bin/regenerate-workspace-index.sh` script was bypassed by the v1.1 manual edits.** The v1.1 review notes that either the regenerator is dead or the manual edits are dead. The v2.0 kernel does not depend on the regenerator (it has its own validator). Future agents maintaining `CONTEXT/workspace-index.json` should be aware of this drift.

**The canonical Workspace OS authority documents live outside the kernel repository.** A future agent looking for the constitution, the authority model, or the canonical model must navigate to `/home/taras/projects/GOVERNANCE/`, `/home/taras/projects/WORKSPACE-OS-CANONICAL-MODEL.md`, etc. The kernel repository is one slice of the broader Workspace OS discipline.

**The `v2.0.0` tag is the canonical GA marker.** Annotated tag `v2.0.0` (object `ccec833929b5f81716fe3e3d880047440493270d`) was created at the GA commit and pushed to the canonical remote. The kernel is past the `v2.0-rc` phase; the GitHub Actions run `30163934239` is green on Python 3.11 and 3.12 against that commit, and the GitHub Release was published on 2026-07-25.

**`daemon.py` references are forward-looking.** Module docstrings mention "future phases will replace this" and "Phase 5+". Future agents reading `daemon.py` should not interpret those references as current functionality.

**`validates against the canonical 14/78 baseline; the live count may differ from 14/78 as missions accumulate.** The 14/78 figure is the freeze baseline; the live `validate` output will report whatever the current state is. The 78 FAILs are the mission-state-integrity noise from older or in-progress `.project-state/<slug>/` directories that have not been retroactively populated with the 8-artifact Sprint Pattern (per `runbook.md` §Quick start).

---

## 13. Development Workflow

A future agent that wants to *work* with this kernel (read-only or write) needs to know the contract. The full rules are in `CONTRIBUTING.md` (if present; otherwise the rules are in `runbook.md` and `RELEASE.md`); this section is the operational summary.

### 13.1 Validation pipeline

A single canonical acceptance command:

```bash
python scripts/release_verify.py
```

This runs, in order, on failure-stop:

1. Ruff check
2. Ruff format check
3. Mypy (per `[tool.mypy]`)
4. Bandit (per `[tool.bandit]`, exclusions B404, B603, B607)
5. Pytest (114 tests, 8 files)
6. pip-audit
7. `python -m build` (wheel + sdist)
8. Archive-content checks (wheel and sdist include `workspace_os/policy.yaml`)
9. Installed-package smoke (wheel installs in isolated env, policy loads without repo access, both console entry points exercised)

For the same evidence from a fresh checkout:

```bash
python scripts/release_verify.py --clean-clone
```

### 13.2 Testing

- Pytest with the configuration in `pyproject.toml` (`[tool.pytest.ini_options]`): `testpaths = ["tests"]`, `addopts = "-q --tb-short"`.
- 8 test files: `test_cli.py` (17), `test_daemon.py` (8), `test_mission.py` (17), `test_package.py` (7), `test_safety.py` (24), `test_state.py` (21), `test_validate.py` (13), `test_validator_migration.py` (7). Total: 114 tests.
- Tests must be deterministic and must not depend on the network or real customer data.
- The package smoke test (`test_package.py`) verifies wheel/sdist contents and `importlib.resources` policy loading.

### 13.3 Release expectations

- The kernel is a Python package; the package version (`pyproject.toml:version`) is `2.0.0`; the release has reached GA. The historical `v2.0-rc` phase string was retired at the GA commit; the README, CHANGELOG, RELEASE, and SUPPORT now refer to the published `v2.0.0` GitHub Release.
- A new commit must pass `python scripts/release_verify.py`.
- The release verifier must succeed on Python 3.11 and 3.12 (per CI).
- The drift policy is versioned (`schema_version: 1`); a schema change requires a migration of the drift-id contract.
- A change to the constitutional authorities requires the formal amendment procedure (Article X) and operator disposition (`AMENDMENTS.md`).

### 13.4 Quality requirements (release-gate)

For any change intended to ship:

- `ruff check` and `ruff format --check` must pass.
- `mypy` (per `[tool.mypy]`) must pass.
- `bandit` (per `[tool.bandit]`, with B404, B603, B607 allowed) must pass with zero MEDIUM/HIGH findings.
- `pytest` (114 tests, 8 files) must pass.
- `pip-audit` must report no high-severity vulnerabilities.
- `python -m build` must produce a wheel and sdist.
- The wheel and sdist must include `workspace_os/policy.yaml`.
- The installed wheel must load the policy via `importlib.resources` without repository access.
- Both console entry points (`workspace-os` and `validator`) must be exercisable from the installed wheel.

### 13.5 Repository-only acceptance

`python scripts/release_verify.py` is the gate. The full pipeline runs in seconds on a warm cache. It does not create a tag, push, or publish. Owner-gated actions (push, tag, GitHub Release, PyPI publication) are separate.

---

## 14. Mental Model

The correct way to think about Workspace OS v2.0.0:

**It is a bounded, local, filesystem-level operating kernel for a single human operator and their AI runtimes — expressed as a single-host, single-process Python package with one runtime dependency, one CLI, one SQLite database, and one drift policy.**

- **Bounded local kernel.** v2.0.0 is a single Python package, not a distributed system. The daemon is a stub. Hosted and multi-host deployment are explicitly post-GA.
- **Filesystem-level operating discipline.** Workspace OS is a contract over a filesystem, not installable software. The kernel implements the local-kernel portion of that discipline. The broader authority plane lives in `GOVERNANCE/`, `RATIFICATION.md`, `AMENDMENTS.md`, and the canonical authority documents.
- **Filesystem is the source of truth.** The eight-artifact Sprint Pattern directories in `.project-state/<slug>/` are the canonical mission state. SQLite is a derived cache. The drift policy is a package resource.
- **Single human operator.** AI is never the operator. The CLI accepts operator input; the validator returns a verdict the operator reads; the operator decides what to fix. The default workspace root is the current working directory so the kernel is portable across hosts without `--workspace` arguments.
- **One runtime dependency.** `PyYAML >= 6.0`. The kernel does not grow dependencies without a versioned policy and dependency review.
- **Symlink rejection at every boundary.** `_safe_io.py` enforces this consistently. A planted symlink is detected at the leaf, at the state root, at any ancestor, and at the validator shim.
- **Drift as a contract.** Drift is classified against a versioned YAML policy. The drift ID is `SHA-256(policy_bytes + canonical_categories)`. Forbidden and mandatory-preserve categories are un-waivable. Accepted drift is recorded in JSONL with a rationale.
- **Concurrent-init defense is built in.** Advisory file lock on `.wsos/.init.lock`. `PRAGMA busy_timeout = 5000`. WAL mode.
- **Idempotent operations.** Workspace, mission, and close operations are idempotent. The kernel does not double-write.
- **PRESERVE is un-waivable.** `missing_security_audit_log`, `missing_audit_json_key`, `sprint_pattern_incomplete` are always hard-fail. The operator cannot override them with a flag or a rationale.
- **No daemon, no hosted, no multi-host, no SDK, no HTTP API, no telemetry, no marketplace, no multi-tenant SaaS.** All of these are explicit non-goals. Future agents must not propose adding them without a successor architecture.

To a senior engineer: think **a small, single-host Python CLI that enforces an 8-file mission layout, persists its audit trail in SQLite, classifies drift against a YAML policy, and refuses to follow symlinks**. The kernel is a state manager, not a workflow engine, not an orchestrator, not a SaaS.

To a product manager: think **"the kernel is the boring, reliable foundation that everything else can build on"**. The kernel's job is to be the durable, recoverable, auditable substrate for the rest of the Workspace OS discipline. The features that make the kernel interesting (drift classification, symlink rejection, audit trail) are also what make it boring to operate — that's the point.

To a security reviewer: think **default-deny at every boundary**. Symlinks are rejected. Mission files are mode 0o600. SQLite is mode 0o600 with WAL sidecars also tightened. The validator shim is ownership-checked. The drift policy has a PRESERVE rule that is un-waivable. The kernel does not promote LLM output to authority.

To a release engineer: think **a single canonical acceptance command** (`python scripts/release_verify.py`), **a single build** (wheel + sdist with packaged policy), **a single peer CLI** (`validator`), and **owner-gated publication** (push, tag, GitHub Release, PyPI upload). The kernel is intentionally committed-and-staged before those gates; the operator's job is to perform the final publication.

To an AI agent: think **"the kernel is one tool in your toolbelt — use it to create missions, run shell commands with audit, and validate the workspace"**. The kernel does not replace the broader Workspace OS discipline; it implements the local-kernel portion. The constitutional authorities live in the broader filesystem; the canonical model is `WORKSPACE-OS-CANONICAL-MODEL.md`; the seven constitutional primitives are referenced, not redefined.

---

## 15. Frequently Misunderstood Things

The following are common misconceptions. Each is corrected in one or two sentences.

**Misconception 1: "Workspace OS v2.0.0 is a single product."**

It is not. Workspace OS is a **filesystem-level operating discipline**; the v2.0.0 kernel is a **bounded local Python implementation** of the control-plane portion. The authority plane lives in `GOVERNANCE/`, the canonical model in `WORKSPACE-OS-CANONICAL-MODEL.md`, the implementation program in `FINAL-IMPLEMENTATION-PROGRAM.md`. The kernel is one slice.

**Misconception 2: "Workspace OS is a workflow engine."**

It is not. The kernel is a state manager: 8-artifact Sprint Pattern enforcer, SQLite audit trail, drift classifier. It is not a workflow engine, not an orchestrator, not a task runner. The closest analogue is a stateful filesystem validator with a CLI.

**Misconception 3: "Workspace OS v2.0.0 has a daemon."**

It does not. `daemon.py` is an honest unavailable contract stub. `is_daemon_available()` is hard-coded to False. `ipc_request()` raises `DaemonNotAvailableError`. The `workspace-os daemon` subparser is not exposed. The kernel runs as a CLI; there is no long-lived process.

**Misconception 4: "Workspace OS v2.0.0 is hosted or distributed."**

It is not. The kernel is single-host, single-process, single-operator. The `README.md`, `RELEASE.md`, and `SUPPORT.md` are explicit: "no hosted service", "no multi-host deployment", "no distributed operation". The post-blueprint v2.0 program explicitly defers these to a successor architecture.

**Misconception 5: "Workspace OS v2.0.0 is published to PyPI."**

It is not. The wheel and sdist are published on the GitHub Release at <https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0> with `policy.yaml` packaged in both archives. PyPI publication is intentionally deferred; `python3 -m pip index versions workspace-os` reports no distribution. The `v2.0.0` Git tag exists (`ccec833929b5f81716fe3e3d880047440493270d`, peels to `97c3c49e5f54385256f7f52052e1a5eee012a6b4`); PyPI is the only remaining publication surface.

**Misconception 6: "The 14/78 freeze baseline is a current validator count."**

It is not. The 14/78 figure is the **freeze baseline** the drift policy is calibrated against. The live `validate` output will report whatever the current state is — the 78 FAILs are the mission-state-integrity noise from older or in-progress `.project-state/<slug>/` directories that have not been retroactively populated with the 8-artifact Sprint Pattern. The historical 14/66 figure is explicitly obsolete (`policy.yaml:3`).

**Misconception 7: "The 8-artifact Sprint Pattern is enforced by the filesystem only."**

It is not. The enforcement is threefold: filesystem (Mission.create populates and Mission.all_artifacts_present checks), policy (`sprint_pattern_incomplete` is in `mandatory_drift`), and audit (drift-acceptance.jsonl records any acceptance, and PRESERVE means this acceptance is impossible). All three layers must be defeated to bypass the pattern.

**Misconception 8: "`--accept-drift` accepts any drift."**

It does not. `--accept-drift` waives non-forbidden, non-mandatory unexpected drift. It cannot waive `forbidden_drift` (currently `unexpected_db_writer`, `missing_validator_script`) and it cannot waive `mandatory_drift` (currently `missing_security_audit_log`, `missing_audit_json_key`, `sprint_pattern_incomplete`). The R14 PRESERVE rule is un-waivable.

**Misconception 9: "The validator's exit code is the verdict."**

It is not. The Python validator's `ValidatorVerdict.ok` property returns `policy_ok`, which is the policy classification. The frozen shell validator returns nonzero for the canonical 14/78 baseline; the policy classification, not that legacy status, is authoritative (`validate.py:99-100`).

**Misconception 10: "The v1.1 deliverables bundle is the current architecture."**

It is not. The v1.1 deliverables (`workspace-os-v1-deliverables/`) are historical evidence. The v1.1 zero-based architecture review (`independent-architecture-review-v1.1.md`, 2026-06-28) gave the v1.1 architecture a 5/10 score. The post-blueprint v2.0 program explicitly chose the production path through `FINAL-IMPLEMENTATION-PROGRAM.md` (2026-07-22) and the operator disposition (`AMENDMENTS.md`, 2026-07-22), not through the v1.1 deliverables.

**Misconception 11: "`IDENTITY-AUTHORITY-MAP.md` is a current source of truth."**

It is not. It is a 47 KB audit document with 26 `(typo)` annotations about paths that do not exist. It is retained per the amendment retention principle. The canonical identity is `career-operating-system/EngineeringIdentity.md`; the canonical authority model is `GOVERNANCE/AUTHORITY-MODEL.md`. A future agent reading `IDENTITY-AUTHORITY-MAP.md` should treat it as historical evidence, not a current critique.

**Misconception 12: "The kernel depends on the broader Workspace OS authority documents."**

It does not. The kernel is a self-contained Python package. It does not read `GOVERNANCE/`, `RATIFICATION.md`, `AMENDMENTS.md`, `WORKSPACE-OS-CANONICAL-MODEL.md`, or any other authority document. The kernel's contract is the `policy.yaml` it ships with. The broader Workspace OS discipline is enforced by humans and by the operator, not by the kernel.

---

## 16. AI Context Summary (for use as long-term context)

The following facts are stable, evidence-backed, and useful across future conversations. They are intentionally compressed for use in AI conversation contexts that have a token budget.

**Workspace OS v2.0.0 is the released bounded local Python kernel of the Workspace OS discipline.** Released 2026-07-25 at HEAD `97c3c49e5f54385256f7f52052e1a5eee012a6b4`; package version `2.0.0`; annotated Git tag `v2.0.0` is the canonical GA marker. GitHub Release: <https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0>. Repository `github.com/taras-polishchuk/workspace-os`; MIT license. CI green on Python 3.11 and 3.12. PyPI publication is intentionally deferred.

**It is a single-host, single-process Python package.** Python 3.11+. One runtime dependency: `PyYAML >= 6.0`. The package source is ~2,727 lines across 14 files in `src/workspace_os/`. Tests: 114 across 8 files. No daemon, no network, no hosted service.

**It is a filesystem-level operating discipline, not a single product.** Workspace OS is a contract over a filesystem articulated by `GOVERNANCE/`, `WORKSPACE-OS-CANONICAL-MODEL.md`, `RATIFICATION.md`, and `FINAL-IMPLEMENTATION-PROGRAM.md`. The v2.0.0 kernel implements the local-kernel portion of that discipline. The seven constitutional primitives are Identity, Principle, Authority, Knowledge, Mission, Subsystem, Specialization.

**The eight-artifact Sprint Pattern (Constitution Article VII) is the canonical mission layout.** `Mission.create()` materializes 8 files in `.project-state/<slug>/`: `source-task.md`, `progress.md`, `decisions.md`, `blockers.md`, `artifacts.md`, `environment.md`, `execution-log.md`, `final-report.md`. Missing any of these emits `sprint_pattern_incomplete` drift, which is mandatory-preserve and un-waivable.

**The SQLite state database lives at `<workspace>/.wsos/state.db` (mode 0o600).** 5 tables: `workspaces`, `missions`, `mission_artifacts`, `validator_runs`, `agent_runs`. PRAGMAs: `busy_timeout = 5000`, `foreign_keys = ON`, `journal_mode = WAL`. Sidecars (`.db-wal`, `.db-shm`) are tightened to 0o600 on every bootstrap. `WorkspaceState.init()` is serialised with an advisory file lock on `.wsos/.init.lock`.

**The drift policy is versioned.** `policy.yaml` is `schema_version: 1`. The freeze baseline is 14 PASS / 78 FAIL. Three drift classes: `known_drift`, `forbidden_drift` (always hard-fail), `mandatory_drift` (R14 PRESERVE — always hard-fail regardless of any flag). The drift ID is `SHA-256(policy.source_bytes + canonical_actual_categories)`.

**Symlink rejection is a consistent posture at every boundary.** `_safe_io.py` provides `safe_mkdir`, `atomic_write_text`, `tighten_existing_file`, `SymlinkRefusedError`. Mission files are created with `O_NOFOLLOW`. The validator shim is ownership-checked. A planted symlink is detected at the leaf, at the state root, at any ancestor, and at the shim.

**The CLI is the only public surface.** Subcommands: `init`, `mission new/list/close`, `validate`, `agent run`. The peer `validator` CLI is the one exception. No HTTP API, no SDK, no Dashboard, no telemetry, no marketplace, no multi-tenant SaaS.

**The canonical acceptance command is `python scripts/release_verify.py`.** It runs Ruff check, Ruff format, mypy, Bandit, pytest, pip-audit, build, archive-content checks, and installed-package smoke. `--clean-clone` runs the same from a fresh checkout. CI invokes it on Python 3.11 and 3.12.

**The release has reached GA.** The committed candidate was pushed to the canonical remote, remote CI (`30163934239`) is green on Python 3.11 and 3.12, the annotated `v2.0.0` tag peels to `97c3c49e5f54385256f7f52052e1a5eee012a6b4`, and the GitHub Release was published on 2026-07-25. Owner-gated actions remaining: PyPI upload (intentionally deferred).

**v2.0.0 scope (in):** local CLI, SQLite state, mission lifecycle, agent-run recording, Python validator, symlink/concurrent-init defenses, packaged drift policy, canonical release verifier, portable default workspace root. **v2.0.0 scope (out):** daemon, `kgctl approve-canonical` integration, GMR monorepo creation, four-service Compose topology, distributed or hosted operation.

**How to reason about future work.** The drift policy is versioned; a change requires a migration of the drift-id contract. The 8-artifact Sprint Pattern is constitutional (Article VII); a change requires an amendment (Article X). The kernel is a control-plane implementation; changes that affect the authority plane must go through the Workspace OS amendment procedure, not through the kernel repository.

**Stable identifiers and cross-references (for future use):**

- Package: `workspace-os` (PyPI name) / `workspace_os` (Python import)
- Version: `2.0.0` (Python package and Git tag); release phase: GA
- Head commit at GA: `97c3c49e5f54385256f7f52052e1a5eee012a6b4`
- Python: `>= 3.11`
- Runtime dep: `PyYAML >= 6.0`
- Console scripts: `workspace-os`, `validator`
- Default workspace root: current working directory (`Path.cwd()`)
- State dir: `<workspace>/.wsos/`
- Mission dir: `<workspace>/.project-state/<slug>/`
- Agent-run logs: `<workspace>/.wsos/agent-runs/`
- Drift-acceptance audit: `<workspace>/.wsos/drift-acceptance.jsonl`
- Validator policy: `<workspace>/.wsos/policy.yaml` (or shipped via `importlib.resources`)
- Drift policy schema: `schema_version: 1`
- Drift policy baseline: `pass_count: 14, fail_count: 78`
- 8 Sprint Pattern files: `source-task.md`, `progress.md`, `decisions.md`, `blockers.md`, `artifacts.md`, `environment.md`, `execution-log.md`, `final-report.md`
- 5 SQLite tables: `workspaces`, `missions`, `mission_artifacts`, `validator_runs`, `agent_runs`
- 3 mandatory-preserve drift categories: `missing_security_audit_log`, `missing_audit_json_key`, `sprint_pattern_incomplete`
- 2 forbidden drift categories: `unexpected_db_writer`, `missing_validator_script`
- Canonical acceptance command: `python scripts/release_verify.py`
- Repository: `github.com/taras-polishchuk/workspace-os`
- Authority documents: `/home/taras/projects/GOVERNANCE/`, `/home/taras/projects/WORKSPACE-OS-CANONICAL-MODEL.md`, `/home/taras/projects/FINAL-IMPLEMENTATION-PROGRAM.md`

**Do not assume Workspace OS v2.0.0 is a Temporal clone.** It is a state manager, not a workflow engine. The kernel is a CLI + SQLite + 8-artifact enforcer + drift classifier.

**Do not assume the kernel is the whole Workspace OS.** Workspace OS is a discipline over a filesystem; the kernel is the bounded local implementation of the control plane.

**Do not assume the v1.1 deliverables are current.** The v1.1 architecture review is historical evidence; the production path is the v2.0 program.

**Do not assume `IDENTITY-AUTHORITY-MAP.md` is a current source of truth.** It is a 47 KB audit document with 26 typo annotations, retained per the amendment retention principle.

**The `v2.0.0` tag is canonical.** Annotated tag `v2.0.0` peels to `97c3c49e5f54385256f7f52052e1a5eee012a6b4`, was pushed to `origin`, and is the reference for all future work. PyPI is the only remaining publication surface and is intentionally deferred.

**Do not assume the drift policy can be changed casually.** The policy is versioned (`schema_version: 1`); a change requires a version bump, a migration of the drift-id contract, and a release that re-validates the audit trail.

---


## 17. GA Release Evidence

This section is the canonical reference for "Workspace OS v2.0.0 was released and where to find it." It supersedes any earlier claim of "release candidate" or "tag not yet created" elsewhere in this document.

| Item | Value |
|---|---|
| Repository | https://github.com/taras-polishchuk/workspace-os |
| GitHub Release | <https://github.com/taras-polishchuk/workspace-os/releases/tag/v2.0.0> |
| GitHub Release publishedAt | `2026-07-25T15:38:29Z` |
| Tag name | `v2.0.0` |
| Tag object | `ccec833929b5f81716fe3e3d880047440493270d` (annotated) |
| Tag peeled commit | `97c3c49e5f54385256f7f52052e1a5eee012a6b4` |
| PyPI publication | intentionally deferred |
| GitHub Actions run (green) | <https://github.com/taras-polishchuk/workspace-os/actions/runs/30163934239> |
| Python matrix | 3.11, 3.12 |
| Wheel artifact | `workspace_os-2.0.0-py3-none-any.whl`, SHA-256 `82da84b8f4a99afb83bb4b2b6e845d25e5b46d96a4e200c7db94450aca24bd17` |
| Sdist artifact | `workspace_os-2.0.0.tar.gz`, SHA-256 `23118bbd00a4fc5a3b1fefb74869b4a5c847197f896430c9847e90e9c85004ea` |
| GA commit subject | `fix(cli): default workspace root to current directory for portability` |
| Portability commits between certified and released | `6c8c711` (`fix(ci): make CLI tests repository-portable`), `19f392f` (`fix(ci): preserve CLI tests WORKSPACE_OS_ROOT`), `97c3c49e5f54385256f7f52052e1a5eee012a6b4` (portable default workspace root) |
| Post-release docs on `main` (not part of tag) | `3ab758a` (`docs: surface runtime bootstrap procedure in distribution`), `f18b984` (`docs: link bootstrap procedure from runbook`) |

The tag is immutable. Future work that requires a change must cut a new release tag (e.g. `v2.0.1`, `v2.0.0-LTS`) following the constitutional amendment procedure; the existing `v2.0.0` tag is the historical GA baseline.

---

*End of canonical context. The implementation is authoritative. The constitution is frozen. The drift is the contract. The operator is the final authority.*
