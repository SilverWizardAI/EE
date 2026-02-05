"""
MM Mesh Integration

Wrapper for MCP Mesh client with PyQt6 integration.
Includes retry logic for HA failover handling.

Module Size Target: <400 lines (Current: ~250 lines)
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

# Import retry logic
ee_shared_path = Path(__file__).parent.parent.parent / "shared"
if str(ee_shared_path) not in sys.path:
    sys.path.insert(0, str(ee_shared_path))

try:
    from mm_client_retry import (
        retry_on_failure,
        RetryConfig,
        RetryStrategy,
        ConnectionError as RetryConnectionError,
        TimeoutError as RetryTimeoutError,
        ServiceUnavailableError,
    )
    RETRY_AVAILABLE = True
except ImportError:
    RETRY_AVAILABLE = False
    logger.warning("Retry module not available - failover handling disabled")


logger = logging.getLogger(__name__)


# Default retry configuration for HA failover
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=0.5,
    max_delay=10.0,
    strategy=RetryStrategy.EXPONENTIAL,
    jitter=True,
    backoff_factor=2.0,
) if RETRY_AVAILABLE else None


class MeshIntegration(QObject):
    """
    PyQt6-integrated mesh client wrapper.

    Provides:
    - Automatic connection management
    - Qt signal integration
    - Service discovery
    - Tool invocation

    Usage:
        mesh = MeshIntegration(
            instance_name="my_app",
            on_connected=lambda: print("Connected"),
            on_disconnected=lambda: print("Disconnected")
        )
        if mesh.is_available():
            result = mesh.call_tool("other_service", "tool_name", {...})
    """

    # Signals
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        instance_name: str,
        proxy_host: str = "localhost",
        proxy_port: int = 6001,
        auto_connect: bool = True,
        on_connected: Optional[Callable] = None,
        on_disconnected: Optional[Callable] = None
    ):
        """
        Initialize mesh integration.

        Args:
            instance_name: Name to register as
            proxy_host: Mesh proxy host
            proxy_port: Mesh proxy port (HTTP API)
            auto_connect: Auto-connect on init
            on_connected: Callback for connection
            on_disconnected: Callback for disconnection
        """
        super().__init__()

        self.instance_name = instance_name
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self._client = None
        self._connected = False

        # Connect callbacks
        if on_connected:
            self.connected.connect(on_connected)
        if on_disconnected:
            self.disconnected.connect(on_disconnected)

        # Try to import and connect
        if auto_connect:
            self._try_connect()

        logger.info(f"Mesh integration initialized: {instance_name}")

    def _try_connect(self):
        """Try to connect to mesh proxy."""
        try:
            # Import here to make mesh optional
            import sys
            from pathlib import Path
            mm_path = Path.home() / "Library" / "CloudStorage" / "Dropbox" / "A_Coding" / "MM"
            if str(mm_path) not in sys.path:
                sys.path.insert(0, str(mm_path))

            from mcp_mesh.client.mesh_client import MeshClient

            self._client = MeshClient(
                proxy_host=self.proxy_host,
                proxy_port=self.proxy_port
            )

            # Test connection
            services = self._client.list_services()
            self._connected = True
            self.connected.emit()
            logger.info(f"✓ Connected to mesh proxy ({len(services)} services)")

        except Exception as e:
            logger.warning(f"Mesh not available: {e}")
            self._client = None
            self._connected = False

    def is_available(self) -> bool:
        """Check if mesh is available."""
        return self._client is not None and self._connected

    def disconnect(self):
        """Disconnect from mesh."""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.error(f"Error closing mesh client: {e}")
            finally:
                self._client = None
                self._connected = False
                self.disconnected.emit()

    def _wrap_with_retry(self, func: Callable, *args, **kwargs):
        """
        Wrap a mesh client call with retry logic.

        Handles HA failover scenarios with automatic retry.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        if not RETRY_AVAILABLE:
            # No retry available - call directly
            return func(*args, **kwargs)

        @retry_on_failure(
            config=DEFAULT_RETRY_CONFIG,
            on_retry=lambda attempt, exc: logger.info(
                f"Retry attempt {attempt + 1} after {type(exc).__name__}: {exc}"
            )
        )
        def _retryable_call():
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Map to retryable exceptions
                error_str = str(e).lower()

                if "connection" in error_str or "refused" in error_str:
                    raise RetryConnectionError(str(e))
                elif "timeout" in error_str:
                    raise RetryTimeoutError(str(e))
                elif "503" in error_str or "unavailable" in error_str:
                    raise ServiceUnavailableError(str(e))
                else:
                    # Unknown error - let it propagate
                    raise

        return _retryable_call()

    def list_services(self) -> List[Dict[str, Any]]:
        """
        List all available services.

        Automatically retries on failover-related failures.

        Returns:
            List of service info dictionaries
        """
        if not self.is_available():
            logger.warning("Mesh not available for list_services")
            return []

        try:
            return self._wrap_with_retry(self._client.list_services)
        except Exception as e:
            logger.error(f"Error listing services (all retries failed): {e}")
            self.error.emit(str(e))
            return []

    def get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get info about a specific service.

        Automatically retries on failover-related failures.

        Args:
            service_name: Service to query

        Returns:
            Service info dict or None
        """
        if not self.is_available():
            logger.warning(f"Mesh not available for get_service_info({service_name})")
            return None

        try:
            return self._wrap_with_retry(self._client.get_service_info, service_name)
        except Exception as e:
            logger.error(f"Error getting service info (all retries failed): {e}")
            self.error.emit(str(e))
            return None

    def call_tool(
        self,
        service_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Call a tool on a remote service.

        Automatically retries on failover-related failures.

        Args:
            service_name: Service to call
            tool_name: Tool to invoke
            arguments: Tool arguments

        Returns:
            Tool result or None on error
        """
        if not self.is_available():
            logger.warning(f"Mesh not available for call_tool({service_name}.{tool_name})")
            return None

        try:
            result = self._wrap_with_retry(
                self._client.call_service,
                service_name,
                tool_name,
                arguments
            )
            logger.debug(f"Called {service_name}.{tool_name}: success")
            return result
        except Exception as e:
            logger.error(f"Error calling {service_name}.{tool_name} (all retries failed): {e}")
            self.error.emit(str(e))
            return None

    def find_service_with_tool(self, tool_name: str) -> Optional[str]:
        """
        Find first service that provides a tool.

        Args:
            tool_name: Tool to search for

        Returns:
            Service name or None
        """
        if not self.is_available():
            return None

        try:
            return self._client.find_service_with_tool(tool_name)
        except Exception as e:
            logger.error(f"Error finding service with tool {tool_name}: {e}")
            return None
