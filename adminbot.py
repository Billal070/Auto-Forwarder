import logging
import os
import functools

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

import storage

logger = logging.getLogger(__name__)

_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(x.strip()) for x in _raw.split(",") if x.strip().isdigit()]

router = Router()


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
        "👋 *Telegram Forwarder — Admin Panel*\n\nUse /help to see all commands.",
        parse_mode="Markdown"
    )


@router.message(Command("help"))
@admin_only
async def cmd_help(message: Message):
    await message.answer(
        "📋 *Commands*\n\n"
        "`/addsource @username` — Add source channel\n"
        "`/removesource @username` — Remove source channel\n"
        "`/sources` — List sources\n"
        "`/setdestination @username` — Set destination\n"
        "`/startforward` — Start forwarding\n"
        "`/stopforward` — Stop forwarding\n"
        "`/status` — Show status",
        parse_mode="Markdown"
    )


@router.message(Command("addsource"))
@admin_only
async def cmd_add_source(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: `/addsource @channelname`", parse_mode="Markdown")
        return
    link = parts[1].strip()
    if storage.add_source(link):
        await message.answer(f"✅ Added source: `{link}`", parse_mode="Markdown")
    else:
        await message.answer(f"⚠️ Source `{link}` already exists.", parse_mode="Markdown")


@router.message(Command("removesource"))
@admin_only
async def cmd_remove_source(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: `/removesource @channelname`", parse_mode="Markdown")
        return
    link = parts[1].strip()
    if storage.remove_source(link):
        await message.answer(f"🗑️ Removed: `{link}`", parse_mode="Markdown")
    else:
        await message.answer(f"⚠️ Not found: `{link}`", parse_mode="Markdown")


@router.message(Command("sources"))
@admin_only
async def cmd_sources(message: Message):
    config = storage.load_config()
    sources = config.get("sources", [])
    if not sources:
        await message.answer("📭 No sources yet. Use `/addsource` to add one.", parse_mode="Markdown")
        return
    lines = "\n".join(f"• `{s}`" for s in sources)
    await message.answer(f"📡 *Sources ({len(sources)}):*\n\n{lines}", parse_mode="Markdown")


@router.message(Command("setdestination"))
@admin_only
async def cmd_set_destination(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: `/setdestination @channelname`", parse_mode="Markdown")
        return
    link = parts[1].strip()
    storage.set_destination(link)
    await message.answer(f"✅ Destination set to: `{link}`", parse_mode="Markdown")


@router.message(Command("startforward"))
@admin_only
async def cmd_start_forward(message: Message):
    config = storage.load_config()
    if not config.get("sources"):
        await message.answer("⚠️ No sources added. Use `/addsource` first.", parse_mode="Markdown")
        return
    if not config.get("destination"):
        await message.answer("⚠️ No destination set. Use `/setdestination` first.", parse_mode="Markdown")
        return
    storage.set_forwarding(True)
    await message.answer("▶️ *Forwarding started!*", parse_mode="Markdown")


@router.message(Command("stopforward"))
@admin_only
async def cmd_stop_forward(message: Message):
    storage.set_forwarding(False)
    await message.answer("⏹️ *Forwarding stopped.*", parse_mode="Markdown")


@router.message(Command("status"))
@admin_only
async def cmd_status(message: Message):
    config = storage.load_config()
    sources = config.get("sources", [])
    destination = config.get("destination") or "Not set"
    is_forwarding = config.get("is_forwarding", False)

    status_icon = "▶️ Running" if is_forwarding else "⏹️ Stopped"
    src_list = "\n".join(f"  • `{s}`" for s in sources) if sources else "  _None_"

    await message.answer(
        f"📊 *Forwarder Status*\n\n"
        f"⚙️ *Forwarding:* {status_icon}\n\n"
        f"📡 *Sources ({len(sources)}):*\n{src_list}\n\n"
        f"📤 *Destination:* `{destination}`",
        parse_mode="Markdown"
    )


class AdminBot:
    def __init__(self):
        token = os.getenv("ADMIN_BOT_TOKEN", "")
        if not token:
            raise ValueError("ADMIN_BOT_TOKEN is not set!")
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.dp.include_router(router)

    async def run(self):
        logger.info("✅ Admin bot polling started")
        await self.dp.start_polling(self.bot, drop_pending_updates=True)
