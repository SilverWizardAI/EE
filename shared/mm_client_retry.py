"""
MM Mesh Client Retry Logic

Handles transient failures during Active/Standby failover:
- Connection failures
- Timeouts
- NAK responses
- Exponential backoff with jitter

Module Size Target: <400 lines (Current: ~200 lines)
"""

import time
import random
import logging
from typing import Callable, TypeVar, Optional, Any
from functools import wraps
from enum import Enum


logger = logging.getLogger(__name__)


T = TypeVar('T')


class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"            # Linear backoff
    IMMEDIATE = "immediate"      # No delay between retries


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 0.5,
        max_delay: float = 10.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        jitter: bool = True,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            strategy: Retry strategy (exponential, linear, immediate)
            jitter: Add random jitter to prevent thundering herd
            backoff_factor: Multiplier for exponential backoff
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.jitter = jitter
        self.backoff_factor = backoff_factor


class RetryableError(Exception):
    """Base class for errors that should trigger retry."""
    pass


class ConnectionError(RetryableError):
    """Connection failed - likely during failover."""
    pass


class TimeoutError(RetryableError):
    """Request timed out - possible failover in progress."""
    pass


class ServiceUnavailableError(RetryableError):
    """Service returned unavailable/NAK - temporary issue."""
    pass


class NonRetryableError(Exception):
    """Error that should NOT be retried."""
    pass


def calculate_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """
    Calculate delay before next retry.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    if config.strategy == RetryStrategy.IMMEDIATE:
        delay = 0

    elif config.strategy == RetryStrategy.LINEAR:
        delay = config.base_delay * (attempt + 1)

    else:  # EXPONENTIAL
        delay = config.base_delay * (config.backoff_factor ** attempt)

    # Cap at max_delay
    delay = min(delay, config.max_delay)

    # Add jitter if enabled
    if config.jitter and delay > 0:
        jitter = random.uniform(0, delay * 0.1)  # Up to 10% jitter
        delay += jitter

    return delay


def retry_on_failure(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: tuple = (RetryableError,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable:
    """
    Decorator to retry function on failure.

    Args:
        config: Retry configuration (uses defaults if None)
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Optional callback called on each retry (attempt, exception)

    Returns:
        Decorated function

    Example:
        @retry_on_failure(config=RetryConfig(max_attempts=3))
        def call_mesh_service():
            return mesh_client.call_service("foo", "bar")
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        # Calculate delay
                        delay = calculate_delay(attempt, config)

                        # Log retry
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        # Call retry callback if provided
                        if on_retry:
                            try:
                                on_retry(attempt, e)
                            except Exception as callback_error:
                                logger.error(f"Retry callback failed: {callback_error}")

                        # Wait before retry
                        if delay > 0:
                            time.sleep(delay)
                    else:
                        # Final attempt failed
                        logger.error(
                            f"All {config.max_attempts} attempts failed. "
                            f"Last error: {e}"
                        )

                except Exception as e:
                    # Non-retryable exception - fail immediately
                    logger.error(f"Non-retryable error: {e}")
                    raise

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


class RetryableHTTPClient:
    """
    HTTP client wrapper with built-in retry logic.

    Automatically retries on common transient failures:
    - Connection errors (during failover)
    - 503 Service Unavailable (NAK)
    - Timeouts
    """

    def __init__(
        self,
        base_url: str,
        config: Optional[RetryConfig] = None,
        timeout: float = 10.0,
    ):
        """
        Initialize retryable HTTP client.

        Args:
            base_url: Base URL for all requests
            config: Retry configuration
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.config = config or RetryConfig()
        self.timeout = timeout

    def _is_retryable_error(self, response: Any) -> bool:
        """Check if HTTP response indicates retryable error."""
        # Import here to avoid circular dependency
        try:
            status_code = response.status_code
            return status_code in (503, 502, 504)  # Service unavailable, bad gateway, gateway timeout
        except:
            return False

    @retry_on_failure()
    def get(self, path: str, **kwargs) -> Any:
        """
        HTTP GET with retry.

        Args:
            path: URL path (relative to base_url)
            **kwargs: Additional arguments for requests.get

        Returns:
            Response object

        Raises:
            RetryableError: If request fails after all retries
        """
        import requests

        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            response = requests.get(url, timeout=self.timeout, **kwargs)

            if self._is_retryable_error(response):
                raise ServiceUnavailableError(
                    f"Service returned {response.status_code}"
                )

            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Connection failed: {e}")
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request timed out: {e}")
        except requests.exceptions.HTTPError as e:
            # Don't retry 4xx errors (client errors)
            if 400 <= e.response.status_code < 500:
                raise NonRetryableError(f"Client error: {e}")
            raise

    @retry_on_failure()
    def post(self, path: str, **kwargs) -> Any:
        """
        HTTP POST with retry.

        Args:
            path: URL path (relative to base_url)
            **kwargs: Additional arguments for requests.post

        Returns:
            Response object

        Raises:
            RetryableError: If request fails after all retries
        """
        import requests

        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            response = requests.post(url, timeout=self.timeout, **kwargs)

            if self._is_retryable_error(response):
                raise ServiceUnavailableError(
                    f"Service returned {response.status_code}"
                )

            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Connection failed: {e}")
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request timed out: {e}")
        except requests.exceptions.HTTPError as e:
            # Don't retry 4xx errors (client errors)
            if 400 <= e.response.status_code < 500:
                raise NonRetryableError(f"Client error: {e}")
            raise
