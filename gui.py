import sys
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
import pyperclip
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QBrush, QColor, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QProgressBar, QTextEdit, QFileDialog,
    QGroupBox, QGridLayout, QMessageBox, QHeaderView, QCheckBox,
    QSpinBox, QStatusBar, QAbstractItemView, QRadioButton,
    QButtonGroup, QScrollArea, QFrame, QSizePolicy,
    QSystemTrayIcon, QMenu,
)

from downloader import (
    YouTubeDownloader,
    DownloadCancelled,
    friendly_error,
    installed_ytdlp_version,
    latest_ytdlp_version,
    is_newer_version,
)
from cookies import CookieManager
from settings import SettingsManager
from version import __version__


def _app_icon() -> QIcon:
    """ساخت آیکون برنامه (از assets/icon.png؛ در حالت exe هم جستجو می‌کند)"""
    import os

    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(os.path.join(exe_dir, "assets", "icon.png"))
        if hasattr(sys, "_MEIPASS"):
            candidates.append(os.path.join(sys._MEIPASS, "assets", "icon.png"))
    candidates.append(str(Path(__file__).resolve().parent / "assets" / "icon.png"))

    for c in candidates:
        if os.path.isfile(c):
            return QIcon(c)
    return QIcon()


def _setup_file_logging():
    """تنظیم logging برای نوشتن لاگ‌ها در فایل (با چرخش خودکار)"""
    log_dir = Path.home() / ".youtube_downloader" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("youtube_downloader")
    logger.setLevel(logging.INFO)
    if not logger.handlers:  # جلوگیری از handler تکراری
        handler = RotatingFileHandler(
            log_dir / "app.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
    logger.propagate = False


# توقف کوتاه بین ویدئوهای پلی‌لیست (ثانیه) برای جلوگیری از تشخیص ربات یوتیوب
PLAYLIST_ITEM_DELAY = 3.0


def _is_bot_block_error(msg: str) -> bool:
    """تشخیص خطای «Sign in to confirm you're not a bot» یوتیوب"""
    m = (msg or "").lower()
    return (
        "sign in to confirm" in m
        or "not a bot" in m
        or "please sign in" in m
        or "confirm you're not a bot" in m
    )


class WorkerSignals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(dict)
    formats_ready = pyqtSignal(dict)
    playlist_ready = pyqtSignal(dict)
    playlist_size = pyqtSignal(dict)
    playlist_item_done = pyqtSignal(int)
    update_checked = pyqtSignal(str, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    status = pyqtSignal(str)


from ui_utils import (
    YOUTUBE_URL_RE,
    is_playlist_url,
    QUALITY_OPTIONS,
    QUALITY_HEIGHT,
    NumericTableWidgetItem,
    DARK_QSS,
    DONE_ROLE,
)
from ui_builder import MainWindowUIBuilder


class MainWindow(MainWindowUIBuilder, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("دانلودر یوتیوب — yt-dlp GUI")
        self.setWindowIcon(_app_icon())
        self.resize(1250, 900)
        self.setMinimumSize(900, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.settings = SettingsManager()
        self.cookie_mgr = CookieManager()
        self.downloader = YouTubeDownloader()
        self.signals = WorkerSignals()

        self.signals.log.connect(self._append_log)
        self.signals.progress.connect(self._on_progress)
        self.signals.formats_ready.connect(self._on_formats_ready)
        self.signals.playlist_ready.connect(self._on_playlist_ready)
        self.signals.playlist_size.connect(self._on_playlist_size)
        self.signals.playlist_item_done.connect(self._on_playlist_item_done)
        self.signals.update_checked.connect(self._on_update_checked)
        self.signals.finished.connect(self._on_finished)
        self.signals.error.connect(self._on_error)
        self.signals.status.connect(self._set_status)

        self.is_downloading = False
        self.current_info = None
        self.all_formats = []
        self.playlist_items = []
        self.playlist_sizes = {}
        self._size_gen = 0
        self._workers = []
        self._download_meta = None
        self.playlist_title = ""
        self.queue = []
        self._playlist_result = None

        # تسک‌بار ویندوز (ITaskbarList3) — مقداردهی اولیه
        self._taskbar_progress = None
        self._taskbar_initialized = False

        self.tray = None
        self._build_ui()
        self._setup_tray()
        self._load_settings_into_ui()
        self._detect_clipboard_url()
        self._detect_browsers()
        self._check_external_tools()
        self._load_history()
        self._refresh_ytdlp_version_label()

    # ================= ساخت UI =================
    # ================= تنظیمات =================
    def _load_settings_into_ui(self):
        self.path_input.setText(self.settings.get("download_path"))
        self.retries_spin.setValue(int(self.settings.get("retries", 5)))
        use_custom = bool(self.settings.get("use_custom_cookie", False))
        if use_custom:
            self.radio_file.setChecked(True)
            self.cookie_file_input.setText(self.settings.get("custom_cookie_path", ""))

        self.proxy_check.setChecked(bool(self.settings.get("proxy_enabled", False)))
        self.proxy_host.setText(self.settings.get("proxy_host", ""))
        self.proxy_port.setValue(int(self.settings.get("proxy_port", 8080)))
        proto = self.settings.get("proxy_proto", "http")
        idx = self.proxy_proto.findText(proto)
        if idx >= 0:
            self.proxy_proto.setCurrentIndex(idx)

        self.subtitle_check.setChecked(bool(self.settings.get("subtitle_enabled", False)))
        self.subtitle_langs.setText(self.settings.get("subtitle_langs", "fa,en"))
        self.subtitle_auto_check.setChecked(bool(self.settings.get("subtitle_auto", False)))

        self.rate_limit_spin.setValue(int(self.settings.get("rate_limit", 0)))
        self.notify_check.setChecked(bool(self.settings.get("notify_enabled", True)))

    # ================= Clipboard =================
    def _detect_clipboard_url(self):
        try:
            text = pyperclip.paste().strip()
        except Exception:
            text = ""
        if text and YOUTUBE_URL_RE.match(text):
            self.url_input.setText(text)
            self._append_log("[info] لینک یوتیوب از کلیپ‌بورد بارگذاری شد.")
        else:
            self.url_input.setPlaceholderText(
                "لینکی در کلیپ‌بورد یافت نشد. لطفاً دستی وارد کنید..."
            )

    def _validate_url(self, text: str):
        text = text.strip()
        if not text:
            self.url_status.setText("")
            return
        if YOUTUBE_URL_RE.match(text):
            self.url_status.setText("✅ معتبر")
            self.url_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.url_status.setText("❌ نامعتبر")
            self.url_status.setStyleSheet("color: red; font-weight: bold;")

    # ================= مرورگرها =================
    def _detect_browsers(self):
        installed = self.cookie_mgr.detect_installed_browsers()
        self.browser_combo.clear()
        if installed:
            self.browser_combo.addItems(installed)
            saved = self.settings.get("browser", "Chrome")
            if saved in installed:
                self.browser_combo.setCurrentText(saved)
            self._append_log(f"[info] مرورگرهای شناسایی‌شده: {', '.join(installed)}")
        else:
            self._append_log(
                "[warning] هیچ مرورگر پشتیبانی‌شده‌ای یافت نشد. از فایل cookies.txt استفاده کنید."
            )
            QMessageBox.warning(
                self, "کوکی",
                "هیچ مرورگر پشتیبانی‌شده‌ای یافت نشد.\n"
                "لطفاً از فایل cookies.txt استفاده کنید."
            )
            self.radio_file.setChecked(True)

    def _check_external_tools(self):
        """بررسی وجود ffmpeg و aria2c در زمان اجرا"""
        import shutil
        from downloader import _find_ffmpeg_location

        bundled_dir = _find_ffmpeg_location()  # در نسخه exe، پوشه ابزارهای باندل‌شده
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg and bundled_dir:
            ffmpeg = bundled_dir  # ffmpeg باندل‌شده

        aria2c = shutil.which("aria2c")
        if not aria2c and bundled_dir and (Path(bundled_dir) / "aria2c.exe").is_file():
            aria2c = str(Path(bundled_dir) / "aria2c.exe")
        if not ffmpeg:
            self._append_log(
                "[warning] ⚠️ FFmpeg یافت نشد — دانلود صدا (mp3) و ادغام ویدئو+صدا کار نمی‌کند."
            )
            QMessageBox.warning(
                self, "FFmpeg یافت نشد",
                "FFmpeg روی سیستم نصب نیست.\n\n"
                "برای دانلود صدا (mp3) و ادغام ویدئو+صدا به FFmpeg نیاز دارید.\n\n"
                "نصب در ویندوز:\nwinget install Gyan.FFmpeg",
            )
        else:
            self._append_log("[info] ✅ FFmpeg یافت شد.")
        if aria2c:
            self._append_log("[info] 🚀 aria2c یافت شد — دانلود موازی فعال است.")
        else:
            self._append_log("[info] ℹ️ aria2c یافت نشد (اختیاری — برای سرعت بیشتر نصب کنید).")

        node = shutil.which("node")
        if not node:
            self._append_log("[warning] ⚠️ Node.js یافت نشد — دانلود زیرنویس کار نمی‌کند.")
            QMessageBox.warning(
                self, "Node.js یافت نشد",
                "Node.js روی سیستم نصب نیست.\n\n"
                "برای دانلود زیرنویس (تولید PO Token) به Node.js نسخه ۲۲ یا بالاتر نیاز دارید.\n\n"
                "دانلود و نصب از: https://nodejs.org",
            )
        else:
            self._append_log("[info] ✅ Node.js یافت شد — دانلود زیرنویس فعال است.")

    def _toggle_cookie_mode(self):
        use_browser = self.radio_browser.isChecked()
        self.browser_combo.setEnabled(use_browser)
        self.btn_refresh_browsers.setEnabled(use_browser)
        self.cookie_file_input.setEnabled(not use_browser)
        self.btn_browse_cookie.setEnabled(not use_browser)
        self.settings.set("use_custom_cookie", not use_browser)

    def _browse_cookie_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب فایل cookies.txt", "",
            "Cookie Files (*.txt);;All Files (*)"
        )
        if path:
            if self.cookie_mgr.validate_cookie_file(path):
                self.cookie_file_input.setText(path)
                self.settings.set("custom_cookie_path", path)
                self._append_log(f"[info] فایل کوکی انتخاب شد: {path}")
            else:
                QMessageBox.warning(self, "خطا", "فایل انتخابی یک cookies.txt معتبر نیست.")

    # ================= مسیر =================
    def _browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, "انتخاب پوشه ذخیره", self.path_input.text() or str(Path.home())
        )
        if path:
            self.path_input.setText(path)
            self.settings.set("download_path", path)

    # ================= استخراج فرمت‌ها =================
    def _fetch_formats(self):
        url = self.url_input.text().strip()
        if not url or not YOUTUBE_URL_RE.match(url):
            QMessageBox.warning(self, "خطا", "لطفاً یک لینک معتبر یوتیوب وارد کنید.")
            return

        # اگر لینک پلی‌لیست بود، مسیر پلی‌لیست را برو
        if is_playlist_url(url):
            self._fetch_playlist(url)
            return

        self._set_status("در حال استخراج فرمت‌ها...")
        self.btn_fetch.setEnabled(False)
        self.table.setRowCount(0)
        self.tabs.setCurrentIndex(0)  # تب دانلود

        self._spawn_thread(self._fetch_worker, (url,))

    def _fetch_worker(self, url):
        try:
            browser, cookie_file = self._current_cookie()
            if cookie_file and not self.cookie_mgr.validate_cookie_file(cookie_file):
                self.signals.error.emit("فایل کوکی نامعتبر است.")
                return

            info = self.downloader.extract_formats(
                url,
                cookie_browser=browser,
                cookie_file=cookie_file,
                retries=int(self.retries_spin.value()),
                log_callback=lambda m: self.signals.log.emit(m),
                proxy=self._current_proxy(),
            )

            # دفاع در عمق: اگر yt-dlp در عمل یک پلی‌لیست برگرداند
            # (مثلاً URL حاوی list= که تشخیص ندادیم یا لینک کانال)، به مسیر پلی‌لیست بفرست
            if info and (
                info.get("_type") == "playlist"
                or (info.get("entries") and not info.get("formats"))
            ):
                self.signals.playlist_ready.emit(
                    self.downloader._normalize_playlist(info)
                )
                return

            self.signals.formats_ready.emit(info)
        except Exception as e:
            self.signals.error.emit(f"خطا در استخراج فرمت‌ها: {e}")
        finally:
            self.signals.log.emit("[info] استخراج فرمت‌ها به پایان رسید.")

    def _on_formats_ready(self, info: dict):
        self.current_info = info
        self.all_formats = self.downloader.parse_formats(info)
        self._apply_filter()
        self.btn_fetch.setEnabled(True)
        self._set_status(f"فرمت‌ها آماده شد ({len(self.all_formats)} مورد)")

        title = info.get("title", "?")
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "?")
        try:
            duration_str = self._fmt_time(int(duration)) if duration else "?"
        except (TypeError, ValueError):
            duration_str = "?"

        self._append_log(f"[info] 📺 عنوان: {title}")
        self._append_log(f"[info] 👤 کانال: {uploader}")
        self._append_log(f"[info] ⏱️  مدت: {duration_str}")
        self._append_log(f"[info] 📊 تعداد فرمت‌ها: {len(self.all_formats)}")

        kinds = {"video+audio": 0, "video": 0, "audio": 0, "other": 0}
        for f in self.all_formats:
            kinds[f["kind"]] += 1
        self._append_log(
            f"[info] ترکیبی: {kinds['video+audio']}, "
            f"ویدئو تنها: {kinds['video']}, "
            f"صدا تنها: {kinds['audio']}, "
            f"سایر: {kinds['other']}"
        )

    # ================= پلی‌لیست =================
    def _current_cookie(self):
        """بازگرداندن منبع کوکی فعلی بر اساس UI"""
        if self.radio_browser.isChecked():
            return self.browser_combo.currentText().strip() or None, None
        return None, self.cookie_file_input.text().strip() or None

    def _current_proxy(self):
        """ساخت URL پراکسی بر اساس UI؛ اگر غیرفعال یا بدون میزبان بود None برمی‌گرداند"""
        if not self.proxy_check.isChecked():
            return None
        host = self.proxy_host.text().strip()
        if not host:
            return None
        proto = self.proxy_proto.currentText()
        port = self.proxy_port.value()
        return f"{proto}://{host}:{port}"

    def _current_subtitles(self):
        """بازگرداندن تنظیمات زیرنویس: (زبان‌ها یا None، خودکار)"""
        if not self.subtitle_check.isChecked():
            return None, False
        langs = self.subtitle_langs.text().strip() or "all"
        return langs, self.subtitle_auto_check.isChecked()

    def _current_rate_limit(self) -> int:
        """محدودیت سرعت دانلود به KB/s (۰ = بدون محدودیت)"""
        try:
            return int(self.rate_limit_spin.value())
        except Exception:
            return 0

    def _spawn_thread(self, target, args=()):
        """شروع thread و ردیابی آن برای بستن ایمن"""
        self._workers = [t for t in self._workers if t.is_alive()]
        t = threading.Thread(target=target, args=args, daemon=True)
        t.start()
        self._workers.append(t)
        return t

    def _resolve_format(self) -> str:
        """تعیین selector فرمت بر اساس ورودی/جدول/پیش‌فرض + حالت فقط-صدا"""
        fmt = self.format_id_input.text().strip()
        if not fmt:
            selected_rows = sorted(set(i.row() for i in self.table.selectedIndexes()))
            if selected_rows:
                ids = [self.table.item(r, 0).text() for r in selected_rows]
                fmt = "+".join(ids)
                self._append_log(f"[info] فرمت‌های انتخابی از جدول: {fmt}")
            else:
                fmt = "bestvideo+bestaudio/best"
                self._append_log("[info] هیچ فرمتی انتخاب نشد — استفاده از best.")
        if self.audio_only_check.isChecked() and fmt in ("", "bestvideo+bestaudio/best"):
            fmt = "bestaudio/best"
        return fmt

    def _resolve_playlist_format(self) -> str:
        """تعیین selector کیفیت برای دانلود پلی‌لیست"""
        if self.audio_only_check.isChecked():
            return "bestaudio/best"
        return self.playlist_quality_combo.currentData() or "bestvideo+bestaudio/best"

    def _fetch_playlist(self, url):
        self._set_status("در حال استخراج پلی‌لیست...")
        self.btn_fetch.setEnabled(False)
        self.playlist_table.setRowCount(0)
        self._spawn_thread(self._playlist_fetch_worker, (url,))

    def _playlist_fetch_worker(self, url):
        try:
            browser, cookie_file = self._current_cookie()
            if cookie_file and not self.cookie_mgr.validate_cookie_file(cookie_file):
                self.signals.error.emit("فایل کوکی نامعتبر است.")
                return
            info = self.downloader.extract_playlist(
                url,
                cookie_browser=browser,
                cookie_file=cookie_file,
                retries=int(self.retries_spin.value()),
                log_callback=lambda m: self.signals.log.emit(m),
                proxy=self._current_proxy(),
            )
            self.signals.playlist_ready.emit(info)
        except Exception as e:
            self.signals.error.emit(f"خطا در استخراج پلی‌لیست: {e}")
        finally:
            self.signals.log.emit("[info] استخراج پلی‌لیست به پایان رسید.")

    def _on_playlist_ready(self, info: dict):
        self.playlist_items = info.get("entries", [])
        self.playlist_title = info.get("title", "") or "پلی‌لیست"
        self.playlist_sizes = {}
        self._size_gen += 1
        count = len(self.playlist_items)
        self.lbl_playlist_title.setText(
            f"🎵 {info.get('title', 'پلی‌لیست')} — {count} ویدئو"
        )
        self._fill_playlist_table(self.playlist_items)
        self.tabs.setCurrentIndex(1)  # تب پلی‌لیست
        self.btn_fetch.setEnabled(True)
        self.btn_pl_download.setEnabled(True)
        self._set_status(f"پلی‌لیست آماده شد ({count} ویدئو)")
        self._append_log(f"[info] 📋 پلی‌لیست «{info.get('title', '?')}» — {count} ویدئو")
        self._append_log("[info] ⏳ در حال محاسبه حجم تقریبی ویدئوها...")
        self._start_size_fetch()

    def _start_size_fetch(self):
        """شروع برآورد حجم ویدئوها در پس‌زمینه (تدریجی و بدون قفل UI)"""
        gen = self._size_gen
        browser, cookie_file = self._current_cookie()
        proxy = self._current_proxy()
        self._spawn_thread(self._playlist_size_worker, (gen, browser, cookie_file, proxy))

    def _playlist_size_worker(self, gen, browser, cookie_file, proxy):
        # دانلودر جداگانه تا با دانلود اصلی و پرچم لغو تداخل نکند
        size_dl = YouTubeDownloader()
        heights = [None, 2160, 1440, 1080, 720, 480, 360, "audio"]
        for idx, v in enumerate(self.playlist_items):
            if gen != self._size_gen:
                return  # پلی‌لیست جدید بارگذاری شد — متوقف شو
            try:
                info = size_dl.extract_formats(
                    v["url"], cookie_browser=browser, cookie_file=cookie_file, retries=2, proxy=proxy
                )
                sizes = {h: size_dl.estimate_size_for_height(info, h) for h in heights}
            except Exception:
                sizes = {}
            self.signals.playlist_size.emit({"gen": gen, "index": idx, "sizes": sizes})

    def _on_playlist_size(self, data: dict):
        if data.get("gen") != self._size_gen:
            return  # پاسخ از پلی‌لیست قبلی — نادیده بگیر
        idx = data.get("index")
        if idx is None or idx >= len(self.playlist_items):
            return
        self.playlist_sizes[idx] = data.get("sizes", {})
        self._update_row_size(idx)

    def _current_quality_height(self):
        if self.audio_only_check.isChecked():
            return "audio"
        sel = self.playlist_quality_combo.currentData()
        return QUALITY_HEIGHT.get(sel, None)

    def _update_row_size(self, row):
        if row >= self.playlist_table.rowCount():
            return
        sizes = self.playlist_sizes.get(row)
        if not sizes:
            self.playlist_table.setItem(row, 4, QTableWidgetItem("…"))
            return
        h = self._current_quality_height()
        bytes_ = sizes.get(h, 0)
        if bytes_:
            self.playlist_table.setItem(
                row, 4, QTableWidgetItem(YouTubeDownloader._human_size(bytes_))
            )
        else:
            self.playlist_table.setItem(row, 4, QTableWidgetItem("نامشخص"))

    def _refresh_playlist_sizes(self, *_):
        for r in range(self.playlist_table.rowCount()):
            self._update_row_size(r)

    def _fill_playlist_table(self, items):
        self.playlist_table.setRowCount(len(items))
        for row, v in enumerate(items):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked)
            self.playlist_table.setItem(row, 0, chk)

            idx = v.get("index") or (row + 1)
            self.playlist_table.setItem(row, 1, QTableWidgetItem(str(idx)))
            self.playlist_table.setItem(row, 2, QTableWidgetItem(str(v.get("title", ""))))

            dur = v.get("duration")
            dur_str = self._fmt_time(int(dur)) if dur else "?"
            self.playlist_table.setItem(row, 3, QTableWidgetItem(dur_str))

            self.playlist_table.setItem(row, 4, QTableWidgetItem("…"))  # حجم (در حال محاسبه)
            self.playlist_table.setItem(row, 5, QTableWidgetItem(str(v.get("uploader", ""))))

    def _playlist_select_all(self):
        for r in range(self.playlist_table.rowCount()):
            item = self.playlist_table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _playlist_select_none(self):
        for r in range(self.playlist_table.rowCount()):
            item = self.playlist_table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _on_playlist_item_done(self, row: int):
        """علامت‌گذاری ویدئوی دانلودشده با تیک سبز"""
        if 0 <= row < self.playlist_table.rowCount():
            item = self.playlist_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(DONE_ROLE, "done")
                self.playlist_table.viewport().update()

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """حذف کاراکترهای غیرمجاز ویندوز از نام پوشه/فایل"""
        import re

        name = re.sub(r'[<>:"/\\|?*]', "_", (name or "").strip())
        name = name.strip().rstrip(".").strip()
        return name or "playlist"

    def _playlist_output_dir(self, base_dir: str) -> str:
        """ساخت (و بازگرداندن) زیرپوشه‌ای به نام پلی‌لیست"""
        name = self._sanitize_filename(self.playlist_title)
        d = Path(base_dir) / name
        d.mkdir(parents=True, exist_ok=True)
        return str(d)

    def _start_playlist_download(self):
        selected = []  # لیست (شماره‌ردیف, ویدئو) برای علامت‌گذاری تیک سبز
        for r in range(self.playlist_table.rowCount()):
            chk = self.playlist_table.item(r, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked and r < len(self.playlist_items):
                selected.append((r, self.playlist_items[r]))

        if not selected:
            QMessageBox.information(self, "توجه", "ابتدا ویدئو(های) موردنظر را از لیست انتخاب کنید.")
            return

        output_dir = self.path_input.text().strip()
        if not output_dir or not Path(output_dir).is_dir():
            QMessageBox.warning(self, "خطا", "مسیر ذخیره نامعتبر است.")
            return

        # ویدئوهای پلی‌لیست در زیرپوشه‌ای به نام خود پلی‌لیست ذخیره می‌شوند
        output_dir = self._playlist_output_dir(output_dir)
        self._append_log(f"[info] 📁 پوشه ذخیره پلی‌لیست: {output_dir}")

        fmt = self._resolve_playlist_format()
        audio_only = self.audio_only_check.isChecked()
        browser, cookie_file = self._current_cookie()
        proxy = self._current_proxy()
        subtitle_langs, subtitle_auto = self._current_subtitles()
        retries = int(self.retries_spin.value())
        audio_fmt = self.audio_format_combo.currentText()

        quality_label = self.playlist_quality_combo.currentText()
        self._download_meta = {
            "title": f"{self.playlist_title} ({len(selected)} ویدئو)",
            "format": quality_label,
            "type": "playlist",
        }

        self.is_downloading = True
        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_fetch.setEnabled(False)
        self.btn_pl_download.setEnabled(False)
        self.progress_bar.setValue(0)
        self._show_taskbar_progress()
        self._set_taskbar_value(0)
        self._set_status(f"در حال دانلود {len(selected)} ویدئو از پلی‌لیست...")

        self._spawn_thread(
            self._playlist_download_worker,
            (selected, output_dir, fmt, browser, cookie_file, retries, audio_only, audio_fmt,
             proxy, subtitle_langs, subtitle_auto, self._current_rate_limit()),
        )

    def _playlist_download_worker(self, videos, output_dir, fmt, browser, cookie_file,
                                  retries, audio_only, audio_fmt, proxy, subtitle_langs, subtitle_auto,
                                  rate_limit=0):
        total = len(videos)
        success = 0
        failed = 0

        def _dl_one(v):
            """دانلود یک ویدئو از پلی‌لیست"""
            self.downloader.download(
                url=v["url"],
                output_dir=output_dir,
                format_selector=fmt,
                cookie_browser=browser,
                cookie_file=cookie_file,
                retries=retries,
                audio_only=audio_only,
                audio_format=audio_fmt,
                progress_callback=lambda d: self.signals.progress.emit(d),
                log_callback=lambda m: self.signals.log.emit(m),
                postprocessor_callback=lambda p: self.signals.status.emit(
                    f"پس‌پردازش: {p}"
                ),
                proxy=proxy,
                subtitle_langs=subtitle_langs,
                subtitle_auto=subtitle_auto,
                rate_limit=rate_limit,
            )

        for i, (row, v) in enumerate(videos, 1):
            if self.downloader.cancel_flag.is_set():
                self.signals.error.emit("دانلود پلی‌لیست توسط کاربر لغو شد.")
                return
            title = v.get("title", "?")
            self.signals.log.emit(f"[info] ⏬ ({i}/{total}) در حال دانلود: {title}")
            self.signals.status.emit(f"دانلود ویدئوی {i} از {total}")
            done = False
            try:
                _dl_one(v)
                success += 1
                done = True
                self.signals.playlist_item_done.emit(row)
                self.signals.log.emit(f"[info] ✅ ({i}/{total}) تمام شد: {title}")
            except DownloadCancelled:
                self.signals.error.emit("دانلود توسط کاربر لغو شد.")
                return
            except Exception as e:
                err = str(e)
                # اگر خطای تشخیص ربات یوتیوب بود، توقف کوتاه و یک‌بار تلاش مجدد
                if _is_bot_block_error(err):
                    self.signals.log.emit(
                        f"[warning] ⚠️ تشخیص ربات یوتیوب — توقف کوتاه و تلاش مجدد: {title}"
                    )
                    time.sleep(PLAYLIST_ITEM_DELAY * 2)
                    try:
                        _dl_one(v)
                        success += 1
                        done = True
                        self.signals.playlist_item_done.emit(row)
                        self.signals.log.emit(
                            f"[info] ✅ ({i}/{total}) تمام شد (تلاش دوم): {title}"
                        )
                    except DownloadCancelled:
                        self.signals.error.emit("دانلود توسط کاربر لغو شد.")
                        return
                    except Exception as e2:
                        err = str(e2)
                if not done:
                    failed += 1
                    self.signals.log.emit(f"[error] خطا در «{title}»: {friendly_error(err)}")
            # توقف کوتاه بین ویدئوها برای جلوگیری از تشخیص ربات (به‌جز آخرین ویدئو)
            if i < total:
                time.sleep(PLAYLIST_ITEM_DELAY)

        self._playlist_result = (success, failed)
        self.signals.finished.emit()

    def _apply_filter(self):
        idx = self.filter_combo.currentIndex()
        if not self.all_formats:
            self.table.setRowCount(0)
            self.lbl_format_count.setText("0")
            return

        filtered = []

        if idx == 0:  # همه
            filtered = list(self.all_formats)

        elif idx == 1:  # فقط ویدئو
            filtered = [f for f in self.all_formats if f["kind"] == "video"]

        elif idx == 2:  # فقط صدا
            filtered = [f for f in self.all_formats if f["kind"] == "audio"]

        elif idx == 3:  # ویدئو+صدا
            filtered = [f for f in self.all_formats if f["kind"] == "video+audio"]

        elif idx == 4:  # بدون storyboard
            filtered = [
                f for f in self.all_formats
                if "storyboard" not in (f["vcodec"] or "").lower()
                and "storyboard" not in (f.get("note") or "").lower()
            ]

        elif idx == 5:  # بالاترین کیفیت هر رزولوشن
            seen = {}
            for f in self.all_formats:
                if f["kind"] not in ("video+audio", "video"):
                    continue
                res = f["resolution"]
                if res not in seen or f["size_bytes"] > seen[res]["size_bytes"]:
                    seen[res] = f
            filtered = sorted(seen.values(), key=lambda x: -x["size_bytes"])

        self._fill_table(filtered)

    def _fill_table(self, formats: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(formats))

        for row, f in enumerate(formats):
            values = [
                f["id"],
                f.get("audio_id", ""),
                f["resolution"],
                str(f["fps"]),
                f.get("language", ""),
                f["vcodec"],
                f["acodec"],
                f["abr"],
                f["size"],
                f["kind"],
                f["ext"],
            ]
            for col, val in enumerate(values):
                if col == 8:  # ستون سایز — مرتب‌سازی عددی
                    item = NumericTableWidgetItem(str(val))
                    item.setData(Qt.ItemDataRole.UserRole, f.get("size_bytes", 0))
                else:
                    item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                if f["kind"] == "video":
                    item.setForeground(QBrush(QColor("#89b4fa")))
                elif f["kind"] == "audio":
                    item.setForeground(QBrush(QColor("#a6e3a1")))

                # ستون «آیدی صدا» — رنگ زرد متمایز برای دیده‌شدن واضح
                if col == 1 and val:
                    item.setForeground(QBrush(QColor("#f9e2af")))

                self.table.setItem(row, col, item)

        self.table.setSortingEnabled(True)
        self.lbl_format_count.setText(str(len(formats)))

    # ================= استفاده از انتخاب جدول =================
    def _use_selected_formats(self):
        selected_rows = sorted(set(i.row() for i in self.table.selectedIndexes()))
        if not selected_rows:
            QMessageBox.information(
                self, "توجه",
                "لطفاً ابتدا یک یا چند فرمت را از جدول انتخاب کنید."
            )
            return

        ids = []
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ids.append(item.text())

        self.format_id_input.setText("+".join(ids))
        self._append_log(f"[info] ID فرمت‌ها در فیلد وارد شد: {'+'.join(ids)}")

    # ================= شروع دانلود =================
    def _toggle_audio_only(self, checked: bool):
        self.audio_format_combo.setEnabled(checked)
        if hasattr(self, "playlist_quality_combo"):
            self.playlist_quality_combo.setEnabled(not checked)
            self._refresh_playlist_sizes()

    def _build_task(self) -> dict:
        """ساخت دیکشنری تسک از وضعیت فعلی UI"""
        url = self.url_input.text().strip()
        output_dir = self.path_input.text().strip()
        fmt = self._resolve_format()
        audio_only = self.audio_only_check.isChecked()
        browser, cookie_file = self._current_cookie()
        proxy = self._current_proxy()
        subtitle_langs, subtitle_auto = self._current_subtitles()
        retries = int(self.retries_spin.value())
        audio_fmt = self.audio_format_combo.currentText()
        title = self.current_info.get("title", "?") if self.current_info else "?"
        return {
            "title": title, "url": url, "output_dir": output_dir, "fmt": fmt,
            "browser": browser, "cookie_file": cookie_file, "retries": retries,
            "audio_only": audio_only, "audio_fmt": audio_fmt, "proxy": proxy,
            "subtitle_langs": subtitle_langs, "subtitle_auto": subtitle_auto,
            "rate_limit": self._current_rate_limit(),
        }

    def _start_task(self, task: dict):
        """شروع دانلود یک تسک"""
        self._download_meta = {"title": task["title"], "format": task["fmt"], "type": "video"}
        self.is_downloading = True
        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_fetch.setEnabled(False)
        self.progress_bar.setValue(0)
        self._show_taskbar_progress()
        self._set_taskbar_value(0)
        self._set_status(f"در حال دانلود: {task['title']}...")
        self._spawn_thread(self._download_worker, (task,))

    def _start_download(self):
        """شروع دانلود فوری (تک‌ویدئو)"""
        url = self.url_input.text().strip()
        if not url or not YOUTUBE_URL_RE.match(url):
            QMessageBox.warning(self, "خطا", "لطفاً یک لینک معتبر یوتیوب وارد کنید.")
            return

        output_dir = self.path_input.text().strip()
        if not output_dir or not Path(output_dir).is_dir():
            QMessageBox.warning(self, "خطا", "مسیر ذخیره نامعتبر است.")
            return

        task = self._build_task()
        self._append_log(f"[info] Format selector: {task['fmt']}")
        self._start_task(task)

    def _enqueue_current(self):
        """افزودن تسک فعلی به صف دانلود"""
        url = self.url_input.text().strip()
        if not url or not YOUTUBE_URL_RE.match(url):
            QMessageBox.warning(self, "خطا", "لطفاً یک لینک معتبر یوتیوب وارد کنید.")
            return

        output_dir = self.path_input.text().strip()
        if not output_dir or not Path(output_dir).is_dir():
            QMessageBox.warning(self, "خطا", "مسیر ذخیره نامعتبر است.")
            return

        task = self._build_task()
        self.queue.append(task)
        self._refresh_queue_ui()
        self._append_log(f"[info] ➕ به صف اضافه شد: {task['title']} ({len(self.queue)} مورد)")
        self._process_queue()

    def _process_queue(self):
        """پردازش صف: اگر بیکار و صف خالی نبود، مورد بعدی را شروع کن"""
        if self.is_downloading or not self.queue:
            return
        task = self.queue.pop(0)
        self._refresh_queue_ui()
        self._append_log(f"[info] ⏬ شروع دانلود از صف: {task['title']}")
        self._start_task(task)

    def _refresh_queue_ui(self):
        """به‌روزرسانی نمایش لیست صف"""
        if not hasattr(self, "queue_list"):
            return
        self.queue_list.clear()
        for i, task in enumerate(self.queue, 1):
            self.queue_list.addItem(f"{i}. {task['title']} — {task['fmt']}")

    def _remove_selected_from_queue(self):
        """حذف مورد انتخاب‌شده از صف"""
        if not hasattr(self, "queue_list"):
            return
        row = self.queue_list.currentRow()
        if 0 <= row < len(self.queue):
            removed = self.queue.pop(row)
            self._refresh_queue_ui()
            self._append_log(f"[info] 🗑️ از صف حذف شد: {removed['title']}")

    def _download_worker(self, task):
        try:
            self.downloader.download(
                url=task["url"],
                output_dir=task["output_dir"],
                format_selector=task["fmt"],
                cookie_browser=task["browser"],
                cookie_file=task["cookie_file"],
                retries=task["retries"],
                audio_only=task["audio_only"],
                audio_format=task["audio_fmt"],
                progress_callback=lambda d: self.signals.progress.emit(d),
                log_callback=lambda m: self.signals.log.emit(m),
                postprocessor_callback=lambda p: self.signals.status.emit(
                    f"پس‌پردازش: {p}"
                ),
                proxy=task["proxy"],
                subtitle_langs=task["subtitle_langs"],
                subtitle_auto=task["subtitle_auto"],
                rate_limit=task.get("rate_limit", 0),
            )
            self.signals.finished.emit()
        except DownloadCancelled:
            self.signals.error.emit("دانلود توسط کاربر لغو شد.")
        except Exception as e:
            self.signals.error.emit(f"خطای دانلود: {e}")

    def _cancel_download(self):
        if self.is_downloading:
            self.downloader.cancel()
            self._append_log("[warning] درخواست لغو دانلود ارسال شد...")
            self.btn_cancel.setEnabled(False)
            self._hide_taskbar_progress()
            # لغو کامل: صف را هم خالی کن
            if self.queue:
                self.queue.clear()
                self._refresh_queue_ui()
                self._append_log("[warning] صف دانلود نیز پاک شد.")

    # ================= هندلرها =================
    def _on_progress(self, d: dict):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = int(downloaded * 100 / total)
                self.progress_bar.setValue(pct)
                self._set_taskbar_value(pct)
            speed = d.get("speed")
            eta = d.get("eta")
            if speed:
                self.lbl_speed.setText(
                    f"سرعت: {YouTubeDownloader._human_size(speed)}/s"
                )
            if eta is not None:
                self.lbl_eta.setText(f"زمان باقی‌مانده: {self._fmt_time(eta)}")
            if total:
                self.lbl_size.setText(
                    f"حجم: {YouTubeDownloader._human_size(downloaded)} / "
                    f"{YouTubeDownloader._human_size(total)}"
                )
        elif status == "finished":
            self.progress_bar.setValue(100)
            self._set_status("دانلود قطعه تکمیل شد...")

    def _fmt_time(self, seconds: int) -> str:
        seconds = int(seconds)
        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def _on_finished(self):
        self.is_downloading = False
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_fetch.setEnabled(True)
        self.btn_pl_download.setEnabled(bool(self.playlist_items))
        self._set_status("✅ دانلود با موفقیت انجام شد.")
        self._append_log("[info] دانلود با موفقیت به پایان رسید.")
        self._record_history()
        if self.queue:
            # موردهای بیشتری در صف است — بدون دیالوگ ادامه بده
            self._process_queue()
        else:
            self._set_taskbar_value(100)
            self._hide_taskbar_progress()
            if self._playlist_result is not None:
                success, failed = self._playlist_result
                self._playlist_result = None
                if failed == 0:
                    self._notify("دانلود کامل شد", f"{success} ویدئو با موفقیت دانلود شد")
                    QMessageBox.information(
                        self, "موفق",
                        f"دانلود پلی‌لیست کامل شد: {success} ویدئو با موفقیت دانلود شد.",
                    )
                else:
                    self._notify("پایان دانلود پلی‌لیست", f"موفق: {success} — ناموفق: {failed}")
                    QMessageBox.warning(
                        self, "پایان دانلود پلی‌لیست",
                        f"دانلود پلی‌لیست پایان یافت:\n✅ موفق: {success}\n❌ ناموفق: {failed}",
                    )
            else:
                self._notify("دانلود کامل شد", "دانلود با موفقیت به پایان رسید")
                QMessageBox.information(self, "موفق", "دانلود با موفقیت به پایان رسید.")

    def _on_error(self, msg: str):
        self.is_downloading = False
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_fetch.setEnabled(True)
        self.btn_pl_download.setEnabled(bool(self.playlist_items))
        self._set_status(f"❌ خطا: {msg}")
        self._append_log(f"[error] {msg}")
        if self.queue:
            # ادامه صف با وجود خطا (خطا لاگ شده است)
            self._process_queue()
        else:
            self._hide_taskbar_progress()
            friendly = friendly_error(msg)
            self._notify("خطای دانلود", friendly)
            QMessageBox.critical(self, "خطا", friendly)

    def _append_log(self, msg: str):
        self.log_box.append(msg)
        sb = self.log_box.verticalScrollBar()
        sb.setValue(sb.maximum())
        logging.getLogger("youtube_downloader").info(msg)

    def _set_status(self, msg: str):
        self.lbl_status.setText(f"وضعیت: {msg}")
        self.statusBar().showMessage(msg)

    # ================= تاریخچه =================
    def _load_history(self):
        self._refresh_history_table()

    def _refresh_history_table(self):
        history = self.settings.get_history()
        self.history_table.setRowCount(len(history))
        for row, rec in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(rec.get("title", ""))))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(rec.get("date", ""))))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(rec.get("format", ""))))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(rec.get("type", ""))))

    def _clear_history(self):
        ret = QMessageBox.question(
            self, "پاک کردن تاریخچه",
            "آیا مطمئن هستید که تاریخچه دانلود پاک شود؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.settings.set("history", [])
            self._refresh_history_table()
            self._append_log("[info] تاریخچه دانلود پاک شد.")

    def _record_history(self):
        meta = self._download_meta
        if not meta:
            return
        from datetime import datetime
        self.settings.add_history({
            "title": meta.get("title", "?"),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "format": meta.get("format", ""),
            "type": meta.get("type", "video"),
        })
        self._refresh_history_table()
        self._download_meta = None

    # ================= ذخیره تنظیمات در بستن =================
    def _save_settings(self):
        self.settings.set("download_path", self.path_input.text())
        self.settings.set("browser", self.browser_combo.currentText())
        self.settings.set("retries", int(self.retries_spin.value()))
        self.settings.set("use_custom_cookie", self.radio_file.isChecked())
        self.settings.set("custom_cookie_path", self.cookie_file_input.text())
        self.settings.set("proxy_enabled", self.proxy_check.isChecked())
        self.settings.set("proxy_host", self.proxy_host.text().strip())
        self.settings.set("proxy_port", int(self.proxy_port.value()))
        self.settings.set("proxy_proto", self.proxy_proto.currentText())
        self.settings.set("subtitle_enabled", self.subtitle_check.isChecked())
        self.settings.set("subtitle_langs", self.subtitle_langs.text().strip())
        self.settings.set("subtitle_auto", self.subtitle_auto_check.isChecked())
        self.settings.set("rate_limit", int(self.rate_limit_spin.value()))
        self.settings.set("notify_enabled", self.notify_check.isChecked())

    # ================= منوی برنامه =================
    def _exit_app(self):
        """خروج از برنامه (از منو) — از closeEvent برای تأیید دانلود فعال استفاده می‌کند"""
        self.close()

    def _show_about(self):
        QMessageBox.about(
            self,
            "درباره برنامه",
            f"<h3>دانلودر یوتیوب — نسخه {__version__}</h3>"
            "<p>اپلیکیشن دسکتاپ دانلود ویدئو و صوت از یوتیوب.</p>"
            "<p><b>تکنولوژی:</b> Python + PyQt6 + yt-dlp</p>"
            "<p>رابط کاربری فارسی (راست‌به‌چپ)</p>",
        )

    def _show_help(self):
        QMessageBox.information(
            self,
            "راهنمای استفاده",
            "<b>۱) دانلود ویدئو:</b> لینک را وارد کنید → استخراج فرمت‌ها → انتخاب کیفیت → شروع دانلود.<br>"
            "<b>۲) پلی‌لیست:</b> لینک پلی‌لیست → انتخاب ویدئوها → دانلود.<br>"
            "<b>۳) صف دانلود:</b> برای دانلود پشت‌سرهم از «افزودن به صف» استفاده کنید.<br>"
            "<b>۴) زیرنویس:</b> در بخش ذخیره‌سازی، زیرنویس را فعال کنید.<br>"
            "<b>۵) تنظیمات:</b> مسیر ذخیره، محدودیت سرعت، اعلان‌ها و به‌روزرسانی در تب «⚙️ تنظیمات».<br><br>"
            "<b>میان‌برها:</b> Ctrl+Q (خروج)، F1 (راهنما).",
        )

    # ================= اعلان سیستم (Tray) =================
    def _setup_tray(self):
        """راه‌اندازی آیکون tray برای اعلان‌های ویندوز"""
        self.tray = None
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return
            icon = _app_icon()
            if icon.isNull():
                return
            self.tray = QSystemTrayIcon(icon, self)
            self.tray.setToolTip("دانلودر یوتیوب")
            menu = QMenu()
            act_show = menu.addAction("نمایش پنجره")
            act_show.triggered.connect(self._restore_window)
            menu.addSeparator()
            act_exit = menu.addAction("خروج")
            act_exit.triggered.connect(self._exit_app)
            self.tray.setContextMenu(menu)
            self.tray.activated.connect(self._on_tray_activated)
            self.tray.show()
        except Exception:
            self.tray = None

    def _restore_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._restore_window()

    def _notify(self, title: str, message: str):
        """نمایش اعلان ویندوز (در صورت فعال بودن تنظیمات)"""
        try:
            if not self.notify_check.isChecked():
                return
            if self.tray is not None:
                self.tray.showMessage(
                    title, message, QSystemTrayIcon.MessageIcon.Information, 5000
                )
            else:
                self.statusBar().showMessage(f"{title} — {message}", 5000)
        except Exception:
            pass

    # ================= به‌روزرسانی yt-dlp =================
    def _refresh_ytdlp_version_label(self):
        try:
            self.lbl_ytdlp_version.setText(f"نسخهٔ فعلی: {installed_ytdlp_version()}")
        except Exception:
            pass

    def _menu_check_update(self):
        self.tabs.setCurrentIndex(3)  # تب تنظیمات
        self._check_ytdlp_update()

    def _check_ytdlp_update(self):
        """بررسی به‌روزرسانی yt-dlp در پس‌زمینه (بدون قفل UI)"""
        self.lbl_update_status.setText("⏳ در حال بررسی...")
        self.lbl_update_status.setStyleSheet("color: #a6adc8;")
        self.btn_check_update.setEnabled(False)
        self._spawn_thread(self._update_check_worker)

    def _update_check_worker(self):
        current = installed_ytdlp_version()
        latest = latest_ytdlp_version() or ""
        self.signals.update_checked.emit(current, latest)

    def _on_update_checked(self, current: str, latest: str):
        self.btn_check_update.setEnabled(True)
        self.lbl_ytdlp_version.setText(f"نسخهٔ فعلی: {current}")
        if not latest:
            self.lbl_update_status.setText("❌ بررسی ناموفق — اتصال اینترنت را بررسی کنید")
            self.lbl_update_status.setStyleSheet("color: #f38ba8;")
            self._append_log("[warning] بررسی به‌روزرسانی yt-dlp ناموفق بود.")
            return
        if is_newer_version(latest, current):
            self.lbl_update_status.setText(f"⚠️ نسخهٔ جدیدتر موجود است: {latest}")
            self.lbl_update_status.setStyleSheet("color: #f9e2af;")
            self._append_log(f"[warning] نسخهٔ جدید yt-dlp موجود است: {current} → {latest}")
            self._notify("به‌روزرسانی yt-dlp", f"نسخهٔ جدید {latest} موجود است (فعلی: {current})")
        else:
            self.lbl_update_status.setText(f"✅ به‌رو است (آخرین نسخه: {latest})")
            self.lbl_update_status.setStyleSheet("color: #a6e3a1;")
            self._append_log(f"[info] yt-dlp به‌رو است (نسخه {current}).")

    # ================= ابزارهای نگهداری =================
    def _open_log_folder(self):
        try:
            folder = Path.home() / ".youtube_downloader" / "logs"
            folder.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"باز کردن پوشهٔ لاگ ناموفق بود:\n{e}")

    def _open_download_folder(self):
        p = self.path_input.text().strip()
        if p and Path(p).is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        else:
            QMessageBox.warning(self, "خطا", "مسیر ذخیره معتبر نیست.")

    def _clear_log(self):
        self.log_box.clear()
        self._append_log("[info] لاگ پاک شد.")

    # ================= پیشرفت در تسک‌بار ویندوز =================
    def showEvent(self, event):
        """راه‌اندازی QWinTaskbarProgress پس از نمایش پنجره (که windowHandle معتبر می‌شود)"""
        super().showEvent(event)
        self._setup_taskbar()

    def _setup_taskbar(self):
        """ایجاد TaskbarProgress (ITaskbarList3) پس از نمایش پنجره (فقط ویندوز و فقط یک بار)"""
        if self._taskbar_initialized:
            return
        self._taskbar_initialized = True
        if sys.platform != "win32":
            return
        try:
            from taskbar import TaskbarProgress

            hwnd = int(self.winId())
            self._taskbar_progress = TaskbarProgress(hwnd)
        except Exception:
            # ساخت ITaskbarList3 شکست خورد — بی‌صدا رد شو
            self._taskbar_progress = None

    def _show_taskbar_progress(self):
        if self._taskbar_progress is not None:
            self._taskbar_progress.show()

    def _hide_taskbar_progress(self):
        if self._taskbar_progress is not None:
            self._taskbar_progress.hide()

    def _set_taskbar_value(self, value: int):
        if self._taskbar_progress is not None:
            self._taskbar_progress.set_value(max(0, min(100, int(value))), 100)

    def closeEvent(self, event):
        if self.is_downloading:
            ret = QMessageBox.question(
                self, "خروج از برنامه",
                "دانلود در حال انجام است. می‌خواهید دانلود را لغو کرده و برنامه را ببندید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if ret != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.downloader.cancel()
            # صبر کوتاه برای پایان ایمن و حذف فایل‌های ناقص .part
            for t in list(self._workers):
                t.join(timeout=2)
        self._save_settings()
        event.accept()


def run_app():
    _setup_file_logging()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_QSS)
    app.setWindowIcon(_app_icon())
    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())