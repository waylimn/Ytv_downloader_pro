"""Shared handler helpers: access gate, safe message editing."""
import logging

from telegram import LinkPreviewOptions, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ApplicationHandlerStop, ContextTypes

import config
from database import db
from ui import texts

log = logging.getLogger(__name__)
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)
HTML = ParseMode.HTML


def is_admin(user_id):
    return user_id in config.ADMIN_IDS


async def gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Runs before every handler: registers the user and blocks banned / non-allowed users."""
    user = update.effective_user
    if not user or user.is_bot:
        return
    db.upsert_user(user.id, user.username, user.first_name)
    if is_admin(user.id):
        return
    denied = None
    if config.ALLOWED_USERS and user.id not in config.ALLOWED_USERS:
        denied = texts.PRIVATE
    elif db.is_banned(user.id):
        denied = texts.BANNED
    if denied:
        if update.callback_query:
            await update.callback_query.answer(denied, show_alert=True)
        elif update.effective_message:
            await update.effective_message.reply_text(denied)
        raise ApplicationHandlerStop


async def reply(update: Update, text, markup=None):
    return await update.effective_message.reply_text(
        text, parse_mode=HTML, reply_markup=markup, link_preview_options=NO_PREVIEW
    )


async def edit_any(query, text, markup=None):
    """Edit the callback message; if it's a photo card, replace it with a text message."""
    msg = query.message
    try:
        if msg is not None and msg.photo:
            chat = msg.chat
            await msg.delete()
            await chat.send_message(text, parse_mode=HTML, reply_markup=markup,
                                    link_preview_options=NO_PREVIEW)
        else:
            await query.edit_message_text(text, parse_mode=HTML, reply_markup=markup,
                                          link_preview_options=NO_PREVIEW)
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise


async def edit_card(bot, chat_id, message_id, is_photo, text, markup=None):
    """Edit a card (photo caption or plain text). Never raises – used for live progress."""
    try:
        if is_photo:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=text,
                                           parse_mode=HTML, reply_markup=markup)
        else:
            await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id,
                                        parse_mode=HTML, reply_markup=markup,
                                        link_preview_options=NO_PREVIEW)
        return True
    except TelegramError as e:
        if "not modified" not in str(e).lower():
            log.debug("edit_card failed: %s", e)
        return False
