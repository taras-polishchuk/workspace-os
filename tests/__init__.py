"""Test suite for workspace-os Phase 1.

Target: ≥50 tests (blueprint §17.2). Tests use pytest and a temporary
workspace root via ``tmp_path``. The validator wrapper test invokes the
real ``bin/validate-workspace.sh`` against a synthetic workspace root
that contains a stub ``bin/`` directory.
"""
