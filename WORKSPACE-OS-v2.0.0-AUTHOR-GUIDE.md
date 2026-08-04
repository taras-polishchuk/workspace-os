# How to Actually Use Workspace OS

A practical guide for the author, six months later, who has forgotten almost everything.

Released version: Workspace OS v2.0.0 (commit `97c3c49e5f54385256f7f52052e1a5eee012a6b4`, annotated tag `v2.0.0`). What is described below is the behaviour of that release and nothing else.

---

## 1. What is Workspace OS?

In plain language: Workspace OS is a thin notekeeping system for the long work you do on your machine.

It is not a notebook you type into. It is a small Python tool that knows how to create, find, list, close, and audit one specific kind of folder — a *mission* — inside one specific kind of directory — a *workspace*. It keeps a SQLite database of those missions, and it gives you a tiny command line to talk to that database.

What it does for you, day to day:

- it remembers every mission you open, in order, with timestamps and a status;
- it writes a fixed 8-file skeleton into each new mission folder so you never have to think about what to call the files;
- it logs every shell command you ask it to log, so you can look back and see what you actually did;
- it runs a Python validator against your workspace and remembers the verdict of each run.

What it does not do:

- it does not touch your project code;
- it does not run a server, a daemon, or a background process;
- it does not sync to the cloud;
- it does not install, manage, or supervise your other tools;
- it does not have an opinion about how you organise the files inside your projects.

After installing it, the only thing that changes is: you get a `workspace-os` command, and inside whichever directory you point it at, it creates two hidden folders (`.wsos/` and `.project-state/`) that hold its own bookkeeping. Nothing else about your machine changes.

---

## 2. What is the repository?

This is the part that confuses everyone. There are five different things people call "Workspace OS", and they are all real and all different:

| Thing | Where it lives | What it is |
|---|---|---|
| **GitHub repository** | https://github.com/taras-polishchuk/workspace-os | Source code, issues, releases, CI. This is what other people see. |
| **Python package** | `workspace-os/dist/workspace_os-2.0.0-py3-none-any.whl` (or on PyPI someday) | A wheel you can `pip install`. It contains the code. |
| **Installed CLI** | `~/.local/bin/workspace-os` after `pip install` | A runnable program on your `$PATH`. Type `workspace-os` and it runs. |
| **Runtime state** | `<workspace>/.wsos/` inside any workspace you initialise | The SQLite database `state.db`, an init lock file, an `agent-runs/` folder, and a `drift-acceptance.jsonl` audit file. |
| **Missions** | `<workspace>/.project-state/<slug>/` inside that same workspace | The 8-file mission folders that Workspace OS creates for you. |

Picture it like this:

```
 GitHub repo  (taras-polishchuk/workspace-os)
       │
       │  pip install (or pip install -e .)
       ▼
 Installed CLI   workspace-os   on your $PATH
       │
       │  workspace-os init
       ▼
 Inside a workspace you choose, e.g. /home/taras/projects
       ├── .wsos/                     ← runtime (SQLite + agent-run logs)
       │     ├── state.db
       │     ├── agent-runs/*.log
       │     └── drift-acceptance.jsonl
       └── .project-state/            ← missions (the 8-file skeleton)
             ├── mission-a/
             │     ├── source-task.md
             │     ├── progress.md
             │     ├── decisions.md
             │     ├── blockers.md
             │     ├── artifacts.md
             │     ├── environment.md
             │     ├── execution-log.md
             │     └── final-report.md
             └── mission-b/
                   └── (same 8 files)
```

The five things are connected by a single rule: **Workspace OS only does anything inside the directory you point it at.** It does not look at your home directory. It does not scan for repositories. It does not have a global database. It does not auto-discover anything. If you do not point it at a directory and run `init` in it, Workspace OS effectively does not exist on that machine.

---

## 3. What happens when somebody clones the repository?

If you are reading this in the future and you have just run:

```bash
git clone https://github.com/taras-polishchuk/workspace-os.git
cd workspace-os
```

…here is what you have and what you do not have.

What you have:

- the **source code** for the `workspace-os` Python package (`src/workspace_os/`);
- the **release-verification script** (`scripts/release_verify.py`);
- the **README, CHANGELOG, RELEASE, SUPPORT, runbook**, and the two canonical context documents;
- a **pre-built wheel** if `dist/` was checked in (it is normally gitignored — you build it yourself);
- the **GitHub Actions workflow** (`.github/workflows/ci.yml`).

What you do not have:

- an installed CLI — cloning is not installing;
- a workspace — there is nothing to validate, no missions, no `.wsos/`;
- any state about your own work — this is a fresh checkout, not your data;
- a daemon, a server, or anything running in the background.

The clone is just the source. To actually use it, you have to install the package and then point it at a directory.

The standard sequence after cloning, end-to-end:

```bash
git clone https://github.com/taras-polishchuk/workspace-os.git
cd workspace-os
python -m pip install -e ".[dev]"     # editable install, dev deps for tests
workspace-os --version                # confirm the CLI is now installed
```

After this, `workspace-os` is a real command in your shell. You have not yet told it about any workspace — it has nothing to act on until you `init` one.

What Workspace OS expects from you, in order:

1. A directory you want to be a workspace. It can be anywhere you can write to. It can be empty. It can already have projects in it. Workspace OS will only ever add `.wsos/` and `.project-state/` at its top level; it will never read or modify anything else.
2. A single command — `workspace-os --workspace <that directory> init` — that creates `.wsos/` and registers the directory in the SQLite database.
3. After that, you create missions with `workspace-os mission new <slug>`, list them with `workspace-os mission list`, and close them with `workspace-os mission close <slug>`.

Everything else flows from those three commands.

---

## 4. How would a completely new user start?

Suppose you have an empty directory called `~/my-first-workspace/` and nothing else. You want to use Workspace OS in it. Here is exactly what you do.

Open a terminal:

```bash
cd ~/my-first-workspace

# 1. Make sure the package is installed (one-time).
python -m pip install workspace-os==2.0.0
# or, from a local clone:
# python -m pip install -e /path/to/workspace-os

# 2. Initialise this directory as a workspace.
workspace-os --workspace . init

# 3. Create your first mission.
workspace-os --workspace . mission new my-first-mission

# 4. See what was created.
workspace-os --workspace . mission list

# 5. (Optional) Run the validator against the workspace.
workspace-os --workspace . validate
```

Now look at the directory:

```
~/my-first-workspace/
├── .wsos/                          ← created by step 2
│     ├── state.db                  ← SQLite database
│     ├── .init.lock                ← empty lock file
│     └── agent-runs/               ← empty until you log a command
└── .project-state/                 ← created by step 3
      └── my-first-mission/
            ├── source-task.md      ← 8 standard files, each with a header
            ├── progress.md
            ├── decisions.md
            ├── blockers.md
            ├── artifacts.md
            ├── environment.md
            ├── execution-log.md
            └── final-report.md
```

That is the entire first-use experience. Nothing else got created. Nothing in `~/my-first-workspace/` outside `.wsos/` and `.project-state/` was touched.

The files that matter:

- `state.db` — every workspace and mission you ever create is recorded here. Open it with `sqlite3` if you want to inspect it directly. The schema has five tables: `workspaces`, `missions`, `mission_artifacts`, `validator_runs`, `agent_runs`.
- `.project-state/<slug>/*.md` — these are yours to write into. The 8-file skeleton is a structure, not a constraint: edit them, add detail, leave them sparse — Workspace OS does not read them at runtime. It only checks they exist when you ask it to.

The files you can ignore:

- `.init.lock` — internal concurrency lock. You will never edit it.
- `agent-runs/*.log` — append-only audit log of commands you chose to record. Read-only for you.
- `drift-acceptance.jsonl` — only used by the validator's `--accept-drift` flow.

---

## 5. How does Workspace OS relate to projects?

Suppose your workspace contains:

```
/home/taras/projects/
├── OperatorOS/                 ← a real product repository
├── Knowledge OS/               ← a real product repository
├── JobTracker/                 ← a real product repository
└── MyProduct/                  ← a real product repository
```

Workspace OS does **none** of the following to those directories:

- it does not open them,
- it does not read them,
- it does not index them,
- it does not modify them,
- it does not write anything next to them,
- it does not run anything inside them,
- it does not know they exist.

Workspace OS only writes into two places at the top of the workspace:

- `.wsos/` (a hidden directory it owns end-to-end)
- `.project-state/` (mission folders you create on demand)

The projects themselves sit beside these folders as ordinary directories. Their `.git/`, their source code, their `node_modules/`, their `target/`, their `Cargo.lock`, their `.env`, their everything — all untouched and unobserved.

The boundary is absolute. If you grep your workspace for files Workspace OS has ever written, you will only ever find files inside `.wsos/` and `.project-state/`. That is the entire surface area.

Workspace OS does keep its own state — but that state is also a directory you can see and delete. The `.wsos/state.db` SQLite file is the only database. There is no cloud copy, no global config file in your home directory, no hidden sidecar outside the workspace you chose.

---

## 6. How does MY workspace work?

This is the actual machine. The workspace root is `/home/taras/projects`. It already has `.wsos/` and `.project-state/` from before this guide was written, and they hold real state.

What Workspace OS sees when you point it there:

```
/home/taras/projects/
├── .wsos/                              ← Workspace OS runtime
│     ├── state.db                      ← SQLite, ~70 KB today
│     ├── .init.lock                    ← concurrency lock, empty
│     ├── agent-runs/                   ← command audit logs
│     └── drift-acceptance.jsonl        ← validator drift records
├── .project-state/                     ← 170+ mission folders today
│     ├── kgctl-vault-cli-propagation-bug-2026-07-24/
│     ├── operatoros-platform-v1-final-release-curation-2026-07-24/
│     ├── workspace-os-v2-0-0-canonical-context-2026-07-25/
│     ├── ... and 167 more ...
│     └── (your new mission goes here)
│
├── OperatorOS/                         ← a product repo, NEVER touched
├── Knowledge OS/                       ← a product repo, NEVER touched
├── JobTracker/                         ← a product repo, NEVER touched
├── MyProduct/                          ← a product repo, NEVER touched
├── ARCHITECTURE.md                     ← a top-level symlink, untouched
├── IDENTITY.md                         ← a top-level symlink, untouched
├── GOVERNANCE/                         ← constitutional docs, untouched
├── CONTEXT/                            ← workspace index, untouched
├── CLAUDE.md                           ← AI agent context file, untouched
├── (170+ more top-level entries, all ordinary files and dirs)
```

What belongs to Workspace OS, and only to Workspace OS:

- `/home/taras/projects/.wsos/` — including everything inside it.
- `/home/taras/projects/.project-state/` — including everything inside it. (You write into the mission folders; Workspace OS only manages their names, creation, and listing.)

What never gets modified by Workspace OS:

- everything else under `/home/taras/projects/`, which includes every product repository, every governance document, every context file, every top-level symlink, every configuration file, every script, every binary, and every piece of data you keep in your workspace.

If you forget this, the rule to remember is: **Workspace OS only ever owns its own two hidden directories.** Everything else in `/home/taras/projects/` is your problem, not its.

---

## 7. Typical daily workflow

Below is a realistic day. The exact commands are taken from the released CLI; the narrative is reconstructed from what the commands actually do.

### Morning

You open a terminal and check what you were doing yesterday:

```bash
cd /home/taras/projects
workspace-os mission list
```

Output (abridged):

```
mission_id slug                                     status     created_at
--------------------------------------------------------------------------------
6          kgctl-vault-cli-propagation-bug-2026-07-24 open       2026-07-24 08:48
5          operatoros-platform-v1-final-release-curation-2026-07-24 open  ...
4          operatoros-v1-launch-2026-07-24              open       ...
```

Pick the open mission you want to continue, or start a new one.

### New mission

```bash
workspace-os --workspace /home/taras/projects mission new kgctl-secret-rotation-2026-07-25
```

This:

- creates `/home/taras/projects/.project-state/kgctl-secret-rotation-2026-07-25/` with the 8 standard files pre-populated with a header;
- inserts a row into the `missions` table;
- inserts 8 rows into `mission_artifacts` (one per file).

Open `source-task.md` and write what you are doing and why. Use the other files as your work journal. Workspace OS does not read them.

### Validation

Before declaring work done, or whenever you want a structural sanity check:

```bash
workspace-os --workspace /home/taras/projects validate
```

This:

- reads `policy.yaml` (bundled inside the installed package, no path gymnastics);
- runs the Python validator against the workspace;
- parses the `Summary: N passed, M failed` line;
- records one row in `validator_runs` regardless of pass/fail;
- prints the verdict and exits 0 (warning-only by default) or 1 (strict).

The validator's verdict is informational — it tells you which drift conditions exist in your workspace, not whether your work is correct. On a busy workspace you will see many FAILs from old missions whose 8 files are not all populated; that is normal.

### Agent execution

If you want Workspace OS to log a shell command you ran:

```bash
workspace-os --workspace /home/taras/projects agent run --mission kgctl-secret-rotation-2026-07-25 -- rg "TODO" src/
```

This:

- runs the command with `subprocess.run`, exits with the same code;
- writes `command:` and `exit_code:` lines to a new `.wsos/agent-runs/run-<workspace_id>-<ms>-<pid>.log` file;
- inserts one row into `agent_runs`, optionally linked to the mission.

You do not have to use `agent run`. You can run commands normally. `agent run` is only for the cases where you want a permanent log of "this is what I did on mission X".

### Evidence

Everything Workspace OS recorded for today is in two places:

- `.wsos/state.db` — query it directly:
  ```bash
  sqlite3 /home/taras/projects/.wsos/state.db
  > .tables
  > SELECT slug, status, created_at FROM missions ORDER BY mission_id DESC LIMIT 5;
  > SELECT run_id, ts, pass_count, fail_count FROM validator_runs ORDER BY ts DESC LIMIT 5;
  > SELECT command, exit_code FROM agent_runs ORDER BY run_id DESC LIMIT 5;
  ```
- `.wsos/agent-runs/*.log` — raw command records.

If the validator accepted drift (`workspace-os validate --accept-drift --accept-rationale "..." --mission kgctl-secret-rotation-2026-07-25`), that audit row is in `.wsos/drift-acceptance.jsonl`.

### Finish

When a mission is done:

```bash
workspace-os --workspace /home/taras/projects mission close kgctl-secret-rotation-2026-07-25
```

This flips the mission's `status` to `closed` and sets `closed_at`. It is idempotent — running it again does not error. The 8 files stay on disk; closing is a marker, not a deletion.

### Next mission

The next morning, `workspace-os mission list` shows your closed mission alongside the new ones, ordered by id, with timestamps. That is the entire cycle.

---

## 8. What is NOT Workspace OS?

This is the section that prevents most confusion. Each item below is something Workspace OS looks similar to but is not.

- **Git.** Git tracks file content inside one repository. Workspace OS tracks mission metadata inside one workspace. They never meet. Workspace OS does not run `git`, does not read `.git/`, does not know about branches or commits.
- **GitHub.** GitHub is a hosted Git service. Workspace OS has a GitHub repository (the source code) and a GitHub Release (the wheel), but Workspace OS itself is a local program. After `pip install`, GitHub is irrelevant to the running program.
- **Claude Code.** Claude Code is an AI coding agent. Workspace OS has no AI in it. It is a deterministic Python program. If you use Claude Code as the operator, Claude Code talks to your shell, your editor, your files; Workspace OS is one of the things it can talk to.
- **Hermes.** Hermes is an autonomous CLI agent with persistent memory and a gateway. Workspace OS is a deterministic Python tool. They can be used together — Hermes can be the operator that drives `workspace-os` — but they are different systems. Workspace OS does not call Hermes; Hermes can call Workspace OS.
- **ChatGPT / any LLM.** Workspace OS contains no LLM calls. No model is queried. No API key is required at runtime.
- **OperatorOS.** OperatorOS is a separate product repository (`/home/taras/projects/operatoros-platform/`). Workspace OS is the local-kernel tool that sits beside it. They share a workspace root but are independent.
- **Knowledge OS.** Knowledge OS is another separate product repository. Workspace OS does not import it, link it, or know about it.
- **AI Factory.** Same status: a separate product. Workspace OS's only contact with AI Factory concepts is the `agent run` subcommand, which logs commands you ran; it has nothing to do with model training.
- **Python.** Workspace OS is *implemented* in Python (Python 3.11+). It is not *a Python distribution* — it does not replace your Python, it uses it.
- **SQLite.** Workspace OS uses SQLite to store its database. It is not a database product. The SQLite file at `.wsos/state.db` is owned by Workspace OS; treat it as its internal file, not as a shared database.
- **Mission folders (the directories themselves).** When Workspace OS creates `.project-state/foo/`, it owns the directory and its 8 file names. It does not own what you write inside the files. The markdown is yours.
- **Project repositories.** Workspace OS has nothing to do with any of your product repositories. It does not clone, push, build, test, or release them.
- **Filesystem.** Workspace OS uses the filesystem; it is not the filesystem. It writes only inside the workspace root you give it, only into `.wsos/` and `.project-state/`.

The single rule that resolves every confusion: **Workspace OS is one Python tool with a CLI and a small SQLite database, scoped to one workspace root.** Anything you are tempted to assign to it that is bigger than that, it does not do.

---

## 9. Frequently misunderstood concepts

Twenty-three of them, each with the correct answer.

1. **"I cloned the repository, so Workspace OS is running."**
   No. Cloning gives you source code. To run anything you must `pip install` it. Cloning + reading source ≠ running.

2. **"I installed the package, so it now manages my projects."**
   No. Installation only puts the `workspace-os` binary on your `$PATH`. It manages nothing until you point it at a workspace and run `init`.

3. **"Workspace OS auto-discovers my repositories."**
   No. It has no concept of "my repositories". It does not scan your workspace, ever.

4. **"Workspace OS reads my source code."**
   No. It only writes to `.wsos/` and `.project-state/`. It never opens files inside your project directories.

5. **"Workspace OS modifies my project files."**
   No. It cannot. It has no code path that touches anything outside `.wsos/` and `.project-state/`.

6. **"Workspace OS runs a daemon in the background."**
   No. There is no daemon. The `daemon.py` module is an honest stub; `is_daemon_available()` returns `False`; `workspace-os daemon` is not even a CLI subcommand. Every Workspace OS action is a foreground CLI invocation that exits.

7. **"Workspace OS talks to GitHub at runtime."**
   No. The runtime is local. Only the install step or `pip install` reaches the network. After install, no network is used.

8. **"Workspace OS has a database somewhere else."**
   No. There is one database, `.wsos/state.db`, inside the workspace root you chose. Delete that file and the data is gone.

9. **"Workspace OS replaces Git."**
   No. They do different things. You can use Git inside your workspace and Workspace OS at the same time. Workspace OS does not even know Git exists.

10. **"Workspace OS replaces my todo app."**
    No. Workspace OS is a structure for long, multi-day missions, not a personal task manager. The 8 files inside each mission are yours to use however you want — for todos, for journals, for design notes.

11. **"Workspace OS requires me to use its 8-file template exactly."**
    No. Workspace OS creates the 8 files with a header, then forgets about them. You can delete files inside the mission folder, add files, rename them. Only `workspace-os mission new` and `workspace-os validate` look at the structure, and only loosely.

12. **"Workspace OS automatically runs the validator."**
    No. `workspace-os validate` is a manual command. There is no cron, no pre-commit hook, no auto-run.

13. **"If I run `workspace-os validate`, my workspace is broken."**
    No. The validator emits informational FAILs for any drift condition. A FAIL on a mission whose 8 files are not all populated is expected. The validator's verdict does not mean your work is wrong.

14. **"Workspace OS syncs across machines."**
    No. It does not. If you want to sync `.wsos/` and `.project-state/`, you have to do it yourself (e.g. by Git, or by backup).

15. **"Workspace OS has a UI."**
    No. The only interface is the CLI. There is no web UI, no desktop UI, no TUI.

16. **"Workspace OS is on PyPI."**
    Not yet. As of v2.0.0 GA, the only install paths are `pip install <wheel>` from the GitHub Release URL, or `pip install -e .` from a local clone. PyPI publication is intentionally deferred.

17. **"Workspace OS is one of my AI agents."**
    No. Workspace OS has no AI inside it. AI agents can be the operator that drives Workspace OS, but Workspace OS itself is dumb code.

18. **"Workspace OS replaces my notes."**
    No. Each mission folder is a notes folder, but Workspace OS does not parse the notes. Your notes are your notes.

19. **"Workspace OS requires a server."**
    No. No HTTP server, no socket, no port binding. Everything runs as a one-shot CLI process.

20. **"Workspace OS locks me in."**
    No. The runtime state is two visible directories in your workspace. Delete `.wsos/` and `.project-state/` and your workspace is exactly as it was before. The mission folders are plain markdown.

21. **"Workspace OS is the same thing as the project named `Workspace OS` in my workspace."**
    There is no such project. The repository you cloned (`workspace-os`) is the source code; it is itself one of the ordinary repositories under your workspace root. Workspace OS the tool is the `workspace-os` CLI you installed from it. They are different things.

22. **"Workspace OS' default workspace is `/home/taras/projects`."**
    No. As of the GA release (`97c3c49`), the default is the current working directory (`Path.cwd()`). Older documentation said `/home/taras/projects`; that is historical. Pass `--workspace` explicitly if you want a specific root.

23. **"Workspace OS has a release phase called `v2.0-rc`."**
    No. The release phase `v2.0-rc` was retired at the GA commit. The current release is `v2.0.0` GA, tag `v2.0.0`, peels to `97c3c49`. Older `v2.0-rc` references in older documents are historical.

---

## 10. Architecture from the user's perspective

This section describes what actually happens, not how it is implemented.

When you run a command, here is what changes:

| Command | What happens | Where state lives | What changes | What stays untouched |
|---|---|---|---|---|
| `workspace-os init` | Creates `.wsos/`, `state.db`, the lock file. Registers your workspace in the `workspaces` table. | `.wsos/state.db` | New `.wsos/` directory; new row in `workspaces`. | Everything else. |
| `workspace-os mission new <slug>` | Creates `.project-state/<slug>/` with 8 markdown files. Inserts one row in `missions`, 8 rows in `mission_artifacts`. | `.project-state/<slug>/`, `.wsos/state.db` | New mission directory; new rows in `missions` + `mission_artifacts`. | Everything else. |
| `workspace-os mission list` | Reads the `missions` table for your workspace, prints a table. | `.wsos/state.db` (read-only) | Nothing. | Everything. |
| `workspace-os mission close <slug>` | Sets the mission's `status` to `closed` and `closed_at` to now. | `.wsos/state.db` | One row update. | Everything else. |
| `workspace-os validate` | Reads `policy.yaml` (bundled in the installed package), runs the Python validator, parses the `Summary: N passed, M failed` line, inserts a row in `validator_runs`. | `.wsos/state.db`, optional `--output` file | New row in `validator_runs`. | The workspace itself; the validator reads but does not modify it. |
| `workspace-os validate --accept-drift --accept-rationale "..."` | Same as above, plus appends a record to `.wsos/drift-acceptance.jsonl` (atomically, with an advisory file lock to prevent races). | `.wsos/drift-acceptance.jsonl` | New JSONL line. | The validator verdict; this only annotates acceptance. |
| `workspace-os agent run -- <cmd>` | Runs `<cmd>` with `subprocess.run`, captures exit code, writes a `.log` file under `.wsos/agent-runs/`, inserts a row in `agent_runs`. | `.wsos/agent-runs/*.log`, `.wsos/state.db` | New log file; new row in `agent_runs`. | The mission folder (unless you pass `--mission <slug>`, in which case the run is linked to the mission). |

Two operational details that matter when you actually use it:

- **Atomic writes.** Every file Workspace OS writes goes through an atomic-rename helper that refuses to follow symlinks. So if you plant a symlink at `.wsos/state.db`, it refuses to write through it. This is a defence, not a feature you need to use.
- **Advisory lock.** Concurrent calls to `workspace-os init` against the same workspace are serialised by a file lock (`.wsos/.init.lock`). If you `init` twice, the second call does not corrupt the database; it just sees the existing one. Concurrent validator runs that accept drift use a separate advisory lock so two `drift-acceptance.jsonl` appends cannot lose a record.

If you want to reset everything and start over:

```bash
rm -rf /home/taras/projects/.wsos /home/taras/projects/.project-state
workspace-os --workspace /home/taras/projects init
```

That returns the workspace to its pre-Workspace-OS state.

---

## 11. How should I use it tomorrow morning?

Concrete answer, for tomorrow morning, sitting at the MacBook with `/home/taras/projects` open.

You do not need to do anything to start using Workspace OS. It is already installed (the `workspace-os` command is on your `$PATH` at `~/.local/bin/workspace-os`). The workspace is already initialised (`/home/taras/projects/.wsos/` exists). The mission list is already populated with everything you have been working on.

Tomorrow morning, the entire routine is:

1. **Open a terminal.** `cd /home/taras/projects` (or it will already be there).
2. **Check what's open.** `workspace-os mission list`. Read the output. See what is `open` and what is `closed`. That's your backlog.
3. **Decide what to do today.** Either:
   - Continue an existing open mission: open `.project-state/<slug>/source-task.md`, read what you wrote, continue.
   - Close a mission that is done: edit its `final-report.md`, then `workspace-os mission close <slug>`.
   - Start a new mission: `workspace-os --workspace /home/taras/projects mission new <today-slug>`, then open `source-task.md` and write what you are doing.
4. **Work.** Use your normal editor, terminal, browser, AI agent. Workspace OS does nothing while you work. It does not interrupt you. It does not auto-validate. It does not auto-log.
5. **Optionally, log a command.** When you do something that should be in the audit trail: `workspace-os agent run --mission <slug> -- <the command>`. The exit code propagates and the command is recorded.
6. **Optionally, validate.** `workspace-os --workspace /home/taras/projects validate`. Look at the verdict. Treat FAILs as informational.
7. **Tomorrow morning, repeat from step 2.**

That is the entire practical answer. There is no other ritual. Workspace OS does not own your time, your editor, your agent, or your project files. It owns two hidden directories and one CLI, and it stays out of the way otherwise.

If you remember nothing else, remember this: **Workspace OS is two hidden directories (`.wsos/` and `.project-state/`) and one CLI (`workspace-os`).** It lives where you point it, does only what you ask, and forgets everything it was not asked to do.

---

## Appendix: where to look if you forget

- `workspace-os --version` — confirms the CLI is installed and prints the package version (`workspace-os 2.0.0`).
- `workspace-os --help` — lists all subcommands.
- `workspace-os mission --help` — mission subcommands.
- `sqlite3 /home/taras/projects/.wsos/state.db` — direct read access to the database.
- `/home/taras/projects/.wsos/agent-runs/` — raw command logs.
- `/home/taras/projects/.project-state/<slug>/source-task.md` — what you wrote when you started this mission.
- `/home/taras/projects/.wsos/drift-acceptance.jsonl` — accepted-drift audit (one JSON object per line).
- `WORKSPACE-OS-v2.0.0-GA-CERTIFICATE.md` (in the cloned repo) — immutable historical certificate of what was released.
- `WORKSPACE-OS-v2.0.0-CANONICAL-CONTEXT.md` (in the cloned repo) — long-form canonical context, 17 sections.
- `/home/taras/projects/GOVERNANCE/WORKSPACE-CONSTITUTION.md` — the constitution Workspace OS implements. Article VII defines the 8-file Sprint Pattern. Article X defines how to amend it.