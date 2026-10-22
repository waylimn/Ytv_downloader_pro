"""SQLite storage: users, settings and download history."""
import sqlite3
import threading
import time
from datetime import datetime

import config

_lock = threading.RLock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    joined_at   INTEGER NOT NULL,
    last_seen   INTEGER NOT NULL,
    banned      INTEGER NOT NULL DEFAULT 0,
    def_fmt     TEXT NOT NULL DEFAULT 'ask',
    def_audio   TEXT NOT NULL DEFAULT '192',
    def_video   TEXT NOT NULL DEFAULT '720'
);
CREATE TABLE IF NOT EXISTS downloads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    title       TEXT,
    url         TEXT,
    fmt         TEXT,
    quality     TEXT,
    status      TEXT,
    size_bytes  INTEGER DEFAULT 0,
    created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dl_user ON downloads(user_id, created_at);
"""

SETTING_COLUMNS = {"def_fmt", "def_audio", "def_video"}


def init():
    global _conn
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    with _lock:
        _conn.executescript(SCHEMA)
        _conn.commit()


def _exec(sql, params=()):
    with _lock:
        cur = _conn.execute(sql, params)
        _conn.commit()
        return cur


def _one(sql, params=()):
    with _lock:
        return _conn.execute(sql, params).fetchone()


def _all(sql, params=()):
    with _lock:
        return _conn.execute(sql, params).fetchall()


# ───────────── users ─────────────
def upsert_user(user_id, username, first_name):
    now = int(time.time())
    _exec(
        """INSERT INTO users (user_id, username, first_name, joined_at, last_seen)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
               username = excluded.username,
               first_name = excluded.first_name,
               last_seen = excluded.last_seen""",
        (user_id, username, first_name, now, now),
    )


def get_user(user_id):
    return _one("SELECT * FROM users WHERE user_id = ?", (user_id,))


def is_banned(user_id):
    row = _one("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    return bool(row and row["banned"])


def set_banned(user_id, banned):
    cur = _exec("UPDATE users SET banned = ? WHERE user_id = ?", (1 if banned else 0, user_id))
    return cur.rowcount > 0


def set_setting(user_id, column, value):
    if column not in SETTING_COLUMNS:
        raise ValueError("Unknown setting")
    _exec(f"UPDATE users SET {column} = ? WHERE user_id = ?", (value, user_id))


def all_user_ids():
    return [r["user_id"] for r in _all("SELECT user_id FROM users WHERE banned = 0")]


# ───────────── downloads ─────────────
def log_download(user_id, title, url, fmt, quality, status, size_bytes=0):
    _exec(
        """INSERT INTO downloads (user_id, title, url, fmt, quality, status, size_bytes, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, (title or "")[:200], url, fmt, quality, status, int(size_bytes or 0), int(time.time())),
    )


def history(user_id, limit=10):
    return _all(
        "SELECT * FROM downloads WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
    )


def clear_history(user_id):
    _exec("DELETE FROM downloads WHERE user_id = ?", (user_id,))


def _today_start():
    return int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def count_today(user_id):
    row = _one(
        "SELECT COUNT(*) AS c FROM downloads WHERE user_id = ? AND status = 'done' AND created_at >= ?",
        (user_id, _today_start()),
    )
    return row["c"] if row else 0


def user_stats(user_id):
    row = _one(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(fmt = 'mp3'), 0) AS mp3,
                  COALESCE(SUM(fmt = 'mp4'), 0) AS mp4,
                  COALESCE(SUM(size_bytes), 0) AS size
           FROM downloads WHERE user_id = ? AND status = 'done'""",
        (user_id,),
    )
    return dict(row)


def global_stats():
    users = _one("SELECT COUNT(*) AS c, COALESCE(SUM(banned), 0) AS b FROM users")
    dl = _one(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(size_bytes), 0) AS size,
                  COALESCE(SUM(created_at >= ?), 0) AS today
           FROM downloads WHERE status = 'done'""",
        (_today_start(),),
    )
    return {
        "users": users["c"],
        "banned": users["b"],
        "downloads": dl["total"],
        "today": dl["today"],
        "size": dl["size"],
    }
