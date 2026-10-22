"""Small helpers: formatting, URL parsing, progress bars."""
import html
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse

_YT_RE = re.compile(
    r"https?://(?:[\w-]+\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com)/[^\s<>\"']+",
    re.I,
)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def find_youtube_url(text):
    m = _YT_RE.search(text or "")
    return m.group(0).rstrip(").,]") if m else None


def esc(value):
    return html.escape(str(value if value is not None else ""), quote=False)


def clean_error(text):
    text = _ANSI_RE.sub("", str(text or "")).strip()
    return re.sub(r"^ERROR:\s*", "", text)


def truncate(text, n):
    text = str(text or "")
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def human_size(num):
    if not num:
        return "?"
    num = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024


def human_duration(seconds):
    if not seconds:
        return "—"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def human_count(n):
    if n is None:
        return "—"
    n = float(n)
    for suffix, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if n >= div:
            return f"{n / div:.1f}{suffix}".replace(".0", "")
    return str(int(n))


def human_date(yyyymmdd):
    try:
        return datetime.strptime(str(yyyymmdd), "%Y%m%d").strftime("%d %b %Y")
    except ValueError:
        return "—"


def ts_date(ts, fmt="%d %b %Y"):
    return datetime.fromtimestamp(ts).strftime(fmt)


def progress_bar(pct, width=12):
    pct = max(0.0, min(100.0, float(pct or 0)))
    filled = int(round(pct / 100 * width))
    return "▰" * filled + "▱" * (width - filled)


def parse_url_parts(url):
    """Return (video_id, list_id) from any YouTube URL."""
    try:
        u = urlparse(url)
    except ValueError:
        return None, None
    host = (u.hostname or "").lower()
    qs = parse_qs(u.query)
    list_id = (qs.get("list") or [None])[0]
    vid = (qs.get("v") or [None])[0]
    parts = [p for p in u.path.split("/") if p]
    if not vid:
        if host.endswith("youtu.be") and parts:
            vid = parts[0]
        elif parts and parts[0] in ("shorts", "live", "embed", "v") and len(parts) > 1:
            vid = parts[1]
    return vid, list_id


def playlist_url(list_id):
    return f"https://www.youtube.com/playlist?list={list_id}"


def video_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def thumb_urls(video_id):
    """Best-first list of JPEG thumbnail URLs Telegram can fetch."""
    return [
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]


def friendly_error(exc):
    s = clean_error(exc)
    low = s.lower()
    rules = (
        ("confirm you’re not a bot", "🤖 YouTube asked for a bot check. Add a cookies file (see README → Troubleshooting)."),
        ("confirm you're not a bot", "🤖 YouTube asked for a bot check. Add a cookies file (see README → Troubleshooting)."),
        ("sign in", "🔐 This video needs a signed-in account. Add a cookies file (see README)."),
        ("private video", "🔒 This video is private."),
        ("members-only", "💎 This video is for channel members only."),
        ("join this channel", "💎 This video is for channel members only."),
        ("age", "🔞 Age-restricted video — a cookies file from a logged-in account is needed."),
        ("copyright", "©️ This video is blocked for copyright reasons."),
        ("not available in your country", "🌍 This video is blocked in the server's region."),
        ("unavailable", "🚫 This video is unavailable (removed or restricted)."),
        ("live event", "📡 Live streams aren't supported."),
        ("ffmpeg", "🛠 ffmpeg is missing on the server. Install it (see README)."),
        ("429", "⏱ YouTube is rate-limiting the server. Please try again in a few minutes."),
        ("unsupported url", "🔗 That link isn't a supported YouTube URL."),
        ("is not a valid url", "🔗 That link isn't a valid YouTube URL."),
    )
    for needle, message in rules:
        if needle in low:
            return message
    return "❌ " + truncate(s or "Unknown error", 220)
