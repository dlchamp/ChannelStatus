"""Pre-script check"""

import asyncio
import os
import time

from bot.config import model


def db_file_exists():
    """Check if db file exists"""
    path = "./bot/config/config.sqlite3"
    cwd = os.getcwd()
    print("Checking DB file...")

    if not os.path.exists(path):
        print(f'DB File not found - creating "{cwd}/bot/config/config.sqlite3"...')
        open(path, "w+").close()
        print(f"DB file created")
        return False

    else:
        print("DB file Found, skipping DB initialization")
        return True


async def init_db():
    """Create db tables and columns"""
    print("Initializing database...")
    time.sleep(1.5)
    await model.create()
    print("Database initialized - tables created...")


def token_check():
    """check that token is not none"""
    print("Checking that bot token has been supplied")
    return os.getenv("TOKEN") != ""


def pre_check():
    """main pre-check function"""

    print("======Starting Pre-check process =====")
    time.sleep(1)
    if not db_file_exists():
        time.sleep(2)
        asyncio.run(init_db())

    time.sleep(1)
    if not token_check():
        print(
            "Token was not supplied. Please make sure the token is valid and provided in the token.env file"
        )
        print("===== Pre-check failed =====")
        print("\n")
        return exit()

    print("===== Pre-check script passed =====")
    print("\n")
