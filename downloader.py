import os
import re
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

import yt_dlp

from cookies import CookieManager


def _find_ffmpeg_location() -> Optional[str]:
    """پیدا کردن پوشه‌ای که ffmpeg باندل‌شده (PyInstaller) در آن است.

    در حالت عادی None برمی‌گرداند (از PATH سیستم استفاده می‌شود).
    در حالت باندل‌شده، مسیر ffmpeg همراه exe را برمی‌گرداند.
    """
    if not getattr(sys, "frozen", False):
        return None  # اجرای عادی — از PATH سیستم استفاده کن
    candidates = []
    if hasattr(sys, "_MEIPASS"):  # حالت onefile
        candidates.append(sys._MEIPASS)
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(exe_dir)                      # ffmpeg کنار exe
    candidates.append(os.path.join(exe_dir, "_internal"))  # حالت onedir
    for c in candidates:
        if c and os.path.isfile(os.path.join(c, "ffmpeg.exe")):
            return c
    return None


# ---------- ترجمه پیام‌های خطای yt-dlp به فارسی ----------
_FRIENDLY_ERRORS = (
    (("sign in to confirm", "not a bot", "confirm you're not a bot"),
     "یوتیوب درخواست شما را «ربات» تشخیص داد. راهکارها:\n"
     "۱) در تب تنظیمات، «استفاده از کوکی مرورگر» (مثلاً Firefox) را فعال کنید — معمولاً بهتر از فایل cookies.txt کار می‌کند.\n"
     "۲) اگر VPN/پراکسی دارید، سرور را عوض کنید.\n"
     "۳) کمی صبر کنید و دوباره تلاش کنید."),
    (("private video", "this video is private"),
     "این ویدئو خصوصی است و قابل دانلود نیست."),
    (("video unavailable", "removed by the uploader", "deleted"),
     "ویدئو در دسترس نیست (حذف شده یا توسط صاحبش محدود شده است)."),
    (("age-restricted", "age restricted", "sign in to view", "inappropriate"),
     "این ویدئو محدودیت سنی دارد و برای دانلود باید با حساب کاربری وارد شوید (کوکی)."),
    (("members-only", "members only", "join this channel"),
     "این ویدئو فقط برای اعضای کانال قابل دسترسی است."),
    (("premieres in", "premiere"),
     "این ویدئو هنوز منتشر نشده است."),
    (("live event will begin", "this live event"),
     "پخش زنده هنوز شروع نشده است."),
    (("requested format is not available", "no video formats found", "no formats found"),
     "فرمت انتخاب‌شده موجود نیست. لطفاً یک فرمت دیگر (یا «بهترین کیفیت») انتخاب کنید."),
    (("unable to download webpage", "failed to resolve", "getaddrinfo",
      "name or service not known", "temporary failure in name resolution", "urlopen error"),
     "اتصال به یوتیوب برقرار نشد. اتصال اینترنت یا تنظیمات پراکسی را بررسی کنید."),
    (("http error 403", "403 forbidden"),
     "دسترسی رد شد (خطای ۴۰۳). یک کوکی مرورگر تازه یا پراکسی دیگر امتحان کنید."),
    (("http error 429", "too many requests"),
     "درخواست‌های بیش از حد — کمی صبر کنید و دوباره تلاش کنید."),
    (("read timed out", "timed out", "connection reset", "connection aborted",
      "connection refused", "remote end closed"),
     "اتصال شبکه قطع یا کند شد. لطفاً دوباره تلاش کنید."),
    (("ffmpeg", "postprocessing", "post-process"),
     "خطا در پس‌پردازش (FFmpeg). نصب‌بودن FFmpeg را بررسی کنید."),
    (("unsupported url", "not a valid url"),
     "این لینک پشتیبانی نمی‌شود. لطفاً یک لینک معتبر یوتیوب وارد کنید."),
    (("cookies", "cookie file", "failed to decrypt"),
     "خطا در کوکی‌ها. از کوکی مرورگر تازه استفاده کنید یا مرورگر را ببندید."),
    (("disk", "no space left", "permission denied", "access is denied"),
     "خطای دیسک یا دسترسی. فضای آزاد و مسیر ذخیره را بررسی کنید."),
)


def friendly_error(msg: str) -> str:
    """تبدیل پیام خطای yt-dlp به یک پیام فارسی قابل فهم."""
    low = (msg or "").lower()
    for keys, fa in _FRIENDLY_ERRORS:
        if any(k in low for k in keys):
            return fa
    return msg


# ---------- بررسی به‌روزرسانی yt-dlp ----------
def installed_ytdlp_version() -> str:
    """نسخهٔ فعلی yt-dlp نصب‌شده."""
    try:
        import yt_dlp
        return yt_dlp.version.__version__
    except Exception:
        return "?"


def latest_ytdlp_version(timeout: int = 8) -> Optional[str]:
    """آخرین نسخهٔ yt-dlp از PyPI (None در صورت خطای شبکه)."""
    import json
    import urllib.request

    try:
        with urllib.request.urlopen("https://pypi.org/pypi/yt-dlp/json", timeout=timeout) as r:
            return json.load(r)["info"]["version"]
    except Exception:
        return None


def version_tuple(v: str) -> tuple:
    """تبدیل رشتهٔ نسخه به tuple عددی برای مقایسهٔ درست."""
    try:
        return tuple(int(x) for x in re.findall(r"\d+", str(v)))
    except Exception:
        return ()


def is_newer_version(latest: str, current: str) -> bool:
    """آیا نسخهٔ latest از current جدیدتر است؟"""
    lt, ct = version_tuple(latest), version_tuple(current)
    return bool(lt and ct and lt > ct)


class DownloadCancelled(Exception):
    """استثنای لغو دانلود توسط کاربر"""
    pass


class _YdlLogger:
    """لاگر ساده برای yt-dlp که پیام‌ها را به callback می‌فرستد"""

    def __init__(self, cb: Optional[Callable[[str], None]] = None):
        self.cb = cb

    def debug(self, msg):
        if self.cb:
            self.cb(msg)

    def warning(self, msg):
        if self.cb:
            self.cb(f"[warning] {msg}")

    def error(self, msg):
        if self.cb:
            self.cb(f"[error] {msg}")


class YouTubeDownloader:
    """کلاس مدیریت دانلود و استخراج اطلاعات با yt-dlp"""

    # User-Agent پیش‌فرض شبیه Chrome ویندوز
    DEFAULT_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # ⚡ تنظیمات سرعت — قابل تغییر بر اساس نیاز
    CONCURRENT_FRAGMENTS = 8        # تعداد دانلود همزمان قطعات (پیش‌فرض: 1)
    HTTP_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB — همان مقداری که throttle یوتیوب را bypass می‌کند
    BUFFER_SIZE = 1024 * 1024       # 1MB بافر

    def __init__(self):
        self.cancel_flag = threading.Event()
        self.current_ydl: Optional[yt_dlp.YoutubeDL] = None

    def cancel(self):
        """درخواست لغو دانلود جاری"""
        self.cancel_flag.set()

    def _reset(self):
        self.cancel_flag.clear()

    # ---------- ساخت base_opts ----------
    def _build_base_opts(
        self,
        cookie_browser: Optional[str] = None,
        cookie_file: Optional[str] = None,
        retries: int = 5,
        quiet: bool = False,
        verbose: bool = False,
        proxy: Optional[str] = None,
        rate_limit: int = 0,
        resume: bool = True,
        use_aria2c: bool = True,
    ) -> dict:
        """ساخت پارامترهای پایه برای yt-dlp — با تنظیمات سرعت بالا"""

        opts = {
            "quiet": quiet,
            "no_warnings": quiet,
            "retries": retries,
            "fragment_retries": retries,
            "socket_timeout": 30,
            "nocheckcertificate": False,
            "ignoreerrors": False,

            # ⚡⚡⚡ تنظیمات کلیدی سرعت ⚡⚡⚡
            # ۱. تعداد دانلود همزمان قطعات ویدئوهای HLS/DASH
            "concurrent_fragment_downloads": self.CONCURRENT_FRAGMENTS,

            # ۲. اندازه چانک HTTP — یوتیوب throttle می‌کند اگر چانک بیشتر از 10MB باشد
            #    این مقدار دقیقاً 10MB است تا از throttle جلوگیری شود
            "http_chunk_size": self.HTTP_CHUNK_SIZE,

            # ۳. اندازه بافر دریافت داده
            "buffersize": self.BUFFER_SIZE,

            # ⚡ User-Agent شبیه مرورگر واقعی برای دور زدن بلاک یوتیوب
            "http_headers": {
                "User-Agent": self.DEFAULT_UA,
                "Accept-Language": "en-US,en;q=0.9",
            },

            # ⚡ استفاده از کلاینت‌های web برای سازگاری با کوکی‌ها
            # default: زیرنویس را درست دانلود می‌کند، web_safari: ویدئوی باکیفیت (HLS)
            # web_creator: فرمت‌های DASH کامل (فقط-ویدئو/فقط-صدا) — دور زدن آزمایش SABR یوتیوب
            "extractor_args": {
                "youtube": {
                    "player_client": ["default", "web_safari", "web_creator"],
                }
            },
        }

        # 🐢 محدودیت سرعت دانلود (KB/s → بایت بر ثانیه). ۰ = بدون محدودیت
        if rate_limit and rate_limit > 0:
            opts["ratelimit"] = int(rate_limit) * 1024

        # ▶️ ادامهٔ دانلود ناقص (Resume) — پیش‌فرض yt-dlp روشن است
        opts["continuedl"] = bool(resume)

        # ⚡ دانلودر خارجی aria2c (اختیاری)
        # نکته مهم: برای فرمت‌های HLS (m3u8) از دانلودر داخلی استفاده می‌کنیم،
        # چون aria2c روی HLS یوتیوب شکست می‌خورد («aria2c exited with code 1»)
        if use_aria2c and self._has_aria2c():
            opts["external_downloader"] = {
                "default": "aria2c",
                "m3u8": "native",
                "m3u8_native": "native",
            }
            opts["external_downloader_args"] = {
                "aria2c": [
                    "-x", str(self.CONCURRENT_FRAGMENTS),  # تعداد کانکشن
                    "-s", str(self.CONCURRENT_FRAGMENTS),  # تعداد split
                    "-k", "1M",                             # حداقل سایز chunk
                    "--min-split-size=1M",
                ]
            }

        if verbose:
            opts["verbose"] = True

        # ⚡ اولویت با فایل کوکی اگر داده شده باشد
        if cookie_file:
            cookie_path = str(Path(cookie_file).resolve())
            if not os.path.isfile(cookie_path):
                raise FileNotFoundError(f"فایل کوکی یافت نشد: {cookie_path}")

            cookie_path = CookieManager.normalize_cookie_file(cookie_path)
            opts["cookiefile"] = cookie_path
            if not quiet:
                print(f"[debug] cookiefile set to: {cookie_path}")

        elif cookie_browser:
            browser = cookie_browser.lower().strip()
            browser_map = {
                "chrome": "chrome",
                "firefox": "firefox",
                "edge": "edge",
                "opera": "opera",
                "brave": "brave",
                "chromium": "chromium",
                "vivaldi": "vivaldi",
                "safari": "safari",
            }
            browser_name = browser_map.get(browser, browser)
            opts["cookiesfrombrowser"] = (browser_name,)
            if not quiet:
                print(f"[debug] cookiesfrombrowser set to: {browser_name}")

        if proxy:
            opts["proxy"] = proxy
            if not quiet:
                print(f"[debug] proxy set to: {proxy}")

        # ffmpeg باندل‌شده (در نسخه exe) — برای استخراج صدا و ادغام
        ffmpeg_loc = _find_ffmpeg_location()
        if ffmpeg_loc:
            opts["ffmpeg_location"] = ffmpeg_loc

        return opts

    @staticmethod
    def _has_aria2c() -> bool:
        """بررسی نصب بودن aria2c روی سیستم"""
        import shutil
        return shutil.which("aria2c") is not None

    # ---------- استخراج فرمت‌ها ----------
    def extract_formats(
        self,
        url: str,
        cookie_browser: Optional[str] = None,
        cookie_file: Optional[str] = None,
        retries: int = 5,
        log_callback: Optional[Callable[[str], None]] = None,
        verbose: bool = False,
        proxy: Optional[str] = None,
    ) -> dict:
        """استخراج لیست فرمت‌های موجود"""
        self._reset()
        opts = self._build_base_opts(
            cookie_browser, cookie_file, retries, quiet=True, verbose=verbose, proxy=proxy
        )
        opts["skip_download"] = True

        if log_callback:
            log_callback(f"[info] در حال استخراج اطلاعات از: {url}")
            src = opts.get("cookiefile") or opts.get("cookiesfrombrowser")
            log_callback(f"[debug] منبع کوکی: {src}")
            log_callback(
                f"[info] ⚡ تنظیمات سرعت: {self.CONCURRENT_FRAGMENTS} دانلود همزمان، "
                f"چانک {self.HTTP_CHUNK_SIZE // (1024*1024)}MB"
            )
            if "external_downloader" in opts:
                log_callback(f"[info] 🚀 دانلودر خارجی: {opts['external_downloader']}")

        opts["logger"] = _YdlLogger(log_callback)
        opts["verbose"] = verbose

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return info

    # ---------- استخراج پلی‌لیست ----------
    def extract_playlist(
        self,
        url: str,
        cookie_browser: Optional[str] = None,
        cookie_file: Optional[str] = None,
        retries: int = 5,
        log_callback: Optional[Callable[[str], None]] = None,
        proxy: Optional[str] = None,
    ) -> dict:
        """استخراج لیست ویدئوهای یک پلی‌لیست (سریع و بدون دانلود)"""
        self._reset()
        opts = self._build_base_opts(cookie_browser, cookie_file, retries, quiet=True, proxy=proxy)
        opts["skip_download"] = True
        opts["extract_flat"] = "in_playlist"  # فقط اطلاعات سطحی هر ویدئو (سریع)
        opts["logger"] = _YdlLogger(log_callback)

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return self._normalize_playlist(info)

    @staticmethod
    def _normalize_playlist(info: dict) -> dict:
        """تبدیل دیکشنری پلی‌لیست yt-dlp به ساختار استاندارد برنامه"""
        entries = info.get("entries") or []
        items = []
        for e in entries:
            if not e:
                continue
            vid = e.get("url") or e.get("webpage_url")
            if not vid and e.get("id"):
                vid = f"https://www.youtube.com/watch?v={e['id']}"
            if not vid:
                continue
            items.append({
                "id": e.get("id", ""),
                "title": e.get("title", "") or "(بدون عنوان)",
                "url": vid,
                "duration": e.get("duration"),
                "uploader": e.get("uploader") or e.get("channel") or "",
                "index": e.get("playlist_index", 0) or 0,
            })

        return {
            "title": info.get("title", "") or "پلی‌لیست",
            "uploader": info.get("uploader") or info.get("channel") or "",
            "entries": items,
            "count": len(items),
        }

    # ---------- دانلود ----------
    def download(
        self,
        url: str,
        output_dir: str,
        format_selector: str,
        cookie_browser: Optional[str] = None,
        cookie_file: Optional[str] = None,
        retries: int = 5,
        audio_only: bool = False,
        audio_format: str = "mp3",
        progress_callback: Optional[Callable[[dict], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        postprocessor_callback: Optional[Callable[[str], None]] = None,
        proxy: Optional[str] = None,
        subtitle_langs: Optional[str] = None,
        subtitle_auto: bool = False,
        rate_limit: int = 0,
        resume: bool = True,
        use_aria2c: bool = True,
    ):
        """دانلود ویدئو/صدا با فرمت انتخاب‌شده — با حداکثر سرعت"""
        self._reset()
        opts = self._build_base_opts(
            cookie_browser, cookie_file, retries, quiet=False, proxy=proxy,
            rate_limit=rate_limit, resume=resume, use_aria2c=use_aria2c,
        )

        outtmpl = str(Path(output_dir) / "%(title)s [%(id)s].%(ext)s")
        opts["outtmpl"] = outtmpl
        opts["format"] = format_selector
        opts["merge_output_format"] = "mp4/mkv"

        if audio_only:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": "192",
                }
            ]

        if subtitle_langs or subtitle_auto:
            opts["subtitlesformat"] = "srt"
            if subtitle_langs:
                langs = [l.strip() for l in subtitle_langs.split(",") if l.strip()]
                opts["subtitleslangs"] = langs or ["all"]
            else:
                opts["subtitleslangs"] = ["all"]
            # هم زیرنویس دستی و هم خودکار را بنویس (اکثر ویدئوها فقط زیرنویس خودکار دارند)
            opts["writesubtitles"] = True
            opts["writeautomaticsub"] = True

        def _progress_hook(d):
            if self.cancel_flag.is_set():
                raise DownloadCancelled("دانلود توسط کاربر لغو شد")
            if progress_callback:
                progress_callback(d)

        def _pp_hook(d):
            if postprocessor_callback:
                postprocessor_callback(d.get("postprocessor", ""))

        opts["progress_hooks"] = [_progress_hook]
        opts["postprocessor_hooks"] = [_pp_hook]

        opts["logger"] = _YdlLogger(log_callback)

        try:
            self._run_download(opts, url)
        except DownloadCancelled:
            raise
        except Exception as e:
            err = str(e)
            retry = False

            # ۱) اگر دانلودر خارجی aria2c شکست خورد، با دانلودر داخلی yt-dlp دوباره تلاش کن
            if "aria2c" in err.lower() and opts.get("external_downloader"):
                if log_callback:
                    log_callback(
                        "[warning] ⚠️ دانلودر خارجی aria2c شکست خورد — "
                        "تلاش مجدد با دانلودر داخلی yt-dlp..."
                    )
                opts.pop("external_downloader", None)
                opts.pop("external_downloader_args", None)
                retry = True

            # ۲) اگر زیرنویس فعال بود، بدون زیرنویس هم تلاش کن تا ویدئو همچنان دانلود شود
            if subtitle_langs or subtitle_auto:
                if log_callback:
                    log_callback("[warning] تلاش مجدد بدون زیرنویس...")
                for k in ("writesubtitles", "writeautomaticsub", "subtitleslangs", "subtitlesformat"):
                    opts.pop(k, None)
                retry = True

            if retry:
                self._reset()
                self._run_download(opts, url)
            else:
                raise

    def _run_download(self, opts: dict, url: str):
        """اجرای دانلود با یک YoutubeDL و مدیریت لغو"""
        with yt_dlp.YoutubeDL(opts) as ydl:
            self.current_ydl = ydl
            try:
                ydl.download([url])
            finally:
                self.current_ydl = None
                if self.cancel_flag.is_set():
                    raise DownloadCancelled("دانلود توسط کاربر لغو شد")

    # ---------- کمکی: پارس فرمت‌ها ----------
    @staticmethod
    def parse_formats(info: dict) -> list:
        """تبدیل اطلاعات فرمت‌ها به لیست دیکشنری برای نمایش در جدول"""
        formats = []

        duration = info.get("duration") or 0
        try:
            duration = float(duration)
        except (TypeError, ValueError):
            duration = 0.0

        for f in info.get("formats", []) or []:
            format_id = f.get("format_id", "")
            ext = f.get("ext", "")
            vcodec = f.get("vcodec", "none") or "none"
            acodec = f.get("acodec", "none") or "none"
            resolution = f.get("resolution") or (
                f"{f.get('width', '?')}x{f.get('height', '?')}"
                if f.get("width") else "audio only"
            )
            fps = f.get("fps", "")
            abr = f.get("abr", "")
            vbr = f.get("vbr", "")
            tbr = f.get("tbr", "")
            abr_num = float(abr) if isinstance(abr, (int, float)) else 0.0
            tbr_num = float(tbr) if isinstance(tbr, (int, float)) else 0.0

            filesize = f.get("filesize") or f.get("filesize_approx")
            if not filesize and tbr and duration:
                try:
                    filesize = float(tbr) * 1000 * duration / 8
                except (TypeError, ValueError):
                    filesize = 0

            if filesize:
                size_str = YouTubeDownloader._human_size(filesize)
            else:
                size_str = "?"

            language = (
                f.get("language")
                or f.get("language_preference")
                or ""
            )
            lang_display = YouTubeDownloader._format_language(language)

            has_video = vcodec != "none"
            has_audio = acodec != "none"
            if has_video and has_audio:
                kind = "video+audio"
            elif has_video:
                kind = "video"
            elif has_audio:
                kind = "audio"
            else:
                kind = "other"

            formats.append({
                "id": format_id,
                "ext": ext,
                "resolution": resolution,
                "fps": fps,
                "vcodec": vcodec,
                "acodec": acodec,
                "abr": f"{abr:.1f}k" if isinstance(abr, (int, float)) else "",
                "vbr": f"{vbr:.1f}k" if isinstance(vbr, (int, float)) else "",
                "tbr": f"{tbr:.1f}k" if isinstance(tbr, (int, float)) else "",
                "size": size_str,
                "size_bytes": int(filesize) if filesize else 0,
                "note": f.get("format_note", ""),
                "kind": kind,
                "filesize": filesize or 0,
                "language": lang_display,
                "language_raw": language,
                "abr_num": abr_num,
                "tbr_num": tbr_num,
            })

        order = {"video+audio": 0, "video": 1, "audio": 2, "other": 3}
        formats.sort(key=lambda x: (
            order.get(x["kind"], 9),
            -x["size_bytes"],
        ))

        # بهترین فرمت صدا برای ترکیب با فرمت‌های فقط-ویدئو (ستون «آیدی صدا»)
        best_audio_id = ""
        best_audio_br = -1.0
        for f in formats:
            if f["kind"] == "audio":
                br = f["abr_num"] or f["tbr_num"] or 0.0
                if br > best_audio_br:
                    best_audio_br = br
                    best_audio_id = f["id"]
        for f in formats:
            f["audio_id"] = best_audio_id if f["kind"] == "video" else ""

        return formats

    @staticmethod
    def _format_language(lang_code) -> str:
        """تبدیل کد زبان به نام قابل خواندن"""
        if not lang_code:
            return ""

        if isinstance(lang_code, dict):
            lang_code = lang_code.get("code") or lang_code.get("name") or ""
            if isinstance(lang_code, dict):
                lang_code = lang_code.get("code", "")

        lang_code = str(lang_code).lower().strip()

        lang_map = {
            "en": "English", "en-us": "English (US)", "en-gb": "English (UK)",
            "fa": "فارسی", "ar": "Arabic", "iw": "Hebrew", "he": "Hebrew",
            "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
            "zh-cn": "Chinese (CN)", "zh-tw": "Chinese (TW)",
            "de": "German", "de-de": "German",
            "fr": "French", "fr-fr": "French",
            "es": "Spanish", "es-us": "Spanish (US)",
            "it": "Italian", "pt": "Portuguese", "pt-br": "Portuguese (BR)",
            "ru": "Russian", "uk": "Ukrainian", "pl": "Polish",
            "nl": "Dutch", "nl-nl": "Dutch",
            "hi": "Hindi", "bn": "Bengali", "ml": "Malayalam",
            "id": "Indonesian", "tr": "Turkish", "vi": "Vietnamese",
            "th": "Thai", "sv": "Swedish", "no": "Norwegian",
            "da": "Danish", "fi": "Finnish", "cs": "Czech",
            "el": "Greek", "hu": "Hungarian", "ro": "Romanian",
        }
        return lang_map.get(lang_code, lang_code)

    @staticmethod
    def _human_size(size_bytes: int) -> str:
        try:
            size_bytes = float(size_bytes)
        except Exception:
            return "?"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def _format_size(f: dict, duration=None) -> int:
        """حجم یک فرمت به بایت؛ اگر filesize نبود از bitrate تخمین بزن"""
        sz = f.get("filesize") or f.get("filesize_approx")
        if sz:
            return int(sz)
        tbr = f.get("tbr")
        dur = duration if duration else f.get("duration")
        if tbr and dur:
            try:
                return int(float(tbr) * 1000 * float(dur) / 8)
            except (TypeError, ValueError):
                return 0
        return 0

    @staticmethod
    def estimate_size_for_height(info: dict, height) -> int:
        """برآورد حجم کل (بایت) یک ویدئو برای حداکثر ارتفاع مشخص.

        height: عدد (مثل 1080) یا None (بهترین کیفیت) یا "audio" (فقط صدا)
        """
        formats = info.get("formats") or []
        duration = info.get("duration")
        if not formats:
            return 0

        def is_audio(f):
            return (f.get("vcodec") or "none") == "none" and (f.get("acodec") or "none") != "none"

        def is_video(f):
            return (f.get("vcodec") or "none") != "none"

        if height == "audio":
            audios = [f for f in formats if is_audio(f)]
            if not audios:
                return 0
            best = max(audios, key=lambda f: f.get("tbr") or 0)
            return YouTubeDownloader._format_size(best, duration)

        videos = [f for f in formats if is_video(f)]
        if height is not None:
            videos = [f for f in videos if (f.get("height") or 0) <= height]
        if not videos:
            return 0

        combined = [f for f in videos if (f.get("acodec") or "none") != "none"]
        video_only = [f for f in videos if (f.get("acodec") or "none") == "none"]
        audios = [f for f in formats if is_audio(f)]

        best_v = max(video_only, key=lambda f: ((f.get("height") or 0), f.get("tbr") or 0)) if video_only else None
        best_c = max(combined, key=lambda f: ((f.get("height") or 0), f.get("tbr") or 0)) if combined else None
        best_a = max(audios, key=lambda f: f.get("tbr") or 0) if audios else None

        # معادل bestvideo+bestaudio (فقط-ویدئو + صدا)
        if best_v and best_a:
            return YouTubeDownloader._format_size(best_v, duration) + YouTubeDownloader._format_size(best_a, duration)
        if best_c:
            return YouTubeDownloader._format_size(best_c, duration)
        if best_v:
            return YouTubeDownloader._format_size(best_v, duration)
        if best_a:
            return YouTubeDownloader._format_size(best_a, duration)
        return 0