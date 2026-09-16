"""ساخت رابط کاربری برنامه (میکسین برای MainWindow)

این ماژول فقط ساخت ویجت‌های UI را بر عهده دارد. متدهای آن روی نمونه MainWindow
عمل می‌کنند (دسترسی به self) و سیگنال‌ها را به handler های MainWindow وصل می‌کنند.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
    QProgressBar, QTextEdit, QGroupBox, QHeaderView, QCheckBox,
    QSpinBox, QStatusBar, QAbstractItemView, QRadioButton,
    QButtonGroup, QScrollArea, QFrame, QSizePolicy,
)

from ui_utils import QUALITY_OPTIONS


class MainWindowUIBuilder:
    """میکسین ساخت رابط کاربری"""

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

        # ---- گروه پراکسی ----
        proxy_group = QGroupBox("🌐 پراکسی (Proxy)")
        proxy_layout = QHBoxLayout(proxy_group)
        self.proxy_check = QCheckBox("فعال")
        self.proxy_proto = QComboBox()
        self.proxy_proto.addItems(["http", "socks5", "socks4", "https"])
        self.proxy_host = QLineEdit()
        self.proxy_host.setPlaceholderText("میزبان (مثلاً 127.0.0.1)")
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(8080)
        proxy_layout.addWidget(self.proxy_check)
        proxy_layout.addWidget(QLabel("نوع:"))
        proxy_layout.addWidget(self.proxy_proto)
        proxy_layout.addWidget(QLabel("میزبان:"))
        proxy_layout.addWidget(self.proxy_host, 1)
        proxy_layout.addWidget(QLabel("پورت:"))
        proxy_layout.addWidget(self.proxy_port)
        main_layout.addWidget(proxy_group)

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
        for label, selector, _height in QUALITY_OPTIONS:
            self.playlist_quality_combo.addItem(label, selector)
        self.playlist_quality_combo.currentIndexChanged.connect(self._refresh_playlist_sizes)
        q_layout.addWidget(self.playlist_quality_combo)
        q_layout.addStretch()
        playlist_layout.addLayout(q_layout)

        self.playlist_table = QTableWidget(0, 6)
        self.playlist_table.setHorizontalHeaderLabels(["", "#", "عنوان", "مدت", "حجم", "کانال"])
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
        ph.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.playlist_table.setColumnWidth(0, 32)
        self.playlist_table.setColumnWidth(1, 46)
        self.playlist_table.setColumnWidth(3, 72)
        self.playlist_table.setColumnWidth(4, 90)
        self.playlist_table.setColumnWidth(5, 150)
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

        # زیرنویس
        bottom_layout.addWidget(QLabel("زیرنویس:"), 2, 0)
        self.subtitle_check = QCheckBox("دانلود")
        bottom_layout.addWidget(self.subtitle_check, 2, 1)
        self.subtitle_langs = QLineEdit()
        self.subtitle_langs.setPlaceholderText("زبان‌ها (fa,en یا all)")
        bottom_layout.addWidget(self.subtitle_langs, 2, 2)
        self.subtitle_auto_check = QCheckBox("خودکار")
        bottom_layout.addWidget(self.subtitle_auto_check, 2, 3)

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

        bottom_layout.addLayout(btn_layout, 3, 0, 1, 4)

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

        # ---- گروه تاریخچه ----
        history_group = QGroupBox("📜 تاریخچه دانلود")
        history_layout = QVBoxLayout(history_group)
        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["عنوان", "تاریخ", "کیفیت", "نوع"])
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setMinimumHeight(160)
        hh = self.history_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(1, 140)
        self.history_table.setColumnWidth(2, 140)
        self.history_table.setColumnWidth(3, 80)
        history_layout.addWidget(self.history_table)
        hist_btn = QHBoxLayout()
        self.btn_clear_history = QPushButton("🗑️ پاک کردن تاریخچه")
        self.btn_clear_history.clicked.connect(self._clear_history)
        hist_btn.addStretch()
        hist_btn.addWidget(self.btn_clear_history)
        history_layout.addLayout(hist_btn)
        main_layout.addWidget(history_group)

        # ⚡ فضای انتهایی برای فاصله مناسب
        main_layout.addStretch(1)

        # ---- StatusBar ----
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("آماده")

        self._append_log("[info] برنامه راه‌اندازی شد.")
