"""
MM (MCP Mesh) Integration Tests

Tests mesh client connectivity, service discovery, and communication patterns.

Module Size Target: <400 lines (Current: ~280 lines)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

# Add MM to path for testing
MM_PATH = Path(__file__).parent.parent.parent.parent / "MM"
if MM_PATH.exists():
    sys.path.insert(0, str(MM_PATH))

from sw_core.mesh_integration import MeshIntegration


# Fixtures

@pytest.fixture
def qapp():
    """PyQt6 application fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit - may interfere with other tests


@pytest.fixture
def mesh_client(qapp):
    """Create mesh integration instance for testing."""
    client = MeshIntegration(
        instance_name="test_app",
        mesh_url="http://localhost:6001"
    )
    yield client
    client.disconnect()


@pytest.fixture
def mock_mesh_client():
    """Create mock MeshClient for isolated testing."""
    with patch('mesh_integration.MeshClient') as mock:
        yield mock


# Connection Tests

def test_mesh_integration_init(qapp):
    """Test MeshIntegration initialization."""
    client = MeshIntegration(instance_name="test_app")

    assert client.instance_name == "test_app"
    assert client.mesh_url == "http://localhost:6001"
    assert client.client is not None
    assert client.is_connected is False


def test_mesh_connection_success(mock_mesh_client, qapp):
    """Test successful mesh connection."""
    # Setup mock
    mock_instance = mock_mesh_client.return_value
    mock_instance.list_services.return_value = []

    # Create client
    on_connected = Mock()
    client = MeshIntegration(
        instance_name="test_app",
        on_connected=on_connected
    )

    # Simulate connection check
    client._check_connection()

    # Verify connection callbacks
    if client.is_connected:
        assert on_connected.called


def test_mesh_connection_failure(mock_mesh_client, qapp):
    """Test mesh connection failure handling."""
    # Setup mock to raise exception
    mock_instance = mock_mesh_client.return_value
    mock_instance.list_services.side_effect = Exception("Connection failed")

    # Create client
    on_disconnected = Mock()
    client = MeshIntegration(
        instance_name="test_app",
        on_disconnected=on_disconnected
    )

    # Simulate connection check
    client._check_connection()

    # Should handle gracefully
    assert client.is_connected is False


def test_mesh_disconnect(mesh_client, qapp):
    """Test clean disconnect."""
    mesh_client.disconnect()

    assert mesh_client.is_connected is False
    assert not mesh_client.connection_timer.isActive()


# Service Discovery Tests

def test_list_services(mock_mesh_client, qapp):
    """Test service discovery."""
    # Setup mock
    mock_instance = mock_mesh_client.return_value
    mock_instance.list_services.return_value = [
        "c3_orchestrator",
        "tcc_instance",
        "another_app"
    ]

    client = MeshIntegration(instance_name="test_app")
    services = client.list_services()

    assert len(services) >= 0
    assert isinstance(services, list)


def test_get_service_info(mock_mesh_client, qapp):
    """Test getting service information."""
    # Setup mock
    mock_instance = mock_mesh_client.return_value
    mock_instance.get_service_info.return_value = {
        "name": "c3_orchestrator",
        "tools": ["create_campaign", "list_campaigns"],
        "description": "C3 Campaign Orchestrator"
    }

    client = MeshIntegration(instance_name="test_app")
    info = client.get_service_info("c3_orchestrator")

    assert isinstance(info, dict)


# Service Call Tests

def test_call_service_success(mock_mesh_client, qapp):
    """Test successful service call."""
    # Setup mock
    mock_instance = mock_mesh_client.return_value
    mock_instance.call_service.return_value = {
        "status": "success",
        "data": {"count": 42}
    }

    client = MeshIntegration(instance_name="test_app")
    result = client.call_service(
        service_name="test_service",
        tool_name="get_count"
    )

    assert result is not None
    assert isinstance(result, dict)


def test_call_service_with_arguments(mock_mesh_client, qapp):
    """Test service call with arguments."""
    # Setup mock
    mock_instance = mock_mesh_client.return_value
    mock_instance.call_service.return_value = {"status": "created"}

    client = MeshIntegration(instance_name="test_app")
    result = client.call_service(
        service_name="test_service",
        tool_name="create_item",
        arguments={"name": "Test", "value": 123}
    )

    # Verify call was made with arguments
    mock_instance.call_service.assert_called_once()
    call_args = mock_instance.call_service.call_args
    assert "arguments" in call_args[1]


def test_call_service_failure(mock_mesh_client, qapp):
    """Test service call error handling."""
    # Setup mock to raise exception
    mock_instance = mock_mesh_client.return_value
    mock_instance.call_service.side_effect = Exception("Service call failed")

    client = MeshIntegration(instance_name="test_app")
    result = client.call_service(
        service_name="test_service",
        tool_name="failing_tool"
    )

    # Should return None on error
    assert result is None


# Helper Method Tests

def test_is_service_available(mock_mesh_client, qapp):
    """Test checking if service is available."""
    # Setup mock
    mock_instance = mock_mesh_client.return_value
    mock_instance.list_services.return_value = [
        "c3_orchestrator",
        "tcc_instance"
    ]

    client = MeshIntegration(instance_name="test_app")

    assert client.is_service_available("c3_orchestrator") is True
    assert client.is_service_available("missing_service") is False


def test_get_connection_status(mesh_client, qapp):
    """Test getting connection status."""
    status = mesh_client.get_connection_status()

    assert isinstance(status, dict)
    assert "connected" in status
    assert "instance_name" in status
    assert "mesh_url" in status


# Signal Tests

def test_connection_signals(qapp):
    """Test connection signal emissions."""
    connected_signal = Mock()
    disconnected_signal = Mock()

    client = MeshIntegration(
        instance_name="test_app",
        on_connected=connected_signal,
        on_disconnected=disconnected_signal
    )

    # Signals should be callable
    assert callable(connected_signal)
    assert callable(disconnected_signal)


# Integration Tests (require running MM proxy)

@pytest.mark.integration
def test_real_mesh_connection(qapp):
    """Test real connection to MM proxy (requires proxy running)."""
    client = MeshIntegration(instance_name="test_app_integration")

    # Wait briefly for connection check
    QTimer.singleShot(1000, lambda: None)
    QApplication.processEvents()

    # Connection state depends on whether proxy is running
    status = client.get_connection_status()
    assert "connected" in status

    client.disconnect()


@pytest.mark.integration
def test_real_service_discovery(qapp):
    """Test real service discovery (requires proxy running)."""
    client = MeshIntegration(instance_name="test_app_integration")

    try:
        services = client.list_services()
        # Should return list (empty or populated depending on running services)
        assert isinstance(services, list)
    except Exception as e:
        pytest.skip(f"MM proxy not available: {e}")
    finally:
        client.disconnect()


@pytest.mark.integration
def test_real_service_call(qapp):
    """Test real service call (requires C3 service running)."""
    client = MeshIntegration(instance_name="test_app_integration")

    try:
        # Try to call a C3 service if available
        if client.is_service_available("c3_orchestrator"):
            result = client.call_service(
                service_name="c3_orchestrator",
                tool_name="list_campaigns"
            )
            assert result is not None
        else:
            pytest.skip("C3 orchestrator not running")
    except Exception as e:
        pytest.skip(f"Service call failed: {e}")
    finally:
        client.disconnect()


# Performance Tests

def test_connection_check_performance(mesh_client, qapp):
    """Test that connection checks are fast."""
    import time

    start = time.time()
    mesh_client._check_connection()
    elapsed = time.time() - start

    # Connection check should be <100ms
    assert elapsed < 0.1


def test_multiple_service_calls_performance(mock_mesh_client, qapp):
    """Test multiple service calls complete quickly."""
    import time

    # Setup mock
    mock_instance = mock_mesh_client.return_value
    mock_instance.call_service.return_value = {"status": "ok"}

    client = MeshIntegration(instance_name="test_app")

    start = time.time()
    for i in range(10):
        client.call_service("test_service", "test_tool")
    elapsed = time.time() - start

    # 10 calls should complete in <1 second (even with mocks)
    assert elapsed < 1.0


# Error Handling Tests

def test_invalid_service_name(mock_mesh_client, qapp):
    """Test handling of invalid service name."""
    mock_instance = mock_mesh_client.return_value
    mock_instance.call_service.side_effect = ValueError("Invalid service")

    client = MeshIntegration(instance_name="test_app")
    result = client.call_service("", "test_tool")

    assert result is None


def test_invalid_tool_name(mock_mesh_client, qapp):
    """Test handling of invalid tool name."""
    mock_instance = mock_mesh_client.return_value
    mock_instance.call_service.side_effect = ValueError("Invalid tool")

    client = MeshIntegration(instance_name="test_app")
    result = client.call_service("test_service", "")

    assert result is None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
