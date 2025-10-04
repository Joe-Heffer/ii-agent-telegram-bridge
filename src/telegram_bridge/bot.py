import asyncio
import logging

import telebot

from telegram_bridge.agent import IIAgentClient
from telegram_bridge.constants import SPLIT_MESSAGE_LENGTH, TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN environment variable is required. "
        "Please set it in your .env file or environment."
    )

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
agent = IIAgentClient()


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Hi! I'm your ii-agent assistant. Send me any message and I'll help you out.\n\n"
        "I can help with research, coding, planning, and more!",
    )


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    logger.info("Message received %s", message.chat.id)
    try:
        # Show typing indicator
        bot.send_chat_action(message.chat.id, "typing")

        # Get response from ii-agent (using chat.id as session_id)
        # Run async function in event loop
        ai_reply = asyncio.run(agent.send_message(message.text, session_id=str(message.chat.id)))

        # Split long messages (Telegram limit is 4096 chars)
        if len(ai_reply) > SPLIT_MESSAGE_LENGTH:
            for i in range(0, len(ai_reply), SPLIT_MESSAGE_LENGTH):
                bot.send_message(message.chat.id, ai_reply[i : i + SPLIT_MESSAGE_LENGTH])
        else:
            bot.reply_to(message, ai_reply)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        logger.error(f"Error: {e}")


def run():
    """Start the Telegram bot"""
    logger.info("Telegram bot is running...")
    bot.infinity_polling()
