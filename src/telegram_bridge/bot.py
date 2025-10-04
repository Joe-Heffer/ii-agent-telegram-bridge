import logging

import requests
import telebot

from telegram_bridge.constants import II_AGENT_URL, SPLIT_MESSAGE_LENGTH, TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Hi! I'm your ii-agent assistant. Send me any message and I'll help you out.\n\n"
        "I can help with research, coding, planning, and more!",
    )


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    logger.info("Message recieved %s", message.chat.id)
    try:
        # Show typing indicator
        bot.send_chat_action(message.chat.id, "typing")

        # Call your ii-agent
        # Adjust this based on how ii-agent exposes its API
        response = requests.post(
            f"{II_AGENT_URL}/api/chat",  # Update endpoint as needed
            json={"message": message.text, "user_id": str(message.from_user.id)},
            timeout=120,
        )

        ai_reply = response.json().get("response", "Sorry, something went wrong.")

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
