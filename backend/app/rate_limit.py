from collections import defaultdict
from time import monotonic

from fastapi import HTTPException, status

_attempts: dict[str, list[float]] = defaultdict(list)


def enforce_rate_limit(key: str, max_attempts: int, window_seconds: int) -> None:
    now = monotonic()
    recent = [timestamp for timestamp in _attempts[key] if now - timestamp < window_seconds]
    if len(recent) >= max_attempts:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts. Try again later")
    recent.append(now)
    _attempts[key] = recent
