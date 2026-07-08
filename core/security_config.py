"""
Security configuration and middleware for Ziva.
Provides rate limiting, input sanitization, and API key authentication.
"""

import os
import time
import logging
import re
from collections import defaultdict
from functools import wraps
from typing import Optional, Callable

logger = logging.getLogger("Security")

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv("ZIVA_RATE_LIMIT", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("ZIVA_RATE_LIMIT_REQUESTS", "120"))
RATE_LIMIT_WINDOW = int(os.getenv("ZIVA_RATE_LIMIT_WINDOW", "60"))  # seconds

# API Key
API_KEY_ENABLED = os.getenv("ZIVA_API_KEY_ENABLED", "false").lower() == "true"
API_KEY = os.getenv("ZIVA_API_KEY", "")

# Input limits
MAX_INPUT_LENGTH = int(os.getenv("ZIVA_MAX_INPUT_LENGTH", "10000"))


class RateLimiter:
    """Simple in-memory rate limiter (token bucket)."""

    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS,
                 window: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window = window
        self._buckets: dict = defaultdict(list)

    def check(self, key: str) -> tuple:
        """
        Check if a request is allowed.
        Returns (allowed: bool, remaining: int, reset_time: int)
        """
        now = time.time()
        cutoff = now - self.window

        # Clean old entries
        self._buckets[key] = [t for t in self._buckets[key] if t > cutoff]

        if len(self._buckets[key]) >= self.max_requests:
            reset_time = int(self._buckets[key][0] + self.window)
            return False, 0, reset_time

        self._buckets[key].append(now)
        remaining = self.max_requests - len(self._buckets[key])
        return True, remaining, int(now + self.window)


_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _limiter


def sanitize_input(text: str) -> str:
    """Sanitize user input: strip control characters, limit length."""
    if not text:
        return ""

    # Remove null bytes and control characters (except newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Limit length
    if len(text) > MAX_INPUT_LENGTH:
        text = text[:MAX_INPUT_LENGTH]
        logger.warning(f"Input truncated to {MAX_INPUT_LENGTH} chars")

    return text.strip()


def validate_api_key(request_headers: dict) -> bool:
    """Validate API key from request headers."""
    if not API_KEY_ENABLED or not API_KEY:
        return True

    auth = request_headers.get("authorization", "")
    if auth.startswith("Bearer "):
        provided_key = auth[7:]
    else:
        provided_key = request_headers.get("x-api-key", "")

    return provided_key == API_KEY


def require_api_key(func: Callable) -> Callable:
    """Decorator to require API key on FastAPI endpoints."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from fastapi import Request, HTTPException

        request = None
        for arg in args:
            if hasattr(arg, "headers"):
                request = arg
                break
        if not request:
            for _, v in kwargs.items():
                if hasattr(v, "headers"):
                    request = v
                    break

        if request and not validate_api_key(dict(request.headers)):
            raise HTTPException(status_code=401, detail="Invalid API key")

        return await func(*args, **kwargs)
    return wrapper
