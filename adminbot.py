import logging
import os
import functools

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message

import storage

logger = logging.getLogger(__name__)

_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(x.strip()) for x in _raw.split(",") if x.strip().isdigit()]

router = Router()

# Shared reference to userbot (set from main.py)
_userbot = None

def set_userbot(userbot):
    global _userbot
    _userbot = userbot


def admin_only(func):
    @functools.wraps(func)
    async def wrapper(message: Message, **kwargs):
        if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
            await message.answer("⛔ You are not authorized.")
            return
        return await func(message, **kwargs)
    return wrapper


@router.message(Command("start"))
@admin_only
async def cmd_start(message: Message):
    await message.answer(
        "👋 *Telegram Forwarder — Admin Panel*\n\n"
        "Just send me any message and I'll forward it to the target group!\n\n"
        "Use /help to see all commands.",
        parse_mode="Markdown"
    )


@router.message(Command("help"))
@admin_only
async def cmd_help(message: Message):
    await message.answer(
        "📋 *Commands*\n\n"
        "📤 *Forwarding*\n"
        "`/setdestination @username` — Set target group/channel\n"
        "`/startforward` — Enable forwarding\n"
        "`/stopforward` — Disable forwarding\n"
        "`/status` — Show current status\n\n"
        "💬 *How to use*\n"
        "Just send any message here (text, photo, video, etc.) "
        "and the userbot will forward it to the target group automatically!",
        parse_mode="Markdown"
    )


@router.message(Command("setdestination"))
@admin_only
async def cmd_set_destination(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: `/setdestination @groupname`", parse_mode="Markdown")
        return
    link = parts[1].strip()
    storage.set_destination(link)
    await message.answer(f"✅ Target set to: `{link}`", parse_mode="Markdown")


@router.message(Command("startforward"))
@admin_only
async def cmd_start_forward(message: Message):
    config = storage.load_config()
    if not config.get("destination"):
        await message.answer("⚠️ No target set. Use `/setdestination` first.", parse_mode="Markdown")
        return
    storage.set_forwarding(True)
    await message.answer(
        "▶️ *Forwarding enabled!*\n\nSend me any message and I'll forward it to the target group.",
        parse_mode="Markdown"
    )


@router.message(Command("stopforward"))
@admin_only
async def cmd_stop_forward(message: Message):
    storage.set_forwarding(False)
    await message.answer("⏹️ *Forwarding stopped.*", parse_mode="Markdown")


@router.message(Command("status"))
@admin_only
async def cmd_status(message: Message):
    config = storage.load_config()
    destination = config.get("destination") or "Not set"
    is_forwarding = config.get("is_forwarding", False)
    connected = _userbot.is_connected() if _userbot else False

    status_icon = "▶️ Enabled" if is_forwarding else "⏹️ Disabled"
    conn_icon = "🟢 Connected" if connected else "🔴 Disconnected"

    await message.answer(
        f"📊 *Status*\n\n"
        f"🤖 *Userbot:* {conn_icon}\n"
        f"⚙️ *Forwarding:* {status_icon}\n"
        f"📤 *Target:* `{destination}`",
        parse_mode="Markdown"
    )


@router.message(~F.text.startswith("/"))
@admin_only
async def handle_forward_message(message: Message):
    """Forward any non-command message to the target group via userbot."""
    config = storage.load_config()

    if not config.get("is_forwarding"):
        await message.answer("⏹️ Forwarding is OFF. Use `/startforward` to enable.", parse_mode="Markdown")
        return

    destination = config.get("destination")
    if not destination:
        await message.answer("⚠️ No target set. Use `/setdestination` first.", parse_mode="Markdown")
        return

    if not _userbot or not _userbot.is_connected():
        await message.answer("❌ Userbot is not connected. Check Railway logs.", parse_mode="Markdown")
        return

    # Get the message content and send via userbot
    success = await _userbot.send_message_to(destination, message)

    if success:
        await message.answer("✅ Forwarded!")
    else:
        await message.answer("❌ Failed to forward. Check Railway logs.")


class AdminBot:
    def __init__(self, userbot):
        token = os.getenv("ADMIN_BOT_TOKEN", "")
        if not token:
            raise ValueError("ADMIN_BOT_TOKEN is not set!")
        set_userbot(userbot)
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.dp.include_router(router)

    async def run(self):
        logger.info("✅ Admin bot polling started")
        await self.dp.start_polling(self.bot, drop_pending_updates=True)
