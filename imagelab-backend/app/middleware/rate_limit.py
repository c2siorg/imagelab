import asyncio
import logging
import time

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_middleware_instances: list["ShareRateLimitMiddleware"] = []


class ShareRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = {}  # ip -> list of timestamps
        self.lock = asyncio.Lock()
        self.request_count = 0
        _middleware_instances.append(self)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/share"):
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            async with self.lock:
                timestamps = self.requests.get(ip, [])

                # Keep only timestamps in the last 1.0 seconds
                timestamps = [t for t in timestamps if now - t < 1.0]

                if len(timestamps) >= 30:
                    logger.warning("Rate limit exceeded for IP %s on path %s", ip, path)
                    self.requests[ip] = timestamps
                    return Response(
                        content='{"detail": "Too many requests. Please try again later."}',
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        media_type="application/json",
                    )

                timestamps.append(now)
                self.requests[ip] = timestamps

                # Clean up memory occasionally
                self.request_count += 1
                if self.request_count % 100 == 0:
                    expired_ips = [k for k, v in self.requests.items() if not v or now - v[-1] >= 1.0]
                    for k in expired_ips:
                        self.requests.pop(k, None)

        return await call_next(request)


def reset_share_rate_limit_state() -> None:
    """Clear in-memory counters (used by tests to avoid cross-test pollution)."""
    for middleware in _middleware_instances:
        middleware.requests.clear()
        middleware.request_count = 0
