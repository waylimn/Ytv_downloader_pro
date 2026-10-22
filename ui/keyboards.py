"""Inline keyboards."""
from telegram import InlineKeyboardButton as B
from telegram import InlineKeyboardMarkup as M

import config
from services.utils import human_size
from ui import texts


def home(is_admin=False):
    rows = [
        [B("📥 How to use", callback_data="m:howto"), B("⚙️ Settings", callback_data="m:settings")],
        [B("📜 History", callback_data="m:history"), B("📊 My stats", callback_data="m:stats")],
        [B("❓ Help", callback_data="m:help"), B("ℹ️ About", callback_data="m:about")],
    ]
    if is_admin:
        rows.append([B("🛡 Admin panel", callback_data="m:admin")])
    return M(rows)


def back_home():
    return M([[B("🏠 Main menu", callback_data="m:home")]])


def settings(user):
    return M([
        [B(f"🎯 Action: {texts.FMT_LABEL[user['def_fmt']]}", callback_data="s:fmt")],
        [B(f"🎵 Audio: {user['def_audio']} kbps", callback_data="s:aq"),
         B(f"🎬 Video: {texts.video_label(user['def_video'])}", callback_data="s:vq")],
        [B("🏠 Main menu", callback_data="m:home")],
    ])


def history(has_rows):
    row = []
    if has_rows:
        row.append(B("🗑 Clear", callback_data="h:clear"))
    row.append(B("🏠 Main menu", callback_data="m:home"))
    return M([row])


def admin():
    return M([[B("🔄 Refresh", callback_data="m:admin"), B("🏠 Main menu", callback_data="m:home")]])


# ───────────── download flow ─────────────
def _nav(tok, back=None):
    row = []
    if back:
        row.append(B("⬅️ Back", callback_data=f"dl:back:{tok}:{back}"))
    row.append(B("❌ Cancel", callback_data=f"dl:x:{tok}"))
    return row


def card_video(tok, has_playlist=False):
    rows = [
        [B("🎵 Audio (MP3)", callback_data=f"dl:fmt:{tok}:mp3"),
         B("🎬 Video (MP4)", callback_data=f"dl:fmt:{tok}:mp4")],
        [B("🖼 Thumbnail", callback_data=f"dl:thumb:{tok}")],
    ]
    if has_playlist:
        rows.append([B("📃 Use the full playlist instead", callback_data=f"dl:pl:{tok}")])
    rows.append(_nav(tok))
    return M(rows)


def scope(tok, count):
    cap = min(count, config.MAX_PLAYLIST_ITEMS)
    opts = [n for n in (1, 5, 10) if n < cap] + [cap]
    row = [B(f"{'All ' if n == count else 'First '}{n}", callback_data=f"dl:scope:{tok}:{n}") for n in opts]
    rows = [row[i:i + 3] for i in range(0, len(row), 3)]
    rows.append(_nav(tok))
    return M(rows)


def formats(tok, back):
    return M([
        [B("🎵 Audio (MP3)", callback_data=f"dl:fmt:{tok}:mp3"),
         B("🎬 Video (MP4)", callback_data=f"dl:fmt:{tok}:mp4")],
        _nav(tok, back),
    ])


def audio_quality(tok, info, back="fmt"):
    names = {"128": "Standard", "192": "High", "320": "Studio"}
    dur = info.get("duration") if info["kind"] == "video" else None
    rows = []
    for br in ("128", "192", "320"):
        size = f" · ~{human_size(int(dur) * int(br) * 125)}" if dur else ""
        warn = "⚠️ " if dur and int(dur) * int(br) * 125 > config.MAX_UPLOAD_BYTES else ""
        rows.append([B(f"{warn}🎧 {br} kbps · {names[br]}{size}", callback_data=f"dl:q:{tok}:a{br}")])
    rows.append(_nav(tok, back))
    return M(rows)


def video_quality(tok, info, back="fmt"):
    rows = []
    if info["kind"] == "video":
        for o in info["options"]:
            label = f"⭐ Best · {o['res']}p" if o["q"] == "best" and o["res"] else (
                "⭐ Best" if o["q"] == "best" else f"{o['res']}p")
            if o["size"]:
                warn = "⚠️ " if o["size"] > config.MAX_UPLOAD_BYTES else ""
                label = f"{warn}{label} · ~{human_size(o['size'])}"
            rows.append([B(label, callback_data=f"dl:q:{tok}:{o['q']}")])
    else:
        rows.append([B("⭐ Best", callback_data=f"dl:q:{tok}:best"),
                     B("1080p", callback_data=f"dl:q:{tok}:1080")])
        rows.append([B("720p", callback_data=f"dl:q:{tok}:720"),
                     B("480p", callback_data=f"dl:q:{tok}:480"),
                     B("360p", callback_data=f"dl:q:{tok}:360")])
    rows.append(_nav(tok, back))
    return M(rows)


def stop(tok):
    return M([[B("🛑 Stop", callback_data=f"dl:stop:{tok}")]])


def done():
    return M([[B("⬇️ New download", callback_data="m:howto"), B("🏠 Main menu", callback_data="m:home")]])
