"""Timeout helpers: every invariant receives its own bounded execution window."""
from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable, TypeVar

__all__ = ["DEFAULT_CHECK_TIMEOUT", "bounded_subprocess", "run_with_timeout"]

T = TypeVar("T")
DEFAULT_CHECK_TIMEOUT = 10.0


def run_with_timeout(function: Callable[..., T], *args, timeout: float = DEFAULT_CHECK_TIMEOUT, **kwargs) -> T:
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ws-validator")
    future = executor.submit(function, *args, **kwargs)
    try:
        return future.result(timeout=timeout)
    except FutureTimeout as exc:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise TimeoutError(f"check timed out after {timeout:g}s") from exc
    finally:
        if future.done():
            executor.shutdown(wait=True)


def bounded_subprocess(command: list[str], *, timeout: float = DEFAULT_CHECK_TIMEOUT, **kwargs) -> subprocess.CompletedProcess:
    """Run a subprocess with the same per-operation bound used by scans."""
    return subprocess.run(command, timeout=timeout, **kwargs)
