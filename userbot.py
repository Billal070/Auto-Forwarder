import logging
import os
from io import BytesIO

from telethon import TelegramClient
from telethon.sessions import StringSession

import storage

logger = logging.getLogger(__name__)


class UserBot:
    def __init__(self):
        self.api_id = int(os.getenv("API_ID", "0"))
        self.api_hash = os.getenv("API_HASH", "")
        session_string = "".join(os.getenv("SESSION_STRING", "").split())

        if session_string:
            logger.info(f"🔑 Session string loaded (length: {len(session_string)})")
        else:
            logger.warning("⚠️ No SESSION_STRING — using file session")

        self.client = TelegramClient(
            StringSession(session_string) if session_string else "data/userbot_session",
            self.api_id,
            self.api_hash,
        )

    async def start(self):
        await self.client.start()
        me = await self.client.get_me()
        logger.info(f"✅ Userbot logged in as @{me.username} ({me.phone})")
        await self.client.run_until_disconnected()

    async def send_message_to(self, destination: str, message) -> bool:
        """Send a message received from admin bot to the destination via userbot."""
        try:
            entity = await self.client.get_entity(destination)

            if message.text:
                await self.client.send_message(entity, message.text)

            elif message.photo:
                file = await message.bot.get_file(message.photo[-1].file_id)
                downloaded = await message.bot.download_file(file.file_path)
                caption = message.caption or ""
                await self.client.send_file(entity, BytesIO(downloaded), caption=caption)

            elif message.video:
                file = await message.bot.get_file(message.video.file_id)
                downloaded = await message.bot.download_file(file.file_path)
                caption = message.caption or ""
                await self.client.send_file(entity, BytesIO(downloaded), caption=caption)

            elif message.document:
                file = await message.bot.get_file(message.document.file_id)
                downloaded = await message.bot.download_file(file.file_path)
                caption = message.caption or ""
                await self.client.send_file(entity, BytesIO(downloaded), caption=caption)

            elif message.audio:
                file = await message.bot.get_file(message.audio.file_id)
                downloaded = await message.bot.download_file(file.file_path)
                caption = message.caption or ""
                await self.client.send_file(entity, BytesIO(downloaded), caption=caption)

            elif message.voice:
                file = await message.bot.get_file(message.voice.file_id)
                downloaded = await message.bot.download_file(file.file_path)
                await self.client.send_file(entity, BytesIO(downloaded), voice_note=True)

            elif message.sticker:
                file = await message.bot.get_file(message.sticker.file_id)
                downloaded = await message.bot.download_file(file.file_path)
                await self.client.send_file(entity, BytesIO(downloaded))

            else:
                logger.warning("⚠️ Unsupported message type")
                return False

            logger.info(f"✅ Sent message to {destination}")
            return True

        except Exception as e:
            logger.error(f"❌ Send error: {type(e).__name__}: {e}", exc_info=True)
            return False

    def is_connected(self) -> bool:
        return self.client.is_connected()
