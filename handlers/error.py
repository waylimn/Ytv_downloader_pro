import logging

from telegram import Update
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Unhandled error", exc_info=context.error)
    if isinstance(update, Update):
        try:
            if update.callback_query:
                await update.callback_query.answer("⚠️ Something went wrong. Please try again.", show_alert=True)
            elif update.effective_message:
                await update.effective_message.reply_text("⚠️ Something went wrong. Please try again.")
        except Exception:  # noqa: BLE001
            pass
