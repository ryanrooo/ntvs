"""Config-gated write-abuse protection (PR-3 / FR-035).

Lightweight, in-process protections for the open write endpoints:

* per-client (IP) sliding-window rate limit,
* a honeypot field check (a hidden field that only bots fill),
* a shared director token check for verification resolve.

All of it is OFF unless ``NTVS_WRITE_GATING`` is truthy, so local/demo behaves
like the prototype while production turns it on. When gating rejects a request,
callers must persist nothing and return a clear message.
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def gating_enabled() -> bool:
    return os.getenv("NTVS_WRITE_GATING", "").strip().lower() in {"1", "true", "on", "yes"}


def _window_seconds() -> int:
    return int(os.getenv("NTVS_RATE_WINDOW", "60"))


def _max_per_window() -> int:
    return int(os.getenv("NTVS_RATE_MAX", "5"))


def check_rate_limit(client_ip: str | None, *, now: float | None = None) -> bool:
    """Return True if the client may write, False if throttled. No-op when gating off."""
    if not gating_enabled():
        return True
    now = time.monotonic() if now is None else now
    cutoff = now - _window_seconds()
    key = client_ip or "unknown"
    with _lock:
        bucket = _hits[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= _max_per_window():
            return False
        bucket.append(now)
        return True


def is_honeypot_tripped(honeypot_value: str | None) -> bool:
    """A filled honeypot field means a bot. Never trips when gating is off."""
    if not gating_enabled():
        return False
    return bool(honeypot_value and str(honeypot_value).strip())


def verify_director_token(token: str | None) -> bool:
    """True when the shared director token matches (or gating is off)."""
    if not gating_enabled():
        return True
    expected = os.getenv("NTVS_DIRECTOR_TOKEN", "")
    return bool(expected) and token == expected


def reset() -> None:
    """Clear rate-limit state (tests)."""
    with _lock:
        _hits.clear()
