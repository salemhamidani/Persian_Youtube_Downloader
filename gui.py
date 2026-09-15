import sys
import threading
import pyperclip
import re
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


class WorkerSignals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(dict)
    formats_ready = pyqtSignal(dict)
    playlist_ready = pyqtSignal(dict)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    status = pyqtSignal(str)


YOUTUBE_URL_RE = re.compile(
    r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/.+$",
    re.IGNORECASE,
)


def is_playlist_url(url: str) -> bool:
    """تشخیص لینک پلی‌لیست از لینک تک‌ویدئو"""
    u = (url or "").strip().lower()
    # هر لینکی که پارامتر list= داشته باشد (حتی watch?v=...&list=...) پلی‌لیست است
    return "/playlist" in u or "list=" in u


# گزینه‌های کیفیت برای دانلود پلی‌لیست: (برچسب، selector یت-dlp)
QUALITY_OPTIONS = [
    ("بهترین کیفیت (خودکار)", "bestvideo+bestaudio/best"),
    ("2160p — 4K", "bestvideo[height<=2160]+bestaudio/best[height<=2160]"),
    ("1440p — 2K", "bestvideo[height<=1440]+bestaudio/best[height<=1440]"),
    ("1080p — Full HD", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
    ("720p — HD", "bestvideo[height<=720]+bestaudio/best[height<=720]"),
    ("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]"),
    ("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]"),
    ("فقط صدا (بهترین)", "bestaudio/best"),
]


class MainWindow(QMainWindow):
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
        self.signals.finished.connect(self._on_finished)
        self.signals.error.connect(self._on_error)
        self.signals.status.connect(self._set_status)

        self.is_downloading = False
        self.current_info = None
        self.all_formats = []
        self.playlist_items = []

        self._build_ui()
        self._load_settings_into_ui()
        self._detect_clipboard_url()
        self._detect_browsers()

    # ================= ساخت UI =================
    def _build_ui(self):
        # ⚡ QScrollArea اصلی: کل محتوای برنامه داخل آن قرار می‌گیرد
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(self.scroll)

        # ⚡ محتوای داخل اسکرول
        central = QWidget()
        self.scroll.setWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ---- گروه لینک ----
        link_group = QGroupBox("۱) لینک ویدئو")
        link_layout = QHBoxLayout(link_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("لینک یوتیوب را وارد کنید...")
        self.url_input.textChanged.connect(self._validate_url)
        link_layout.addWidget(QLabel("URL:"))
        link_layout.addWidget(self.url_input, 1)

        self.btn_fetch = QPushButton("🔍 استخراج فرمت‌ها")
        self.btn_fetch.clicked.connect(self._fetch_formats)
        link_layout.addWidget(self.btn_fetch)

        self.url_status = QLabel("")
        self.url_status.setMinimumWidth(90)
        link_layout.addWidget(self.url_status)

        main_layout.addWidget(link_group)

        # ---- گروه کوکی ----
        cookie_group = QGroupBox("۲) کوکی‌ها")
        cookie_layout = QGridLayout(cookie_group)

        self.radio_browser = QRadioButton("استفاده از کوکی مرورگر")
        self.radio_file = QRadioButton("بارگذاری فایل cookies.txt")
        self.radio_browser.setChecked(True)
        self.cookie_group_btns = QButtonGroup(self)
        self.cookie_group_btns.addButton(self.radio_browser)
        self.cookie_group_btns.addButton(self.radio_file)
        self.radio_browser.toggled.connect(self._toggle_cookie_mode)

        self.browser_combo = QComboBox()
        cookie_layout.addWidget(self.radio_browser, 0, 0)
        cookie_layout.addWidget(QLabel("مرورگر:"), 0, 1)
        cookie_layout.addWidget(self.browser_combo, 0, 2)
        self.btn_refresh_browsers = QPushButton("🔄 بازخوانی")
        self.btn_refresh_browsers.clicked.connect(self._detect_browsers)
        cookie_layout.addWidget(self.btn_refresh_browsers, 0, 3)

        cookie_layout.addWidget(self.radio_file, 1, 0)
        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setReadOnly(True)
        self.cookie_file_input.setPlaceholderText("مسیر فایل cookies.txt...")
        cookie_layout.addWidget(self.cookie_file_input, 1, 1, 1, 2)
        self.btn_browse_cookie = QPushButton("📂 Browse")
        self.btn_browse_cookie.clicked.connect(self._browse_cookie_file)
        cookie_layout.addWidget(self.btn_browse_cookie, 1, 3)

        main_layout.addWidget(cookie_group)

        # ---- گروه فرمت‌ها ----
        format_group = QGroupBox("۳) فرمت‌های موجود")
        format_layout = QVBoxLayout(format_group)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("فیلتر:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "همه",
            "فقط ویدئو (تصویر بدون صدا)",
            "فقط صدا",
            "ویدئو+صدا (تک‌فایل آماده)",
            "بدون storyboard",
            "بالاترین کیفیت هر رزولوشن",
        ])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()

        filter_layout.addWidget(QLabel("تعداد نمایش:"))
        self.lbl_format_count = QLabel("0")
        self.lbl_format_count.setStyleSheet("font-weight: bold; color: #1976d2;")
        filter_layout.addWidget(self.lbl_format_count)

        format_layout.addLayout(filter_layout)

        # ⚡ جدول با ستون‌های اضافه‌شده
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "ID", "کیفیت", "FPS", "زبان",
            "کدک ویدئو", "کدک صدا", "بیت‌ریت صدا",
            "سایز", "نوع", "کانتینر"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        for i, w in enumerate([70, 130, 55, 100, 130, 130, 90, 110, 110, 80]):
            self.table.setColumnWidth(i, w)

        # ⚡ ارتفاع ثابت و قابل تنظیم برای جدول (چون داخل QScrollArea است)
        self.table.setMinimumHeight(320)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        format_layout.addWidget(self.table, 1)

        # ---- انتخاب ID مستقیم ----
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("یا ID فرمت را مستقیم وارد کنید:"))
        self.format_id_input = QLineEdit()
        self.format_id_input.setPlaceholderText(
            "مثال: 137+140 (ویدئو+صدا) یا bestaudio یا 96-17"
        )
        id_layout.addWidget(self.format_id_input, 1)

        self.btn_use_selected = QPushButton("📌 استفاده از انتخاب جدول")
        self.btn_use_selected.clicked.connect(self._use_selected_formats)
        id_layout.addWidget(self.btn_use_selected)

        format_layout.addLayout(id_layout)

        # ⚡ ارتفاع حداقلی برای گروه فرمت‌ها
        format_group.setMinimumHeight(450)
        self.format_group = format_group
        main_layout.addWidget(format_group)

        # ---- گروه پلی‌لیست ----
        self.playlist_group = QGroupBox("🎵 پلی‌لیست")
        playlist_layout = QVBoxLayout(self.playlist_group)

        self.lbl_playlist_title = QLabel("")
        self.lbl_playlist_title.setStyleSheet("font-weight: bold; color: #1976d2;")
        playlist_layout.addWidget(self.lbl_playlist_title)

        # کیفیت دانلود پلی‌لیست
        q_layout = QHBoxLayout()
        q_layout.addWidget(QLabel("کیفیت دانلود:"))
        self.playlist_quality_combo = QComboBox()
        for label, selector in QUALITY_OPTIONS:
            self.playlist_quality_combo.addItem(label, selector)
        q_layout.addWidget(self.playlist_quality_combo)
        q_layout.addStretch()
        playlist_layout.addLayout(q_layout)

        self.playlist_table = QTableWidget(0, 5)
        self.playlist_table.setHorizontalHeaderLabels(["", "#", "عنوان", "مدت", "کانال"])
        self.playlist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.playlist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.playlist_table.setAlternatingRowColors(True)
        self.playlist_table.verticalHeader().setVisible(False)
        self.playlist_table.verticalHeader().setDefaultSectionSize(26)
        ph = self.playlist_table.horizontalHeader()
        ph.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        ph.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        ph.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        ph.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        ph.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.playlist_table.setColumnWidth(0, 32)
        self.playlist_table.setColumnWidth(1, 46)
        self.playlist_table.setColumnWidth(3, 72)
        self.playlist_table.setColumnWidth(4, 150)
        self.playlist_table.setMinimumHeight(260)
        playlist_layout.addWidget(self.playlist_table)

        pl_btn_layout = QHBoxLayout()
        self.btn_pl_select_all = QPushButton("✅ انتخاب همه")
        self.btn_pl_select_none = QPushButton("◻️ هیچ‌کدام")
        self.btn_pl_download = QPushButton("⬇️ دانلود انتخاب‌شده")
        self.btn_pl_download.setMinimumHeight(34)
        self.btn_pl_download.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-weight: bold; border-radius:6px; }"
            "QPushButton:disabled { background-color: #9e9e9e; }"
        )
        self.btn_pl_download.setEnabled(False)
        self.btn_pl_select_all.clicked.connect(self._playlist_select_all)
        self.btn_pl_select_none.clicked.connect(self._playlist_select_none)
        self.btn_pl_download.clicked.connect(self._start_playlist_download)
        pl_btn_layout.addWidget(self.btn_pl_select_all)
        pl_btn_layout.addWidget(self.btn_pl_select_none)
        pl_btn_layout.addStretch()
        pl_btn_layout.addWidget(self.btn_pl_download)
        playlist_layout.addLayout(pl_btn_layout)

        self.playlist_group.setVisible(False)  # تا بارگذاری پلی‌لیست پنهان می‌ماند
        main_layout.addWidget(self.playlist_group)

        # ---- گروه ذخیره‌سازی + دانلود ----
        bottom_group = QGroupBox("۴) ذخیره‌سازی و دانلود")
        bottom_layout = QGridLayout(bottom_group)

        bottom_layout.addWidget(QLabel("مسیر ذخیره:"), 0, 0)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        bottom_layout.addWidget(self.path_input, 0, 1, 1, 2)
        self.btn_browse_path = QPushButton("📂 Browse")
        self.btn_browse_path.clicked.connect(self._browse_output_dir)
        bottom_layout.addWidget(self.btn_browse_path, 0, 3)

        bottom_layout.addWidget(QLabel("تعداد تلاش مجدد:"), 1, 0)
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 50)
        bottom_layout.addWidget(self.retries_spin, 1, 1)

        self.audio_only_check = QCheckBox("فقط صدا (استخراج با FFmpeg)")
        self.audio_only_check.toggled.connect(self._toggle_audio_only)
        bottom_layout.addWidget(self.audio_only_check, 1, 2)

        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "m4a", "opus", "flac", "wav"])
        self.audio_format_combo.setEnabled(False)
        bottom_layout.addWidget(self.audio_format_combo, 1, 3)

        btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("⬇️ شروع دانلود")
        self.btn_download.setMinimumHeight(38)
        self.btn_download.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-weight: bold; border-radius:6px; }"
            "QPushButton:disabled { background-color: #9e9e9e; }"
        )
        self.btn_download.clicked.connect(self._start_download)
        btn_layout.addWidget(self.btn_download, 3)

        self.btn_cancel = QPushButton("⛔ لغو دانلود")
        self.btn_cancel.setMinimumHeight(38)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setStyleSheet(
            "QPushButton { background-color: #c62828; color: white; font-weight: bold; border-radius:6px; }"
            "QPushButton:disabled { background-color: #9e9e9e; }"
        )
        self.btn_cancel.clicked.connect(self._cancel_download)
        btn_layout.addWidget(self.btn_cancel, 1)

        self.btn_clear_log = QPushButton("🧹 پاک کردن لاگ")
        self.btn_clear_log.clicked.connect(lambda: self.log_box.clear())
        btn_layout.addWidget(self.btn_clear_log, 1)

        bottom_layout.addLayout(btn_layout, 2, 0, 1, 4)

        main_layout.addWidget(bottom_group)

        # ---- پیشرفت ----
        progress_group = QGroupBox("۵) وضعیت و پیشرفت")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        info_layout = QHBoxLayout()
        self.lbl_speed = QLabel("سرعت: —")
        self.lbl_eta = QLabel("زمان باقی‌مانده: —")
        self.lbl_size = QLabel("حجم: —")
        self.lbl_status = QLabel("وضعیت: آماده")
        for w in [self.lbl_speed, self.lbl_eta, self.lbl_size, self.lbl_status]:
            w.setStyleSheet("font-weight: bold;")
            info_layout.addWidget(w)
        progress_layout.addLayout(info_layout)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; "
            "font-family: Consolas, monospace;"
        )
        self.log_box.setMinimumHeight(180)
        progress_layout.addWidget(self.log_box)

        main_layout.addWidget(progress_group)

        # ⚡ فضای انتهایی برای فاصله مناسب
        main_layout.addStretch(1)

        # ---- StatusBar ----
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("آماده")

        self._append_log("[info] برنامه راه‌اندازی شد.")

    # ================= تنظیمات =================
    def _load_settings_into_ui(self):
        self.path_input.setText(self.settings.get("download_path"))
        self.retries_spin.setValue(int(self.settings.get("retries", 5)))
        use_custom = bool(self.settings.get("use_custom_cookie", False))
        if use_custom:
            self.radio_file.setChecked(True)
            self.cookie_file_input.setText(self.settings.get("custom_cookie_path", ""))

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

        t = threading.Thread(target=self._fetch_worker, args=(url,), daemon=True)
        t.start()

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
        t = threading.Thread(target=self._playlist_fetch_worker, args=(url,), daemon=True)
        t.start()

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
            )
            self.signals.playlist_ready.emit(info)
        except Exception as e:
            self.signals.error.emit(f"خطا در استخراج پلی‌لیست: {e}")
        finally:
            self.signals.log.emit("[info] استخراج پلی‌لیست به پایان رسید.")

    def _on_playlist_ready(self, info: dict):
        self.playlist_items = info.get("entries", [])
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
            self.playlist_table.setItem(row, 4, QTableWidgetItem(str(v.get("uploader", ""))))

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
        retries = int(self.retries_spin.value())
        audio_fmt = self.audio_format_combo.currentText()

        self.is_downloading = True
        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_fetch.setEnabled(False)
        self.btn_pl_download.setEnabled(False)
        self.progress_bar.setValue(0)
        self._set_status(f"در حال دانلود {len(selected)} ویدئو از پلی‌لیست...")

        t = threading.Thread(
            target=self._playlist_download_worker,
            args=(selected, output_dir, fmt, browser, cookie_file,
                  retries, audio_only, audio_fmt),
            daemon=True,
        )
        t.start()

    def _playlist_download_worker(self, videos, output_dir, fmt, browser, cookie_file,
                                  retries, audio_only, audio_fmt):
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
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                if f["kind"] == "video":
                    item.setForeground(Qt.GlobalColor.darkBlue)
                elif f["kind"] == "audio":
                    item.setForeground(Qt.GlobalColor.darkGreen)

                if col == 7:
                    item.setData(Qt.ItemDataRole.UserRole, f.get("size_bytes", 0))

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

        retries = int(self.retries_spin.value())
        audio_fmt = self.audio_format_combo.currentText()

        t = threading.Thread(
            target=self._download_worker,
            args=(url, output_dir, fmt, browser, cookie_file,
                  retries, audio_only, audio_fmt),
            daemon=True,
        )
        t.start()

    def _download_worker(self, url, output_dir, fmt, browser, cookie_file,
                        retries, audio_only, audio_fmt):
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

    def _set_status(self, msg: str):
        self.lbl_status.setText(f"وضعیت: {msg}")
        self.statusBar().showMessage(msg)

    # ================= ذخیره تنظیمات در بستن =================
    def closeEvent(self, event):
        self.settings.set("download_path", self.path_input.text())
        self.settings.set("browser", self.browser_combo.currentText())
        self.settings.set("retries", int(self.retries_spin.value()))
        self.settings.set("use_custom_cookie", self.radio_file.isChecked())
        self.settings.set("custom_cookie_path", self.cookie_file_input.text())
        event.accept()


def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())