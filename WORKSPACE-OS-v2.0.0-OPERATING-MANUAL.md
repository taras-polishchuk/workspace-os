# The Daily Operating Model Around Workspace OS

An operational handbook for the author, explaining how Workspace OS v2.0.0 fits into a real workday together with Hermes, ChatGPT, Claude Code, Git, GitHub, the repositories, VS Code / Cursor, the terminal, SSH, and the home lab.

This is not Workspace OS documentation. This is the operating manual around Workspace OS. Workspace OS itself is already documented elsewhere (`WORKSPACE-OS-v2.0.0-AUTHOR-GUIDE.md`, `WORKSPACE-OS-v2.0.0-GA-CERTIFICATE.md`, `WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md`). What follows is everything else — the tools, the boundaries, the routines, the mistakes to avoid, and what a normal day actually looks like.

Released Workspace OS version: `v2.0.0` (commit `97c3c49e5f54385256f7f52052e1a5eee012a6b4`, annotated tag `v2.0.0`). All references below are to that release.

---

## 1. What actually happens when I begin work in the morning?

The order is the point. Get the order wrong and the rest of the day collapses into noise.

```
open terminal
   ↓
open workspace       (cd /home/taras/projects)
   ↓
Workspace OS        (workspace-os mission list)
   ↓
Hermes              (hermes chat, with workspace context loaded)
   ↓
ChatGPT             (a separate browser tab; for things outside the workspace)
   ↓
repositories        (the ordinary cd into operatoros-platform, etc.)
   ↓
Git                 (git status, git fetch, git log)
   ↓
finish work
```

Each arrow is one decision. Read it as a rule.

**Terminal → workspace.** Open a terminal and `cd /home/taras/projects`. This is the workspace root. Everything else in this document happens relative to that directory or inside directories beneath it.

**Workspace → Workspace OS.** Before doing anything else, run `workspace-os mission list`. This tells you two things: which missions are open (your real backlog), and whether your workspace is in a healthy state. Reading this list takes five seconds and prevents most "what was I doing yesterday" confusion.

**Workspace OS → Hermes.** When you need to delegate work to an autonomous agent — code review, doc writing, repo archaeology, a long investigation — open Hermes (`hermes chat`, or a Telegram channel wired to the Hermes gateway). Hermes is a smart operator that lives in this same terminal. It can read everything in `/home/taras/projects/`, can run Git, can run GitHub CLI, can SSH to the home lab, and can write into your workspace following your delegation rules. It cannot — and should not — start or close Workspace OS missions for you. You decide what missions exist; Hermes works inside the mission you point it at.

**Hermes → ChatGPT.** ChatGPT is a separate browser tab, on chat.openai.com or the desktop app. Use it for things that are *not* about your workspace: conceptual questions, learning a new framework, drafting copy, market research. ChatGPT has no idea what `workspace-os mission list` returned. It does not need to. If you find yourself wanting ChatGPT to know about your missions, the answer is usually to use Hermes instead, or to read the canonical context document of the relevant project (e.g. `operatoros-platform/OPERATOROS-PLATFORM-v1.0.0-CANONICAL-CONTEXT.md`).

**ChatGPT → repositories.** The crossover point. If ChatGPT has produced something that needs to land in a repository, you copy it into the right file, then commit it via Git. ChatGPT did not commit anything. Hermes did not commit anything. You commit. (Or Hermes commits with your approval, recorded in the audit trail.)

**Repositories → Git.** Each repository has its own `git status`, `git fetch`, `git log`. Workspace OS does not run any of these for you. You run them yourself, or you delegate to Hermes via a typed instruction.

**Git → finish work.** When the day's Git log shows what you set out to do, the day is done. Optionally: `workspace-os mission close <slug>` for missions that ended. Optionally: commit any pending changes in `/home/taras/projects/.project-state/<slug>/` if you wrote notes worth keeping.

The two non-obvious rules in the diagram:

- **Workspace OS comes before Hermes, not after.** If you start Hermes first, it will not know which mission you are working on. Five seconds of `workspace-os mission list` is the cheapest context-loader in your toolkit.
- **ChatGPT does not see your workspace.** Treating ChatGPT as if it did — pasting `workspace-os mission list` output into ChatGPT and asking it what to do — is a common mistake. ChatGPT has no model of `/home/taras/projects/`. Hermes does. Pick the right tool.

---

## 2. Where should Workspace OS be used? Where should it NOT be used?

The rule is simple: Workspace OS is for **multi-day, multi-step, multi-file work that produces a durable outcome and benefits from a paper trail.** If the work meets all three of those criteria, it deserves a mission. If it does not, it does not.

**Workspace OS should be used for:**

- An architectural redesign of an existing product (`workspace-os mission new operatoros-platform-v2-architecture-2026-07-26`).
- A release cycle (`workspace-os mission new workspace-os-v2-1-release-2026-08-10`).
- A multi-week research investigation (`workspace-os mission new ai-factory-research-vector-db-2026-07-28`).
- A cross-repository migration (`workspace-os mission new hermes-to-operatoros-bridge-migration-2026-08-02`).
- A long-running operator project that touches several repos and needs weekly status notes (`workspace-os mission new q3-portfolio-update-2026-07-15`).
- A piece of work where you will need to come back tomorrow and remember what you decided today.

**Workspace OS should NOT be used for:**

- A one-line typo fix to a README. No mission.
- A single small pull request that will be merged within a day. No mission.
- A single ChatGPT conversation about a concept. No mission.
- A single `git commit`. No mission.
- An exploratory chat with Hermes that may or may not produce anything. No mission.
- Quick debugging sessions under 30 minutes. No mission.

The boundary test is: **will this work have a `final-report.md` that says something other than "I did a thing"?** If yes, mission. If no, no mission.

**Should every repository become a mission?** No. Repositories are not missions. They are folders in your workspace. A repository may be the *target* of many missions over time. It is not itself a mission.

**Should every bug become a mission?** No. A one-line bug fix is not a mission. A bug that will take multiple days, touch several files, require coordination with another system, and benefit from a written record — that is a mission. "Fix the typo in the README" is not. "Migrate the auth subsystem from session cookies to JWT" might be.

**Should every conversation become a mission?** No. Conversations are ephemeral. Only the outcome of a conversation — if it produces a durable deliverable — might warrant a mission.

**Should every AI prompt become a mission?** No. Prompts are inputs to AI systems. Missions are containers for work. The ratio of prompts to missions should be roughly 50:1 or higher. If you are creating a mission per prompt, you are using Workspace OS wrong.

**The "would I write a final-report.md?" test** is the operational litmus test. If the answer is "no, this is too small", skip the mission.

---

## 3. How should Workspace OS interact with Hermes?

Hermes is an autonomous CLI agent with persistent memory, a gateway (Telegram, Discord, Slack), and rich filesystem / Git / GitHub / SSH tools. In the v2.0.0 release, Hermes does not have any built-in Workspace OS skill — it interacts with Workspace OS as a normal shell user would: by invoking the `workspace-os` CLI.

The interaction model is: **you define the mission, Hermes does the work inside it.**

### What Hermes should read inside a mission

- The mission's `source-task.md` — to know what the mission is about.
- The mission's `progress.md` — to know where the work currently stands.
- The mission's `decisions.md` — to know what has already been decided.
- The mission's `blockers.md` — to know what is in the way.
- The mission's `execution-log.md` — to know what was done previously.
- The mission's `artifacts.md` — to know what was produced.

These are all written by you (the operator) or by Hermes (under your direction). They form the context that any session — human or AI — needs to pick up where the previous one left off.

### What Hermes should write inside a mission

- The mission's `execution-log.md` — append a timestamped note for every action Hermes took under that mission.
- The mission's `decisions.md` — if Hermes made a design choice, record it.
- The mission's `blockers.md` — if Hermes hit a blocker, record it.
- The mission's `artifacts.md` — list every file Hermes produced.
- The mission's `progress.md` — update the current state after each significant step.
- The mission's `final-report.md` — at the end of the mission, summarise.

### What Hermes should never touch

- `.wsos/` — never edit, never delete, never rename. The SQLite database is owned by the `workspace-os` CLI, not by Hermes.
- Files inside other repositories that are not part of the current mission's scope. If the mission is about `operatoros-platform`, Hermes can edit files inside that repository (subject to the mission's normal Git discipline). It must not touch `workspace-os/` source unless the mission is explicitly about that.
- `/home/taras/projects/.project-state/<other-slug>/` — missions are isolated. If a mission needs to reference another mission, it does so by name in `decisions.md`, not by editing the other mission.
- `/home/taras/projects/GOVERNANCE/` — the constitutional documents are frozen unless an amendment is in progress. Hermes should never edit them casually; if it believes an amendment is needed, it should raise it as a decision in the current mission's `decisions.md`.

### What Hermes should never do to Workspace OS

- Hermes should not run `workspace-os mission new <slug>` on its own initiative. That is an operator decision. The operator opens the mission; Hermes works inside it.
- Hermes should not run `workspace-os mission close <slug>` on its own initiative. Closing a mission is a deliberate operator action. Hermes can recommend closure, but you close.
- Hermes should not run `workspace-os validate` and treat its output as a failure. The validator's FAILs are informational. If you want them treated as failures, use `--strict`, and only when you decide to.
- Hermes should not delete or reset `.wsos/` or `.project-state/`. If a reset is needed, you do it.

### The clean delegation pattern

The clean way to use Hermes with Workspace OS is:

1. You open a mission (`workspace-os mission new foo-2026-07-26`).
2. You write the initial `source-task.md` and `progress.md`.
3. You start Hermes (`hermes chat`).
4. You give Hermes the mission slug and the path to the mission folder.
5. Hermes reads the mission, plans, executes, writes its findings into the mission's markdown files, and reports back.
6. You review the changes, decide what to commit, and commit (or have Hermes commit with your approval).
7. When the mission is done, you run `workspace-os mission close foo-2026-07-26`.

Hermes is the worker. You are the operator. Workspace OS is the notebook.

---

## 4. How should Workspace OS interact with ChatGPT?

ChatGPT is a remote browser-based AI service. It does not have filesystem access to your workspace unless you paste things into it. The interaction model is therefore: **you copy context in, ChatGPT responds, you copy the answer out.**

### When should ChatGPT know about missions?

Almost never. ChatGPT does not need to know that `kgctl-vault-cli-propagation-bug-2026-07-24` exists. If you find yourself pasting a mission list into ChatGPT, you are using the wrong tool. Use Hermes, which has the workspace.

### When should ChatGPT be told about a mission?

In exactly one situation: when the mission's deliverable is text or copy that you want polished for an external audience — a blog post, a job application, a public README. Then you can:

1. Open the relevant mission's `artifacts.md` and `final-report.md`.
2. Compose a draft based on those notes.
3. Paste the draft into ChatGPT for editing.
4. Copy the result back into the artifact.
5. Commit it to the right repository.

ChatGPT is a writing tool in this context, not an operator. It does not know the workspace. It does not need to.

### When should Workspace OS be mentioned to ChatGPT?

Never, unless you are asking ChatGPT to help you draft a section of `WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md` or similar — i.e. when the *content* is about Workspace OS, not when Workspace OS is the *environment* in which ChatGPT is running.

### When is ChatGPT irrelevant?

For almost every coding task. If you are writing code, debugging, refactoring, designing an API, or doing anything that requires knowledge of the actual files in your workspace, use Hermes (which has filesystem access) or your editor (which has filesystem access), not ChatGPT. ChatGPT's main value in this workflow is for: conceptual learning, copy editing, language translation, brainstorming, and answering questions about a technology without touching your code.

### The clean pattern

- Hermes: anything that touches `/home/taras/projects/`.
- ChatGPT: anything that does not.

When in doubt, use Hermes, because Hermes can read the same files you can.

---

## 5. How should Workspace OS interact with Claude Code?

Claude Code is the Anthropic CLI agent. It has its own context-loading mechanism, often driven by a `CLAUDE.md` file at the workspace root or per-repository. The interaction model is closer to Hermes than to ChatGPT: Claude Code has shell and file tools, so it can in principle run `workspace-os mission list` and `workspace-os mission new` like any other CLI.

### What Claude Code should use Workspace OS for

- Reading the current mission list at session start, if you ask it to.
- Reading the markdown inside `.project-state/<slug>/` to understand context for the work you are asking it to do.
- Optionally writing into the mission's `execution-log.md` and `progress.md` to record its work.

### What Claude Code should ignore

- Workspace OS's internal SQLite database.
- The validator's verdict, unless you have explicitly asked it to interpret it.
- Other missions' folders.
- `.wsos/` entirely.

### The CLAUDE.md convention

The workspace root already has a `/home/taras/projects/CLAUDE.md` (read it; it is the project-level rule file for Claude Code). That file should not redefine identity (it points at `IDENTITY.md` for that), and it should not redefine Workspace OS rules. If you want Claude Code to follow Workspace OS conventions during a session, the cleanest thing is to:

1. Tell Claude Code the mission slug at the start of the session.
2. Let Claude Code read the mission's markdown.
3. Let it do the work.
4. Let it write back into the mission's markdown.

Do not expect Claude Code to know about Workspace OS unprompted. It is a tool that you point at a mission, not a tool that understands your operating model from scratch.

### Claude Code vs. Hermes

Both are autonomous CLI agents. The choice is operational, not technical:

- Use **Hermes** when the work fits your existing delegation patterns, your Telegram/Discord/Slack channels, and your home lab. Hermes has the gateway infrastructure already wired.
- Use **Claude Code** when you want a fresh interactive REPL session for a specific problem, and you do not want the work to fan out to messaging channels.

Both can use Workspace OS the same way: read the mission, do the work, write back into the mission.

---

## 6. How should Git relate to Workspace OS?

This is the most important conceptual distinction. **Missions and commits are different concepts that track different things.**

### Mission lifecycle

```
Open mission (workspace-os mission new <slug>)
   ↓
Plan + write initial source-task.md, progress.md
   ↓
Do work, write progress.md / execution-log.md as you go
   ↓
Hit a decision → record in decisions.md
   ↓
Hit a blocker → record in blockers.md
   ↓
Produce an artifact → list in artifacts.md
   ↓
Mission complete → workspace-os mission close <slug>
   ↓
Mission is now closed, with final-report.md as the canonical record
```

A mission is a unit of *intent*. It exists to answer the question: "What did I set out to do, and what happened?"

### Git lifecycle

```
git checkout -b feature/foo
   ↓
many commits (one per logical change)
   ↓
git push, open PR
   ↓
review, fix, more commits
   ↓
PR merged into main
   ↓
git checkout main, git pull
   ↓
branch is closed, commit history is preserved
```

A Git branch is a unit of *change*. It exists to answer the question: "What code changed, and how?"

### They are different, and the relationship is many-to-many

- **One mission, many commits.** A typical multi-day mission produces 10–50 commits across one or more branches. The mission is the paper trail of *why*; the commits are the paper trail of *what changed in code*.
- **Many missions, one commit.** A single commit might close the last open question in two missions, if the underlying code change resolved both.
- **Mission starts before branch, mission closes after merge.** Open the mission when you decide to do the work. Close the mission when the work is fully done — usually after the PR is merged and the branch is cleaned up. The mission lifecycle is wider than the Git lifecycle.

### Why they are different

Missions are about *narrative*: what was I trying to do, what did I decide, what blocked me, what did I produce. Git commits are about *deltas*: before vs after, in source code. They overlap when a commit's commit message references the mission slug (and they should — every commit message in a multi-day mission should include the slug), but they are not the same thing.

A practical rule: **commit messages cite the mission; mission files cite the commits.** `git log --grep=<slug>` should find every commit made under that mission. `decisions.md` should reference the commit SHAs that implemented the decisions.

### Where GitHub fits

GitHub is the host of your Git remotes. Workspace OS does not know about GitHub. GitHub does not know about Workspace OS. The only connection is that PR titles and commit messages should cite the mission slug, so that anyone reading the PR (human or AI agent) can find the mission folder if they need the full paper trail.

---

## 7. How should multiple repositories work?

You have many repositories in your workspace. Some of them are products (`operatoros-platform`, `knowledge-os`, `ai-factory`, `jobtracker`, `workspace-os` itself). Some of them are personal utilities. They all sit beside each other in `/home/taras/projects/`. Workspace OS does not see any of them.

### A single workspace, many repositories

```
/home/taras/projects/
├── workspace-os/                  ← tool source
├── operatoros-platform/           ← product repo
├── knowledge-os/                  ← product repo
├── ai-factory/                    ← product repo
├── jobtracker/                    ← product repo
├── ... many more ...
│
├── .wsos/                         ← Workspace OS runtime (one workspace, one DB)
└── .project-state/                ← missions (all of them, for any repo)
        ├── operatoros-v2-arch-2026-07-26/
        ├── ai-factory-vector-db-2026-07-28/
        └── hermes-to-operatoros-migration-2026-08-02/
```

One workspace, one `.wsos/`, one `.project-state/`. All missions for all repositories live in that one `.project-state/`. There is no per-repository Workspace OS state.

### Can one mission involve several repositories?

Yes. A mission is a workspace-scoped concept, not a repository-scoped concept. If your work touches three repositories, the mission touches three repositories. The 8-file mission folder in `.project-state/<slug>/` records all of it.

Example: a migration mission from Hermes to OperatorOS. It would touch:

- `operatoros-platform/` (new code)
- `hermes-agent/` (or its installed copy) (removed integration)
- `workspace-os/` (CLI change to remove the legacy bridge)
- The home lab scripts (`/home/taras/projects/scripts/`)
- Possibly a GitHub repo for `operatoros-platform-installer`

All of that goes into one mission folder. Workspace OS does not care.

### Should repositories have their own missions?

They already do, conceptually, by way of the mission slug convention. The current `.project-state/` has mission slugs like `operatoros-v1-launch-2026-07-24` and `workspace-os-v2-0-0-canonical-context-2026-07-25`. The slug encodes:

1. The product or subsystem (`operatoros-v1`, `workspace-os-v2`).
2. The purpose (`launch`, `canonical-context`, `ga-hardening`).
3. The date.

That convention is enough. You do not need a separate Workspace OS workspace per repository. You do not need per-repository `.wsos/` directories. One workspace is the right granularity.

### What if I want a clean mission that only touches one repository?

Just put it under a slug like `operatoros-platform-fix-typo-2026-07-26`. The slug is descriptive. The mission folder will be created at `/home/taras/projects/.project-state/operatoros-platform-fix-typo-2026-07-26/`. The work in `progress.md` will reference files inside `/home/taras/projects/operatoros-platform/`. Workspace OS does not care; it only sees a slug.

### What if I work on two repositories at once with overlapping concerns?

Open two missions. Each one gets its own slug, its own folder, its own progress notes. Reference each other in `decisions.md` if needed. Do not try to express cross-repo work as one giant mission; split it where the natural seams are.

---

## 8. Three realistic workdays

These are reconstructed from real missions in your `.project-state/` history. Names are illustrative.

### Day A — Small bug fix

The morning: you wake up, find a one-line bug in `operatoros-platform/` (a missing import). The fix is trivial.

```
08:00  open terminal, cd /home/taras/projects
08:01  workspace-os mission list                  (5 open missions, none trivial)
08:02  skip Workspace OS — this is a one-line fix
08:02  cd operatoros-platform/
08:03  git status                                  (clean)
08:03  git fetch origin
08:04  git checkout -b fix/missing-import
08:05  edit the file, add the import
08:05  git diff                                    (one-line change)
08:06  git add -p, git commit -m "fix: missing import in foo.py (operatoros-platform-v2-...)"
08:07  git push -u origin fix/missing-import
08:08  open PR on GitHub
08:10  CI runs
08:20  PR merged
08:21  git checkout main, git pull
08:21  cd /home/taras/projects
08:22  done
```

Hermes: not used. ChatGPT: not used. Workspace OS: not used. The fix is too small for any of them.

If the fix had taken multiple days, involved tests, involved a design decision about how the import should be structured, you would have opened a mission. For one-line fixes, you do not.

### Day B — Large architecture project

The morning: you have decided to redesign how `ai-factory/` interacts with `knowledge-os/` for v3 of the architecture. The work will take two weeks, span three repositories, and produce a written design document plus a reference implementation.

```
08:00  open terminal, cd /home/taras/projects
08:01  workspace-os mission list                  (review existing open missions)
08:02  workspace-os mission new ai-factory-knowledge-os-v3-arch-2026-07-26
08:03  open .project-state/ai-factory-knowledge-os-v3-arch-2026-07-26/source-task.md
       write the goal, the scope, the non-goals
08:30  open Hermes (hermes chat)
08:31  tell Hermes: mission slug is ai-factory-knowledge-os-v3-arch-2026-07-26,
       read source-task.md, begin research on current architecture
08:35  Hermes reads the relevant files (system-graph.md, ai-factory/AI-FACTORY-ARCHITECTURE-v2.md,
       knowledge-os/, OPERATOROS-PLATFORM-v1.0.0-CANONICAL-CONTEXT.md, etc.)
08:50  Hermes writes its findings into execution-log.md and decisions.md
09:30  you read Hermes's findings, ask Hermes to draft a design proposal
10:00  Hermes drafts the proposal into artifacts.md
10:30  you review, ask Hermes to refine, ask ChatGPT to copy-edit the executive summary
11:00  you commit the proposal to ai-factory/ as a markdown file
11:00  cd ai-factory/
11:01  git checkout -b design/v3-architecture
11:01  git add docs/v3-architecture.md
11:02  git commit -m "docs: v3 architecture proposal (mission ai-factory-knowledge-os-v3-arch-2026-07-26)"
11:03  git push -u origin design/v3-architecture
11:04  open PR
11:30  lunch
...
afternoon
...
18:00  cd /home/taras/projects
18:01  update .project-state/ai-factory-knowledge-os-v3-arch-2026-07-26/progress.md
18:05  git add .project-state/ai-factory-knowledge-os-v3-arch-2026-07-26/
18:06  git commit -m "mission progress: ai-factory-knowledge-os-v3-arch-2026-07-26 day 1"
       (note: you can commit the mission folder under the workspace root, or under the
       product repo's docs/, depending on convention; either is fine.)
18:07  done
```

Over the next two weeks:

- The mission stays open.
- Progress, decisions, blockers, artifacts, execution-log get updated daily.
- Commits and PRs flow through `ai-factory/`, `knowledge-os/`, possibly `workspace-os/`, each tagged with the mission slug in commit messages.
- Hermes is invoked when you want a deep investigation; ChatGPT is invoked when you want copy editing; Claude Code is invoked when you want a focused interactive session.
- At the end, you write the final-report.md, then `workspace-os mission close ai-factory-knowledge-os-v3-arch-2026-07-26`.

### Day C — Release day

The morning: `workspace-os v2.0.0` is going GA today. There is a release checklist, a tag to cut, a GitHub Release to publish, a wheel to upload.

```
07:00  open terminal, cd /home/taras/projects
07:01  workspace-os mission list                  (the v2.0 GA mission should be open)
07:02  cd workspace-os/
07:03  git fetch origin
07:03  git log --oneline -20                      (review the last few commits)
07:04  python scripts/release_verify.py --clean-clone    (canonical gate)
       ... all green ...
07:30  commit the canonical context document and the GA certificate (if not already)
       git add WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md WORKSPACE-OS-v2.0.0-GA-CERTIFICATE.md
       git commit -m "docs: add GA canonical context and release certificate"
07:32  git push origin main
07:35  watch GitHub Actions: 30163934239 on the released commit
07:40  confirm CI green on Python 3.11 and 3.12
07:45  git tag -a v2.0.0 <sha> -m "Workspace OS v2.0.0 GA release."
07:46  git push origin v2.0.0
07:50  gh release create v2.0.0 --target <sha> --title "Workspace OS v2.0.0" --notes-file notes.md dist/workspace_os-2.0.0-py3-none-any.whl dist/workspace_os-2.0.0.tar.gz
08:00  curl -L https://github.com/taras-polishchuk/workspace-os/releases/download/v2.0.0/workspace_os-2.0.0-py3-none-any.whl -o /tmp/check.whl
08:01  verify SHA-256 of /tmp/check.whl against the GA Certificate
08:05  done — release is live
08:10  update .project-state/workspace-os-v2-ga-hardening-2026-07-25/final-report.md
08:11  workspace-os mission close workspace-os-v2-ga-hardening-2026-07-25
08:12  cd /home/taras/projects
08:13  start a new mission: workspace-os-v2-0-1-maintenance-2026-08-15 (placeholder for the next phase)
```

Hermes: used earlier in the cycle to drive the audit and post-GA baseline freeze. Today is mostly manual because the tag and release are owner-gated.

ChatGPT: not used. This is mechanical work with very specific commands.

Claude Code: not used for the release itself. If a fix needs investigation during the day, Claude Code might be spun up interactively.

The pattern: **Workspace OS owns the paper trail; Git owns the code; GitHub owns the release; the operator owns all three.**

---

## 9. Common mistakes

Thirty of them, each with the correction.

1. **"I need a mission for every commit."**
   No. Commits are code deltas. Missions are units of intent. One mission contains many commits; one commit rarely contains a full mission.

2. **"I should create a Workspace OS mission before every ChatGPT question."**
   No. ChatGPT questions are inputs, not work. Create a mission only when you are starting multi-step work that will produce a deliverable.

3. **"Workspace OS is the source of truth for what I did today."**
   No. Git is the source of truth for what code changed. Workspace OS is the source of truth for what you *intended* to do and what you *wrote down*. They are different.

4. **"Workspace OS replaces Git."**
   No. See above. Workspace OS does not run Git, does not read `.git/`, does not know about commits.

5. **"Workspace OS replaces my TODO list."**
   No. Use whatever TODO app you like for short-term tasks. Use Workspace OS for multi-day missions. Different time horizons.

6. **"Workspace OS replaces my notes app."**
   No. Mission folders are not your general notebook. They are mission-scoped working notes. Your other notes (Obsidian, Notion, Apple Notes) still exist.

7. **"I should put my CV in a mission."**
   No. Your CV is not a mission. It is a document that lives somewhere appropriate.

8. **"Every Hermes session needs its own mission."**
   No. One mission may contain many Hermes sessions. Open the mission once, run Hermes many times under it, close the mission once.

9. **"Workspace OS will automatically validate my work."**
   No. `workspace-os validate` is manual. There is no cron, no pre-commit hook, no auto-run.

10. **"I should run `workspace-os validate` every time I save a file."**
    No. Run it when you want a structural sanity check, not as part of your editor save loop.

11. **"Workspace OS owns my entire `/home/taras/projects/` directory."**
    No. Workspace OS owns `.wsos/` and `.project-state/` and nothing else. Every other directory is yours.

12. **"I should commit `.wsos/` to Git."**
    No. `.wsos/` is local runtime state. It is gitignored in normal practice. Do not commit it.

13. **"I should commit `.project-state/<slug>/source-task.md` to a product repo."**
    No. `.project-state/` lives in your workspace, not in any product repo. It is the operator's notes, not the product's documentation. Product docs go inside the product repository.

14. **"A mission is the same as a Git branch."**
    No. A branch is a code delta. A mission is an intent record. They overlap in time and reference each other, but they are not the same thing.

15. **"Workspace OS will tell me if my mission is on track."**
    No. Workspace OS does not analyse your work. It stores what you wrote down. Whether the mission is on track is your judgement, informed by reading what you wrote.

16. **"Workspace OS syncs across machines."**
    No. If you want to sync, sync `.project-state/<slug>/` yourself (e.g. with Git, or by backing up the workspace).

17. **"I need a workspace per machine."**
    No. You can have one workspace per machine, or one workspace that you sync between machines. The release does not prescribe.

18. **"The 8 files inside a mission are required."**
    No. Workspace OS creates 8 files with a header, then forgets about them. You can add, delete, rename, or repurpose them. Only `workspace-os mission new` and `workspace-os validate` look at them, loosely.

19. **"I need to close every mission before I can stop work."**
    No. Missions stay open until you close them. You can have many open at once. The list is not a checklist you must zero out.

20. **"If a mission is closed, its folder is gone."**
    No. Closing a mission only updates a row in the SQLite database. The folder and all 8 files stay on disk forever.

21. **"Workspace OS will run my tests."**
    No. Workspace OS does not run tests. Your test runner runs tests.

22. **"Workspace OS will deploy my code."**
    No. Workspace OS does not deploy. CI/CD deploys.

23. **"Workspace OS will track my time."**
    No. There is no time tracking. The mission's `created_at` and `closed_at` timestamps are the only time data.

24. **"Workspace OS will remind me to close open missions."**
    No. There is no notification system. If you want a reminder, use your calendar or Hermes cron.

25. **"I should run `workspace-os init` for each new repository."**
    No. One `init` per workspace root. Repositories inside the workspace do not need their own.

26. **"Workspace OS knows what GitHub remote my repository uses."**
    No. Workspace OS does not read Git config. Git knows that.

27. **"Workspace OS will catch my secrets."**
    No. Workspace OS has no scanner. You must not commit secrets, period. Use `.gitignore` and pre-commit hooks for that.

28. **"I should delete the validator's FAILs."**
    No. The validator's FAILs are informational. Many of them come from old missions whose 8 files are not all populated. That is normal. Do not try to zero them out.

29. **"Workspace OS is the same as OperatorOS Platform."**
    No. Workspace OS is a local Python tool. OperatorOS Platform is a separate product repository. They share a workspace root but are independent.

30. **"Workspace OS is the same as Knowledge OS."**
    No. Same answer. Independent product, different purpose.

---

## 10. Tomorrow morning — the actual answer

You open the MacBook. `/home/taras/projects` is the workspace root. OperatorOS needs work. Hermes, ChatGPT, and Claude Code are all available. Workspace OS is installed. Here is exactly what you do.

### The first five minutes

```
# 1. Open a terminal.
# 2. Move to the workspace.
cd /home/taras/projects

# 3. Ask Workspace OS what is open.
workspace-os mission list
```

Read the output. You will see a list of open missions. Some of them will be about OperatorOS. Some of them will be about other things. Some will be stale and need closing.

### The next five minutes

Decide what you are doing today. Three possibilities.

**Possibility 1: continue an open OperatorOS mission.** Find the relevant slug in the mission list.

```
workspace-os mission list | grep operatoros
```

Pick the one that matches today's intent. Open its folder.

```
cat .project-state/<slug>/source-task.md
cat .project-state/<slug>/progress.md
cat .project-state/<slug>/decisions.md
cat .project-state/<slug>/blockers.md
```

You now know what the mission is, where it stands, what was decided, and what is blocking. Continue.

**Possibility 2: start a new OperatorOS mission.** No slug matches today's intent.

```
workspace-os mission new operatoros-<purpose>-2026-07-26
```

Open `.project-state/operatoros-<purpose>-2026-07-26/source-task.md` and write the goal. Open `progress.md` and write the starting state. Now you have a mission.

**Possibility 3: do a one-line fix.** Skip the mission entirely. Skip Workspace OS entirely. Go straight to `cd operatoros-platform/` and do the work.

### The work itself

```
# Optional: check the repo state.
cd operatoros-platform/
git status
git fetch origin
git log --oneline -5

# Do the work. Use your editor. Use Hermes. Use ChatGPT. Use Claude Code.
# They do not need to know about Workspace OS — they just need to know
# about the current mission if you told them.
```

If you delegated to Hermes:

```
# Tell Hermes the mission slug.
# Hermes will read the mission folder and write back into it.
```

If you used `workspace-os agent run` to log a command:

```
workspace-os agent run --mission <slug> -- <command>
```

If you ran the validator:

```
workspace-os --workspace /home/taras/projects validate
```

### The end of the day

```
cd /home/taras/projects

# Update the mission's progress.md if there is anything to record.
# Commit any code changes to the product repository with a commit
# message that includes the mission slug.

# Optionally, commit the mission folder updates under the workspace
# root if you want them backed up:
git add .project-state/<slug>/
git commit -m "mission progress: <slug>"

# If the mission is done, close it.
workspace-os mission close <slug>

# Tomorrow morning, run `workspace-os mission list` again. Repeat.
```

That is the entire routine. It is the same routine every day, with two knobs:

- **The mission.** Today you are working on one mission. Open it at the start of the day, close it (or not) at the end.
- **The tool mix.** Some days are pure code (editor + Git). Some days involve deep research (Hermes). Some days involve copy editing (ChatGPT). Some days involve an interactive REPL (Claude Code). The mix changes; the routine does not.

### The one-line summary

**Open a mission, do the work in your editor and through your AI agents, write down what happened, close the mission.** Workspace OS is the notebook. Everything else is the work.

---

## Appendix: quick reference card

| I want to … | Tool to use |
|---|---|
| See today's backlog | `workspace-os mission list` |
| Start a multi-day project | `workspace-os mission new <slug>` |
| Close a finished project | `workspace-os mission close <slug>` |
| Log a shell command to a mission | `workspace-os agent run --mission <slug> -- <cmd>` |
| Get a structural sanity check | `workspace-os --workspace /home/taras/projects validate` |
| Delegate a deep investigation | Hermes (`hermes chat`), pointed at a mission |
| Polish copy or learn a concept | ChatGPT, no workspace context |
| Focused interactive coding session | Claude Code, pointed at a mission |
| Make a code change | Your editor + Git, in the product repository |
| Cut a release tag | `git tag -a vX.Y.Z <sha>` + `git push origin vX.Y.Z` |
| Publish a GitHub Release | `gh release create vX.Y.Z --target <sha> --title … --notes-file … dist/*` |
| Inspect the database directly | `sqlite3 /home/taras/projects/.wsos/state.db` |
| Reset everything | `rm -rf /home/taras/projects/.wsos /home/taras/projects/.project-state && workspace-os init` |