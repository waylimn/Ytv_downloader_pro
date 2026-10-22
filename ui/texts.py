"""All user-facing message text (Telegram HTML)."""
import config
from services.utils import (
    esc, human_count, human_date, human_duration, human_size, progress_bar, truncate, ts_date,
)

BRAND = "YT Downloader Pro"

FMT_LABEL = {"ask": "🤔 Ask every time", "mp3": "🎵 Always MP3", "mp4": "🎬 Always MP4"}
FMT_CYCLE = ["ask", "mp3", "mp4"]
AQ_CYCLE = ["128", "192", "320"]
VQ_CYCLE = ["best", "1080", "720", "480", "360"]


def video_label(q):
    return "Best" if q == "best" else f"{q}p"


def quality_label(fmt, quality):
    if fmt == "mp3":
        return f"MP3 · {quality.lstrip('a')} kbps"
    return f"MP4 · {video_label(quality)}"


# ───────────────────────── menus ─────────────────────────
def home(name):
    return (
        f"🤖 <b>{BRAND}</b>\n\n"
        f"👋 Hello, <b>{esc(name)}</b>!\n\n"
        "Send me any <b>YouTube</b> link and I'll deliver it right here in chat:\n\n"
        "🎵 <b>MP3</b> — 128 / 192 / 320 kbps\n"
        "🎬 <b>MP4</b> — Best, 1080p, 720p, 480p, 360p\n"
        "📃 <b>Playlists</b> — sent one by one\n"
        "🖼 <b>Thumbnails</b> — HD cover images\n\n"
        "👇 Paste a link, or pick an option below."
    )


def howto():
    return (
        "📥 <b>How to use</b>\n\n"
        "1️⃣ Copy a YouTube video or playlist link\n"
        "2️⃣ Paste it here in the chat\n"
        "3️⃣ Choose 🎵 Audio or 🎬 Video\n"
        "4️⃣ Pick the quality (file sizes are estimated)\n"
        "5️⃣ Watch the live progress bar — your file arrives in chat ✅\n\n"
        "💡 <b>Tips</b>\n"
        "• Use ⚙️ Settings to skip menus with your favourite quality\n"
        f"• Telegram bots can upload up to <b>{config.MAX_UPLOAD_MB} MB</b> per file — pick a lower quality for long videos\n"
        f"• Playlists: up to <b>{config.MAX_PLAYLIST_ITEMS}</b> items per request\n"
        "• Tap 🛑 Stop at any time to cancel a running download"
    )


def help_text():
    return (
        "❓ <b>Help &amp; commands</b>\n\n"
        "/start — main menu\n"
        "/menu — main menu\n"
        "/settings — default format &amp; quality\n"
        "/history — your last downloads\n"
        "/stats — your usage statistics\n"
        "/about — about this bot\n"
        "/cancel — cancel a pending selection\n\n"
        "Just paste a YouTube link to begin 🚀"
    )


def about():
    return (
        f"ℹ️ <b>{BRAND}</b>\n\n"
        "⚡ Powered by <b>yt-dlp</b> + <b>ffmpeg</b>\n"
        "🔒 Files are processed temporarily and deleted right after sending\n"
        f"📦 Upload limit: <b>{config.MAX_UPLOAD_MB} MB</b>\n"
        f"🧵 Parallel jobs: <b>{config.MAX_CONCURRENT_JOBS}</b>\n\n"
        "⚖️ Please download only content you have the right to save, and respect "
        "YouTube's Terms of Service and copyright laws."
    )


def settings(user):
    return (
        "⚙️ <b>Settings</b>\n\n"
        f"🎯 Default action: <b>{FMT_LABEL[user['def_fmt']]}</b>\n"
        f"🎵 Audio quality: <b>{user['def_audio']} kbps</b>\n"
        f"🎬 Video quality: <b>{video_label(user['def_video'])}</b>\n\n"
        "When the default action is MP3 or MP4, single videos start downloading "
        "instantly with your chosen quality — no extra taps.\n\n"
        "👇 Tap a button to change a value."
    )


def history(rows):
    if not rows:
        return "📜 <b>History</b>\n\nNothing here yet — send me a YouTube link to get started! 🚀"
    icons = {"done": "✅", "failed": "⚠️", "skipped": "📦", "cancelled": "🛑"}
    lines = ["📜 <b>Your last downloads</b>\n"]
    for r in rows:
        kind = "🎵" if r["fmt"] == "mp3" else "🎬"
        size = f" · {human_size(r['size_bytes'])}" if r["size_bytes"] else ""
        lines.append(
            f"{icons.get(r['status'], '•')} {kind} <i>{esc(truncate(r['title'], 42))}</i>"
            f"\n      {esc(r['quality'] and quality_label(r['fmt'], r['quality']))}{size} · {ts_date(r['created_at'], '%d %b %H:%M')}"
        )
    return "\n".join(lines)


def stats(user, s):
    return (
        "📊 <b>Your statistics</b>\n\n"
        f"📅 Member since: <b>{ts_date(user['joined_at'])}</b>\n"
        f"✅ Completed downloads: <b>{s['total']}</b>\n"
        f"🎵 MP3 files: <b>{s['mp3']}</b>\n"
        f"🎬 MP4 files: <b>{s['mp4']}</b>\n"
        f"📦 Total delivered: <b>{human_size(s['size']) if s['size'] else '0 B'}</b>"
    )


def admin(g, active_jobs):
    return (
        "🛡 <b>Admin panel</b>\n\n"
        f"👥 Users: <b>{g['users']}</b>  (🚫 banned: {g['banned']})\n"
        f"⬇️ Downloads today: <b>{g['today']}</b>\n"
        f"✅ Downloads total: <b>{g['downloads']}</b>\n"
        f"📦 Data delivered: <b>{human_size(g['size']) if g['size'] else '0 B'}</b>\n"
        f"🧵 Active jobs: <b>{active_jobs}</b>\n\n"
        "<b>Commands</b>\n"
        "/broadcast &lt;text&gt; — message all users\n"
        "/ban &lt;user_id&gt; — block a user\n"
        "/unban &lt;user_id&gt; — unblock a user"
    )


NOT_A_LINK = (
    "🤔 <b>That doesn't look like a YouTube link.</b>\n\n"
    "Please send a video or playlist URL, for example:\n"
    "<code>https://youtu.be/dQw4w9WgXcQ</code>"
)
PRIVATE = "🔒 This is a private bot. You don't have access."
BANNED = "🚫 You have been blocked from using this bot."
EXPIRED = "⌛ This selection expired. Please send the link again."
NOT_YOURS = "🙅 This menu belongs to someone else."
ANALYSING = "🔎 <b>Analysing link…</b>\nThis only takes a moment."
BUSY = "⏳ <b>You already have a download running.</b>\nWait for it to finish, or tap 🛑 Stop on its message."
COOLDOWN = "🐢 Slow down a little — try again in a few seconds."


def lookup_failed(reason):
    return f"{reason}\n\nCheck the link and try again."


# ───────────────────────── cards ─────────────────────────
def card(info, prompt=""):
    if info["kind"] == "playlist":
        head = (
            f"📃 <b>{esc(truncate(info['title'], 120))}</b>\n"
            f"👤 {esc(info.get('uploader') or 'Unknown')}\n"
            f"🎞 <b>{info['count']}</b> videos"
        )
    else:
        head = (
            f"🎬 <b>{esc(truncate(info['title'], 140))}</b>\n"
            f"👤 {esc(info.get('uploader') or 'Unknown')}\n"
            f"⏱ {human_duration(info.get('duration'))}   "
            f"👁 {human_count(info.get('views'))}   "
            f"📅 {human_date(info.get('upload_date'))}"
        )
    return f"{head}\n\n{prompt}" if prompt else head


PROMPT_VIDEO = "👇 <b>What would you like?</b>"
PROMPT_SCOPE = "📏 <b>How many videos?</b>"
PROMPT_FORMAT = "👇 <b>Choose a format</b>"
PROMPT_AUDIO = "🎧 <b>Choose audio quality</b>"
PROMPT_VIDEO_Q = "📺 <b>Choose video quality</b>\n<i>⚠️ = may exceed the upload limit</i>"


def playlist_scope_note(info):
    if info["count"] > config.MAX_PLAYLIST_ITEMS:
        return f"\n<i>Max {config.MAX_PLAYLIST_ITEMS} items per request.</i>"
    return ""


# ───────────────────────── job progress ─────────────────────────
def queued(job):
    return (
        "⏳ <b>Waiting in queue…</b>\n"
        f"{_item_line(job)}\n\n"
        "Another download is running. Yours starts automatically."
    )


def _item_line(job):
    icon = "🎵" if job.fmt == "mp3" else "🎬"
    return f"{icon} <i>{esc(truncate(job.title, 80))}</i>\n⚙️ {quality_label(job.fmt, job.quality)}"


def progress(job):
    p = job.progress
    counter = f" · {job.index}/{job.total}" if job.total > 1 else ""
    if p.phase == "downloading":
        pct = (p.done / p.total * 100) if p.total else 0
        stream = f" (part {p.stream}/{p.streams})" if p.streams > 1 else ""
        lines = [f"⏬ <b>Downloading{stream}</b>{counter}", _item_line(job), ""]
        lines.append(f"{progress_bar(pct)} <b>{pct:.1f}%</b>" if p.total else "▱▱▱▱▱▱▱▱▱▱▱▱ …")
        if p.total:
            lines.append(f"📦 {human_size(p.done)} / {human_size(p.total)}")
        extra = []
        if p.speed:
            extra.append(f"🚀 {human_size(p.speed)}/s")
        if p.eta is not None:
            extra.append(f"⏳ ETA {human_duration(p.eta) if p.eta else '0:00'}")
        if extra:
            lines.append("   ".join(extra))
        return "\n".join(lines)
    if p.phase == "processing":
        what = "Converting to MP3" if job.fmt == "mp3" else "Merging video &amp; audio"
        return f"🔧 <b>{what}…</b>{counter}\n{_item_line(job)}\n\n▰▰▰▰▰▰▰▰▰▰▱▱ almost there"
    if p.phase == "uploading":
        return f"📤 <b>Uploading to Telegram…</b>{counter}\n{_item_line(job)}\n\n▰▰▰▰▰▰▰▰▰▰▰▱ sending"
    return f"🚀 <b>Starting…</b>{counter}\n{_item_line(job)}"


def finished(job, sent, failed, cancelled, limit_hit=False):
    if cancelled:
        head = "🛑 <b>Stopped</b>"
    elif sent and not failed:
        head = "✅ <b>All done!</b>"
    elif sent:
        head = "⚠️ <b>Finished with some problems</b>"
    else:
        head = "❌ <b>Nothing could be sent</b>"
    lines = [head, "", f"📨 Sent: <b>{sent}</b> of <b>{job.total}</b> file(s)"]
    if failed:
        lines.append(f"⚠️ Failed or skipped: <b>{failed}</b>")
    if limit_hit:
        lines.append(f"📅 Daily limit of <b>{config.DAILY_LIMIT}</b> downloads reached.")
    lines.append("\n🧹 Temporary files were removed.")
    return "\n".join(lines)


def item_failed(name, reason):
    return f"⚠️ <b>{esc(truncate(name, 80))}</b>\n{reason}"


def too_large(name, size):
    return (
        f"📦 <b>{esc(truncate(name, 80))}</b>\n"
        f"The file is <b>{human_size(size)}</b>, above the <b>{config.MAX_UPLOAD_MB} MB</b> upload limit.\n"
        "💡 Try again with a lower quality."
    )


def media_caption(title, uploader, size, label, bot_username):
    parts = [f"{'🎵' if label.startswith('MP3') else '🎬'} <b>{esc(truncate(title, 150))}</b>"]
    if uploader:
        parts.append(f"👤 {esc(truncate(uploader, 60))}")
    parts.append(f"📦 {human_size(size)} · ⚙️ {label}")
    if bot_username:
        parts.append(f"\n🤖 via @{esc(bot_username)}")
    return "\n".join(parts)
