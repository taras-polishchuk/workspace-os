"""Mission directory creation per Article VII Sprint Pattern (8 artifacts).

The Sprint Pattern is the canonical 8-file mission structure (Constitution Article VII):

    .project-state/<slug>/
        source-task.md      (what + why)
        progress.md         (current state)
        decisions.md        (key choices with rationale)
        blockers.md         (open issues)
        artifacts.md        (produced files)
        environment.md      (system snapshot)
        execution-log.md    (timestamped actions)
        final-report.md     (closure)

Mission.create() materializes this structure with a uniform template header
in each file so downstream tools can find/replace the slug deterministically.
"""

from __future__ import annotations

import datetime
import os
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__all__ = [
    "SPRINT_PATTERN_FILES",
    "SLUG_RE",
    "Mission",
    "InvalidSlugError",
]

SPRINT_PATTERN_FILES = (
    "source-task.md",
    "progress.md",
    "decisions.md",
    "blockers.md",
    "artifacts.md",
    "environment.md",
    "execution-log.md",
    "final-report.md",
)

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")


class InvalidSlugError(ValueError):
    """Raised when a mission slug does not match the canonical pattern."""


def _validate_slug(slug: str) -> None:
    if not SLUG_RE.match(slug):
        raise InvalidSlugError(
            f"Invalid mission slug {slug!r}: must be lowercase alphanumeric with hyphens, "
            f"start/end alphanumeric, length 2..64."
        )


def _format_utc_timestamp(t: float) -> str:
    """Format a Unix timestamp as a UTC ISO-8601 string.

    Uses ``datetime`` rather than ``time.strftime`` so the UTC label is
    derived from ``timezone.utc`` rather than hardcoded — if a future
    maintainer swaps the source timezone, the label still reflects reality.
    """
    return datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def _format_utc_date(t: float) -> str:
    """Format a Unix timestamp as a UTC date string (YYYY-MM-DD)."""
    return datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc).strftime("%Y-%m-%d")


@dataclass
class Mission:
    """A workspace-os mission directory.

    Lifted from the de facto filesystem pattern of pre-Phase-1 mission
    directories; ``Mission.create`` makes the structure reproducible
    without shell ``mkdir -p`` + 8 ``touch`` calls.
    """

    slug: str
    root_path: Path
    state_root: Path
    workspace_root: Path

    @classmethod
    def create(
        cls,
        slug: str,
        workspace_root: Path,
        state_root: Optional[Path] = None,
        *,
        overwrite: bool = False,
    ) -> "Mission":
        """Create a new mission directory at the canonical location.

        Args:
            slug: Mission slug (e.g. ``workspace-os-v2-phase-1``).
            workspace_root: The workspace root (e.g. ``/home/taras/projects``).
            state_root: Override the default ``.project-state/`` parent.
            overwrite: If True and the directory exists, remove it first.

        Raises:
            InvalidSlugError: slug fails the canonical regex.
            FileExistsError: a mission with this slug already exists and
                ``overwrite`` is False.
            FileNotFoundError: the workspace root or state root does not
                exist or is not writable.
            NotADirectoryError: ``state_root`` is a regular file.
            OSError: the target path is a symbolic link (defence against
                ``shutil.rmtree`` symlink attacks).
        """
        _validate_slug(slug)
        if state_root is None:
            state_root = workspace_root / ".project-state"
        mission_dir = state_root / slug
        if mission_dir.is_symlink():
            # Refuse to operate on a symlinked mission directory. Either
            # the symlink was planted by another actor (TOCTOU) or by
            # a prior failed Mission.create. Either way, the safe move
            # is to refuse rather than risk following the symlink into
            # arbitrary filesystem territory.
            raise OSError(
                f"refusing to operate on symbolic link at {mission_dir}"
            )
        if mission_dir.exists():
            if not overwrite:
                raise FileExistsError(
                    f"Mission directory {mission_dir} already exists. "
                    f"Pass overwrite=True to replace, or use a different slug."
                )
            shutil.rmtree(mission_dir)
        if not mission_dir.parent.exists():
            mission_dir.parent.mkdir(parents=True, exist_ok=False)
        elif not mission_dir.parent.is_dir():
            raise NotADirectoryError(
                f"state root parent is not a directory: {mission_dir.parent}"
            )
        mission_dir.mkdir(parents=True, exist_ok=False)
        mission = cls(
            slug=slug,
            root_path=mission_dir,
            state_root=state_root,
            workspace_root=workspace_root,
        )
        mission._populate()
        return mission

    def _populate(self) -> None:
        """Create the 8 Sprint Pattern files with header templates."""
        ts = _format_utc_timestamp(time.time())
        date = _format_utc_date(time.time())
        headers = {
            "source-task.md": (
                f"# Source Task — {self.slug}\n\n"
                f"> **Mission slug:** `{self.slug}`\n"
                f"> **Created:** {ts}\n"
                f"> **Workspace root:** `{self.workspace_root}`\n\n"
                f"## What\n\n<TODO: what is this mission doing?>\n\n"
                f"## Why\n\n<TODO: why is it needed?>\n\n"
                f"## Acceptance criteria\n\n<TODO: bullet list>\n"
            ),
            "progress.md": (
                f"# Progress — {self.slug}\n\n"
                f"[STATUS: in progress]\n\n"
                f"## Completed\n\n- <TODO: bullet>\n\n"
                f"## Current\n\n- <TODO: bullet>\n\n"
                f"## Not yet started\n\n- <TODO: bullet>\n"
            ),
            "decisions.md": (
                f"# Decisions — {self.slug}\n\n"
                f"### {ts} · <TODO: short title>\n\n"
                f"- **Context:** <TODO>\n"
                f"- **Decision:** <TODO>\n"
                f"- **Rationale:** <TODO>\n"
                f"- **Alternatives considered:** <TODO>\n"
            ),
            "blockers.md": (
                f"# Blockers — {self.slug}\n\n"
                f"## Active\n\n"
                f"### {ts} · <TODO: short title>\n\n"
                f"- **Status:** <TODO>\n"
                f"- **What:** <TODO>\n"
                f"- **Why:** <TODO>\n"
                f"- **Impact:** <TODO>\n"
                f"- **Next:** <TODO>\n"
            ),
            "artifacts.md": (
                f"# Artifacts — {self.slug}\n\n"
                f"## Produced\n\n"
                f"- <TODO: path — role>\n"
            ),
            "environment.md": (
                f"# Environment — {self.slug}\n\n"
                f"| Field | Value |\n"
                f"|---|---|\n"
                f"| Date | {date} |\n"
                f"| Workspace root | `{self.workspace_root}` |\n"
                f"| Mission root | `{self.root_path}` |\n"
            ),
            "execution-log.md": (
                f"# Execution Log — {self.slug}\n\n"
                f"[{ts}] [bootstrap] Mission directory created at `{self.root_path}`.\n"
            ),
            "final-report.md": (
                f"# Final Report — {self.slug}\n\n"
                f"(To be written at mission close.)\n"
            ),
        }
        for filename, content in headers.items():
            target = self.root_path / filename
            # Mission files are operator-private by default.
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
            except BaseException:
                # Best-effort cleanup if write fails mid-stream.
                try:
                    os.unlink(target)
                except OSError:
                    pass
                raise

    def exists(self) -> bool:
        return self.root_path.exists() and self.root_path.is_dir()

    def all_artifacts_present(self) -> tuple[bool, list[str]]:
        """Return (ok, missing). ok=True iff all 8 files exist and are non-empty."""
        missing: list[str] = []
        for filename in SPRINT_PATTERN_FILES:
            p = self.root_path / filename
            if not p.exists() or p.stat().st_size == 0:
                missing.append(filename)
        return (len(missing) == 0, missing)
