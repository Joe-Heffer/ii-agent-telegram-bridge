# Telegram chat bot bridge for ii-agent

A bridge server for [ii-agent](https://github.com/Intelligent-Internet/ii-agent) to use a [Telegram bot](https://core.telegram.org/bots).

## Installation

```bash
pip install git+https://github.com/Joe-Heffer/ii-agent-telegram-bridge.git
```

### Configuration

Set environment variables:

- `TELEGRAM_BOT_TOKEN` is the unique authentication token provided by [Telegram's BotFather](https://telegram.me/BotFather) when you create a bot.
- `II_AGENT_URL` is the location of the ii-agent API, which defaults to `http://localhost:8000`

## Usage

Run the bot:

```bash
telegram-bridge
```

With custom log level:

```bash
telegram-bridge --log_level DEBUG
```

## Development

Install with dev dependencies:

```bash
pip install -e ".[dev]"
```

Run linting:

```bash
ruff check --fix
```
