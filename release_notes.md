# Persian YouTube Downloader v1.1.0

A fast, beautiful GUI YouTube downloader with a Persian (RTL) interface — built with Python, PyQt6 and yt-dlp.

---

## ✨ What's new in v1.1.0

### Interface
- **Settings tab** — default download path, cookie source, proxy, speed limit, notifications, update check and maintenance tools in one place
- **Video info panel** — thumbnail, channel, duration, views and likes right after extracting formats
- **Dark theme + tabbed UI** — Video / Playlist / History / Settings
- **Menu bar** — File (Exit `Ctrl+Q`) and Help (Guide `F1`, About, Check for updates)
- **Windows taskbar progress** — download percentage on the taskbar icon
- **Custom application icon**

### Downloads
- **Audio formats in the playlist quality selector** — MP3 128/192/320 kbps, M4A (AAC), Opus, FLAC (lossless), WAV, in addition to all video qualities (4K → 360p)
- **Batch download** — paste many links (one per line) and queue them all at once
- **Download queue** — several videos/playlists one after another
- **Speed limit** — cap the download rate (KB/s)
- **Explicit Resume** — continue partially downloaded files (can be turned off)
- **Playlist search/filter** — filter playlist items by title or duration
- **Playlist subfolder** — each playlist is saved into a folder named after it
- **Green check mark** — downloaded playlist videos are ticked in green

### Reliability & experience
- **System notifications** — Windows notification (plus tray icon) when a download finishes or fails
- **Friendly error messages** — common yt-dlp errors translated into clear, actionable guidance
- **yt-dlp update check** — compares the installed version with PyPI
- **aria2c fix** — TLS failures now automatically fall back to the built-in downloader, and HLS formats always use the native downloader (no more `aria2c exited with code 1`)
- **Accurate results** — the app no longer reports "success" when a playlist download actually failed

---

## 📦 Installation

1. Download the ZIP file below and extract it.
2. Run `Persian_Youtube_Downloader.exe`.

> No Python or any other dependency required — everything is bundled.

## ⚙️ Bundled tools

| Tool | Purpose |
|------|---------|
| **FFmpeg** | Audio extraction and video+audio merging |
| **aria2c** | Optional parallel downloader (can be enabled in Settings) |

## 📝 Optional requirement

- **Node.js** — only needed for downloading subtitles: <https://nodejs.org>

## 💡 Tip

For the most reliable downloads, enable **"Use browser cookies"** (e.g. Firefox) in the Settings tab instead of using a `cookies.txt` file.

---

📥 All releases: <https://github.com/salemhamidani/Persian_Youtube_Downloader/releases>
