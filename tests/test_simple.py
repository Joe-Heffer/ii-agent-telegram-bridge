"""Simple test to debug mocking."""

import os
from unittest.mock import Mock, patch

# Set env var
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"

# Create mock
mock_bot = Mock()

# Patch and import
with patch("telebot.TeleBot", return_value=mock_bot):
    import telegram_bridge.bot

    print("bot object:", telegram_bridge.bot.bot)
    print("Is same as mock?", telegram_bridge.bot.bot is mock_bot)
    print("All mock calls so far:", mock_bot.method_calls)

    # Test call
    msg = Mock()
    telegram_bridge.bot.send_welcome(msg)

    print("\nAfter send_welcome:")
    print("reply_to called?", mock_bot.reply_to.called)
    print("reply_to call count:", mock_bot.reply_to.call_count)
    print("All mock calls:", mock_bot.method_calls)
