"""Tests for telegram_bridge.bot module."""

import os
import random
import sys
import uuid
from unittest.mock import Mock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_modules():
    """Reset telegram_bridge modules before each test."""
    # Remove the modules if they were already imported
    modules_to_reset = ["telegram_bridge.bot", "telegram_bridge.constants"]
    for module in modules_to_reset:
        if module in sys.modules:
            del sys.modules[module]
    yield
    # Clean up after test
    for module in modules_to_reset:
        if module in sys.modules:
            del sys.modules[module]


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    token = f"{random.randint(999, 9999)}:{uuid.uuid4()}"
    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": token}, clear=False):
        yield token


def test_bot_initialization(mock_env):
    """Test that bot is initialized with correct token."""
    with patch("telebot.TeleBot") as mock_telebot:
        import telegram_bridge.bot

        mock_telebot.assert_called_once_with(mock_env)


def test_message_handlers_registered(mock_env):
    """Test that message handlers are registered."""
    mock_bot_instance = Mock()
    with patch("telebot.TeleBot", return_value=mock_bot_instance):
        import telegram_bridge.bot

        # Verify handlers were registered
        assert mock_bot_instance.message_handler.call_count == 2


def test_run(mock_env):
    """Test run function calls infinity_polling."""
    mock_bot_instance = Mock()
    with patch("telebot.TeleBot", return_value=mock_bot_instance):
        import telegram_bridge.bot

        telegram_bridge.bot.run()

        mock_bot_instance.infinity_polling.assert_called_once()


def test_constants_loaded(mock_env):
    """Test that constants are properly loaded."""
    with patch("telebot.TeleBot"):
        import telegram_bridge.bot
        from telegram_bridge.constants import (
            II_AGENT_URL,
            SPLIT_MESSAGE_LENGTH,
            TELEGRAM_BOT_TOKEN,
        )

        assert II_AGENT_URL == "http://localhost:8000"
        assert SPLIT_MESSAGE_LENGTH == 4000
        assert TELEGRAM_BOT_TOKEN == mock_env
