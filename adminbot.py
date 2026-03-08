import asyncio
import functools
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import storage

logger = logging.getLogger(__name__)

# Parse admin IDs from env (comma-separated)
_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(x.strip()) for x in _raw.split(",") if x.strip().isdigit()]


# ── Auth decorator ──────────────────────────────────────────────────────────

def admin_only(func):
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if ADMIN_IDS and user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔ You are not authorized to use this bot.")
            return
        return await func(self, update, context)
    return wrapper


# ── Admin Bot class ─────────────────────────────────────────────────────────

class AdminBot:
    def __init__(self, userbot):
        self.userbot = userbot
        token = os.getenv("ADMIN_BOT_TOKEN", "")
        if not token:
            raise ValueError("ADMIN_BOT_TOKEN is not set!")
        self.app = Application.builder().token(token).build()
        self._register_handlers()

    def _register_handlers(self):
        handlers = [
            ("start",          self.cmd_start),
            ("help",           self.cmd_help),
            ("addsource",      self.cmd_add_source),
            ("removesource",   self.cmd_remove_source),
            ("sources",        self.cmd_sources),
            ("setdestination", self.cmd_set_destination),
            ("startforward",   self.cmd_start_forward),
            ("stopforward",    self.cmd_stop_forward),
            ("status",         self.cmd_status),
        ]
        for name, handler in handlers:
            self.app.add_handler(CommandHandler(name, handler))

    # ── Commands ─────────────────────────────────────────────────────────────

    @admin_only
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "👋 *Telegram Forwarder — Admin Panel*\n\n"
            "Use /help to see all available commands."
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    @admin_only
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "📋 *Available Commands*\n\n"
            "➕ *Sources*\n"
            "`/addsource @username` — Add a source channel\n"
            "`/removesource @username` — Remove a source channel\n"
            "`/sources` — List all source channels\n\n"
            "📤 *Destination*\n"
            "`/setdestination @username` — Set destination channel\n\n"
            "▶️ *Forwarding*\n"
            "`/startforward` — Start auto-forwarding\n"
            "`/stopforward` — Stop auto-forwarding\n\n"
            "ℹ️ *Info*\n"
            "`/status` — Show current status\n"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    @admin_only
    async def cmd_add_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Usage: `/addsource @channelname` or `/addsource https://t.me/channelname`",
                parse_mode="Markdown"
            )
            return
        link = context.args[0]
        added = storage.add_source(link)
        if added:
            await update.message.reply_text(f"✅ Added source: `{link}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ Source `{link}` already exists.", parse_mode="Markdown")

    @admin_only
    async def cmd_remove_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Usage: `/removesource @channelname`",
                parse_mode="Markdown"
            )
            return
        link = context.args[0]
        removed = storage.remove_source(link)
        if removed:
            await update.message.reply_text(f"🗑️ Removed source: `{link}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ Source `{link}` not found.", parse_mode="Markdown")

    @admin_only
    async def cmd_sources(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        config = storage.load_config()
        sources = config.get("sources", [])
        if not sources:
            await update.message.reply_text("📭 No source channels added yet.\nUse `/addsource` to add one.", parse_mode="Markdown")
            return
        lines = "\n".join(f"• `{s}`" for s in sources)
        await update.message.reply_text(f"📡 *Source Channels ({len(sources)}):*\n\n{lines}", parse_mode="Markdown")

    @admin_only
    async def cmd_set_destination(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "Usage: `/setdestination @channelname` or `/setdestination https://t.me/channelname`",
                parse_mode="Markdown"
            )
            return
        link = context.args[0]
        storage.set_destination(link)
        await update.message.reply_text(f"✅ Destination set to: `{link}`", parse_mode="Markdown")

    @admin_only
    async def cmd_start_forward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        config = storage.load_config()
        if not config.get("sources"):
            await update.message.reply_text("⚠️ No sources added. Use `/addsource` first.", parse_mode="Markdown")
            return
        if not config.get("destination"):
            await update.message.reply_text("⚠️ No destination set. Use `/setdestination` first.", parse_mode="Markdown")
            return
        storage.set_forwarding(True)
        await update.message.reply_text("▶️ *Forwarding started!*\nMessages from sources will now be forwarded.", parse_mode="Markdown")

    @admin_only
    async def cmd_stop_forward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        storage.set_forwarding(False)
        await update.message.reply_text("⏹️ *Forwarding stopped.*", parse_mode="Markdown")

    @admin_only
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        config = storage.load_config()
        sources = config.get("sources", [])
        destination = config.get("destination") or "Not set"
        is_forwarding = config.get("is_forwarding", False)
        connected = self.userbot.is_connected()

        status_icon = "▶️ Running" if is_forwarding else "⏹️ Stopped"
        conn_icon = "🟢 Connected" if connected else "🔴 Disconnected"
        src_list = "\n".join(f"  • `{s}`" for s in sources) if sources else "  _None_"

        text = (
            f"📊 *Forwarder Status*\n\n"
            f"🔗 *Userbot:* {conn_icon}\n"
            f"⚙️ *Forwarding:* {status_icon}\n\n"
            f"📡 *Sources ({len(sources)}):*\n{src_list}\n\n"
            f"📤 *Destination:* `{destination}`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
