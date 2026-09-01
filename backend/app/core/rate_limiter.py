"""Production Rate Limiter and Abuse Protection Engine (TASK 19).

Provides:
  - Thread-safe in-memory sliding window rate limiting.
  - Pluggable storage architecture (in-memory default, Redis-compatible interface for distributed deployments).
  - Configurable rate limit categories: auth, prediction, read, admin, export.
  - Safe client IP extraction with trusted proxy validation.
  - FastAPI dependency for route-level enforcement.
  - Standardized HTTP 429 response with Retry-After header.
"""

from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timezone
import math
import threading
import time
from typing import Callable, Optional
from fastapi import HTTPException, Request, status

from backend.app.core.config import settings
from backend.app.core.logger import get_logger

logger = get_logger("telecom_churn.rate_limiter")


class BaseRateLimitStore(ABC):
    """Abstract storage backend for rate limiting counters."""

    @abstractmethod
    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int, int]:
        """Check if request is allowed under the rate limit.

        Returns:
            (allowed: bool, current_count: int, retry_after_seconds: int)
        """
        pass

    @abstractmethod
    def reset(self, key: Optional[str] = None) -> None:
        """Reset counters for a specific key or all keys (useful in tests)."""
        pass


class InMemorySlidingWindowStore(BaseRateLimitStore):
    """Thread-safe sliding window rate limit counter using in-memory deques."""

    def __init__(self):
        self._lock = threading.Lock()
        self._records: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int, int]:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._records[key]

            # Evict timestamps older than the sliding window
            while timestamps and timestamps[0] <= window_start:
                timestamps.popleft()

            current_count = len(timestamps)
            if current_count >= limit:
                # Calculate remaining seconds until oldest timestamp slides out of window
                oldest = timestamps[0]
                retry_after = max(1, math.ceil(oldest + window_seconds - now))
                return False, current_count, retry_after

            timestamps.append(now)
            return True, current_count + 1, 0

    def reset(self, key: Optional[str] = None) -> None:
        with self._lock:
            if key is not None:
                self._records.pop(key, None)
            else:
                self._records.clear()


# Global in-memory store instance
_default_store = InMemorySlidingWindowStore()


def get_client_identifier(request: Request) -> str:
    """Extract a safe client identifier (IP or Authenticated User ID) with trusted proxy checks."""
    client_ip = "127.0.0.1"

    # Check direct client host
    if request.client and request.client.host:
        client_ip = request.client.host

    # Only inspect X-Forwarded-For if client is a configured trusted proxy
    trusted_proxies = settings.trusted_proxy_list
    if client_ip in trusted_proxies:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # First IP in chain is the original client
            client_ip = forwarded_for.split(",")[0].strip()

    return client_ip


class RateLimiter:
    """FastAPI dependency for rate limiting specific endpoint categories."""

    def __init__(
        self,
        category: str,
        limit_override: Optional[int] = None,
        window_seconds: int = 60,
        store: Optional[BaseRateLimitStore] = None,
    ):
        self.category = category.lower()
        self.limit_override = limit_override
        self.window_seconds = window_seconds
        self.store = store or _default_store

    def _get_category_limit(self) -> int:
        if self.limit_override is not None:
            return self.limit_override

        category_map = {
            "auth": settings.RATE_LIMIT_AUTH_PER_MINUTE,
            "prediction": settings.RATE_LIMIT_PREDICTION_PER_MINUTE,
            "read": settings.RATE_LIMIT_READ_PER_MINUTE,
            "admin": settings.RATE_LIMIT_ADMIN_PER_MINUTE,
            "export": settings.RATE_LIMIT_EXPORT_PER_MINUTE,
        }
        return category_map.get(self.category, settings.RATE_LIMIT_READ_PER_MINUTE)

    def __call__(self, request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        limit = self._get_category_limit()
        if limit <= 0:
            return  # Unlimited

        client_id = get_client_identifier(request)
        rate_key = f"{self.category}:{client_id}"

        allowed, current_count, retry_after = self.store.is_allowed(
            key=rate_key,
            limit=limit,
            window_seconds=self.window_seconds,
        )

        if not allowed:
            req_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or "req-unknown"
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "category": self.category,
                    "client_ip": client_id,
                    "limit": limit,
                    "current_count": current_count,
                    "retry_after": retry_after,
                    "path": request.url.path,
                    "request_id": req_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests for '{self.category}' operations. Rate limit of {limit} requests per minute exceeded.",
                headers={"Retry-After": str(retry_after)},
            )


# Pre-configured category rate limiters for direct dependency injection
rate_limit_auth = RateLimiter(category="auth")
rate_limit_prediction = RateLimiter(category="prediction")
rate_limit_read = RateLimiter(category="read")
rate_limit_admin = RateLimiter(category="admin")
rate_limit_export = RateLimiter(category="export")
