import logging
import os

from telethon import TelegramClient, events
from telethon.sessions import StringSession

import storage

logger = logging.getLogger(__name__)


def parse_username(src: str) -> str:
    """Extract clean username or ID from any Telegram link format."""
    src = src.strip()
    # Handle t.me/username or t.me/username/123 (message links)
    for prefix in ["https://t.me/", "http://t.me/", "t.me/"]:
        if src.startswith(prefix):
            src = src[len(prefix):]
    # Remove message ID suffix (e.g. channel/123)
    src = src.split("/")[0]
    # Remove leading @
    src = src.lstrip("@")
    return src.lower()


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
        self._register_handler()
        await self.client.run_until_disconnected()

    def _register_handler(self):

        @self.client.on(events.NewMessage(incoming=True))
        async def on_new_message(event):
            try:
                config = storage.load_config()

                if not config.get("is_forwarding"):
                    return

                destination = config.get("destination")
                if not destination:
                    return

                sources = config.get("sources", [])
                if not sources:
                    return

                # Get chat info
                chat = await event.get_chat()
                chat_username = getattr(chat, "username", None) or ""
                chat_id = event.chat_id

                # Build set of parsed source identifiers
                matched = False
                for src in sources:
                    src_clean = parse_username(src)

                    # Match by username
                    if chat_username and src_clean == chat_username.lower():
                        matched = True
                        break

                    # Match by numeric ID (handle -100 prefix for supergroups/channels)
                    src_id = src_clean.lstrip("-")
                    cid = str(abs(chat_id))
                    if src_id == cid or src_id == cid.lstrip("100"):
                        matched = True
                        break

                if not matched:
                    return

                logger.info(f"📨 Forwarding from {chat_username or chat_id} → {destination}")

                # Resolve destination entity fresh each time (handles username changes)
                dest_entity = await self.client.get_entity(destination)
                await self.client.forward_messages(dest_entity, event.message)
                logger.info(f"✅ Forwarded successfully!")

            except Exception as e:
                logger.error(f"❌ Forward error: {type(e).__name__}: {e}", exc_info=True)

    def is_connected(self) -> bool:
        return self.client.is_connected()
