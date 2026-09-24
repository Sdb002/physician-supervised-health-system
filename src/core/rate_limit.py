"""In-memory failed-login throttle, keyed by email.

Stdlib-only (matches src/core/security.py's constraints on this machine — see
README). Per-process, in-memory: fine for the single-worker dev/demo
deployment this app targets; a multi-worker production deployment would need
a shared store (e.g. the database) instead.
"""

import time
from collections import defaultdict, deque

_WINDOW_SECONDS = 15 * 60
_MAX_FAILURES = 10

_failures: dict[str, deque] = defaultdict(deque)


def _prune(key: str) -> deque:
    attempts = _failures[key]
    cutoff = time.time() - _WINDOW_SECONDS
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    return attempts


def login_allowed(key: str) -> bool:
    return len(_prune(key)) < _MAX_FAILURES


def record_login_failure(key: str) -> None:
    _prune(key).append(time.time())


def record_login_success(key: str) -> None:
    _failures.pop(key, None)
