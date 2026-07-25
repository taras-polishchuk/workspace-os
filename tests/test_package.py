"""Package-level tests."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import yaml

import workspace_os
from workspace_os.policy import load_policy
from workspace_os.validate import DEFAULT_POLICY_RESOURCE

ROOT = Path(__file__).resolve().parents[1]


def test_ci_invokes_canonical_release_verifier():
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    jobs = workflow["jobs"]
    steps = jobs["release-verify"]["steps"]
    commands = [step.get("run", "") for step in steps]
    assert "python scripts/release_verify.py" in commands


def test_release_verifier_supports_clean_clone_mode():
    source = (ROOT / "scripts" / "release_verify.py").read_text(encoding="utf-8")
    assert 'parser.add_argument("--clean-clone", action="store_true")' in source
    assert '"clone", "--quiet", "--no-local"' in source


def test_version_is_2_0_0():
    assert workspace_os.__version__ == "2.0.0"


def test_phase_is_v2_0_rc():
    assert workspace_os.__phase__ == "v2.0-rc"


def test_public_api_exports():
    assert hasattr(workspace_os, "WorkspaceState")
    assert hasattr(workspace_os, "Mission")
    assert hasattr(workspace_os, "SPRINT_PATTERN_FILES")
    assert hasattr(workspace_os, "run_validator")
    assert hasattr(workspace_os, "ValidatorVerdict")


def test_default_policy_is_a_packaged_resource():
    resource = files("workspace_os").joinpath("policy.yaml")
    assert resource == DEFAULT_POLICY_RESOURCE
    assert resource.is_file()
    assert "schema_version: 1" in resource.read_text(encoding="utf-8")


def test_repository_policy_matches_packaged_policy():
    repository_policy = Path(__file__).resolve().parents[1] / "policy.yaml"
    assert repository_policy.read_bytes() == DEFAULT_POLICY_RESOURCE.read_bytes()
    assert load_policy(DEFAULT_POLICY_RESOURCE).schema_version == 1
