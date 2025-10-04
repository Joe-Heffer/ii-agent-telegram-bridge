#!/usr/bin/env python3
import argparse
import logging

import telegram_bridge.bot

DESCRIPTION = "Telegram bot bridge for ii-agent"


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

    telegram_bridge.bot.run()


if __name__ == "__main__":
    main()
