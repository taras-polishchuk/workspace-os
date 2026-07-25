"""Command-line entry point for ``python3 -m workspace_os.validator``."""

from __future__ import annotations

import argparse
import sys

from . import run_validation

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Workspace OS filesystem invariants")
    parser.add_argument(
        "--workspace",
        default=None,
        help="workspace root (default: $WORKSPACE, $WORKSPACE_OS_ROOT, or $PWD)",
    )
    # M-12 fix: validate --check-timeout > 0
    parser.add_argument(
        "--check-timeout",
        type=float,
        default=10.0,
        help="per-invariant timeout in seconds (must be > 0)",
    )
    args = parser.parse_args(argv)
    if args.check_timeout <= 0:
        print(f"error: --check-timeout must be > 0 (got {args.check_timeout})", file=sys.stderr)
        return 2
    _, output, exit_code = run_validation(args.workspace, check_timeout=args.check_timeout)
    sys.stdout.write(output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
