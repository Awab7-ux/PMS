import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from flask import request

from backend.app.utils.responses import build_response

_rate_store: dict[str, list[float]] = defaultdict(list)


def rate_limit(max_requests: int = 10, window_seconds: int = 60, key_prefix: str = ""):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr or "unknown"
            key = f"{key_prefix}:{client_ip}"
            now = time.time()
            _rate_store[key] = [t for t in _rate_store[key] if now - t < window_seconds]
            if len(_rate_store[key]) >= max_requests:
                return build_response(False, {}, "Rate limit exceeded. Try again later.", {}, 429)
            _rate_store[key].append(now)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
