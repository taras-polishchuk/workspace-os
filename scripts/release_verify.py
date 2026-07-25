#!/usr/bin/env python3
"""Run the canonical Workspace OS release-candidate gates."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def python_tool(name: str) -> list[str]:
    return [sys.executable, "-m", name]


def verify_archive_contents(dist: Path) -> tuple[Path, Path]:
    wheels = sorted(dist.glob("workspace_os-*.whl"))
    sdists = sorted(dist.glob("workspace_os-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(f"expected one wheel and one sdist, found {wheels=} {sdists=}")
    wheel, sdist = wheels[0], sdists[0]
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = archive.namelist()
    with tarfile.open(sdist) as archive:
        sdist_names = archive.getnames()
    if "workspace_os/policy.yaml" not in wheel_names:
        raise RuntimeError("wheel omits workspace_os/policy.yaml")
    if not any(name.endswith("/src/workspace_os/policy.yaml") for name in sdist_names):
        raise RuntimeError("sdist omits src/workspace_os/policy.yaml")
    return wheel, sdist


def create_venv(path: Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(path)
    return path / "bin" / "python"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean-clone", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    if args.clean_clone:
        with tempfile.TemporaryDirectory(prefix="workspace-os-clone-") as raw:
            clone = Path(raw) / "repo"
            run(["git", "clone", "--quiet", "--no-local", str(ROOT), str(clone)])
            command = [sys.executable, str(clone / "scripts" / "release_verify.py")]
            if args.output_dir is not None:
                command += ["--output-dir", str(args.output_dir.resolve())]
            run(command, cwd=clone)
        return 0

    run([*python_tool("ruff"), "check", "src", "tests"])
    run([*python_tool("ruff"), "format", "--check", "src", "tests"])
    run([*python_tool("mypy"), "src"])
    run([*python_tool("bandit"), "-q", "-c", "pyproject.toml", "-r", "src"])
    run([sys.executable, "-m", "pytest", "-q"])
    with tempfile.TemporaryDirectory(prefix="workspace-os-audit-") as raw:
        requirements = Path(raw) / "requirements.txt"
        requirements.write_text("PyYAML>=6.0\n", encoding="utf-8")
        run([*python_tool("pip_audit"), "-r", str(requirements)])

    if args.output_dir is None:
        dist = ROOT / "dist"
        if dist.exists():
            shutil.rmtree(dist)
    else:
        dist = args.output_dir.resolve()
        dist.mkdir(parents=True, exist_ok=True)
        for artifact in dist.glob("workspace_os-*"):
            artifact.unlink()
    run([sys.executable, "-m", "build", "--outdir", str(dist)])
    wheel, sdist = verify_archive_contents(dist)

    with tempfile.TemporaryDirectory(prefix="workspace-os-install-") as raw:
        install_root = Path(raw)
        smoke_python = create_venv(install_root / "venv")
        run([str(smoke_python), "-m", "pip", "install", "--quiet", str(wheel)])
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        code = (
            "from importlib.resources import files; "
            "from workspace_os.policy import load_policy; "
            "from workspace_os.validate import DEFAULT_POLICY_RESOURCE; "
            "assert files('workspace_os').joinpath('policy.yaml').is_file(); "
            "assert load_policy(DEFAULT_POLICY_RESOURCE).schema_version == 1"
        )
        run([str(smoke_python), "-I", "-c", code], cwd=install_root, env=env)
        run(
            [str(smoke_python), "-I", "-m", "workspace_os.cli", "--version"],
            cwd=install_root,
            env=env,
        )
        run(
            [str(smoke_python), "-I", "-m", "workspace_os.validator", "--help"],
            cwd=install_root,
            env=env,
        )

    print(f"RELEASE VERIFY PASS: {wheel.name} {sdist.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
