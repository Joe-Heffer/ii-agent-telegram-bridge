# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot bridge for ii-agent. It receives messages from Telegram users and forwards them to an ii-agent instance running locally, then returns the agent's responses back to Telegram.

## Architecture

**Single Module Design**: The entire application is in `src/telegram_bridge/__main__.py`. This is a simple bridge with:

- Telegram bot using `pyTeleBot` library
- HTTP client calling ii-agent's REST API
- Message handling that splits long responses (>4000 chars) to comply with Telegram's 4096 character limit

**Key Components**:

- `TELEGRAM_BOT_TOKEN`: Environment variable for Telegram bot authentication
- `II_AGENT_URL`: Hardcoded to `http://localhost:8000` (ii-agent endpoint)
- Message handlers for `/start`, `/help`, and general messages
- Error handling with user-friendly error messages

**Data Flow**:

1. User sends message to Telegram bot
2. Bot forwards to ii-agent via `POST /api/chat` with `message` and `user_id`
3. ii-agent response is extracted from JSON response
4. Response sent back to Telegram (split if >4000 chars)

## Running the Bot

**Prerequisites**:

- Set `TELEGRAM_BOT_TOKEN` environment variable
- Ensure ii-agent is running at `http://localhost:8000`

**Install the package**:

```bash
pip install -e .
```

Code linting

```bash
ruff check --fix
```

**Start the bot**:

```bash
telegram-bridge
```

**With custom log level**:

```bash
telegram-bridge --log_level DEBUG
```

**Alternative (run as module)**:

```bash
python -m telegram_bridge --log_level DEBUG
```
