"""ii-agent client for handling chat interactions."""

import logging

import requests

from telegram_bridge.constants import II_AGENT_URL

logger = logging.getLogger(__name__)


class IIAgentClient:
    """Client for interacting with ii-agent API."""

    def __init__(self, base_url: str = II_AGENT_URL):
        """Initialize the ii-agent client.

        Args:
            base_url: Base URL for the ii-agent API
        """
        self.base_url = base_url
        self.session = requests.Session()

    def _post(self, endpoint: str, data: dict, timeout: int = 120) -> requests.Response:
        """Make a POST request to the ii-agent API.

        Args:
            endpoint: API endpoint path
            data: JSON data to send
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        return response

    def send_message(self, message: str, session_id: str, timeout: int = 120) -> str:
        """Send a message to ii-agent and get response.

        Args:
            message: The message text to send
            session_id: Session identifier (typically user ID)
            timeout: Request timeout in seconds

        Returns:
            The response text from ii-agent

        Raises:
            requests.RequestException: If the request fails
        """
        logger.debug(f"Sending message to ii-agent for session {session_id}")

        response = self._post(
            f"/api/sessions/{session_id}/messages",
            {"content": message},
            timeout=timeout,
        )

        ai_reply = response.json()["response"]
        logger.debug(f"Received response from ii-agent: {len(ai_reply)} chars")

        return ai_reply
