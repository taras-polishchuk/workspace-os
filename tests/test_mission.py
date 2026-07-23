"""Tests for workspace_os.mission.Mission."""

from __future__ import annotations

from pathlib import Path

import pytest

from workspace_os.mission import (
    SPRINT_PATTERN_FILES,
    InvalidSlugError,
    Mission,
)


def test_create_writes_8_artifacts(tmp_path: Path):
    m = Mission.create("test-slug", workspace_root=tmp_path)
    for filename in SPRINT_PATTERN_FILES:
        assert (m.root_path / filename).exists(), f"missing {filename}"


def test_create_artifact_contents_non_empty(tmp_path: Path):
    m = Mission.create("test-slug", workspace_root=tmp_path)
    for filename in SPRINT_PATTERN_FILES:
        content = (m.root_path / filename).read_text(encoding="utf-8")
        assert len(content) > 0


def test_create_artifact_contents_have_slug(tmp_path: Path):
    m = Mission.create("test-slug", workspace_root=tmp_path)
    source = (m.root_path / "source-task.md").read_text(encoding="utf-8")
    assert "test-slug" in source
    progress = (m.root_path / "progress.md").read_text(encoding="utf-8")
    assert "test-slug" in progress


def test_create_under_default_state_root(tmp_path: Path):
    m = Mission.create("foo-bar", workspace_root=tmp_path)
    assert m.root_path == tmp_path / ".project-state" / "foo-bar"
    assert m.state_root == tmp_path / ".project-state"


def test_create_with_overwrite(tmp_path: Path):
    Mission.create("alpha", workspace_root=tmp_path)
    with pytest.raises(FileExistsError):
        Mission.create("alpha", workspace_root=tmp_path)
    m = Mission.create("alpha", workspace_root=tmp_path, overwrite=True)
    assert m.exists()


def test_create_with_custom_state_root(tmp_path: Path):
    custom = tmp_path / "custom-state"
    m = Mission.create("beta", workspace_root=tmp_path, state_root=custom)
    assert m.root_path == custom / "beta"


def test_invalid_slug_rejected(tmp_path: Path):
    with pytest.raises(InvalidSlugError):
        Mission.create("InvalidSlug", workspace_root=tmp_path)


def test_slug_starting_with_hyphen_rejected(tmp_path: Path):
    with pytest.raises(InvalidSlugError):
        Mission.create("-foo", workspace_root=tmp_path)


def test_slug_ending_with_hyphen_rejected(tmp_path: Path):
    with pytest.raises(InvalidSlugError):
        Mission.create("foo-", workspace_root=tmp_path)


def test_slug_too_long_rejected(tmp_path: Path):
    with pytest.raises(InvalidSlugError):
        Mission.create("a" * 65, workspace_root=tmp_path)


def test_slug_single_char_rejected(tmp_path: Path):
    with pytest.raises(InvalidSlugError):
        Mission.create("a", workspace_root=tmp_path)


def test_slug_with_underscore_rejected(tmp_path: Path):
    with pytest.raises(InvalidSlugError):
        Mission.create("foo_bar", workspace_root=tmp_path)


def test_slug_with_capital_rejected(tmp_path: Path):
    with pytest.raises(InvalidSlugError):
        Mission.create("Foo", workspace_root=tmp_path)


def test_exists(tmp_path: Path):
    m = Mission.create("exists-slug", workspace_root=tmp_path)
    assert m.exists()


def test_all_artifacts_present(tmp_path: Path):
    m = Mission.create("complete-slug", workspace_root=tmp_path)
    ok, missing = m.all_artifacts_present()
    assert ok is True
    assert missing == []


def test_all_artifacts_missing_after_delete(tmp_path: Path):
    m = Mission.create("partial-slug", workspace_root=tmp_path)
    (m.root_path / "progress.md").unlink()
    ok, missing = m.all_artifacts_present()
    assert ok is False
    assert "progress.md" in missing


def test_sprint_pattern_files_is_tuple_of_8():
    assert isinstance(SPRINT_PATTERN_FILES, tuple)
    assert len(SPRINT_PATTERN_FILES) == 8
    assert "source-task.md" in SPRINT_PATTERN_FILES
    assert "final-report.md" in SPRINT_PATTERN_FILES
