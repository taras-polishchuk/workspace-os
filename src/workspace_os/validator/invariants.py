"""Workspace OS validator invariants ported from the v1.1 shell implementation."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

__all__ = [
    "CheckResult",
    "Check",
    "INVARIANTS",
    "SPRINT_PATTERN_FILES_FOR_PRESERVE",
    "check_amendments",
    "check_authority_uniqueness",
    "check_bootstrap_coherence",
    "check_git_identity_overrides",
    "check_governance_references",
    "check_identity_drift",
    "check_mission_state_integrity",
    "check_path_integrity",
    "check_project_state_root",
    "check_release_policy",
    "check_symlink_integrity",
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    message: str
    details: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


Check = Callable[[Path], CheckResult | list[CheckResult]]
DISPLAY_MARKERS = ("(symlink)", "(this file)", "(legacy)", "(renamed", "(moved", "->", "  (")
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".svelte-kit", ".cache", ".vercel", ".next", "__pycache__", "backups"}

# Canonical 8-artifact Sprint Pattern (per Article VII). Re-exposed here
# so the validator's R14 PRESERVE emit step can detect the
# `sprint_pattern_incomplete` condition without importing mission.py.
SPRINT_PATTERN_FILES_FOR_PRESERVE = (
    "source-task.md", "progress.md", "decisions.md", "blockers.md",
    "artifacts.md", "environment.md", "execution-log.md", "final-report.md",
)


def _result(name: str, ok: bool, message: str, details: Iterable[str] = ()) -> CheckResult:
    return CheckResult(name, "PASS" if ok else "FAIL", message, tuple(details))


def _walk(root: Path):
    yield root
    if not root.is_dir():
        return
    try:
        for child in root.iterdir():
            if child.name in SKIP_DIRS:
                continue
            if child.is_dir() and not child.is_symlink():
                yield from _walk(child)
            else:
                yield child
    except (PermissionError, FileNotFoundError, OSError):
        return


def check_path_integrity(workspace: Path) -> CheckResult:
    index = workspace / "CONTEXT" / "workspace-index.json"
    if not index.is_file():
        return _result("path-integrity", False, f"workspace-index.json not found at {index}")
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _result("path-integrity", False, f"workspace-index.json unreadable: {exc}")
    missing: list[str] = []
    def collect(value):
        if isinstance(value, dict):
            if "phantom" in str(value.get("reason", "")).lower():
                return
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, str) and value.startswith("/home/taras/"):
            if not any(marker in value for marker in DISPLAY_MARKERS) and not Path(value).exists():
                missing.append(value)
    collect(data)
    if missing:
        return _result("path-integrity", False, f"workspace-index.json: {len(missing)} missing paths", (f"MISSING: {p}" for p in missing))
    return _result("path-integrity", True, "workspace-index.json: all load-bearing paths exist")


def check_bootstrap_coherence(workspace: Path) -> list[CheckResult]:
    paths = [workspace / "IDENTITY.md", workspace / "ARCHITECTURE.md", workspace / "GOVERNANCE" / "BOOTSTRAP.md", workspace / "CONTEXT" / "workspace-index.json"]
    return [_result("bootstrap", path.exists(), f"bootstrap: {path.name} resolves" if path.exists() else f"bootstrap: {path} missing") for path in paths]


def _authority_count(workspace: Path, filename: str) -> int:
    return sum(1 for path in _walk(workspace) if path.name == filename and path.is_file())


def check_authority_uniqueness(workspace: Path) -> list[CheckResult]:
    results = []
    for filename in ("EngineeringIdentity.md", "system-graph.md", "AGENT-REGISTRY.md"):
        count = _authority_count(workspace, filename)
        message = f"authority: exactly 1 {filename}" if count == 1 else f"authority: {count} {filename} files (expected 1)"
        results.append(_result("authority", count == 1, message))
    return results


def check_symlink_integrity(workspace: Path) -> list[CheckResult]:
    results = []
    for name in ("IDENTITY.md", "ARCHITECTURE.md"):
        path = workspace / name
        if not path.is_symlink():
            results.append(_result("symlink", False, f"symlink: {name} is not a symlink"))
            continue
        target = os.readlink(path)
        results.append(_result("symlink", path.exists(), f"symlink: {name} -> {target} ({'resolves' if path.exists() else 'broken'})"))
    return results


def check_identity_drift(workspace: Path) -> CheckResult:
    governance, context = workspace / "GOVERNANCE", workspace / "CONTEXT"
    audit = governance / "IDENTITY-AUTHORITY-MAP.md"
    files = list(governance.glob("*.md")) + list(context.glob("*.md")) + [context / "workspace-index.json"]
    patterns = [re.compile(r"\bI am (an?|the) [A-Z][^.]*(engineer|developer|architect|founder)", re.I), re.compile(r"\bTaras (Polishchuk is|is) (an?|the) [A-Z][^.]*(engineer|developer|architect|founder)", re.I), re.compile(r"engineering identity:\s+\S", re.I), re.compile(r"\bcore competency:\s+\S", re.I), re.compile(r"\bI am Taras Polishchuk", re.I)]
    hits = []
    for path in files:
        if path == audit or not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if line.startswith("    ") or line.lstrip().startswith("```"):
                continue
            if any(pattern.search(line) for pattern in patterns):
                hits.append(f"HIT: {path}:{lineno}: {line.strip()[:120]}")
    message = "drift: no identity-statement patterns in canonical (non-audit) governance/CONTEXT" if not hits else f"drift: {len(hits)} identity-statement patterns in canonical files (redefine-id risk)"
    return _result("drift", not hits, message, hits)


def check_amendments(workspace: Path) -> CheckResult:
    ok = (workspace / "GOVERNANCE" / "AMENDMENTS.md").is_file()
    return _result("amendments", ok, f"amendments: GOVERNANCE/AMENDMENTS.md {'exists (Article X)' if ok else 'missing (Article X)'}")


def check_release_policy(workspace: Path) -> CheckResult:
    ok = (workspace / "GOVERNANCE" / "RELEASE-POLICY.md").is_file()
    return _result("release-policy", ok, f"release-policy: GOVERNANCE/RELEASE-POLICY.md {'exists' if ok else 'missing'}")


def check_governance_references(workspace: Path) -> CheckResult:
    governance = workspace / "GOVERNANCE"
    audit = governance / "IDENTITY-AUTHORITY-MAP.md"
    extensions = (".md", ".json", ".sh", ".py", ".ts", ".js", ".yaml", ".yml", ".txt", "/")
    historical = {"AGENT-REGISTRY.md", "CONVENTIONS.md", "executive-summary.md", "hermes-bootstrap.md", "user-operating-profile.md", "high-leverage-assets.md", "workspace-index.json"}
    missing, checked = [], set()
    for doc in sorted(governance.glob("*.md")):
        if doc == audit:
            continue
        fenced = False
        for line in doc.read_text(errors="replace").splitlines():
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced or line.startswith("    "):
                continue
            for match in re.finditer(r"`(/home/taras/projects/[^`]+)`", line):
                value = match.group(1).rstrip(".,;:")
                if value in checked or not value.endswith(extensions) or any(c in value for c in "*?[$"):
                    continue
                checked.add(value)
                if not Path(value).exists() and Path(value).name not in historical:
                    missing.append(value)
    message = "governance: every load-bearing path reference in non-audit docs resolves" if not missing else f"governance: {len(missing)} load-bearing path references do not resolve"
    return _result("governance-references", not missing, message, (f"MISSING: {p}" for p in missing))


def check_git_identity_overrides(workspace: Path) -> CheckResult:
    # WP-08/R13 scope: scan only inside the workspace (skills/scripts/etc. of this workspace).
    # Scanning the operator's ~/.hermes/ makes the result nondeterministic w.r.t. workspace choice
    # (false FAILs on ad-hoc fixtures) — preserve that as a separate audit task, not a validator invariant.
    roots = [workspace / "INSTRUCTIONS", workspace / "bin", workspace / "scripts"]
    extensions = {".md", ".sh", ".bash", ".py", ".js", ".ts", ".mjs", ".cjs", ".rb", ".yaml", ".yml", ".json", ".toml", ".txt", ".prompt", ".tmpl", ""}
    patterns = [(re.compile(r"git\s+-c\s+user\.name\b"), "git -c user.name"), (re.compile(r"git\s+-c\s+user\.email\b"), "git -c user.email"), (re.compile(r"\bgit\s+config\s+user\.name\b"), "git config user.name"), (re.compile(r"\bgit\s+config\s+user\.email\b"), "git config user.email"), (re.compile(r"\bGIT_AUTHOR_NAME\b"), "GIT_AUTHOR_NAME"), (re.compile(r"\bGIT_AUTHOR_EMAIL\b"), "GIT_AUTHOR_EMAIL"), (re.compile(r"\bGIT_COMMITTER_NAME\b"), "GIT_COMMITTER_NAME"), (re.compile(r"\bGIT_COMMITTER_EMAIL\b"), "GIT_COMMITTER_EMAIL")]
    hits = []
    for root in roots:
        for path in _walk(root) if root.exists() else ():
            if not path.is_file() or path.suffix.lower() not in extensions or path.name == "validate-workspace.sh":
                continue
            try:
                lines = path.read_text(errors="replace").splitlines()
            except OSError:
                continue
            fenced = False
            for lineno, line in enumerate(lines, 1):
                stripped = line.lstrip()
                if stripped.startswith(("```", "~~~")):
                    fenced = not fenced
                    continue
                if fenced or line.startswith(("    ", "\t")) or stripped.startswith("echo ") or " echo " in f" {stripped}":
                    continue
                for pattern, label in patterns:
                    match = pattern.search(line)
                    if match and not (match.start() > 0 and line[match.start() - 1] == "`"):
                        hits.append(f"HIT: {path}:{lineno}: [{label}] {stripped[:120]}")
                        break
    message = "git-identity: no override patterns in reusable automation artifacts (Article XI)" if not hits else f"git-identity: {len(hits)} override-pattern hits in reusable automation artifacts (Article XI violation)"
    return _result("git-identity", not hits, message, hits)


def check_project_state_root(workspace: Path) -> CheckResult:
    canonical = (workspace / ".project-state").resolve()
    stray = []
    for path in _walk(workspace):
        if not path.is_dir():
            continue
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved == canonical or canonical in resolved.parents:
            continue
        if path.name in (".project-state", "project-state"):
            stray.append(str(path))
    typo = Path.home() / ".project-state"
    if typo.is_dir():
        stray.append(f"{typo}  [historical typo; canonical root is {canonical}]")
    message = f"project-state-root: only canonical root {canonical}/ exists" if not stray else f"project-state-root: {len(stray)} stray .project-state directory(ies) outside canonical root"
    return _result("project-state-root", not stray, message, (f"STRAY: {p}" for p in stray))


def check_mission_state_integrity(workspace: Path) -> list[CheckResult]:
    root = workspace / ".project-state"
    failures = []
    if root.is_dir():
        for mission in sorted(path for path in root.iterdir() if path.is_dir()):
            for required in ("source-task.md", "progress.md"):
                if not (mission / required).is_file():
                    failures.append(_result("mission-state-integrity", False, f"mission-state-integrity: {mission} missing {required}"))
            source = mission / "source-task.md"
            if source.is_file() and source.stat().st_size == 0:
                failures.append(_result("mission-state-integrity", False, f"mission-state-integrity: {source} is empty (no intent declared)"))
            if source.is_file() and "RECORD OF RECONSTRUCTION" in source.read_text(errors="replace"):
                decisions = mission / "decisions.md"
                if not decisions.is_file() or "Reconstruction rationale" not in decisions.read_text(errors="replace"):
                    failures.append(_result("mission-state-integrity", False, f"mission-state-integrity: {mission} has RECORD OF RECONSTRUCTION but no Reconstruction rationale in decisions.md"))
    return failures or [_result("mission-state-integrity", True, "mission-state-integrity: all sprint dirs have required structural artifacts")]


INVARIANTS: tuple[Check, ...] = (
    check_path_integrity, check_bootstrap_coherence, check_authority_uniqueness,
    check_symlink_integrity, check_identity_drift, check_amendments,
    check_release_policy, check_governance_references, check_git_identity_overrides,
    check_project_state_root, check_mission_state_integrity,
)
