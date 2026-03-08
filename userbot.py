import asyncio
import logging
import os

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat

import storage

logger = logging.getLogger(__name__)


class UserBot:
    def __init__(self):
        self.api_id = int(os.getenv("API_ID", "0"))
        self.api_hash = os.getenv("API_HASH", "")
        session_string = os.getenv("SESSION_STRING", "").strip()

        self.client = TelegramClient(
            StringSession(session_string) if session_string else "data/userbot_session",
            self.api_id,
            self.api_hash,
        )
        self._handler_registered = False

    async def start(self):
        await self.client.start()
        me = await self.client.get_me()
        logger.info(f"✅ Userbot started as @{me.username} ({me.phone})")
        self._register_handler()
        await self.client.run_until_disconnected()

    def _register_handler(self):
        if self._handler_registered:
            return
        self._handler_registered = True

        @self.client.on(events.NewMessage())
        async def on_new_message(event):
            config = storage.load_config()

            if not config.get("is_forwarding"):
                return

            destination = config.get("destination")
            if not destination:
                return

            sources = config.get("sources", [])
            if not sources:
                return

            try:
                chat = await event.get_chat()
                username = getattr(chat, "username", None)
                chat_id = event.chat_id

                # Match source: by @username, t.me/link, or raw chat_id
                matched = False
                for src in sources:
                    src_clean = src.strip().lstrip("@").replace("https://t.me/", "").replace("http://t.me/", "")
                    if username and src_clean.lower() == username.lower():
                        matched = True
                        break
                    if str(chat_id) in src:
                        matched = True
                        break

                if not matched:
                    return

                await self.client.forward_messages(destination, event.message)
                logger.info(f"📨 Forwarded message from {username or chat_id} → {destination}")

            except Exception as e:
                logger.error(f"❌ Forward error: {e}")

    async def get_me(self):
        try:
            return await self.client.get_me()
        except Exception:
            return None

    def is_connected(self) -> bool:
        return self.client.is_connected()
