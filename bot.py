import asyncio
import logging
import shutil

from telegram import BotCommand, Update
from telegram.ext import (
    Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler,
    MessageHandler, TypeHandler, filters,
)

import config
from database import db
from handlers import admin, common, downloader, menu
from handlers.error import error_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

COMMANDS = [
    ("start", "🏠 Main menu"),
    ("settings", "⚙️ Default format & quality"),
    ("history", "📜 Your recent downloads"),
    ("stats", "📊 Your statistics"),
    ("help", "❓ Help & commands"),
    ("about", "ℹ️ About this bot"),
    ("cancel", "🛑 Cancel / stop"),
]


async def post_init(app: Application):
    try:
        await app.bot.set_my_commands([BotCommand(c, d) for c, d in COMMANDS])
        await app.bot.set_my_short_description("🎵🎬 Download YouTube videos, playlists & audio right inside Telegram.")
        await app.bot.set_my_description(
            "Send me any YouTube link and get it as MP3 or MP4 in the quality you choose — "
            "with live progress, playlists, thumbnails and your own saved settings.")
    except Exception as e:  # noqa: BLE001
        log.warning("Couldn't set bot profile/commands: %s", e)
    me = await app.bot.get_me()
    log.info("Bot started as @%s", me.username)


def main():
    if not config.BOT_TOKEN or "PASTE_YOUR" in config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is missing. Copy .env.example to .env and add your token from @BotFather.")
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is not installed. Termux: pkg install ffmpeg   |   Ubuntu: sudo apt install ffmpeg")

    config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    db.init()

    # Newer Python versions no longer create a default event loop automatically.
    asyncio.set_event_loop(asyncio.new_event_loop())

    builder = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .concurrent_updates(True)
        .connect_timeout(30).read_timeout(30).write_timeout(60).pool_timeout(30)
        .post_init(post_init)
    )
    if config.API_BASE_URL:
        base = config.API_BASE_URL if config.API_BASE_URL.endswith("/bot") else config.API_BASE_URL + "/bot"
        builder = builder.base_url(base).local_mode(True)
    app = builder.build()

    app.add_handler(TypeHandler(Update, common.gate), group=-1)

    app.add_handler(CommandHandler("start", menu.start))
    app.add_handler(CommandHandler("menu", menu.menu))
    app.add_handler(CommandHandler("help", menu.help_command))
    app.add_handler(CommandHandler("about", menu.about))
    app.add_handler(CommandHandler("settings", menu.settings))
    app.add_handler(CommandHandler("history", menu.history))
    app.add_handler(CommandHandler("stats", menu.stats))
    app.add_handler(CommandHandler("cancel", downloader.cancel))
    app.add_handler(CommandHandler("admin", admin.admin_panel))
    app.add_handler(CommandHandler("broadcast", admin.broadcast))
    app.add_handler(CommandHandler("ban", admin.ban))
    app.add_handler(CommandHandler("unban", admin.unban))

    app.add_handler(CallbackQueryHandler(menu.menu_callback, pattern=r"^m:"))
    app.add_handler(CallbackQueryHandler(menu.settings_callback, pattern=r"^s:"))
    app.add_handler(CallbackQueryHandler(menu.history_callback, pattern=r"^h:"))
    app.add_handler(CallbackQueryHandler(downloader.dl_callback, pattern=r"^dl:"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                                   downloader.handle_url))
    app.add_error_handler(error_handler)

    log.info("Starting… press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
