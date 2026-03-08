import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def check_env():
    required = ["API_ID", "API_HASH", "ADMIN_BOT_TOKEN", "ADMIN_IDS"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
        logger.error("Please check your .env file or Railway/host environment settings.")
        sys.exit(1)


async def main():
    check_env()

    from userbot import UserBot
    from adminbot import AdminBot

    userbot = UserBot()
    adminbot = AdminBot(userbot)

    logger.info("🚀 Starting Telegram Forwarder...")

    await asyncio.gather(
        userbot.start(),
        adminbot.start(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
