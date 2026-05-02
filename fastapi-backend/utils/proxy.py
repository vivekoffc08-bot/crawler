"""
Proxy management and rate limiting utilities.
Implements exponential backoff and optional proxy rotation.
"""

import asyncio
import random
import time
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Per-domain rate limiter with exponential backoff on 429/503 responses.
    """

    def __init__(self):
        self._last_request: Dict[str, float] = {}
        self._backoff_count: Dict[str, int] = {}
        self._min_delay: float = 1.5
        self._max_delay: float = 4.0

    async def wait(self, domain: str):
        """Wait an appropriate amount of time before making a request to domain."""
        now = time.time()
        last = self._last_request.get(domain, 0)
        backoff = self._backoff_count.get(domain, 0)

        # Base random delay
        base_delay = random.uniform(self._min_delay, self._max_delay)

        # Exponential backoff factor
        if backoff > 0:
            backoff_delay = min(base_delay * (2 ** backoff), 60.0)
            delay = backoff_delay
            logger.warning(f"Backoff level {backoff} for {domain}, waiting {delay:.1f}s")
        else:
            delay = base_delay

        # Ensure minimum time between requests to same domain
        elapsed = now - last
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)

        self._last_request[domain] = time.time()

    def record_success(self, domain: str):
        """Reset backoff counter on successful request."""
        self._backoff_count[domain] = 0

    def record_failure(self, domain: str, status_code: int):
        """Increase backoff on rate-limit or server error."""
        if status_code in (429, 503, 520, 521, 522, 523, 524):
            current = self._backoff_count.get(domain, 0)
            self._backoff_count[domain] = min(current + 1, 5)  # Cap at 5
            logger.warning(
                f"Rate limited by {domain} (HTTP {status_code}), "
                f"backoff now at level {self._backoff_count[domain]}"
            )

    def record_block(self, domain: str):
        """Record a detected bot-block (CAPTCHA, redirect to challenge, etc.)."""
        current = self._backoff_count.get(domain, 0)
        self._backoff_count[domain] = min(current + 2, 5)
        logger.warning(f"Bot detection on {domain}, backoff level {self._backoff_count[domain]}")


# Singleton rate limiter instance
rate_limiter = RateLimiter()


# Free proxy list (optional, for production use)
FREE_PROXIES = [
    # These are placeholder proxies — in production, integrate with a proxy provider
    # or use a rotating proxy service like ScraperAPI, BrightData, etc.
]


def get_proxy() -> Optional[str]:
    """
    Return a random proxy from the pool.
    Returns None if no proxies are configured (direct connection).
    """
    if not FREE_PROXIES:
        return None
    return random.choice(FREE_PROXIES)


async def with_retry(
    coro_factory,
    max_retries: int = 3,
    domain: str = "unknown",
):
    """
    Execute an async callable with retry and exponential backoff.
    
    Args:
        coro_factory: A callable that returns a coroutine (not the coroutine itself)
        max_retries: Maximum number of retry attempts
        domain: Domain name for rate limiting
    
    Returns:
        The result of the coroutine
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            await rate_limiter.wait(domain)
            result = await coro_factory()
            rate_limiter.record_success(domain)
            return result
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {domain}: {e}")
            if attempt < max_retries - 1:
                backoff = random.uniform(2 ** attempt, 2 ** (attempt + 1))
                await asyncio.sleep(backoff)
    raise last_exception
