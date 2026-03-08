import asyncio
import logging
import os
import sys
import threading

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
        sys.exit(1)


def run_admin_bot(adminbot):
    """Run admin bot in its own thread — avoids asyncio conflict with Telethon."""
    logger.info("🎛️ Starting admin bot thread...")
    try:
        adminbot.app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ Admin bot crashed: {e}")


async def main():
    check_env()

    from userbot import UserBot
    from adminbot import AdminBot

    userbot = UserBot()
    adminbot = AdminBot(userbot)

    # Admin bot runs in a separate thread (prevents event loop conflict with Telethon)
    admin_thread = threading.Thread(target=run_admin_bot, args=(adminbot,), daemon=True)
    admin_thread.start()
    logger.info("✅ Admin bot thread started")

    # Userbot runs in the main asyncio loop
    logger.info("🚀 Starting userbot...")
    await userbot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
