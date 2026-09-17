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
    QButtonGroup, QScrollArea, QFrame, QSizePolicy, QTabWidget,
    QListWidget,
)

from ui_utils import QUALITY_OPTIONS, GreenCheckDelegate


class MainWindowUIBuilder:
    """میکسین ساخت رابط کاربری"""

    # ================= ساختار اصلی =================
    def _build_ui(self):
        self._build_menu_bar()
        central = QWidget()
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.tabs = QTabWidget()

        # ---- تب ۱: دانلود ویدئو ----
        download_tab = QWidget()
        self._build_download_tab(download_tab)
        self.tabs.addTab(download_tab, "📥 دانلود ویدئو")

        # ---- تب ۲: پلی‌لیست ----
        playlist_tab = QWidget()
        self._build_playlist_tab(playlist_tab)
        self.tabs.addTab(playlist_tab, "🎵 پلی‌لیست")

        # ---- تب ۳: تاریخچه ----
        history_tab = QWidget()
        self._build_history_tab(history_tab)
        self.tabs.addTab(history_tab, "📜 تاریخچه")

        outer_layout.addWidget(self.tabs, 1)

        # ---- نوار پیشرفت (زیر تب‌ها — همیشه نمایان) ----
        outer_layout.addWidget(self._build_progress_group())

        self.setCentralWidget(central)

        # ---- StatusBar ----
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("آماده")

        self._append_log("[info] برنامه راه‌اندازی شد.")

    # ================= منوی برنامه =================
    def _build_menu_bar(self):
        menubar = self.menuBar()

        # --- منوی فایل ---
        file_menu = menubar.addMenu("فایل")
        act_exit = file_menu.addAction("خروج")
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self._exit_app)

        # --- منوی راهنما ---
        help_menu = menubar.addMenu("راهنما")
        act_help = help_menu.addAction("راهنمای استفاده")
        act_help.setShortcut("F1")
        act_help.triggered.connect(self._show_help)
        act_about = help_menu.addAction("درباره برنامه")
        act_about.triggered.connect(self._show_about)

    # ================= تب دانلود =================
    def _build_download_tab(self, tab):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(self._build_link_group())
        layout.addWidget(self._build_cookie_group())
        layout.addWidget(self._build_proxy_group())
        layout.addWidget(self._build_format_group())
        layout.addWidget(self._build_bottom_group())
        layout.addWidget(self._build_queue_group())
        layout.addStretch(1)

        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    # ================= تب پلی‌لیست =================
    def _build_playlist_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self._build_playlist_group())
        layout.addStretch(1)

    # ================= تب تاریخچه =================
    def _build_history_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self._build_history_group())

    # ================= گروه لینک =================
    def _build_link_group(self):
        group = QGroupBox("۱) لینک ویدئو")
        layout = QHBoxLayout(group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("لینک یوتیوب را وارد کنید...")
        self.url_input.textChanged.connect(self._validate_url)
        layout.addWidget(QLabel("URL:"))
        layout.addWidget(self.url_input, 1)

        self.btn_fetch = QPushButton("🔍 استخراج فرمت‌ها")
        self.btn_fetch.clicked.connect(self._fetch_formats)
        layout.addWidget(self.btn_fetch)

        self.url_status = QLabel("")
        self.url_status.setMinimumWidth(90)
        layout.addWidget(self.url_status)
        return group

    # ================= گروه کوکی =================
    def _build_cookie_group(self):
        group = QGroupBox("۲) کوکی‌ها")
        layout = QGridLayout(group)

        self.radio_browser = QRadioButton("استفاده از کوکی مرورگر")
        self.radio_file = QRadioButton("بارگذاری فایل cookies.txt")
        self.radio_browser.setChecked(True)
        self.cookie_group_btns = QButtonGroup(self)
        self.cookie_group_btns.addButton(self.radio_browser)
        self.cookie_group_btns.addButton(self.radio_file)
        self.radio_browser.toggled.connect(self._toggle_cookie_mode)

        self.browser_combo = QComboBox()
        layout.addWidget(self.radio_browser, 0, 0)
        layout.addWidget(QLabel("مرورگر:"), 0, 1)
        layout.addWidget(self.browser_combo, 0, 2)
        self.btn_refresh_browsers = QPushButton("🔄 بازخوانی")
        self.btn_refresh_browsers.clicked.connect(self._detect_browsers)
        layout.addWidget(self.btn_refresh_browsers, 0, 3)

        layout.addWidget(self.radio_file, 1, 0)
        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setReadOnly(True)
        self.cookie_file_input.setPlaceholderText("مسیر فایل cookies.txt...")
        layout.addWidget(self.cookie_file_input, 1, 1, 1, 2)
        self.btn_browse_cookie = QPushButton("📂 Browse")
        self.btn_browse_cookie.clicked.connect(self._browse_cookie_file)
        layout.addWidget(self.btn_browse_cookie, 1, 3)
        return group

    # ================= گروه پراکسی =================
    def _build_proxy_group(self):
        group = QGroupBox("🌐 پراکسی (Proxy)")
        layout = QHBoxLayout(group)
        self.proxy_check = QCheckBox("فعال")
        self.proxy_proto = QComboBox()
        self.proxy_proto.addItems(["http", "socks5", "socks4", "https"])
        self.proxy_host = QLineEdit()
        self.proxy_host.setPlaceholderText("میزبان (مثلاً 127.0.0.1)")
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(8080)
        layout.addWidget(self.proxy_check)
        layout.addWidget(QLabel("نوع:"))
        layout.addWidget(self.proxy_proto)
        layout.addWidget(QLabel("میزبان:"))
        layout.addWidget(self.proxy_host, 1)
        layout.addWidget(QLabel("پورت:"))
        layout.addWidget(self.proxy_port)
        return group

    # ================= گروه فرمت‌ها =================
    def _build_format_group(self):
        group = QGroupBox("۳) فرمت‌های موجود")
        layout = QVBoxLayout(group)

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
        self.lbl_format_count.setStyleSheet("font-weight: bold; color: #89b4fa;")
        filter_layout.addWidget(self.lbl_format_count)

        layout.addLayout(filter_layout)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels([
            "ID", "آیدی صدا", "کیفیت", "FPS", "زبان",
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
        for i, w in enumerate([70, 80, 130, 55, 100, 130, 130, 90, 110, 110, 80]):
            self.table.setColumnWidth(i, w)

        self.table.setMinimumHeight(320)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.table, 1)

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

        layout.addLayout(id_layout)

        group.setMinimumHeight(450)
        self.format_group = group
        return group

    # ================= گروه پلی‌لیست =================
    def _build_playlist_group(self):
        group = QGroupBox("🎵 پلی‌لیست")
        layout = QVBoxLayout(group)

        self.lbl_playlist_title = QLabel("")
        self.lbl_playlist_title.setStyleSheet("font-weight: bold; color: #89b4fa;")
        layout.addWidget(self.lbl_playlist_title)

        q_layout = QHBoxLayout()
        q_layout.addWidget(QLabel("کیفیت دانلود:"))
        self.playlist_quality_combo = QComboBox()
        for label, selector, _height in QUALITY_OPTIONS:
            self.playlist_quality_combo.addItem(label, selector)
        self.playlist_quality_combo.currentIndexChanged.connect(self._refresh_playlist_sizes)
        q_layout.addWidget(self.playlist_quality_combo)
        q_layout.addStretch()
        layout.addLayout(q_layout)

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
        # delegate برای نمایش تیک سبز ویدئوهای دانلودشده
        self.playlist_table.setItemDelegateForColumn(0, GreenCheckDelegate(self.playlist_table))
        layout.addWidget(self.playlist_table)

        pl_btn_layout = QHBoxLayout()
        self.btn_pl_select_all = QPushButton("✅ انتخاب همه")
        self.btn_pl_select_none = QPushButton("◻️ هیچ‌کدام")
        self.btn_pl_download = QPushButton("⬇️ دانلود انتخاب‌شده")
        self.btn_pl_download.setMinimumHeight(34)
        self.btn_pl_download.setStyleSheet(
            "QPushButton { background-color: #a6e3a1; color: #1e1e2e; font-weight: bold; border-radius:6px; }"
            "QPushButton:disabled { background-color: #45475a; color: #6c7086; }"
        )
        self.btn_pl_download.setEnabled(False)
        self.btn_pl_select_all.clicked.connect(self._playlist_select_all)
        self.btn_pl_select_none.clicked.connect(self._playlist_select_none)
        self.btn_pl_download.clicked.connect(self._start_playlist_download)
        pl_btn_layout.addWidget(self.btn_pl_select_all)
        pl_btn_layout.addWidget(self.btn_pl_select_none)
        pl_btn_layout.addStretch()
        pl_btn_layout.addWidget(self.btn_pl_download)
        layout.addLayout(pl_btn_layout)

        self.playlist_group = group
        return group

    # ================= گروه ذخیره‌سازی و دانلود =================
    def _build_bottom_group(self):
        group = QGroupBox("۴) ذخیره‌سازی و دانلود")
        layout = QGridLayout(group)

        layout.addWidget(QLabel("مسیر ذخیره:"), 0, 0)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        layout.addWidget(self.path_input, 0, 1, 1, 2)
        self.btn_browse_path = QPushButton("📂 Browse")
        self.btn_browse_path.clicked.connect(self._browse_output_dir)
        layout.addWidget(self.btn_browse_path, 0, 3)

        layout.addWidget(QLabel("تعداد تلاش مجدد:"), 1, 0)
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 50)
        layout.addWidget(self.retries_spin, 1, 1)

        self.audio_only_check = QCheckBox("فقط صدا (استخراج با FFmpeg)")
        self.audio_only_check.toggled.connect(self._toggle_audio_only)
        layout.addWidget(self.audio_only_check, 1, 2)

        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "m4a", "opus", "flac", "wav"])
        self.audio_format_combo.setEnabled(False)
        layout.addWidget(self.audio_format_combo, 1, 3)

        # زیرنویس
        layout.addWidget(QLabel("زیرنویس:"), 2, 0)
        self.subtitle_check = QCheckBox("دانلود")
        layout.addWidget(self.subtitle_check, 2, 1)
        self.subtitle_langs = QLineEdit()
        self.subtitle_langs.setPlaceholderText("زبان‌ها (fa,en یا all)")
        layout.addWidget(self.subtitle_langs, 2, 2)
        self.subtitle_auto_check = QCheckBox("خودکار")
        layout.addWidget(self.subtitle_auto_check, 2, 3)

        btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("⬇️ شروع دانلود")
        self.btn_download.setMinimumHeight(38)
        self.btn_download.setStyleSheet(
            "QPushButton { background-color: #a6e3a1; color: #1e1e2e; font-weight: bold; border-radius:6px; }"
            "QPushButton:disabled { background-color: #45475a; color: #6c7086; }"
        )
        self.btn_download.clicked.connect(self._start_download)
        btn_layout.addWidget(self.btn_download, 3)

        self.btn_enqueue = QPushButton("➕ افزودن به صف")
        self.btn_enqueue.clicked.connect(self._enqueue_current)
        btn_layout.addWidget(self.btn_enqueue, 1)

        self.btn_cancel = QPushButton("⛔ لغو دانلود")
        self.btn_cancel.setMinimumHeight(38)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setStyleSheet(
            "QPushButton { background-color: #f38ba8; color: #1e1e2e; font-weight: bold; border-radius:6px; }"
            "QPushButton:disabled { background-color: #45475a; color: #6c7086; }"
        )
        self.btn_cancel.clicked.connect(self._cancel_download)
        btn_layout.addWidget(self.btn_cancel, 1)

        self.btn_clear_log = QPushButton("🧹 پاک کردن لاگ")
        self.btn_clear_log.clicked.connect(lambda: self.log_box.clear())
        btn_layout.addWidget(self.btn_clear_log, 1)

        layout.addLayout(btn_layout, 3, 0, 1, 4)
        return group

    # ================= گروه صف دانلود =================
    def _build_queue_group(self):
        group = QGroupBox("⏳ صف دانلود")
        layout = QVBoxLayout(group)
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(120)
        layout.addWidget(self.queue_list)
        btn_layout = QHBoxLayout()
        self.btn_remove_from_queue = QPushButton("🗑️ حذف انتخاب‌شده از صف")
        self.btn_remove_from_queue.clicked.connect(self._remove_selected_from_queue)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_remove_from_queue)
        layout.addLayout(btn_layout)
        return group

    # ================= گروه پیشرفت =================
    def _build_progress_group(self):
        group = QGroupBox("۵) وضعیت و پیشرفت")
        layout = QVBoxLayout(group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        info_layout = QHBoxLayout()
        self.lbl_speed = QLabel("سرعت: —")
        self.lbl_eta = QLabel("زمان باقی‌مانده: —")
        self.lbl_size = QLabel("حجم: —")
        self.lbl_status = QLabel("وضعیت: آماده")
        for w in [self.lbl_speed, self.lbl_eta, self.lbl_size, self.lbl_status]:
            w.setStyleSheet("font-weight: bold;")
            info_layout.addWidget(w)
        layout.addLayout(info_layout)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(
            "background-color: #11111b; color: #a6adc8; "
            "font-family: Consolas, monospace;"
        )
        self.log_box.setMinimumHeight(140)
        layout.addWidget(self.log_box)
        return group

    # ================= گروه تاریخچه =================
    def _build_history_group(self):
        group = QGroupBox("📜 تاریخچه دانلود")
        layout = QVBoxLayout(group)

        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["عنوان", "تاریخ", "کیفیت", "نوع"])
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setMinimumHeight(260)
        hh = self.history_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.history_table.setColumnWidth(1, 140)
        self.history_table.setColumnWidth(2, 140)
        self.history_table.setColumnWidth(3, 80)
        layout.addWidget(self.history_table)

        hist_btn = QHBoxLayout()
        self.btn_clear_history = QPushButton("🗑️ پاک کردن تاریخچه")
        self.btn_clear_history.clicked.connect(self._clear_history)
        hist_btn.addStretch()
        hist_btn.addWidget(self.btn_clear_history)
        layout.addLayout(hist_btn)
        return group
