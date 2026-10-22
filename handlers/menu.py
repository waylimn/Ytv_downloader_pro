"""Main menu, settings, history, stats, help and about."""
from telegram import Update
from telegram.ext import ContextTypes

from database import db
from handlers import common
from handlers.common import edit_any, is_admin, reply
from ui import keyboards as kb
from ui import texts


def _next(cycle, current):
    try:
        return cycle[(cycle.index(current) + 1) % len(cycle)]
    except ValueError:
        return cycle[0]


def render(screen, user):
    """Return (text, markup) for a screen."""
    uid = user.id
    if screen == "home":
        return texts.home(user.first_name or "there"), kb.home(is_admin(uid))
    if screen == "howto":
        return texts.howto(), kb.back_home()
    if screen == "help":
        return texts.help_text(), kb.back_home()
    if screen == "about":
        return texts.about(), kb.back_home()
    if screen == "settings":
        row = db.get_user(uid)
        return texts.settings(row), kb.settings(row)
    if screen == "history":
        rows = db.history(uid, 10)
        return texts.history(rows), kb.history(bool(rows))
    if screen == "stats":
        return texts.stats(db.get_user(uid), db.user_stats(uid)), kb.back_home()
    if screen == "admin":
        from handlers.downloader import ACTIVE
        return texts.admin(db.global_stats(), len(ACTIVE)), kb.admin()
    return texts.home(user.first_name or "there"), kb.home(is_admin(uid))


def _command(screen):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text, markup = render(screen, update.effective_user)
        await reply(update, text, markup)
    return handler


start = _command("home")
menu = _command("home")
help_command = _command("help")
about = _command("about")
settings = _command("settings")
history = _command("history")
stats = _command("stats")


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    screen = q.data.split(":", 1)[1]
    if screen == "admin" and not is_admin(q.from_user.id):
        await q.answer("Admins only.", show_alert=True)
        return
    await q.answer()
    text, markup = render(screen, q.from_user)
    await edit_any(q, text, markup)


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    action = q.data.split(":", 1)[1]
    row = db.get_user(uid)
    if action == "fmt":
        db.set_setting(uid, "def_fmt", _next(texts.FMT_CYCLE, row["def_fmt"]))
    elif action == "aq":
        db.set_setting(uid, "def_audio", _next(texts.AQ_CYCLE, row["def_audio"]))
    elif action == "vq":
        db.set_setting(uid, "def_video", _next(texts.VQ_CYCLE, row["def_video"]))
    await q.answer("✅ Saved")
    text, markup = render("settings", q.from_user)
    await edit_any(q, text, markup)


async def history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.data == "h:clear":
        db.clear_history(q.from_user.id)
        await q.answer("🗑 History cleared")
    else:
        await q.answer()
    text, markup = render("history", q.from_user)
    await edit_any(q, text, markup)
