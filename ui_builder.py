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
    QListWidget, QPlainTextEdit,
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

        # ---- تب ۴: تنظیمات ----
        settings_tab = QWidget()
        self._build_settings_tab(settings_tab)
        self.tabs.addTab(settings_tab, "⚙️ تنظیمات")

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

        help_menu.addSeparator()
        act_update = help_menu.addAction("بررسی به‌روزرسانی yt-dlp")
        act_update.triggered.connect(self._menu_check_update)

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
        layout.addWidget(self._build_video_info_group())
        layout.addWidget(self._build_format_group())
        layout.addWidget(self._build_batch_group())
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

    # ================= تب تنظیمات =================
    def _build_settings_tab(self, tab):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(self._build_storage_group())
        layout.addWidget(self._build_cookie_group())
        layout.addWidget(self._build_proxy_group())
        layout.addWidget(self._build_speed_group())
        layout.addWidget(self._build_resume_group())
        layout.addWidget(self._build_notify_group())
        layout.addWidget(self._build_update_group())
        layout.addWidget(self._build_maintenance_group())
        layout.addStretch(1)

        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    # ================= گروه ذخیره‌سازی (تب تنظیمات) =================
    def _build_storage_group(self):
        group = QGroupBox("💾 ذخیره‌سازی")
        layout = QGridLayout(group)

        layout.addWidget(QLabel("مسیر ذخیره پیش‌فرض:"), 0, 0)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        layout.addWidget(self.path_input, 0, 1, 1, 2)
        self.btn_browse_path = QPushButton("📂 انتخاب پوشه")
        self.btn_browse_path.clicked.connect(self._browse_output_dir)
        layout.addWidget(self.btn_browse_path, 0, 3)

        layout.addWidget(QLabel("تعداد تلاش مجدد:"), 1, 0)
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 50)
        layout.addWidget(self.retries_spin, 1, 1)
        return group

    # ================= گروه محدودیت سرعت =================
    def _build_speed_group(self):
        group = QGroupBox("🐢 محدودیت سرعت دانلود")
        layout = QHBoxLayout(group)
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(0, 200000)
        self.rate_limit_spin.setSingleStep(50)
        self.rate_limit_spin.setSuffix(" KB/s")
        self.rate_limit_spin.setSpecialValueText("بدون محدودیت")
        layout.addWidget(self.rate_limit_spin)
        hint = QLabel("۰ = بدون محدودیت — مثال: ۵۰۰ یعنی حداکثر ۵۰۰ کیلوبایت بر ثانیه")
        hint.setStyleSheet("color: #a6adc8;")
        layout.addWidget(hint, 1)
        return group

    # ================= گروه اعلان‌ها =================
    def _build_notify_group(self):
        group = QGroupBox("🔔 اعلان‌ها")
        layout = QHBoxLayout(group)
        self.notify_check = QCheckBox("نمایش اعلان ویندوز هنگام پایان یا خطای دانلود")
        layout.addWidget(self.notify_check)
        layout.addStretch()
        return group

    # ================= گروه به‌روزرسانی yt-dlp =================
    def _build_update_group(self):
        group = QGroupBox("⬆️ به‌روزرسانی yt-dlp")
        layout = QHBoxLayout(group)
        self.lbl_ytdlp_version = QLabel("نسخهٔ فعلی: —")
        layout.addWidget(self.lbl_ytdlp_version)
        self.btn_check_update = QPushButton("🔍 بررسی به‌روزرسانی")
        self.btn_check_update.clicked.connect(self._check_ytdlp_update)
        layout.addWidget(self.btn_check_update)
        self.lbl_update_status = QLabel("")
        layout.addWidget(self.lbl_update_status, 1)
        return group

    # ================= گروه نگهداری =================
    def _build_maintenance_group(self):
        group = QGroupBox("🧰 نگهداری و ابزارها")
        layout = QHBoxLayout(group)

        self.btn_open_download = QPushButton("📂 پوشهٔ دانلود")
        self.btn_open_download.clicked.connect(self._open_download_folder)
        layout.addWidget(self.btn_open_download)

        self.btn_open_log = QPushButton("🗂️ پوشهٔ لاگ")
        self.btn_open_log.clicked.connect(self._open_log_folder)
        layout.addWidget(self.btn_open_log)

        self.btn_clear_log2 = QPushButton("🧹 پاک کردن لاگ")
        self.btn_clear_log2.clicked.connect(self._clear_log)
        layout.addWidget(self.btn_clear_log2)

        layout.addStretch()
        return group

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

    # ================= گروه اطلاعات ویدئو (thumbnail) =================
    def _build_video_info_group(self):
        group = QGroupBox("📺 اطلاعات ویدئو")
        layout = QHBoxLayout(group)

        self.thumb_label = QLabel("پس از استخراج، تصویر بندانگشتی اینجا نمایش داده می‌شود")
        self.thumb_label.setFixedSize(240, 135)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setWordWrap(True)
        self.thumb_label.setStyleSheet(
            "background-color: #11111b; border: 1px solid #313244; "
            "border-radius: 6px; color: #6c7086;"
        )
        layout.addWidget(self.thumb_label)

        self.lbl_video_info = QLabel("برای دیدن اطلاعات ویدئو، «استخراج فرمت‌ها» را بزنید.")
        self.lbl_video_info.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        self.lbl_video_info.setWordWrap(True)
        self.lbl_video_info.setStyleSheet("color: #cdd6f4;")
        layout.addWidget(self.lbl_video_info, 1)
        return group

    # ================= گروه دانلود دسته‌ای =================
    def _build_batch_group(self):
        group = QGroupBox("۳) دانلود دسته‌ای (چند لینک)")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("چند لینک را، هر کدام در یک خط، بچسبانید (همه به صف اضافه می‌شوند):"))
        self.batch_input = QPlainTextEdit()
        self.batch_input.setPlaceholderText(
            "https://youtu.be/aaaaaaaaaaa\nhttps://youtu.be/bbbbbbbbbbb"
        )
        self.batch_input.setMaximumHeight(90)
        layout.addWidget(self.batch_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_batch_add = QPushButton("➕ افزودن همه به صف")
        self.btn_batch_add.clicked.connect(self._batch_add_to_queue)
        btn_layout.addWidget(self.btn_batch_add)
        layout.addLayout(btn_layout)
        return group

    # ================= گروه ادامهٔ دانلود (Resume) =================
    def _build_resume_group(self):
        group = QGroupBox("▶️ ادامهٔ دانلود")
        layout = QHBoxLayout(group)
        self.resume_check = QCheckBox(
            "ادامهٔ فایل‌های ناقص (Resume) — در صورت قطع‌شدن، از همان‌جا ادامه بده"
        )
        layout.addWidget(self.resume_check)
        layout.addStretch()
        return group

    # ================= گروه فرمت‌ها =================
    def _build_format_group(self):
        group = QGroupBox("۲) فرمت‌های موجود")
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

        q_layout.addWidget(QLabel("🔍 جستجو:"))
        self.playlist_search = QLineEdit()
        self.playlist_search.setPlaceholderText("جستجو در عنوان یا مدت (مثلاً 10:30)...")
        self.playlist_search.textChanged.connect(self._filter_playlist)
        q_layout.addWidget(self.playlist_search, 1)
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
        group = QGroupBox("۴) تنظیمات دانلود و شروع")
        layout = QGridLayout(group)

        self.audio_only_check = QCheckBox("فقط صدا (استخراج با FFmpeg)")
        self.audio_only_check.toggled.connect(self._toggle_audio_only)
        layout.addWidget(self.audio_only_check, 0, 0)

        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "m4a", "opus", "flac", "wav"])
        self.audio_format_combo.setEnabled(False)
        layout.addWidget(self.audio_format_combo, 0, 1)

        hint = QLabel("💡 مسیر ذخیره، تلاش مجدد و محدودیت سرعت در تب «⚙️ تنظیمات»")
        hint.setStyleSheet("color: #a6adc8;")
        layout.addWidget(hint, 0, 2, 1, 2)

        # زیرنویس
        layout.addWidget(QLabel("زیرنویس:"), 1, 0)
        self.subtitle_check = QCheckBox("دانلود")
        layout.addWidget(self.subtitle_check, 1, 1)
        self.subtitle_langs = QLineEdit()
        self.subtitle_langs.setPlaceholderText("زبان‌ها (fa,en یا all)")
        layout.addWidget(self.subtitle_langs, 1, 2)
        self.subtitle_auto_check = QCheckBox("خودکار")
        layout.addWidget(self.subtitle_auto_check, 1, 3)

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

        layout.addLayout(btn_layout, 2, 0, 1, 4)
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
