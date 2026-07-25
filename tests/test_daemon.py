"""Tests for workspace_os.daemon (Phase 1 stub) + R26 IPC contract tests."""

from __future__ import annotations

import pytest

from workspace_os import daemon


def test_is_daemon_available_false_in_phase_1():
    assert daemon.is_daemon_available() is False


def test_daemon_main_returns_zero():
    assert daemon.daemon_main() == 0


def test_daemon_main_prints_phase_message(capsys):
    daemon.daemon_main()
    captured = capsys.readouterr()
    assert "workspace-os daemon is not yet implemented" in captured.out
    assert "Phase 1" in captured.out


# --- R26 (WP-17) IPC contract tests ---


def test_ipc_contract_version_is_pinned():
    """R26: contract version is pinned so callers can detect breaking changes."""
    assert daemon.IPC_CONTRACT_VERSION == "0-stub"


def test_ipc_request_raises_when_daemon_unavailable():
    """R26 acceptance: any IPC call before daemon implementation MUST raise."""
    with pytest.raises(daemon.DaemonNotAvailableError) as exc_info:
        daemon.ipc_request({"op": "mission.list", "args": {}})
    assert "IPC unavailable" in str(exc_info.value)
    assert "0-stub" in str(exc_info.value)


def test_ipc_request_does_not_silently_fall_through():
    """R26: callers must NOT get a fake response from a missing daemon."""
    # If this test ever passes without raising, the stub is lying.
    try:
        daemon.ipc_request({"op": "anything"})
    except daemon.DaemonNotAvailableError:
        pass  # Expected
    else:
        pytest.fail("DaemonNotAvailableError was NOT raised — daemon stub is lying")


def test_daemon_not_available_error_is_runtime_error():
    """R26: DaemonNotAvailableError is catchable as RuntimeError."""
    assert issubclass(daemon.DaemonNotAvailableError, RuntimeError)


def test_is_daemon_available_returns_bool():
    """R26: feature flag contract is strictly bool, not Optional[int] etc."""
    result = daemon.is_daemon_available()
    assert isinstance(result, bool)
    assert result is False  # Phase 1 invariant
