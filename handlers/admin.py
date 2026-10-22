"""Admin-only commands: /admin /broadcast /ban /unban."""
import asyncio
import logging

from telegram import Update
from telegram.error import Forbidden, RetryAfter, TelegramError
from telegram.ext import ContextTypes

import config
from database import db
from handlers.common import HTML, is_admin, reply
from handlers.menu import render

log = logging.getLogger(__name__)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await reply(update, "🔒 Admins only.")
        return
    text, markup = render("admin", update.effective_user)
    await reply(update, text, markup)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = " ".join(context.args).strip()
    if not text:
        await reply(update, "Usage: <code>/broadcast your message</code>")
        return
    ids = db.all_user_ids()
    status = await reply(update, f"📢 Sending to <b>{len(ids)}</b> users…")

    async def run():
        ok = fail = 0
        for uid in ids:
            try:
                await context.bot.send_message(uid, f"📢 {text}")
                ok += 1
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
                try:
                    await context.bot.send_message(uid, f"📢 {text}")
                    ok += 1
                except TelegramError:
                    fail += 1
            except (Forbidden, TelegramError):
                fail += 1
            await asyncio.sleep(0.05)
        await status.edit_text(f"📢 Broadcast finished\n✅ Delivered: {ok}\n⚠️ Failed: {fail}")

    context.application.create_task(run())


async def _set_ban(update, context, banned):
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].lstrip("-").isdigit():
        await reply(update, f"Usage: <code>/{'ban' if banned else 'unban'} user_id</code>")
        return
    uid = int(context.args[0])
    if uid in config.ADMIN_IDS:
        await reply(update, "⚠️ You can't ban an admin.")
        return
    if db.set_banned(uid, banned):
        await reply(update, f"{'🚫 Banned' if banned else '✅ Unbanned'} <code>{uid}</code>")
    else:
        await reply(update, "❓ That user hasn't used the bot yet.")


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _set_ban(update, context, True)


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _set_ban(update, context, False)
