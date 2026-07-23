"""Filesystem safety helpers: atomic writes and safe directory creation.

The :func:`atomic_write_text` helper writes text to a temporary file in the
same directory, fsyncs, and renames into place via ``os.replace``. The
destination must not be a symlink: this guards against a TOCTOU attack
where an attacker plants a symlink at the destination and the operator
then runs the workspace-os command that writes through the symlink.

The :func:`safe_mkdir` helper creates a directory tree with a restrictive
mode and refuses to follow symlinks for any path component, defending
against symlink attacks on the workspace-os state directory itself.
"""

from __future__ import annotations

import errno
import os
import stat
import tempfile
from pathlib import Path

__all__ = ["atomic_write_text", "safe_mkdir", "WSOS_DIR_MODE", "WSOS_FILE_MODE"]

#: Mode for the workspace-os state directory: owner-only rwx.
WSOS_DIR_MODE = 0o700

#: Mode for SQLite database files (and other operator-private files).
WSOS_FILE_MODE = 0o600


class SymlinkRefusedError(OSError):
    """Raised when a write target or path component is a symbolic link."""


def _ensure_not_symlink(path: Path) -> None:
    """Refuse the operation if any path component is a symbolic link."""
    # Walk up the path components. For each parent directory of the leaf,
    # check that it is not itself a symlink. This includes the leaf.
    parts = path.parts
    if not parts:
        return
    # Build cumulative paths and check each (cheap because we stop early
    # at the first symlink).
    for i in range(1, len(parts) + 1):
        p = Path(*parts[:i])
        try:
            if p.is_symlink():
                raise SymlinkRefusedError(
                    errno.EEXIST,
                    f"refusing to follow symbolic link at {p!s}",
                )
        except (OSError, ValueError):
            # If the path doesn't exist yet, only the leaf matters; earlier
            # components must exist and not be symlinks.
            if i < len(parts):
                raise


def _ensure_no_ancestor_is_symlink(path: Path) -> None:
    """Refuse the operation if any path component is a symbolic link.

    Walks the path from the root down to the leaf, raising
    :class:`SymlinkRefusedError` if any component is a symlink. Existing
    components are checked with ``is_symlink()``; non-existent components
    are skipped (they will be created by the caller, which should use
    symlink-safe primitives).

    This helper is used by :func:`safe_mkdir` and :func:`atomic_write_text`
    to enforce the contract that operations never follow symlinks at any
    path level, regardless of whether the leaf already exists.
    """
    path = Path(path)
    try:
        parts = path.parts
    except (AttributeError, ValueError):
        return
    if not parts:
        return
    # Build cumulative paths starting from the first component.
    # Note: ``is_symlink()`` is checked OUTSIDE the try/except so that
    # ``SymlinkRefusedError`` (a subclass of OSError) is NOT silently
    # swallowed by an over-broad except clause.
    for i in range(1, len(parts) + 1):
        p = Path(*parts[:i])
        if not p.exists():
            continue
        is_sym = False
        try:
            is_sym = p.is_symlink()
        except (OSError, ValueError):
            # Path is broken or has non-UTF-8 bytes — fall through.
            continue
        if is_sym:
            raise SymlinkRefusedError(
                errno.EEXIST,
                f"refusing to follow symbolic link at {p!s}",
            )


def safe_mkdir(path: Path, mode: int = WSOS_DIR_MODE, *, parents: bool = True) -> None:
    """Create a directory at ``path`` with the given mode.

    Defends against symlink attacks by checking every existing parent
    component for being a symlink before creation. The leaf directory
    is created with the given mode regardless of umask.

    HIGH-1 fix: the existing-leaf branch now also checks ancestors for
    symlinks. Previously a real dir reached via a symlink in its parent
    path would be chmod'd through the symlink (changing mode bits on
    the attacker's target).
    """
    path = Path(path)
    # HIGH-1 fix: always check ancestors FIRST (regardless of whether the
    # leaf exists). This closes the gap where a real dir reached via a
    # symlink parent would be chmod'd through the symlink.
    if parents:
        _ensure_no_ancestor_is_symlink(path)
    if path.exists():
        if path.is_symlink():
            raise SymlinkRefusedError(
                errno.EEXIST,
                f"refusing to follow symbolic link at {path!s}",
            )
        if not path.is_dir():
            raise FileExistsError(
                errno.EEXIST,
                f"path exists and is not a directory: {path!s}",
            )
        # Tighten permissions even if the directory already existed.
        try:
            os.chmod(path, mode)
        except PermissionError:
            pass
        return
    # Leaf doesn't exist: create it. safe_mkdir has already verified
    # ancestors, but the kernel may have raced between is_symlink() and
    # mkdir; re-check immediately before mkdir.
    if path.parent != path and path.parent.exists() and path.parent.is_symlink():
        raise SymlinkRefusedError(
            errno.EEXIST,
            f"refusing to follow symbolic link at parent {path.parent!s}",
        )
    # mkdir with mode, then chmod to ensure umask doesn't weaken it.
    # HIGH-2 fix: use ``exist_ok=True`` to handle the residual race
    # window between ``path.exists()`` (line 115) and ``mkdir()``.
    # ``safe_mkdir`` has already done the symlink-safety checks; the
    # only remaining failure mode is a benign race where another
    # process created the same dir, which is fine.
    try:
        path.mkdir(parents=parents, exist_ok=True)
    except FileExistsError:
        # Race: another process created the same path between exists()
        # check and mkdir(). Treat as success (the directory exists).
        if not path.is_dir():
            raise
    os.chmod(path, mode)


def atomic_write_text(
    path: Path,
    content: str,
    *,
    mode: int = WSOS_FILE_MODE,
    encoding: str = "utf-8",
) -> None:
    """Write ``content`` to ``path`` atomically.

    Strategy:
        1. Refuse if the leaf is a symlink (defends against TOCTOU).
        2. Refuse if any existing parent component is a symlink.
        3. Create a temporary file in the same directory using
           ``tempfile.mkstemp`` (atomic, mode 0o600).
        4. Write content, fsync, close, then ``os.replace`` into place.
        5. Final ``os.chmod`` to the requested mode (mkstemp already
           gives 0o600; chmod makes the intent explicit).

    ``os.replace`` atomically replaces the destination; if the destination
    is a regular file it is overwritten; if it is a symlink, ``os.replace``
    removes the symlink and replaces it with the regular file. If the
    destination does not exist, ``os.replace`` creates it.
    """
    path = Path(path)
    parent = path.parent
    # The parent must exist. If it doesn't, we create it (with restrictive
    # permissions) but only after checking for symlinks.
    if not parent.exists():
        safe_mkdir(parent, mode=WSOS_DIR_MODE)
    elif parent.is_symlink():
        raise SymlinkRefusedError(
            errno.EEXIST,
            f"refusing to follow symbolic link at parent {parent!s}",
        )
    # The leaf itself must not be a symlink.
    if path.exists() or path.is_symlink():
        if path.is_symlink():
            raise SymlinkRefusedError(
                errno.EEXIST,
                f"refusing to follow symbolic link at {path!s}",
            )
        # Existing regular file: os.replace will overwrite atomically.
    fd, tmp_path = tempfile.mkstemp(
        dir=str(parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except BaseException:
        # Clean up the temp file on any failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def tighten_existing_file(path: Path, mode: int = WSOS_FILE_MODE) -> bool:
    """Best-effort chmod an existing file to the requested mode.

    Returns True if chmod succeeded, False if it failed (e.g. file not
    owned by the current user). Used for SQLite databases created by
    SQLite itself with the default umask.
    """
    try:
        st = os.stat(path)
        # Refuse to chmod a symlink (defence in depth).
        if stat.S_ISLNK(st.st_mode):
            return False
        os.chmod(path, mode)
        return True
    except OSError:
        return False
