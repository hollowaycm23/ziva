"""
FastAPI middleware for security: rate limiting, input validation, headers.
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.security_config import (
    get_rate_limiter, sanitize_input, validate_api_key,
    RATE_LIMIT_ENABLED, API_KEY_ENABLED, MAX_INPUT_LENGTH
)

logger = logging.getLogger("SecurityMiddleware")


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies:
    1. Rate limiting per IP
    2. API key validation (OPTIONS requests excluded)
    3. Security headers
    4. Request logging
    """

    async def dispatch(self, request: Request, call_next):
        # Skip security for static files and OPTIONS
        if request.method == "OPTIONS":
            return await call_next(request)
        if request.url.path.startswith("/dashboard") or request.url.path.startswith("/static"):
            return await call_next(request)
        if request.url.path in ("/health", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # Rate limiting
        if RATE_LIMIT_ENABLED:
            limiter = get_rate_limiter()
            allowed, remaining, reset_time = limiter.check(client_ip)
            if not allowed:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return Response(
                    content='{"error": "Rate limit exceeded", "retry_after": ' + str(reset_time - int(time.time())) + '}',
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "X-RateLimit-Limit": str(limiter.max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(reset_time - int(time.time())),
                    }
                )

        # API key validation
        if API_KEY_ENABLED and request.url.path.startswith("/v1/"):
            if not validate_api_key(dict(request.headers)):
                logger.warning(f"Invalid API key from {client_ip}")
                return Response(
                    content='{"error": "Invalid API key"}',
                    status_code=401,
                    media_type="application/json",
                )

        # Process request
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"

        return response
