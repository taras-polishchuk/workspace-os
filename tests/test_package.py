"""Package-level tests."""

from __future__ import annotations

import workspace_os


def test_version_is_string():
    assert isinstance(workspace_os.__version__, str)
    assert len(workspace_os.__version__) > 0


def test_phase_is_v0_5_rc():
    # __phase__ is the v0.5-rc release tag, not the original "1" phase tag.
    assert workspace_os.__phase__ == "v0.5-rc"


def test_public_api_exports():
    assert hasattr(workspace_os, "WorkspaceState")
    assert hasattr(workspace_os, "Mission")
    assert hasattr(workspace_os, "SPRINT_PATTERN_FILES")
    assert hasattr(workspace_os, "run_validator")
    assert hasattr(workspace_os, "ValidatorVerdict")
