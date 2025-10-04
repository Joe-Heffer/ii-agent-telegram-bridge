import os

import dotenv

dotenv.load_dotenv()

II_AGENT_URL = os.getenv("II_AGENT_URL", "http://localhost:8000")
"ii-agent WebSocket/API endpoint"

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
"Telegram bot API token"

MAX_TELEGRAM_MESSAGE_LENGTH = 4096
"Maximum length of a Telegram message"

SPLIT_MESSAGE_LENGTH = 4000
"Length at which to split messages for Telegram"
