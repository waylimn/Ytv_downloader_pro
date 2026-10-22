"""The download flow: link → card → format → quality → live job."""
import asyncio
import logging
import secrets
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from telegram import Update
from telegram.error import RetryAfter, TelegramError
from telegram.ext import ContextTypes

import config
from database import db
from handlers.common import HTML, edit_card, is_admin, reply
from services import youtube
from services.utils import find_youtube_url, friendly_error, thumb_urls, truncate
from ui import keyboards as kb
from ui import texts

log = logging.getLogger(__name__)

PENDING = {}   # token -> selection state (cards waiting for the user to click)
ACTIVE = {}    # user_id -> running Job
LAST_REQ = {}  # user_id -> monotonic time of last link request
_sem = asyncio.Semaphore(config.MAX_CONCURRENT_JOBS)

UPLOAD_TIMEOUT = 900


@dataclass
class Job:
    token: str
    user_id: int
    chat_id: int
    message_id: int
    is_photo: bool
    info: dict
    fmt: str
    quality: str
    items: list
    progress: youtube.Progress = field(default_factory=youtube.Progress)
    cancel: threading.Event = field(default_factory=threading.Event)
    index: int = 1
    title: str = ""

    @property
    def total(self):
        return len(self.items)


def _purge():
    now = time.time()
    for tok in [t for t, s in PENDING.items() if now - s["created"] > config.PENDING_TTL]:
        PENDING.pop(tok, None)


def _clean(workdir):
    for child in Path(workdir).iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


# ───────────────────────── link received ─────────────────────────
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    url = find_youtube_url(msg.text)
    if not url:
        await reply(update, texts.NOT_A_LINK, kb.back_home())
        return
    if user.id in ACTIVE:
        await reply(update, texts.BUSY)
        return
    now = time.monotonic()
    if not is_admin(user.id) and now - LAST_REQ.get(user.id, 0) < config.COOLDOWN_SECONDS:
        await reply(update, texts.COOLDOWN)
        return
    LAST_REQ[user.id] = now

    status = await reply(update, texts.ANALYSING)
    try:
        info = await asyncio.to_thread(youtube.inspect_url, url)
    except Exception as e:  # noqa: BLE001
        log.warning("Inspect failed for %s: %s", url, e)
        await status.edit_text(texts.lookup_failed(friendly_error(e)), parse_mode=HTML,
                               reply_markup=kb.back_home())
        return

    if (info["kind"] == "video" and config.MAX_VIDEO_MINUTES
            and (info.get("duration") or 0) > config.MAX_VIDEO_MINUTES * 60):
        await status.edit_text(
            f"⏱ This video is longer than the allowed <b>{config.MAX_VIDEO_MINUTES} minutes</b>.",
            parse_mode=HTML, reply_markup=kb.back_home())
        return

    _purge()
    token = secrets.token_hex(4)
    if info["kind"] == "playlist":
        prompt = texts.PROMPT_SCOPE + texts.playlist_scope_note(info)
        markup = kb.scope(token, info["count"])
        thumb_id = info["thumb_id"]
    else:
        prompt = texts.PROMPT_VIDEO
        markup = kb.card_video(token, has_playlist=bool(info.get("playlist_id")))
        thumb_id = info.get("id")

    caption = texts.card(info, prompt)
    card_msg, is_photo = None, False
    for photo_url in thumb_urls(thumb_id) if thumb_id else []:
        try:
            card_msg = await msg.reply_photo(photo=photo_url, caption=caption, parse_mode=HTML,
                                             reply_markup=markup)
            is_photo = True
            break
        except TelegramError:
            continue
    if card_msg:
        try:
            await status.delete()
        except TelegramError:
            pass
    else:
        await status.edit_text(caption, parse_mode=HTML, reply_markup=markup)
        card_msg = status

    PENDING[token] = {
        "user_id": user.id, "chat_id": card_msg.chat_id, "message_id": card_msg.message_id,
        "is_photo": is_photo, "info": info, "url": url, "fmt": None, "limit": None,
        "created": time.time(),
    }

    # Quick mode: user's saved default action → start immediately for single videos
    row = db.get_user(user.id)
    if info["kind"] == "video" and row and row["def_fmt"] in ("mp3", "mp4"):
        fmt = row["def_fmt"]
        quality = f"a{row['def_audio']}" if fmt == "mp3" else row["def_video"]
        _start_job(context.application, token, fmt, quality)


# ───────────────────────── card buttons ─────────────────────────
async def dl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    parts = q.data.split(":")
    action, tok = parts[1], parts[2]
    arg = parts[3] if len(parts) > 3 else None

    if action == "stop":
        job = ACTIVE.get(q.from_user.id)
        if job and job.token == tok:
            job.cancel.set()
            await q.answer("🛑 Stopping…")
        else:
            await q.answer("Nothing to stop.")
        return

    st = PENDING.get(tok)
    if not st:
        await q.answer(texts.EXPIRED, show_alert=True)
        return
    if st["user_id"] != q.from_user.id:
        await q.answer(texts.NOT_YOURS, show_alert=True)
        return

    info = st["info"]
    bot = context.bot

    async def show(prompt, markup):
        await edit_card(bot, st["chat_id"], st["message_id"], st["is_photo"],
                        texts.card(st["info"], prompt), markup)

    if action == "x":
        PENDING.pop(tok, None)
        await q.answer("Cancelled")
        await edit_card(bot, st["chat_id"], st["message_id"], st["is_photo"],
                        "❎ <b>Cancelled.</b>\nSend another YouTube link whenever you're ready.",
                        kb.back_home())

    elif action == "thumb":
        await q.answer("🖼 Sending thumbnail…")
        for photo_url in thumb_urls(info.get("id")):
            try:
                await bot.send_photo(st["chat_id"], photo=photo_url,
                                     caption=f"🖼 <b>{texts.esc(truncate(info['title'], 150))}</b>",
                                     parse_mode=HTML)
                break
            except TelegramError:
                continue
        else:
            await bot.send_message(st["chat_id"], "⚠️ Couldn't fetch the thumbnail for this video.")

    elif action == "pl":
        await q.answer("📃 Loading playlist…")
        await edit_card(bot, st["chat_id"], st["message_id"], st["is_photo"],
                        "📃 <b>Loading playlist…</b>", None)
        try:
            new_info = await asyncio.to_thread(youtube.inspect_url, st["url"], True)
        except Exception as e:  # noqa: BLE001
            await show(f"{friendly_error(e)}\n\n{texts.PROMPT_VIDEO}",
                       kb.card_video(tok, has_playlist=True))
            return
        st["info"] = new_info
        await show(texts.PROMPT_SCOPE + texts.playlist_scope_note(new_info),
                   kb.scope(tok, new_info["count"]))

    elif action == "scope":
        st["limit"] = max(1, min(int(arg), config.MAX_PLAYLIST_ITEMS, info.get("count") or 1))
        await q.answer()
        await show(texts.PROMPT_FORMAT, kb.formats(tok, "scope"))

    elif action == "fmt":
        st["fmt"] = arg
        await q.answer()
        if arg == "mp3":
            await show(texts.PROMPT_AUDIO, kb.audio_quality(tok, info))
        else:
            await show(texts.PROMPT_VIDEO_Q, kb.video_quality(tok, info))

    elif action == "back":
        await q.answer()
        if info["kind"] == "video":
            await show(texts.PROMPT_VIDEO, kb.card_video(tok, has_playlist=bool(info.get("playlist_id"))))
        elif arg == "scope":
            await show(texts.PROMPT_SCOPE + texts.playlist_scope_note(info), kb.scope(tok, info["count"]))
        else:
            await show(texts.PROMPT_FORMAT, kb.formats(tok, "scope"))

    elif action == "q":
        fmt = st.get("fmt")
        if fmt not in ("mp3", "mp4"):
            await q.answer("Choose audio or video first.", show_alert=True)
            return
        if q.from_user.id in ACTIVE:
            await q.answer("You already have a download running.", show_alert=True)
            return
        await q.answer("🚀 Starting…")
        _start_job(context.application, tok, fmt, arg)

    else:
        await q.answer()


# ───────────────────────── job lifecycle ─────────────────────────
def _start_job(app, token, fmt, quality):
    st = PENDING.pop(token, None)
    if not st or st["user_id"] in ACTIVE:
        return
    info = st["info"]
    if info["kind"] == "playlist":
        limit = st.get("limit") or config.MAX_PLAYLIST_ITEMS
        items = info["entries"][:limit]
    else:
        items = [{"url": info["url"], "title": info["title"], "id": info["id"]}]
    job = Job(token=token, user_id=st["user_id"], chat_id=st["chat_id"], message_id=st["message_id"],
              is_photo=st["is_photo"], info=info, fmt=fmt, quality=quality, items=items,
              title=items[0].get("title") or info["title"])
    ACTIVE[job.user_id] = job
    app.create_task(_run_job(app, job))


async def _progress_loop(bot, job):
    last = None
    while True:
        text = texts.progress(job)
        if text != last:
            await edit_card(bot, job.chat_id, job.message_id, job.is_photo, text, kb.stop(job.token))
            last = text
        await asyncio.sleep(2.5)


async def _run_job(app, job):
    bot = app.bot
    sent = failed = 0
    limit_hit = False
    updater = None
    workdir = None
    try:
        config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        workdir = tempfile.mkdtemp(prefix="ytv_", dir=str(config.TEMP_DIR))
        if _sem.locked():
            await edit_card(bot, job.chat_id, job.message_id, job.is_photo,
                            texts.queued(job), kb.stop(job.token))
        async with _sem:
            updater = asyncio.create_task(_progress_loop(bot, job))
            for idx, item in enumerate(job.items, 1):
                if job.cancel.is_set():
                    break
                if (config.DAILY_LIMIT and not is_admin(job.user_id)
                        and db.count_today(job.user_id) >= config.DAILY_LIMIT):
                    limit_hit = True
                    break
                job.index = idx
                job.title = item.get("title") or job.info["title"]
                job.progress.reset()
                result = await _process_item(bot, job, item, workdir)
                if result == "done":
                    sent += 1
                elif result != "cancelled":
                    failed += 1
    except Exception:  # noqa: BLE001
        log.exception("Job crashed")
        failed = max(failed, job.total - sent)
    finally:
        if updater:
            updater.cancel()
        if workdir:
            shutil.rmtree(workdir, ignore_errors=True)
        ACTIVE.pop(job.user_id, None)
        await edit_card(bot, job.chat_id, job.message_id, job.is_photo,
                        texts.finished(job, sent, failed, job.cancel.is_set(), limit_hit), kb.done())


async def _process_item(bot, job, item, workdir):
    name = item.get("title") or job.info["title"]
    log_args = (job.user_id, name, item["url"], job.fmt, job.quality)
    try:
        meta = await asyncio.to_thread(youtube.download_one, item["url"], job.fmt, job.quality,
                                       workdir, job.progress, job.cancel)
    except Exception as e:  # noqa: BLE001
        _clean(workdir)
        if job.cancel.is_set():
            db.log_download(*log_args, "cancelled")
            return "cancelled"
        log.warning("Download failed for %s: %s", item["url"], e)
        await bot.send_message(job.chat_id, texts.item_failed(name, friendly_error(e)), parse_mode=HTML)
        db.log_download(*log_args, "failed")
        return "failed"

    path = Path(meta["path"])
    try:
        size = path.stat().st_size
        if size > config.MAX_UPLOAD_BYTES:
            await bot.send_message(job.chat_id, texts.too_large(name, size), parse_mode=HTML)
            db.log_download(*log_args, "skipped", size)
            return "skipped"
        job.progress.phase = "uploading"
        await _upload(bot, job, path, meta, size)
        db.log_download(*log_args, "done", size)
        return "done"
    except Exception as e:  # noqa: BLE001
        log.exception("Upload failed for %s", path.name)
        await bot.send_message(job.chat_id,
                               texts.item_failed(name, "📤 Upload failed: " + texts.esc(truncate(str(e), 150))),
                               parse_mode=HTML)
        db.log_download(*log_args, "failed")
        return "failed"
    finally:
        _clean(workdir)


async def _upload(bot, job, path, meta, size):
    label = texts.quality_label(job.fmt, job.quality)
    title = meta.get("title") or job.title
    caption = texts.media_caption(title, meta.get("uploader"), size, label, bot.username)
    duration = int(meta["duration"]) if meta.get("duration") else None
    common = dict(chat_id=job.chat_id, caption=caption, parse_mode=HTML, duration=duration,
                  read_timeout=UPLOAD_TIMEOUT, write_timeout=UPLOAD_TIMEOUT,
                  connect_timeout=30, pool_timeout=30)
    for attempt in (1, 2):
        try:
            with path.open("rb") as f:
                if job.fmt == "mp3":
                    await bot.send_audio(audio=f, filename=path.name, title=title[:100],
                                         performer=(meta.get("uploader") or "")[:100] or None, **common)
                else:
                    await bot.send_video(video=f, filename=path.name, width=meta.get("width"),
                                         height=meta.get("height"), supports_streaming=True, **common)
            return
        except RetryAfter as e:
            if attempt == 2:
                raise
            await asyncio.sleep(e.retry_after + 1)


# ───────────────────────── /cancel ─────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    removed = [t for t, s in PENDING.items() if s["user_id"] == uid]
    for t in removed:
        PENDING.pop(t, None)
    job = ACTIVE.get(uid)
    if job:
        job.cancel.set()
        await reply(update, "🛑 Stopping your running download…")
    elif removed:
        await reply(update, "❎ Pending selection cancelled. Send another link anytime.")
    else:
        await reply(update, "👍 Nothing to cancel.")
