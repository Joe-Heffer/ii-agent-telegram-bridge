# Contributing

Thank you for your interest in contributing to the Telegram Bridge for ii-agent!

## Development Setup

Install the package with development dependencies:

```bash
pip install -e ".[dev,test]"
```

## Code Quality

### Linting

Run ruff to check code quality:

```bash
ruff check --fix
```

### Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run tests with coverage:

```bash
pytest tests/ -v --cov=telegram_bridge --cov-report=term-missing
```

## Project Structure

```
src/telegram_bridge/
├── __init__.py          # Package metadata
├── __main__.py          # CLI entry point
├── bot.py               # Telegram bot implementation
└── constants.py         # Configuration constants
```

## Making Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Running Locally

Set required environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export II_AGENT_URL="http://localhost:8000"  # Optional, defaults to localhost
```

Run the bot:

```bash
telegram-bridge --log_level DEBUG
```

Or run as a module:

```bash
python -m telegram_bridge --log_level DEBUG
```
