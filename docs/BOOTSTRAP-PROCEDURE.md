# Bootstrap Procedure — Implementation Specification

> **Scope:** runtime procedure that an AI agent follows at the start of a fresh session against a Workspace OS workspace when the agent is bound to this kernel. Implementation specification, not architecture.
>
> **Canonical owner of the procedure itself:** `/home/taras/projects/GOVERNANCE/BOOTSTRAP.md` (workspace authority plane).
>
> **Canonical owner of context routing:** `/home/taras/projects/GOVERNANCE/CONTEXT-ROUTING.md` (workspace authority plane).
>
> **Canonical owner of constitution / articles:** `/home/taras/projects/GOVERNANCE/WORKSPACE-CONSTITUTION.md` (workspace authority plane).
>
> **Canonical owner of identity:** `/home/taras/projects/career-operating-system/EngineeringIdentity.md` (target of the `IDENTITY.md` symlink).
>
> **Canonical owner of architecture:** `/home/taras/projects/system-graph.md` (target of the `ARCHITECTURE.md` symlink).
>
> **Owner of this file:** `workspace-os` kernel (`docs/`). This file does **not** redefine the procedure; it specifies the runtime algorithm that any conforming kernel call performs in service of the procedure.

---

## 1. Lifecycle diagram

```
[Agent starts]
      |
      v
[Session initialization: load four canonical files]
      |
      v
[Bootstrap validation: 5 canonical questions]
      |
      v
[Stop condition: do not continue reading the workspace]
      |
      v
[Await task intent]
      |
      v
[Intent branch (per Bootstrap Recipe): career | code | sprint | quick question]
      |
      v
[For "sprint" branch only: locate active mission via CONTEXT/workspace-index.json active_sprints]
      |
      v
[For state-changing work: Mission State Pre-flight — classify]
      |
      v
   /---|---\
  /    |    \
 v     v     v
[One-shot] [Continuation] [New Mission]
              |               |
              v               v
        [Procedure for     [Procedure for
         Continuation]      New Mission]
              \               /
               \             /
                v           v
             [Execute the user request]
                          |
                          v
                 [Execution completed]
```

Stage names are governed by `BOOTSTRAP.md` § "STARTUP ORDER", "Bootstrap validation", "Stop condition", "Mission State Pre-flight", "Mission Classification", "Procedure for Continuation", "Procedure for New Mission"; and by `CONTEXT-ROUTING.md` § "Bootstrap Recipe (verbatim)". See §8 Evidence Matrix.

---

## 2. Bootstrap algorithm

The kernel performs the algorithm on behalf of any conforming AI runtime. Each step has: Goal, Inputs, Outputs, Failure modes, Evidence source.

### Step 1 — Read IDENTITY.md

- **Goal:** load the canonical engineering identity into the runtime's working memory before any other authority is read.
- **Inputs:** workspace root path; `IDENTITY.md` symlink (resolves to `career-operating-system/EngineeringIdentity.md`).
- **Outputs:** in-memory representation sufficient to answer "What is the canonical engineering identity?" (`BOOTSTRAP.md:163`).
- **Failure modes:** symlink target missing — no canonical fallback (`BOOTSTRAP.md:39-52` lists only the bootstrap file set, not identity-spec alternatives).
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:16`; `GOVERNANCE/CONTEXT-ROUTING.md:118`; `WORKSPACE-CONSTITUTION.md` Article V; `WORKSPACE-OS-CANONICAL-MODEL.md` §11.1.

### Step 2 — Read ARCHITECTURE.md

- **Goal:** load the canonical workspace architecture (subsystem map S1–S6, durable structure) into working memory.
- **Inputs:** workspace root path; `ARCHITECTURE.md` symlink (resolves to `system-graph.md`).
- **Outputs:** in-memory representation sufficient to answer "What are the 6 subsystems?" (`BOOTSTRAP.md:164`).
- **Failure modes:** symlink target missing — no canonical fallback.
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:17`; `GOVERNANCE/CONTEXT-ROUTING.md:119`.

### Step 3 — Read GOVERNANCE/BOOTSTRAP.md

- **Goal:** load the procedure text the runtime is following, so the procedure can be re-validated mid-session.
- **Inputs:** workspace root path; `GOVERNANCE/BOOTSTRAP.md`.
- **Outputs:** the bootstrap procedure text in working memory.
- **Failure modes:** missing — bootstrap is incomplete; no canonical fallback.
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:18`; `GOVERNANCE/CONTEXT-ROUTING.md:120`.

### Step 4 — Read CONTEXT/workspace-index.json

- **Goal:** discover workspace state (active missions, operating systems, key paths) without recursive reads.
- **Inputs:** workspace root path; `CONTEXT/workspace-index.json`.
- **Outputs:** structured access to `active_sprints[]`, `operating_systems[]`, etc.
- **Failure modes:**
  - Stale manual overrides listing pre-refactor paths (`executive-summary.md`, root `workspace-index.json`, `hermes-bootstrap.md`, `user-operating-profile.md`) per `WORKSPACE-OS-CANONICAL-MODEL.md:458`.
  - 18 missing absolute paths in current index per `WORKSPACE-OS-CANONICAL-MODEL.md:455-462`.
  - Missing `operatoros-os` / `operatoros-core-cli` registration per `GOVERNANCE/AMENDMENTS.md:482-490`.
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:19`; `GOVERNANCE/CONTEXT-ROUTING.md:121`.

### Step 5 — Stop

- **Goal:** prevent the recursive read anti-pattern. The kernel publishes nothing further; it awaits the runtime's task intent.
- **Inputs:** the cached bootstrap from Steps 1–4.
- **Outputs:** no further reads.
- **Failure modes:** non-compliance is named "the largest source of token waste" (`CONTEXT-ROUTING.md:40-41`). Bootstrap is incomplete if any Step 1–4 file was not loaded.
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:173-179` ("Stop condition").

### Step 6 — Bootstrap validation (5 questions from cache only)

- **Goal:** confirm the four cached files are sufficient.
- **Inputs:** cached Step 1–4 outputs.
- **Outputs:** verification result: complete or incomplete.
- **Decision rule:** if any canonical question is unanswerable from cache → bootstrap is incomplete (`BOOTSTRAP.md:169`).
- **The 5 questions (verbatim from `BOOTSTRAP.md:159-167`):**
  1. What is the canonical engineering identity? — from `IDENTITY.md`.
  2. What are the 6 subsystems? — from `ARCHITECTURE.md`.
  3. What is the current state? — from `CONTEXT/workspace-index.json`.
  4. What should be ignored? — from `GOVERNANCE/BOOTSTRAP.md` "What to ignore" section.
  5. How is authority routed? — from `GOVERNANCE/AUTHORITY-MODEL.md` (loaded at this point in the runtime's working memory; not part of the 4-file canonical load).
- **Failure modes:** bootstrap incomplete — kernel does not invoke any mutation API.
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:159-169`.

### Step 7 — Mission State Pre-flight (mandatory before state-changing actions)

- **Goal:** classify incoming work as One-shot, Continuation, or New Mission before any state mutation.
- **Inputs:** the user request; cached bootstrap; `active_sprints[]` from Step 4.
- **Outputs:** classification result `One-shot | Continuation | New Mission` (slug attached for the latter two).
- **Decision rule (verbatim from `BOOTSTRAP.md:203-215`):**
  - One-shot: Q&A, lookup, single read, explanation → no sprint directory required.
  - Continuation: scope matches an existing `.project-state/<slug>/` → load that slug's `source-task.md` + `progress.md`.
  - New Mission: new scope, new deliverables, new system boundary, new domain, multi-step autonomous work → create `.project-state/<slug>/`, seed `source-task.md` + `progress.md`.
  - **Default if uncertain: New Mission** (`BOOTSTRAP.md:213-214`).
- **State-changing trigger list (`BOOTSTRAP.md:216-236`):**
  - `terminal` commands that deploy, migrate, mutate infra, or modify production.
  - `git commit`, `git push`, force-push, filter-branch, history rewrite.
  - `write_file`, `patch`, or any tool that creates/modifies files in a tracked repo.
  - Editing configuration in `GOVERNANCE/`, `bin/`, `~/.gitconfig`, secret stores.
  - Database migration (SQL applied, schema change, role grant).
  - Cloudflare / Tailscale / AWS / GCP API mutation.
  - DNS record creation or update.
  - Container start / stop / recreate on production host.
  - Any other action whose effect persists beyond the current agent session.
- **Does NOT fire for:** reads, listings, smoke tests that only observe state, conversation.
- **Failure modes:** see §5.
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:183-236`.

### Step 8 — Procedure for "Continuation"

- **Goal:** resume the existing mission cleanly.
- **Inputs:** `.project-state/<slug>/` whose `source-task.md` scope matches the incoming request.
- **Outputs:** loaded `source-task.md` and `progress.md` for that slug.
- **Decision rule:** scope matches → resume; scope feels like a continuation but no existing sprint matches → re-classify as **New Mission** (`BOOTSTRAP.md:257-259`).
- **Failure modes:** appending to an unrelated sprint.
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:250-259`.

### Step 9 — Procedure for "New Mission"

- **Goal:** create the durable record before any engineering action.
- **Inputs:** the user request; cached bootstrap.
- **Outputs:** new `.project-state/<slug>/` directory under canonical root, with `source-task.md` and `progress.md` seeded.
- **Canonical procedure (`BOOTSTRAP.md:237-248`):**
  1. Choose slug: `<topic>-<YYYY-MM-DD>` (e.g. `case-04-public-exposure-2026-07-13`). Verify canonical root: `/home/taras/projects/.project-state/<slug>/`.
  2. Create the directory.
  3. Seed minimum two files (`source-task.md`, `progress.md`); optionally seed the other six (`decisions.md`, `blockers.md`, `artifacts.md`, `environment.md`, `execution-log.md`, `final-report.md`).
  4. Only then proceed to engineering actions.
- **Reconstruction marker:** if creation happens after work began (session loss, context loss, technical crash, or operator request only), `source-task.md` MUST begin with a structured `RECORD OF RECONSTRUCTION` block and `decisions.md` MUST contain a "Reconstruction rationale" section. Reconstruction without marker is "architectural violation" (`BOOTSTRAP.md:275, 278-294`).
- **Failure modes:** see §5.
- **Evidence source:** `GOVERNANCE/BOOTSTRAP.md:237-298`; `VALIDATION-CHECKLIST.md` "Mission State Pre-flight Check" L214-230.

### Step 10 — Execute the user request

- **Goal:** carry out the user's intent within the bootstrap-derived working memory.
- **Inputs:** bootstrap cache; mission state if Classification was Continuation or New Mission; user's request.
- **Outputs:** completed work + persistent workspace mutations.
- **Canonical behavior:** "Hermes then uses tools, skills, subagents, cron, Kanban, and runtime policy to execute." (`WORKSPACE-OS-CANONICAL-MODEL.md:382`.)
- **Failure modes:** unspecified generally; specific protocols exist for Kanban (Article XIV), context compression (validator invariants), and resource exhaustion (Article XIV Principle 3, Mission Handoff).
- **Evidence source:** `WORKSPACE-OS-CANONICAL-MODEL.md:382`; `WORKSPACE-CONSTITUTION.md` Article XIV.

---

## 3. Context loading order

| Order | Action | Source document |
|---|---|---|
| 1 | Read `IDENTITY.md` (≈3K tokens, cached) | `GOVERNANCE/CONTEXT-ROUTING.md:117,118` |
| 2 | Read `ARCHITECTURE.md` (≈3K tokens, cached) | `GOVERNANCE/CONTEXT-ROUTING.md:117,119` |
| 3 | Read `GOVERNANCE/BOOTSTRAP.md` (≈1K tokens, cached) | `GOVERNANCE/CONTEXT-ROUTING.md:117,120` |
| 4 | Read `CONTEXT/workspace-index.json` (≈5K tokens) | `GOVERNANCE/CONTEXT-ROUTING.md:117,121` |
| 5 | STOP. Do not continue reading. | `GOVERNANCE/BOOTSTRAP.md:173-179` |
| 6 | Cache discipline: keep (1)–(4) cached for the session lifetime. | `GOVERNANCE/BOOTSTRAP.md:36, 147-157` |
| 7 | On intent: pick branch. | `GOVERNANCE/CONTEXT-ROUTING.md:113-129` |
| 8 | Before any state-changing action: Mission State Pre-flight. | `GOVERNANCE/BOOTSTRAP.md:183-189` |
| 9 | If Continuation: load `source-task.md` + `progress.md` of matching slug. | `GOVERNANCE/BOOTSTRAP.md:210` |
| 10 | If New Mission: create `<workspace>/.project-state/<slug>/`, seed `source-task.md` + `progress.md`. | `GOVERNANCE/BOOTSTRAP.md:211, 237-248` |
| 11 | Execute. | `WORKSPACE-OS-CANONICAL-MODEL.md:382` |

Items NOT part of the canonical 4-file load that the runtime must handle:

- `GOVERNANCE/AUTHORITY-MODEL.md` — referenced by Bootstrap validation question 5 (`BOOTSTRAP.md:167`); required for the validation step; not in the canonical load.
- `GOVERNANCE/CONTEXT-ROUTING.md` — source of the verbatim recipe; not in the recipe itself.
- `GOVERNANCE/AGENT-REGISTRY.md` — referenced indirectly via the Bootstrap conditional loading table (`BOOTSTRAP.md:67`), not a bootstrap-load step.
- Layer-2 subsystem READMEs (`SUBSYSTEMS/...`) — documented but do not exist on disk per `WORKSPACE-OS-CANONICAL-MODEL.md:457`. Treat as "do not load — does not exist" rather than "must load".

Token budget: ~12K cold start (`WORKSPACE-OS-CANONICAL-MODEL.md:376`).

---

## 4. Runtime inputs

| Input | Purpose | Canonical owner | Required? | Source |
|---|---|---|---|---|
| Workspace root path | Anchor for the four bootstrap files and for `.project-state/`. | (assumed; canonical paths use `/home/taras/projects`) | Required. | `GOVERNANCE/BOOTSTRAP.md:14-21` |
| `IDENTITY.md` | Canonical engineering identity | `career-operating-system/EngineeringIdentity.md` via `IDENTITY.md` symlink | Required. | `GOVERNANCE/BOOTSTRAP.md:16` |
| `ARCHITECTURE.md` | Canonical architecture + subsystem map | `system-graph.md` via `ARCHITECTURE.md` symlink | Required. | `GOVERNANCE/BOOTSTRAP.md:17` |
| `GOVERNANCE/BOOTSTRAP.md` | The procedure itself | `GOVERNANCE/BOOTSTRAP.md` | Required. | `GOVERNANCE/BOOTSTRAP.md:18` |
| `CONTEXT/workspace-index.json` | Machine-readable discovery | `CONTEXT/workspace-index.json` | Required. | `GOVERNANCE/BOOTSTRAP.md:19` |
| Task intent (user request) | Triggers the post-bootstrap intent branch | operator input | Required. | `WORKSPACE-OS-CANONICAL-MODEL.md:376` |
| Active mission list | Input to the Continuation classification path | `CONTEXT/workspace-index.json: active_sprints[]` | Optional (required only when Classification = Continuation). | `GOVERNANCE/CONTEXT-ROUTING.md:128` |
| `.project-state/<slug>/source-task.md` | Scope match for Continuation | `.project-state/<slug>/` | Optional (required only when Classification = Continuation). | `GOVERNANCE/BOOTSTRAP.md:210, 250-255` |
| `.project-state/<slug>/progress.md` | Resumption state | `.project-state/<slug>/` | Optional (same). | `GOVERNANCE/BOOTSTRAP.md:210, 252-255` |
| Mission slug for "New Mission" (`<topic>-<YYYY-MM-DD>`) | New-mission path | operator or runtime | Required when Classification = New Mission. | `GOVERNANCE/BOOTSTRAP.md:239-241` |
| `GOVERNANCE/AUTHORITY-MODEL.md` | Required to answer Bootstrap validation question 5 | `GOVERNANCE/AUTHORITY-MODEL.md` | Required for validation step. | `GOVERNANCE/BOOTSTRAP.md:167` |
| Workspace tier-4 ignore list | Avoid recursive load | `GOVERNANCE/BOOTSTRAP.md:39-52` | Required for any read-after-bootstrap not on the intent branch. | `GOVERNANCE/BOOTSTRAP.md:39-52` |
| Runtime capabilities (tools, skills, subagents, cron, Kanban) | Execution substrate (Hermes-or-equivalent runtime) | runtime config (e.g. `~/.hermes/config.yaml`) | Required when the agent is bound to a runtime. | `WORKSPACE-OS-CANONICAL-MODEL.md:382` |
| Knowledge (skills, ADR/IR/LL, memories) | Stored procedure/skill/lesson content | `~/.hermes/skills/`, `docs/knowledge/`, `~/.hermes/memories/` | Optional. | `WORKSPACE-OS-CANONICAL-MODEL.md:475` |

---

## 5. Runtime outputs

| Output | Definition | Evidence source |
|---|---|---|
| Loaded bootstrap (4 canonical files in memory) | Identity + Architecture + Procedure + Index; cached for session lifetime. | `GOVERNANCE/BOOTSTRAP.md:11-21, 36, 147-157`; `WORKSPACE-OS-CANONICAL-MODEL.md:367-376` |
| Authority scope cached | EngineeringIdentity + system-graph + AUTHORITY-MODEL + CONTEXT-ROUTING + AGENT-REGISTRY (as triggered). | `GOVERNANCE/BOOTSTRAP.md:159-167`; `WORKSPACE-OS-CANONICAL-MODEL.md:227-247` |
| Mission classification | One of One-shot / Continuation / New Mission, recorded before any mutation. | `GOVERNANCE/BOOTSTRAP.md:203-215` |
| Active mission state (Continuation or New Mission) | `source-task.md` + `progress.md` of active slug. | `GOVERNANCE/BOOTSTRAP.md:210-211, 252-253` |
| Mission directory created (New Mission) | `<workspace>/.project-state/<slug>/` with at minimum `source-task.md` + `progress.md`. | `GOVERNANCE/BOOTSTRAP.md:237-248` |
| Stop condition observed | Runtime did not recursively load the workspace after the bootstrap. | `GOVERNANCE/BOOTSTRAP.md:173-179` |
| Bootstrap validation passed | All five canonical questions answerable from cache. | `GOVERNANCE/BOOTSTRAP.md:159-169` |
| Mutation gate honored | The runtime performs non-state-changing reads freely; performs state-changing actions only after Mission State Pre-flight classifies the work. | `GOVERNANCE/BOOTSTRAP.md:183-236` |

---

## 6. Failure handling

Each row: `Failure | Canonical behavior | Source`. Where the document does not specify behavior, the row says so explicitly.

### 6.1 Missing workspace / canonical files

| Failure | Canonical behavior |
|---|---|
| `IDENTITY.md` symlink target missing | No canonical fallback. `WORKSPACE-OS-CANONICAL-MODEL.md:455-462` reports drift but does not prescribe a fallback. |
| `ARCHITECTURE.md` symlink target missing | No canonical fallback. |
| `GOVERNANCE/BOOTSTRAP.md` missing | No canonical fallback. The procedure becomes unverifiable. |
| `CONTEXT/workspace-index.json` missing | No canonical runtime fallback. The kernel validator (Python `bin`-equivalent, see `validator/`) fails this check; the runtime does not synthesize a substitute. |

### 6.2 Missing mission

| Failure | Canonical behavior |
|---|---|
| `active_sprints[]` empty in `workspace-index.json` | Default to "New Mission" if user provides intent that demands work (`BOOTSTRAP.md:213-214`). |
| `.project-state/<slug>/` created post-hoc | `BOOTSTRAP.md:262-298` mandates a `RECORD OF RECONSTRUCTION` block at the top of `source-task.md` and a "Reconstruction rationale" section in `decisions.md`. **Reconstruction without marker is "architectural violation".** |
| Existing `.project-state/<slug>/` has incomplete Sprint Pattern (missing one of 8 artifacts) | Per `policy.yaml` mandatory_drift: this is `sprint_pattern_incomplete`, always PRESERVE — the kernel validator MUST block. (`src/workspace_os/policy.yaml:19-22`.) |
| `.project-state/` created inside any repo (not at `<workspace>/.project-state/`) | No canonical runtime behavior. The validator (`check_project_state_root` per `validator/invariants.py`) and Article VII presume canonical root only. |

### 6.3 Missing context / drift

| Failure | Canonical behavior |
|---|---|
| Bootstrap cache does not contain one of the four canonical files | Bootstrap is incomplete (`BOOTSTRAP.md:169`). |
| Bootstrap validation finds one of the five questions unanswerable from cache | Bootstrap is incomplete (`BOOTSTRAP.md:169`). Kernel does not invoke mutation API. |
| Intent branch wants `SUBSYSTEMS/<subsystem>/README.md` that does not exist | No canonical fallback. Named as real defect in `WORKSPACE-OS-CANONICAL-MODEL.md:457`. |
| `workspace-index.json` lists paths that no longer exist | `WORKSPACE-OS-CANONICAL-MODEL.md:455-462` reports 18 missing paths; no canonical runtime fallback defined. Kernel reads paths as a best-effort discovery; missing entries do not abort Step 4. |
| `workspace-index.json` overrides include pre-refactor paths | No canonical fallback. Listed as drift in `WORKSPACE-OS-CANONICAL-MODEL.md:458`. |

### 6.4 Conflicting authority

| Failure | Canonical behavior |
|---|---|
| Two files claim the same concept | Article II (One Authority per Concept) — drift MUST be resolved, not maintained (`WORKSPACE-CONSTITUTION.md:47-89`). The runtime's resolution contract is not canonical for the bootstrap; the kernel falls back to the on-canonical-path file when possible. |
| Root design docs and `operatoros-platform/docs/authorities/*` differ | No canonical runtime behavior. Platform authority lock uses byte-identical hashes (`WORKSPACE-OS-CANONICAL-MODEL.md:265-272`) for verification, not for runtime conflict resolution. |
| Validator verdict and product verdict disagree | No canonical runtime behavior. `WORKSPACE-OS-CANONICAL-MODEL.md:447-451` allows this only if product-release readiness and Workspace OS conformance remain explicitly separate verdicts. |

### 6.5 Invalid bootstrap / reconstruction

| Failure | Canonical behavior |
|---|---|
| Reconstruction record format is malformed | The kernel validator's Mission State Integrity check MUST detect the missing "Reconstruction rationale" section in `decisions.md` (`validator/invariants.py`, `GOVERNANCE/VALIDATION-CHECKLIST.md:214-230`). No runtime recovery behavior beyond failing that check. |
| Kernel validator emits 14 pass / 78 fail (current observed state) | Per `runbook.md` and `WORKSPACE-OS-CANONICAL-MODEL.md:447-451`: kernel validator failures are non-blocking for product release but blocking for Workspace OS conformance. The bootstrap procedure itself is unaffected — the validator is a separate gate. |
| Bootstrap token cost > 12K | No canonical action beyond the imperative to "load only what you need" (`CONTEXT-ROUTING.md:87`). |

### 6.6 Architecture vs runtime separation

`WORKSPACE-OS-CANONICAL-MODEL.md:401-405`: "Runtime projections, session memory, dashboards, event streams and generated indexes are not automatically durable authority." The kernel treats any state it produces as rebuilt each session unless it has been promoted via the constitutional lifecycle.

---

## 7. State machine

```
START
  ↓
session_initialization                [WORKSPACE-OS-CANONICAL-MODEL.md:367]
  step: read IDENTITY.md              [GOVERNANCE/BOOTSTRAP.md:16]
  step: read ARCHITECTURE.md          [GOVERNANCE/BOOTSTRAP.md:17]
  step: read GOVERNANCE/BOOTSTRAP.md  [GOVERNANCE/BOOTSTRAP.md:18]
  step: read CONTEXT/workspace-index.json [GOVERNANCE/BOOTSTRAP.md:19]
  ↓
stop_condition_observed              [GOVERNANCE/BOOTSTRAP.md:173]
  ↓
bootstrap_validation                 [GOVERNANCE/BOOTSTRAP.md:159]
  gate: 5 canonical questions answerable from cache
  on FAIL: bootstrap_incomplete       [GOVERNANCE/BOOTSTRAP.md:169]
  on PASS:
  ↓
awaiting_intent                      [WORKSPACE-OS-CANONICAL-MODEL.md:376]
  ↓ (user provides request)
mission_state_preflight              [GOVERNANCE/BOOTSTRAP.md:183]
  if read-only/observation: → execute_as_one_shot
  else:
    classification ∈ {one_shot, continuation, new_mission}
    [GOVERNANCE/BOOTSTRAP.md:203-214]
  ↓
  case classification:
    one_shot:        → execute_as_one_shot  [GOVERNANCE/BOOTSTRAP.md:209]
    continuation:    procedure_for_continuation [GOVERNANCE/BOOTSTRAP.md:250-259]
                     load source-task.md + progress.md
                     on no scope match → re-classify as new_mission [GOVERNANCE/BOOTSTRAP.md:257-259]
    new_mission:     procedure_for_new_mission [GOVERNANCE/BOOTSTRAP.md:237-248]
                     create directory; seed source-task.md + progress.md
                     if reconstructed → RECORD OF RECONSTRUCTION block required [GOVERNANCE/BOOTSTRAP.md:278-294]
  ↓
execute                              [WORKSPACE-OS-CANONICAL-MODEL.md:382]
  tools + skills + subagents + cron + Kanban + runtime policy
  ↓
(mission-specific stop conditions; concrete post-execution actions are outside this kernel's bootstrap spec)
```

States whose names are not exactly canonical phrases (legibility-only, not proposed governance):

- `execute_as_one_shot` — canonical classification `One-shot` provides the trigger; no state name is given.
- `bootstrap_incomplete` — canonical label is "the bootstrap is incomplete" (`BOOTSTRAP.md:169`).
- `awaiting_intent` — implied by "stop until task intent is known" (`WORKSPACE-OS-CANONICAL-MODEL.md:376`); not a named state.

---

## 8. Evidence matrix

| Runtime step / concept | Canonical document (out of this repo) | Section | Evidence |
|---|---|---|---|
| Session initialization (4-file load) | `WORKSPACE-OS-CANONICAL-MODEL.md` | §11.1 | L367-378 |
| Bootstrap procedure | `GOVERNANCE/BOOTSTRAP.md` | "STARTUP ORDER" | L11-21 |
| Verbatim bootstrap recipe | `GOVERNANCE/CONTEXT-ROUTING.md` | "Bootstrap Recipe (verbatim)" | L113-129 |
| Token budget (~12K cold start) | `WORKSPACE-OS-CANONICAL-MODEL.md` | §11.1 | L376 |
| Bootstrap validation (5 questions) | `GOVERNANCE/BOOTSTRAP.md` | "Bootstrap validation" | L159-169 |
| Stop condition | `GOVERNANCE/BOOTSTRAP.md` | "Stop condition" | L173-179 |
| Mission State Pre-flight gate | `GOVERNANCE/BOOTSTRAP.md` | "Mission State Pre-flight" | L183-188 |
| Mission classification (3 classes) | `GOVERNANCE/BOOTSTRAP.md` | "Mission Classification" | L203-215 |
| State-changing trigger list | `GOVERNANCE/BOOTSTRAP.md` | "State-changing actions" | L216-236 |
| Procedure for "New Mission" | `GOVERNANCE/BOOTSTRAP.md` | "Procedure for 'New Mission'" | L237-248 |
| Procedure for "Continuation" | `GOVERNANCE/BOOTSTRAP.md` | "Procedure for 'Continuation'" | L250-259 |
| Reconstruction record format | `GOVERNANCE/BOOTSTRAP.md` | "Reconstruction Policy" | L261-294 |
| Reconstruction rationale requirement | `GOVERNANCE/VALIDATION-CHECKLIST.md` | "Mission State Pre-flight Check" | L214-230 |
| Default if uncertain → New Mission | `GOVERNANCE/BOOTSTRAP.md` | "Mission Classification" | L213-214 |
| Sprint Pattern (8 artifacts) | `WORKSPACE-CONSTITUTION.md` | Article VII | L125-141 |
| Sprint Pattern file list (kernel source of truth) | `src/workspace_os/mission.py` | `SPRINT_PATTERN_FILES` | mission.py:38-47 |
| Validator invariants (this kernel) | `src/workspace_os/validator/invariants.py` | INVARIANTS tuple | invariants.py:415-433 |
| Mission Integrity PRESERVE rule | `src/workspace_os/policy.yaml` | mandatory_drift list | policy.yaml:19-22 |
| Article XV (Memory Boundary) | `WORKSPACE-CONSTITUTION.md` | Article XV | L400-471 |
| Article XI (User Identity) | `WORKSPACE-CONSTITUTION.md` | Article XI | L180-256 |
| Article XIV (Autonomous Mission Execution) | `WORKSPACE-CONSTITUTION.md` | Article XIV | L300-398 |
| Mission Handoff 6-element bundle | `WORKSPACE-CONSTITUTION.md` | Article XIV Principle 3 | L328-340 |
| Iteration Budget Discipline | `GOVERNANCE/CONTEXT-ROUTING.md` | "Iteration Budget Discipline" | L132-179 |
| Identity canonical SoT | `WORKSPACE-CONSTITUTION.md` | Article V | L100-111 |
| Architecture canonical SoT | `system-graph.md` | "Subsystem Map" | system-graph.md:20-200 |
| Canonical Model: Runtime Architecture | `WORKSPACE-OS-CANONICAL-MODEL.md` | §11 | L365-406 |
| Canonical Model: Bootstrap Model (drift) | `WORKSPACE-OS-CANONICAL-MODEL.md` | §14 | L453-462 |
| Canonical Model: Knowledge Architecture | `WORKSPACE-OS-CANONICAL-MODEL.md` | §15 | L464-475 |
| Canonical Model: Boundary test | `WORKSPACE-OS-CANONICAL-MODEL.md` | §2.2 | L53-66 |
| Canonical Model: Post-freeze invariant | `WORKSPACE-OS-CANONICAL-MODEL.md` | §29 | L726-744 |
| Tier-4 ignore list | `GOVERNANCE/BOOTSTRAP.md` | "What to ignore by default" | L39-52 |
| Cache refresh cadence | `GOVERNANCE/BOOTSTRAP.md` | "Cache refresh cadence" | L147-157 |
| Subsystem map S1–S6 | `system-graph.md` | "Subsystem Map" | system-graph.md:20-200 |
| Knowledge bases (4 categories) | `WORKSPACE-OS-CANONICAL-MODEL.md` | §15 | L466-475 |
| Validator verifier boundary | `WORKSPACE-OS-CANONICAL-MODEL.md` | §13.3 | L447-451 |

---

## 9. Kernel vs runtime binding

This kernel specifies the procedure for any conforming runtime; the procedure does not depend on a particular runtime. The runtime surface that consumes this procedure (e.g. Hermes, Claude Code, Codex, Gemini) is outside this kernel's scope. Each runtime binding — i.e. how Steps 1–5 sequence in the runtime's actual session-start, where Step 6 sits, how Step 7 gates each tool call, what calls Step 8 / Step 9 in the kernel API — is a separate concern belonging to that runtime's documentation, not to this kernel.

End of specification.
