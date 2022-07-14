import os
import time

from dotenv import load_dotenv

from bot import bot
from check import pre_check

load_dotenv()


def main(bot):
    """Main function that starts the bot and tasks loops"""

    bot.run(os.getenv("TOKEN"))


if __name__ == "__main__":
    pre_check()
    time.sleep(0.5)

    main(bot)
