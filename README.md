<div align="center">

# 🤖 YouTube Telegram Bot — YTDL Bot for Telegram (Termux, VPS & Server)

### Download YouTube videos, playlists, MP3 and MP4 directly inside Telegram — with live progress, quality menus and zero ZIP files.

**by [waylimn](https://github.com/waylimn)**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)
![yt-dlp](https://img.shields.io/badge/Powered%20by-yt--dlp-red)
![Termux](https://img.shields.io/badge/Runs%20on-Termux-black?logo=android)
![License](https://img.shields.io/badge/License-MIT-green)

[Features](#-features) · [Termux Install](#-install-on-termux-android--step-by-step) · [VPS Install](#%EF%B8%8F-install-on-a-vps--linux-server) · [Windows](#-install-on-windows) · [Settings](#%EF%B8%8F-configuration-env) · [FAQ](#-faq)

</div>

---

## 📖 What is this?

**YT Downloader Pro** is a free, open-source **YouTube Telegram bot** (also known as a **ytdl bot for Telegram** or **YouTube to MP3 / MP4 Telegram bot**) written in Python with `python-telegram-bot` and `yt-dlp`.

Send a YouTube link to your bot, choose **🎵 Audio (MP3)** or **🎬 Video (MP4)**, pick a quality, and the file arrives in your Telegram chat. It runs on **Android (Termux)**, any **Linux VPS**, a home **server**, a Raspberry Pi, or **Windows**.

> Searching for a *YouTube downloader Telegram bot*, a *ytdl telegram bot*, a *Termux YouTube downloader bot* or a *YouTube playlist downloader bot*? This is it. ⭐ Star the repo to support it!

---

## ✨ Features

| | Feature |
|---|---|
| 🎬 | **MP4 video** — Best, 1080p, 720p, 480p, 360p (only resolutions the video really has) |
| 🎵 | **MP3 audio** — 128 / 192 / 320 kbps |
| 📃 | **Playlist downloader** — first 1 / 5 / 10 / all, sent one by one |
| 📊 | **Live progress bar** — percent, speed, ETA, converting & uploading steps |
| 🛑 | **Stop button** — cancel any running download |
| 📦 | **Size estimates** — ⚠️ warning if a file may exceed the Telegram upload limit |
| 🖼 | **HD thumbnail download** |
| 🧾 | **Video card** — thumbnail, channel, duration, views, upload date |
| ⚙️ | **Per-user settings** — default action and quality ("quick mode") |
| 📜 | **History & personal stats** (SQLite) |
| 🛡 | **Admin panel** — stats, `/broadcast`, `/ban`, `/unban` |
| 🔒 | **Private mode** (allow-list), daily limit, cooldown, max duration, job queue |
| 🍪 | **Cookies support** for age-restricted / bot-check videos |
| 🧹 | **Auto cleanup** — temporary files are deleted after sending |
| 🌍 | Runs on **Termux, Ubuntu, Debian, Raspberry Pi, VPS, Windows** |

---

## 💬 How it works

1. Open your bot and send a YouTube **video** or **playlist** link
2. Choose 🎵 **Audio** or 🎬 **Video**
3. Choose the quality (file sizes are estimated)
4. Watch the live progress bar
5. Receive the file in the chat ✅

Commands: `/start` `/menu` `/settings` `/history` `/stats` `/help` `/about` `/cancel` — admins also get `/admin` `/broadcast` `/ban` `/unban`.

---

## 🧰 Requirements

- Python **3.10 or newer**
- **ffmpeg**
- A Telegram bot token from **[@BotFather](https://t.me/BotFather)**
- Your numeric Telegram ID from **[@userinfobot](https://t.me/userinfobot)** (to become admin)

---

## 📱 Install on Termux (Android) — step by step

> Works on any Android phone. Use the **F-Droid** version of Termux — the Play Store version is outdated.

**1. Install Termux** from F-Droid: <https://f-droid.org/packages/com.termux/>

**2. Update packages and install tools**

```bash
pkg update && pkg upgrade -y
pkg install python ffmpeg git nano tmux -y
```

**3. Download the bot**

```bash
cd ~
git clone https://github.com/waylimn/Ytv_downloader_pro.git
cd Ytv_downloader_pro
```

*(Using a ZIP instead? Run `termux-setup-storage`, then `cp ~/storage/downloads/YOUR_FILE.zip ~/ && unzip YOUR_FILE.zip`.)*

> ⚠️ Always run the bot from Termux's home folder (`~`), **not** from `/sdcard` or `~/storage/...`.

**4. Install Python requirements**

```bash
pip install -r requirements.txt
```

**5. Create your bot** — in Telegram open **@BotFather** → `/newbot` → copy the **token**.

**6. Create the settings file**

```bash
cp .env.example .env
nano .env
```

Fill in:

```env
BOT_TOKEN=your_token_here
ADMIN_IDS=your_numeric_id
```

Save in nano: `CTRL+O` → `Enter` → `CTRL+X`.

**7. Start the bot**

```bash
python bot.py
```

When you see `Bot started as @yourbot`, open Telegram and send `/start` 🎉

**8. Keep it running in the background**

```bash
termux-wake-lock
tmux new -s bot
python bot.py
```

Detach with `CTRL+B` then `D`. Come back with `tmux attach -t bot`.
Also set Termux to **Battery → Unrestricted** in Android settings.

**9. Update later**

```bash
cd ~/Ytv_downloader_pro
git pull
pip install -U -r requirements.txt
pip install -U yt-dlp
```

---

## 🖥️ Install on a VPS / Linux Server

Tested flow for **Ubuntu 22.04 / 24.04** and **Debian 11/12**. Works on cheap VPS plans, home servers and Raspberry Pi. A VPS uploads files to Telegram **much faster** than a phone.

**1. Connect and install dependencies**

```bash
ssh root@YOUR_SERVER_IP
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv ffmpeg git tmux nano -y
```

**2. (Recommended) create a normal user**

```bash
adduser botuser
usermod -aG sudo botuser
su - botuser
```

**3. Download the bot and create a virtual environment**

```bash
git clone https://github.com/waylimn/Ytv_downloader_pro.git
cd Ytv_downloader_pro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**4. Configure**

```bash
cp .env.example .env
nano .env
```

Set `BOT_TOKEN` and `ADMIN_IDS` (see [Configuration](#%EF%B8%8F-configuration-env)).

**5. Test run**

```bash
python bot.py
```

Send `/start` to your bot. Stop with `CTRL+C`.

### Option A — run 24/7 with tmux (simple)

```bash
tmux new -s bot
source venv/bin/activate
python bot.py
# detach: CTRL+B then D     |     return: tmux attach -t bot
```

### Option B — run 24/7 with systemd (auto-start on reboot, auto-restart on crash)

Replace `botuser` and the path if yours differ:

```bash
sudo nano /etc/systemd/system/ytdl-bot.service
```

```ini
[Unit]
Description=YouTube Telegram Bot (ytdl)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/Ytv_downloader_pro
ExecStart=/home/botuser/Ytv_downloader_pro/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ytdl-bot
sudo systemctl status ytdl-bot
```

Useful commands:

```bash
sudo journalctl -u ytdl-bot -f      # live logs
sudo systemctl restart ytdl-bot     # restart
sudo systemctl stop ytdl-bot        # stop
```

### Update on a server

```bash
cd ~/Ytv_downloader_pro
git pull
source venv/bin/activate
pip install -U -r requirements.txt
pip install -U yt-dlp
sudo systemctl restart ytdl-bot
```

### Bigger files (up to ~2 GB)

The normal Telegram Bot API limits uploads to about **50 MB**. To send larger files, run your own [Telegram Bot API server](https://github.com/tdlib/telegram-bot-api), then set in `.env`:

```env
API_BASE_URL=http://127.0.0.1:8081/bot
MAX_UPLOAD_MB=1990
```

---

## 🪟 Install on Windows

1. Install **Python 3.10+** from <https://www.python.org/downloads/> (tick *Add Python to PATH*)
2. Install **ffmpeg** and add it to PATH (e.g. `winget install Gyan.FFmpeg`)
3. Open PowerShell:

```powershell
git clone https://github.com/waylimn/Ytv_downloader_pro.git
cd Ytv_downloader_pro
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
python bot.py
```

---

## ⚙️ Configuration (`.env`)

| Variable | Description | Default |
|---|---|---|
| `BOT_TOKEN` | Token from @BotFather **(required)** | — |
| `ADMIN_IDS` | Admin Telegram IDs, comma separated | empty |
| `ALLOWED_USERS` | Private bot: only these IDs may use it | empty (everyone) |
| `MAX_UPLOAD_MB` | Upload size limit | `49` |
| `API_BASE_URL` | Self-hosted Bot API server URL | empty |
| `MAX_PLAYLIST_ITEMS` | Max playlist items per request | `25` |
| `MAX_CONCURRENT_JOBS` | Parallel downloads | `2` |
| `COOLDOWN_SECONDS` | Delay between link requests | `5` |
| `DAILY_LIMIT` | Downloads per user per day (`0` = unlimited) | `0` |
| `MAX_VIDEO_MINUTES` | Reject longer videos (`0` = no limit) | `0` |
| `COOKIES_FILE` | Path to a Netscape `cookies.txt` | empty |
| `YTDLP_JS_RUNTIME` | Advanced: JS runtime for yt-dlp, e.g. `node` | empty |

> 🔐 **Never publish your `.env` file or bot token.** The included `.gitignore` already excludes it. If a token leaks, send `/revoke` to @BotFather.

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| `BOT_TOKEN is missing` | Create `.env` (`cp .env.example .env`) and run the bot from inside the project folder |
| `ffmpeg is not installed` | Termux: `pkg install ffmpeg` · Ubuntu/Debian: `sudo apt install ffmpeg` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` (activate the venv first on a VPS) |
| `Conflict: terminated by other getUpdates request` | The bot is running twice. Stop the other copy: `pkill -f bot.py` |
| Downloads suddenly fail | `pip install -U yt-dlp` and restart the bot |
| "YouTube asked for a bot check" / age-restricted | Export cookies (browser extension *Get cookies.txt LOCALLY*), save as `cookies.txt`, set `COOKIES_FILE=cookies.txt`, restart. Use a spare account |
| File above upload limit | Choose a lower quality, or use a self-hosted Bot API server |
| Upload is slow | Upload speed depends on your connection. Use Wi-Fi, a lower quality, or host on a VPS |

---

## ❓ FAQ

**Is this a YouTube downloader Telegram bot?**
Yes. You host it yourself and it downloads YouTube videos, playlists and audio, then sends them to your Telegram chat.

**Can I run a ytdl Telegram bot on my phone?**
Yes. Follow the [Termux guide](#-install-on-termux-android--step-by-step). No root needed.

**Does it support YouTube playlists?**
Yes. Choose how many items to download; they are sent one by one and deleted from the server after each.

**Can it download MP3?**
Yes — 128, 192 or 320 kbps, converted with ffmpeg.

**Why is there a ~50 MB limit?**
That is Telegram's limit for bots using the normal Bot API. Pick a lower quality or run your own Bot API server for up to ~2 GB.

**Is it free?**
Yes, open source under the MIT license.

---

## 🗂 Project structure

```
Ytv_downloader_pro/
├── bot.py              # entry point
├── config.py           # settings from .env
├── handlers/           # menus, download flow, admin, errors, access gate
├── services/           # yt-dlp wrapper and helpers
├── database/           # SQLite storage (users, settings, history)
├── ui/                 # message texts and inline keyboards
├── data/  work/        # database / temporary downloads (auto-managed)
├── requirements.txt
└── .env.example
```

---

## 🤝 Contributing

Issues and pull requests are welcome. If this project helped you, please **⭐ star the repository** — it helps other people find it.

## ⚖️ Disclaimer

This project is for personal and educational use. Only download content you own or have permission to save, and respect YouTube's Terms of Service and the copyright laws of your country. The author is not responsible for misuse.

## 📄 License

This project is under the [MIT License](LICENSE).

---

<div align="center">

**Keywords:** youtube telegram bot · ytdl telegram bot · youtube downloader telegram bot · youtube to mp3 telegram bot · youtube playlist downloader bot · termux youtube downloader · termux telegram bot · yt-dlp telegram bot · python telegram bot · youtube video downloader bot · waylimn

</div>
