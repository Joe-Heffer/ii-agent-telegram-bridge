"""Tests for telegram_bridge.agent module."""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from telegram_bridge.agent import IIAgentClient


@pytest.fixture
def agent_client():
    """Create an IIAgentClient instance for testing."""
    return IIAgentClient(base_url="http://test:8000", device_id="test-client")


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    mock = AsyncMock()
    return mock


class TestIIAgentClient:
    """Tests for IIAgentClient class."""

    def test_initialization_default_url(self):
        """Test client initializes with default URL."""
        with patch("telegram_bridge.agent.II_AGENT_URL", "http://localhost:8000"):
            client = IIAgentClient()
            assert client.ws_url == "ws://localhost:8000/ws?device_id=telegram-bridge"

    def test_initialization_custom_url(self):
        """Test client initializes with custom URL."""
        client = IIAgentClient(base_url="http://custom:9000", device_id="test-id")
        assert client.ws_url == "ws://custom:9000/ws?device_id=test-id"

    def test_initialization_https_to_wss(self):
        """Test HTTPS URL converts to WSS."""
        client = IIAgentClient(base_url="https://secure:9000")
        assert client.ws_url.startswith("wss://")

    def test_initialization_sets_model(self):
        """Test client stores model name."""
        client = IIAgentClient(model_name="test-model")
        assert client.model_name == "test-model"

    @pytest.mark.asyncio
    async def test_connect_success(self, agent_client, mock_websocket):
        """Test successful WebSocket connection."""
        # Mock connection establishment
        mock_websocket.recv.side_effect = [
            json.dumps(
                {
                    "type": "CONNECTION_ESTABLISHED",
                    "content": {"workspace_path": "/workspace/test"},
                }
            ),
            json.dumps({"type": "AGENT_INITIALIZED", "content": {}}),
        ]

        # Create async mock that can be awaited
        async def mock_connect(url):
            return mock_websocket

        with patch("telegram_bridge.agent.websockets.connect", side_effect=mock_connect):
            await agent_client.connect()

        assert agent_client._connected is True
        assert agent_client._initialized is True

    @pytest.mark.asyncio
    async def test_connect_unexpected_event(self, agent_client, mock_websocket):
        """Test connection fails with unexpected event."""
        mock_websocket.recv.return_value = json.dumps({"type": "UNEXPECTED", "content": {}})

        async def mock_connect(url):
            return mock_websocket

        with patch("telegram_bridge.agent.websockets.connect", side_effect=mock_connect):
            with pytest.raises(ConnectionError):
                await agent_client.connect()

    @pytest.mark.asyncio
    async def test_connect_initialization_error(self, agent_client, mock_websocket):
        """Test connection fails when agent initialization fails."""
        mock_websocket.recv.side_effect = [
            json.dumps(
                {
                    "type": "CONNECTION_ESTABLISHED",
                    "content": {"workspace_path": "/workspace/test"},
                }
            ),
            json.dumps({"type": "ERROR", "content": {"message": "Init failed"}}),
        ]

        async def mock_connect(url):
            return mock_websocket

        with patch("telegram_bridge.agent.websockets.connect", side_effect=mock_connect):
            with pytest.raises(ConnectionError, match="Failed to connect to ii-agent"):
                await agent_client.connect()

    @pytest.mark.asyncio
    async def test_connect_idempotent(self, agent_client, mock_websocket):
        """Test connect is idempotent when already connected."""
        agent_client._connected = True
        agent_client._initialized = True

        await agent_client.connect()

        # Should not attempt connection
        mock_websocket.recv.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_success(self, agent_client, mock_websocket):
        """Test sending message successfully."""
        agent_client._connected = True
        agent_client._initialized = True
        agent_client.websocket = mock_websocket

        # Mock response stream
        mock_websocket.recv.side_effect = [
            json.dumps({"type": "agent_response", "content": {"delta": "Hello "}}),
            json.dumps({"type": "agent_response", "content": {"delta": "World"}}),
            json.dumps({"type": "STREAM_COMPLETE", "content": {}}),
        ]

        result = await agent_client.send_message("Test message", "user123")

        assert result == "Hello World"
        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["type"] == "query"
        assert sent_data["content"]["text"] == "Test message"

    @pytest.mark.asyncio
    async def test_send_message_with_text_response(self, agent_client, mock_websocket):
        """Test sending message with complete text response."""
        agent_client._connected = True
        agent_client._initialized = True
        agent_client.websocket = mock_websocket

        mock_websocket.recv.side_effect = [
            json.dumps({"type": "agent_response", "content": {"text": "Complete response"}}),
            json.dumps({"type": "STREAM_COMPLETE", "content": {}}),
        ]

        result = await agent_client.send_message("Test", "user123")
        assert result == "Complete response"

    @pytest.mark.asyncio
    async def test_send_message_handles_tool_use(self, agent_client, mock_websocket):
        """Test message handling with tool usage."""
        agent_client._connected = True
        agent_client._initialized = True
        agent_client.websocket = mock_websocket

        mock_websocket.recv.side_effect = [
            json.dumps(
                {
                    "type": "tool_use",
                    "content": {"tool_name": "bash", "tool_use_id": "123"},
                }
            ),
            json.dumps(
                {
                    "type": "tool_result",
                    "content": {"tool_use_id": "123", "output": "Result", "is_error": False},
                }
            ),
            json.dumps({"type": "agent_response", "content": {"delta": "Done"}}),
            json.dumps({"type": "STREAM_COMPLETE", "content": {}}),
        ]

        result = await agent_client.send_message("Run command", "user123")
        assert result == "Done"

    @pytest.mark.asyncio
    async def test_send_message_agent_error(self, agent_client, mock_websocket):
        """Test handling agent error during message."""
        agent_client._connected = True
        agent_client._initialized = True
        agent_client.websocket = mock_websocket

        mock_websocket.recv.return_value = json.dumps(
            {"type": "ERROR", "content": {"message": "Agent failed"}}
        )

        with pytest.raises(RuntimeError, match="Agent error: Agent failed"):
            await agent_client.send_message("Test", "user123")

    @pytest.mark.asyncio
    async def test_send_message_timeout(self, agent_client, mock_websocket):
        """Test message timeout."""
        agent_client._connected = True
        agent_client._initialized = True
        agent_client.websocket = mock_websocket

        # Simulate slow response
        async def slow_recv():
            await asyncio.sleep(10)
            return json.dumps({"type": "agent_response", "content": {"delta": "slow"}})

        mock_websocket.recv.side_effect = slow_recv

        with pytest.raises(asyncio.TimeoutError):
            await agent_client.send_message("Test", "user123", timeout=1)

    @pytest.mark.asyncio
    async def test_send_message_auto_connect(self, agent_client, mock_websocket):
        """Test send_message auto-connects if not connected."""
        assert agent_client._connected is False

        mock_websocket.recv.side_effect = [
            # Connection phase
            json.dumps(
                {
                    "type": "CONNECTION_ESTABLISHED",
                    "content": {"workspace_path": "/workspace/test"},
                }
            ),
            json.dumps({"type": "AGENT_INITIALIZED", "content": {}}),
            # Message phase
            json.dumps({"type": "agent_response", "content": {"delta": "Response"}}),
            json.dumps({"type": "STREAM_COMPLETE", "content": {}}),
        ]

        async def mock_connect(url):
            return mock_websocket

        with patch("telegram_bridge.agent.websockets.connect", side_effect=mock_connect):
            result = await agent_client.send_message("Test", "user123")

        assert result == "Response"
        assert agent_client._connected is True

    @pytest.mark.asyncio
    async def test_close(self, agent_client, mock_websocket):
        """Test closing WebSocket connection."""
        agent_client.websocket = mock_websocket
        agent_client._connected = True
        agent_client._initialized = True

        await agent_client.close()

        mock_websocket.close.assert_called_once()
        assert agent_client.websocket is None
        assert agent_client._connected is False
        assert agent_client._initialized is False

    @pytest.mark.asyncio
    async def test_close_when_not_connected(self, agent_client):
        """Test closing when no connection exists."""
        agent_client.websocket = None

        await agent_client.close()  # Should not raise

        assert agent_client.websocket is None

    @pytest.mark.asyncio
    @patch("telegram_bridge.agent.logger")
    async def test_logging(self, mock_logger, agent_client, mock_websocket):
        """Test that operations are logged."""
        agent_client._connected = True
        agent_client._initialized = True
        agent_client.websocket = mock_websocket

        mock_websocket.recv.side_effect = [
            json.dumps({"type": "agent_response", "content": {"delta": "Test"}}),
            json.dumps({"type": "STREAM_COMPLETE", "content": {}}),
        ]

        await agent_client.send_message("Hello", "user123")

        # Check that debug logging occurred
        assert mock_logger.debug.called
