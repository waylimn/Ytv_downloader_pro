"""yt-dlp wrapper: link inspection and single-item downloads."""
import os
from pathlib import Path

import yt_dlp

import config
from services.utils import parse_url_parts, playlist_url, video_url

try:  # exists in current yt-dlp; fall back for safety
    from yt_dlp.utils import DownloadCancelled
except ImportError:  # pragma: no cover
    class DownloadCancelled(Exception):
        pass

MEDIA_EXT = (".mp4", ".m4v", ".webm", ".mkv", ".mp3", ".m4a", ".opus", ".aac")
BUCKETS = (1080, 720, 480, 360, 240, 144)


class Progress:
    """Mutable progress state shared between the download thread and the UI loop."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.phase = "starting"  # starting | downloading | processing | uploading
        self.done = 0
        self.total = 0
        self.speed = None
        self.eta = None
        self.stream = 1
        self.streams = 1


def _base_opts():
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
    }
    if config.COOKIES_FILE and os.path.isfile(config.COOKIES_FILE):
        opts["cookiefile"] = config.COOKIES_FILE
    if config.YTDLP_JS_RUNTIME:
        opts["js_runtimes"] = {config.YTDLP_JS_RUNTIME: {}}
    return opts


# ───────────────────────── inspect ─────────────────────────
def _res(fmt):
    w, h = fmt.get("width"), fmt.get("height")
    if w and h:
        return min(w, h)
    return h or 0


def _size(fmt):
    return fmt.get("filesize") or fmt.get("filesize_approx") or 0


def _video_options(info):
    formats = info.get("formats") or []
    vids = [f for f in formats if f.get("vcodec") not in (None, "none") and _res(f)]
    auds = [f for f in formats if f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")]
    best_audio = max((_size(f) for f in auds), default=0)
    if not vids:
        return [{"q": "best", "res": 0, "size": None}]
    max_res = max(_res(f) for f in vids)
    avail = {_res(f) for f in vids}

    def est(limit):
        pool = [f for f in vids if _res(f) <= limit * 1.1]
        if not pool:
            return None
        top = max(_res(f) for f in pool)
        s = max((_size(f) for f in pool if _res(f) == top), default=0)
        return (s + best_audio) if s else None

    options = [{"q": "best", "res": max_res, "size": est(max_res)}]
    for b in BUCKETS:
        # only offer lower steps that the video really has
        if b < max_res * 0.9 and any(abs(r - b) <= b * 0.1 for r in avail):
            options.append({"q": str(b), "res": b, "size": est(b)})
    return options


def inspect_url(url, force_playlist=False):
    """Return a metadata dict for a video or playlist without downloading."""
    vid, lid = parse_url_parts(url)
    as_playlist = bool(lid) and (not vid or force_playlist)

    if as_playlist:
        target = playlist_url(lid)
        opts = {**_base_opts(), "extract_flat": "in_playlist", "skip_download": True,
                "playlistend": config.MAX_PLAYLIST_SCAN}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target, download=False)
        if not info:
            raise ValueError("No playlist information was returned.")
        entries = []
        for e in info.get("entries") or []:
            if not e or not e.get("id"):
                continue
            title = e.get("title") or ""
            if title in ("[Private video]", "[Deleted video]"):
                continue
            entries.append({"id": e["id"], "url": video_url(e["id"]), "title": title or e["id"],
                            "duration": e.get("duration")})
        if not entries:
            raise ValueError("This playlist is empty or unavailable.")
        return {
            "kind": "playlist",
            "id": lid,
            "url": target,
            "title": info.get("title") or "YouTube playlist",
            "uploader": info.get("uploader") or info.get("channel"),
            "count": len(entries),
            "entries": entries,
            "thumb_id": entries[0]["id"],
        }

    opts = {**_base_opts(), "noplaylist": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise ValueError("No video information was returned.")
    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise ValueError("No video found at that link.")
        info = entries[0]
    if info.get("is_live"):
        raise ValueError("Live events are not supported.")
    return {
        "kind": "video",
        "id": info.get("id"),
        "url": video_url(info["id"]) if info.get("id") else url,
        "title": info.get("title") or "YouTube video",
        "uploader": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
        "views": info.get("view_count"),
        "upload_date": info.get("upload_date"),
        "playlist_id": lid,
        "options": _video_options(info),
    }


# ───────────────────────── download ─────────────────────────
def _format_opts(fmt, quality):
    if fmt == "mp3":
        bitrate = quality.lstrip("a") if quality else "192"
        if bitrate not in ("128", "192", "320"):
            bitrate = "192"
        return {
            "format": "bestaudio/best",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate},
                {"key": "FFmpegMetadata", "add_metadata": True},
            ],
        }
    if quality == "best":
        sort = ["vcodec:h264", "res", "acodec:aac"]
    else:
        sort = ["vcodec:h264", f"res:{int(quality)}", "acodec:aac"]
    return {
        "format": "bv*+ba/b",
        "format_sort": sort,
        "merge_output_format": "mp4",
        "postprocessors": [{"key": "FFmpegMetadata", "add_metadata": True}],
    }


def download_one(url, fmt, quality, workdir, progress, cancel_event):
    """Download ONE video into workdir. Blocking – run it in a thread."""
    progress.reset()
    progress.streams = 1 if fmt == "mp3" else 2
    finished = {"n": 0}

    def hook(d):
        if cancel_event.is_set():
            raise DownloadCancelled("cancelled by user")
        status = d.get("status")
        if status == "downloading":
            progress.phase = "downloading"
            progress.done = d.get("downloaded_bytes") or 0
            progress.total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            progress.speed = d.get("speed")
            progress.eta = d.get("eta")
            progress.stream = min(finished["n"] + 1, progress.streams)
        elif status == "finished":
            finished["n"] += 1
            if finished["n"] >= progress.streams:
                progress.phase = "processing"

    def pp_hook(d):
        if d.get("status") == "started":
            progress.phase = "processing"

    def run(extra=None):
        opts = {
            **_base_opts(),
            **_format_opts(fmt, quality),
            "noplaylist": True,
            "outtmpl": "%(title).120B [%(id)s].%(ext)s",
            "paths": {"home": workdir, "temp": os.path.join(workdir, ".tmp")},
            "progress_hooks": [hook],
            "postprocessor_hooks": [pp_hook],
            "concurrent_fragment_downloads": 4,
        }
        if extra:
            opts.update(extra)
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info = run()
    except yt_dlp.utils.DownloadError as e:
        if cancel_event.is_set() or "requested format" not in str(e).lower():
            raise
        # Fallback: loosen format selection
        finished["n"] = 0
        info = run({"format": "bestaudio/best" if fmt == "mp3" else "b", "format_sort": []})

    path = None
    for d in (info.get("requested_downloads") or []):
        fp = d.get("filepath")
        if fp and os.path.isfile(fp):
            path = fp
            break
    if not path:  # fallback: newest media file in workdir
        files = [p for p in Path(workdir).rglob("*")
                 if p.is_file() and p.suffix.lower() in MEDIA_EXT and ".tmp" not in p.parts
                 and ".part" not in p.name]
        if files:
            path = str(max(files, key=lambda p: p.stat().st_mtime))
    if not path:
        raise RuntimeError("Download finished but no media file was produced.")
    return {
        "path": path,
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
        "width": info.get("width"),
        "height": info.get("height"),
    }
