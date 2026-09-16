import sys
import threading
import logging
from logging.handlers import RotatingFileHandler
import pyperclip
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QProgressBar, QTextEdit, QFileDialog,
    QGroupBox, QGridLayout, QMessageBox, QHeaderView, QCheckBox,
    QSpinBox, QStatusBar, QAbstractItemView, QRadioButton,
    QButtonGroup, QScrollArea, QFrame, QSizePolicy,
)

from downloader import YouTubeDownloader, DownloadCancelled
from cookies import CookieManager
from settings import SettingsManager


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


class WorkerSignals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(dict)
    formats_ready = pyqtSignal(dict)
    playlist_ready = pyqtSignal(dict)
    playlist_size = pyqtSignal(dict)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    status = pyqtSignal(str)


from ui_utils import (
    YOUTUBE_URL_RE,
    is_playlist_url,
    QUALITY_OPTIONS,
    QUALITY_HEIGHT,
    NumericTableWidgetItem,
)
from ui_builder import MainWindowUIBuilder


class MainWindow(MainWindowUIBuilder, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("دانلودر یوتیوب — yt-dlp GUI")
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

        self._build_ui()
        self._load_settings_into_ui()
        self._detect_clipboard_url()
        self._detect_browsers()
        self._check_external_tools()
        self._load_history()

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
        ffmpeg = shutil.which("ffmpeg")
        aria2c = shutil.which("aria2c")
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
        self.format_group.setVisible(True)
        self.playlist_group.setVisible(False)

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
        self.format_group.setVisible(True)
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
        # مخفی کردن جدول فرمت‌های تک‌ویدئو تا فرم بزرگ نشود
        self.format_group.setVisible(False)
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
        self.playlist_group.setVisible(True)
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

    def _start_playlist_download(self):
        selected = []
        for r in range(self.playlist_table.rowCount()):
            chk = self.playlist_table.item(r, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked and r < len(self.playlist_items):
                selected.append(self.playlist_items[r])

        if not selected:
            QMessageBox.information(self, "توجه", "ابتدا ویدئو(های) موردنظر را از لیست انتخاب کنید.")
            return

        output_dir = self.path_input.text().strip()
        if not output_dir or not Path(output_dir).is_dir():
            QMessageBox.warning(self, "خطا", "مسیر ذخیره نامعتبر است.")
            return

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
        self._set_status(f"در حال دانلود {len(selected)} ویدئو از پلی‌لیست...")

        self._spawn_thread(
            self._playlist_download_worker,
            (selected, output_dir, fmt, browser, cookie_file, retries, audio_only, audio_fmt,
             proxy, subtitle_langs, subtitle_auto),
        )

    def _playlist_download_worker(self, videos, output_dir, fmt, browser, cookie_file,
                                  retries, audio_only, audio_fmt, proxy, subtitle_langs, subtitle_auto):
        total = len(videos)
        for i, v in enumerate(videos, 1):
            if self.downloader.cancel_flag.is_set():
                self.signals.error.emit("دانلود پلی‌لیست توسط کاربر لغو شد.")
                return
            title = v.get("title", "?")
            self.signals.log.emit(f"[info] ⏬ ({i}/{total}) در حال دانلود: {title}")
            self.signals.status.emit(f"دانلود ویدئوی {i} از {total}")
            try:
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
                )
                self.signals.log.emit(f"[info] ✅ ({i}/{total}) تمام شد: {title}")
            except DownloadCancelled:
                self.signals.error.emit("دانلود توسط کاربر لغو شد.")
                return
            except Exception as e:
                self.signals.log.emit(f"[error] خطا در «{title}»: {e}")
                # ادامه با ویدئوی بعدی
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
                if col == 7:  # ستون سایز — مرتب‌سازی عددی
                    item = NumericTableWidgetItem(str(val))
                    item.setData(Qt.ItemDataRole.UserRole, f.get("size_bytes", 0))
                else:
                    item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                if f["kind"] == "video":
                    item.setForeground(Qt.GlobalColor.darkBlue)
                elif f["kind"] == "audio":
                    item.setForeground(Qt.GlobalColor.darkGreen)

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

    def _start_download(self):
        url = self.url_input.text().strip()
        if not url or not YOUTUBE_URL_RE.match(url):
            QMessageBox.warning(self, "خطا", "لطفاً یک لینک معتبر یوتیوب وارد کنید.")
            return

        output_dir = self.path_input.text().strip()
        if not output_dir or not Path(output_dir).is_dir():
            QMessageBox.warning(self, "خطا", "مسیر ذخیره نامعتبر است.")
            return

        fmt = self._resolve_format()
        audio_only = self.audio_only_check.isChecked()

        self._append_log(f"[info] Format selector: {fmt}")

        self.is_downloading = True
        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_fetch.setEnabled(False)
        self.progress_bar.setValue(0)
        self._set_status("در حال دانلود...")

        browser, cookie_file = self._current_cookie()
        proxy = self._current_proxy()
        subtitle_langs, subtitle_auto = self._current_subtitles()

        retries = int(self.retries_spin.value())
        audio_fmt = self.audio_format_combo.currentText()

        title = self.current_info.get("title", "?") if self.current_info else "?"
        self._download_meta = {
            "title": title,
            "format": fmt,
            "type": "video",
        }

        self._spawn_thread(
            self._download_worker,
            (url, output_dir, fmt, browser, cookie_file, retries, audio_only, audio_fmt,
             proxy, subtitle_langs, subtitle_auto),
        )

    def _download_worker(self, url, output_dir, fmt, browser, cookie_file,
                        retries, audio_only, audio_fmt, proxy, subtitle_langs, subtitle_auto):
        try:
            self.downloader.download(
                url=url,
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

    # ================= هندلرها =================
    def _on_progress(self, d: dict):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = int(downloaded * 100 / total)
                self.progress_bar.setValue(pct)
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
        QMessageBox.information(self, "موفق", "دانلود با موفقیت به پایان رسید.")

    def _on_error(self, msg: str):
        self.is_downloading = False
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_fetch.setEnabled(True)
        self.btn_pl_download.setEnabled(bool(self.playlist_items))
        self._set_status(f"❌ خطا: {msg}")
        self._append_log(f"[error] {msg}")
        QMessageBox.critical(self, "خطا", msg)

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
    win = MainWindow()
    win.show()
    sys.exit(app.exec())