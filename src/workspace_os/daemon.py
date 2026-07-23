"""Minimal local daemon entry stub.

Phase 1 (blueprint §17.2) is CLI-only. The daemon entry point exists as
a stub for Phase 5+ where the kernel evolves into a long-lived process
that owns the SQLite state and exposes a unix-socket API.

This module currently exposes:
    - ``is_daemon_available()`` — feature flag (always False in Phase 1)
    - ``daemon_main()`` — placeholder that exits with a clear message

It is NOT registered as a CLI subcommand in Phase 1.

WP-17 (R26) addition — IPC contract + honest-stub semantics:
- ``IPC_CONTRACT_VERSION = "0-stub"`` — pinned contract version
- ``DaemonNotAvailableError`` — explicit exception when caller attempts
  to use IPC before the daemon is implemented
- ``is_daemon_available()`` MUST stay False in Phase 1
- Any caller that hits daemon IPC must catch ``DaemonNotAvailableError``
  and either fall back to CLI or fail loud — never silently succeed.
"""

from __future__ import annotations


__all__ = [
    "IPC_CONTRACT_VERSION",
    "DaemonNotAvailableError",
    "daemon_main",
    "ipc_request",
    "is_daemon_available",
]


# IPC contract version. Bump ONLY when the socket protocol changes.
IPC_CONTRACT_VERSION = "0-stub"


class DaemonNotAvailableError(RuntimeError):
    """Raised when a caller attempts to use daemon IPC before the daemon is implemented.

    Per R26 acceptance: callers must NOT silently fall through to CLI
    when they thought they were using IPC. Either catch and explicitly
    fall back, or propagate.
    """


def is_daemon_available() -> bool:
    """Phase 1 ships CLI-only; daemon is Phase 5+ per blueprint §17.2."""
    return False


def daemon_main() -> int:
    """Stub entry point. Returns 0 with an informational message.

    Future phases will replace this with a real daemon that:
        - Owns the SQLite write lock.
        - Exposes a unix-socket API for agent runs.
        - Implements cold-boot recovery per blueprint §26.
    """
    print(
        "workspace-os daemon is not yet implemented (Phase 1, blueprint §17.2). "
        "Use the CLI subcommands (init, mission, validate, agent run) for now."
    )
    return 0


def ipc_request(payload: dict) -> dict:
    """Send a request to the daemon over its IPC channel.

    Stub behavior: always raises ``DaemonNotAvailableError``.

    When the daemon is implemented, this function will:
        - Open a unix socket to /tmp/workspace-os-daemon.sock (or $WSOS_DAEMON_SOCK)
        - Send JSON-encoded payload + newline terminator
        - Read JSON response (with timeout)
        - Validate IPC_CONTRACT_VERSION matches
        - Return response dict

    Until then, callers MUST handle ``DaemonNotAvailableError`` explicitly.
    """
    raise DaemonNotAvailableError(
        f"daemon IPC unavailable (contract version {IPC_CONTRACT_VERSION}); "
        "use the CLI subcommands (init, mission, validate, agent run) instead."
    )