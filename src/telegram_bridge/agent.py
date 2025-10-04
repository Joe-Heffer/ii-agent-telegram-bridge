"""ii-agent client for handling chat interactions via WebSocket."""

import asyncio
import json
import logging

import websockets

from telegram_bridge.constants import II_AGENT_URL

logger = logging.getLogger(__name__)


class IIAgentClient:
    """Client for interacting with ii-agent WebSocket API."""

    def __init__(
        self,
        base_url: str = II_AGENT_URL,
        model_name: str = "claude-sonnet-4-20250514",
        device_id: str = "telegram-bridge",
    ):
        """Initialize the ii-agent client.

        Args:
            base_url: Base URL for the ii-agent API
            model_name: LLM model to use
            device_id: Device identifier for the client
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.ws_url = f"{ws_url}/ws?device_id={device_id}"
        self.model_name = model_name
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self.session_id: str | None = None
        self._connected = False
        self._initialized = False

    async def connect(self) -> None:
        """Establish WebSocket connection and initialize agent.

        Raises:
            ConnectionError: If connection or initialization fails
        """
        if self._connected:
            return

        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.debug("WebSocket connection established")

            # Wait for connection confirmation
            response = await self.websocket.recv()
            event = json.loads(response)

            if event["type"] != "CONNECTION_ESTABLISHED":
                raise ConnectionError(f"Unexpected event type: {event['type']}")

            logger.debug(f"Connected to workspace: {event['content'].get('workspace_path')}")
            self._connected = True

            # Initialize agent
            await self._initialize_agent()

        except Exception as e:
            logger.error(f"Failed to connect to ii-agent: {e}")
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            raise ConnectionError(f"Failed to connect to ii-agent: {e}") from e

    async def _initialize_agent(self) -> None:
        """Initialize the agent with model configuration.

        Raises:
            RuntimeError: If initialization fails
        """
        init_message = {
            "type": "init_agent",
            "content": {
                "model_name": self.model_name,
                "tool_args": {},
                "thinking_tokens": 0,
            },
        }

        await self.websocket.send(json.dumps(init_message))
        logger.debug(f"Initializing agent with model: {self.model_name}")

        # Wait for agent initialization
        while True:
            response = await self.websocket.recv()
            event = json.loads(response)

            if event["type"] == "AGENT_INITIALIZED":
                logger.debug("Agent initialized successfully")
                self._initialized = True
                return
            elif event["type"] == "ERROR":
                error_msg = event["content"].get("message", "Unknown error")
                raise RuntimeError(f"Agent initialization failed: {error_msg}")

    async def send_message(self, message: str, session_id: str, timeout: int = 120) -> str:
        """Send a message to ii-agent and get response.

        Args:
            message: The message text to send
            session_id: Session identifier (typically user/chat ID)
            timeout: Request timeout in seconds

        Returns:
            The complete response text from ii-agent

        Raises:
            RuntimeError: If not connected or message fails
            asyncio.TimeoutError: If response times out
        """
        if not self._connected or not self._initialized:
            await self.connect()

        logger.debug(f"Sending message to ii-agent for session {session_id}")

        # Send query
        query_message = {
            "type": "query",
            "content": {
                "text": message,
                "resume": False,
                "files": [],
            },
        }

        await self.websocket.send(json.dumps(query_message))

        # Collect response with timeout
        response_text = ""
        try:
            async with asyncio.timeout(timeout):
                while True:
                    response = await self.websocket.recv()
                    event = json.loads(response)
                    event_type = event["type"]
                    content = event["content"]

                    if event_type == "agent_response":
                        # Accumulate response deltas
                        if "delta" in content:
                            response_text += content["delta"]
                        elif "text" in content:
                            response_text += content["text"]

                    elif event_type == "tool_use":
                        # Log tool usage
                        tool_name = content.get("tool_name", "unknown")
                        logger.debug(f"Agent using tool: {tool_name}")

                    elif event_type == "tool_result":
                        # Log tool results
                        is_error = content.get("is_error", False)
                        if is_error:
                            logger.warning(f"Tool error: {content.get('output', '')[:200]}")

                    elif event_type == "STREAM_COMPLETE":
                        # Response complete
                        logger.debug(f"Received complete response: {len(response_text)} chars")
                        return response_text

                    elif event_type == "ERROR":
                        error_msg = content.get("message", "Unknown error")
                        raise RuntimeError(f"Agent error: {error_msg}")

        except asyncio.TimeoutError:
            logger.error(f"Response timeout after {timeout} seconds")
            raise

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self._connected = False
            self._initialized = False
            logger.debug("WebSocket connection closed")
