#!/usr/bin/env python3
import telebot
import requests
import os
import json

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
"Telegram bot API token"
II_AGENT_URL = 'http://localhost:8000'
"ii-agent WebSocket/API endpoint"

logger = logging.getLogger(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
        "👋 Hi! I'm your ii-agent assistant. Send me any message and I'll help you out.\n\n"
        "I can help with research, coding, planning, and more!")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        # Show typing indicator
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call your ii-agent
        # Adjust this based on how ii-agent exposes its API
        response = requests.post(
            f"{II_AGENT_URL}/api/chat",  # Update endpoint as needed
            json={
                'message': message.text,
                'user_id': str(message.from_user.id)
            },
            timeout=120
        )
        
        ai_reply = response.json().get('response', 'Sorry, something went wrong.')
        
        # Split long messages (Telegram limit is 4096 chars)
        if len(ai_reply) > 4000:
            for i in range(0, len(ai_reply), 4000):
                bot.send_message(message.chat.id, ai_reply[i:i+4000])
        else:
            bot.reply_to(message, ai_reply)
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        logger.error(f"Error: {e}")


def get_args() -> argparse.Namespace:
    """
    Command-line arguments
    https://docs.python.org/3/howto/argparse.html
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--log_level", default="INFO")
    return parser.parse_args()


def main():
    args = get_args()
    logging.basicConfig(
        format="%(name)s:%(asctime)s:%(levelname)s:%(message)s", level=args.log_level
    )

    logger.info("Telegram bot is running...")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
