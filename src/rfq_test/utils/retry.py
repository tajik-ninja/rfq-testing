"""Smart retry utilities for infrastructure failures."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_attempts: int = 3
    min_wait_seconds: float = 1.0
    max_wait_seconds: float = 10.0
    multiplier: float = 2.0
    retry_exceptions: tuple = (ConnectionError, TimeoutError, OSError)


async def with_retry(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> T:
    """Execute async function with smart retry.
    
    Only retries on infrastructure failures (connection, timeout).
    Does NOT retry on validation/business logic errors.
    
    Args:
        func: Async function to call
        config: Retry configuration
        **kwargs: Arguments to pass to func
        
    Returns:
        Function result
        
    Raises:
        Original exception after max retries
    """
    config = config or RetryConfig()
    
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type(config.retry_exceptions),
        stop=stop_after_attempt(config.max_attempts),
        wait=wait_exponential(
            multiplier=config.multiplier,
            min=config.min_wait_seconds,
            max=config.max_wait_seconds,
        ),
        reraise=True,
    ):
        with attempt:
            return await func(**kwargs)
    
    # Should not reach here
    raise RuntimeError("Retry logic error")


def _is_sequence_mismatch_error(exc: BaseException) -> bool:
    """Return True if the exception indicates an account sequence mismatch."""
    msg = str(exc).lower()
    return "sequence mismatch" in msg or "incorrect account sequence" in msg


async def retry_on_sequence_mismatch(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    delay: float = 1.0,
    **kwargs,
) -> T:
    """Retry an async function on account sequence mismatch errors.

    The chain can reject transactions when the account sequence (nonce)
    is out of sync. This helper retries only on sequence mismatch,
    with exponential backoff.

    Args:
        func: Async function to call
        *args: Positional arguments to pass to func
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (doubles each retry)
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from the function

    Raises:
        The last exception if all retries fail (or any non-sequence-mismatch error)
    """
    last_exception: Optional[BaseException] = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except BaseException as e:
            if _is_sequence_mismatch_error(e):
                last_exception = e
                if attempt < max_retries:
                    wait_time = delay * (2**attempt)
                    logger.warning(
                        "Sequence mismatch on attempt %s/%s, retrying in %ss: %s",
                        attempt + 1,
                        max_retries + 1,
                        wait_time,
                        e,
                    )
                    await asyncio.sleep(wait_time)
                    continue
            raise

    if last_exception is not None:
        raise last_exception
    raise RuntimeError("Retry logic error")
