"""Entry point for the stealth heist game.

Deliberately thin: all logic lives in src/core/game.py so this file stays
readable and easy to present.
"""
from src.core.game import Game


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()
