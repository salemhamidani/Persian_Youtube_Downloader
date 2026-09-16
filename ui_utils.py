"""توابع و ثابت‌های کمکی رابط کاربری (مستقل از MainWindow)"""
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem


YOUTUBE_URL_RE = re.compile(
    r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/.+$",
    re.IGNORECASE,
)


def is_playlist_url(url: str) -> bool:
    """تشخیص لینک پلی‌لیست از لینک تک‌ویدئو"""
    u = (url or "").strip().lower()
    # هر لینکی که پارامتر list= داشته باشد (حتی watch?v=...&list=...) پلی‌لیست است
    return "/playlist" in u or "list=" in u


# گزینه‌های کیفیت برای دانلود پلی‌لیست: (برچسب، selector یت-dlp، حداکثر ارتفاع یا 'audio')
QUALITY_OPTIONS = [
    ("بهترین کیفیت (خودکار)", "bestvideo+bestaudio/best", None),
    ("2160p — 4K", "bestvideo[height<=2160]+bestaudio/best[height<=2160]", 2160),
    ("1440p — 2K", "bestvideo[height<=1440]+bestaudio/best[height<=1440]", 1440),
    ("1080p — Full HD", "bestvideo[height<=1080]+bestaudio/best[height<=1080]", 1080),
    ("720p — HD", "bestvideo[height<=720]+bestaudio/best[height<=720]", 720),
    ("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]", 480),
    ("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]", 360),
    ("فقط صدا (بهترین)", "bestaudio/best", "audio"),
]

# نگاشت selector به ارتفاع برای برآورد حجم
QUALITY_HEIGHT = {s: h for (_, s, h) in QUALITY_OPTIONS}


class NumericTableWidgetItem(QTableWidgetItem):
    """آیتم جدول با مرتب‌سازی عددی (برای ستون‌هایی مثل سایز/حجم)"""

    def __lt__(self, other):
        a = self.data(Qt.ItemDataRole.UserRole)
        b = other.data(Qt.ItemDataRole.UserRole)
        if a is not None and b is not None:
            try:
                return float(a) < float(b)
            except (TypeError, ValueError):
                pass
        return super().__lt__(other)


# استایل تم تیره (Catppuccin-inspired)
DARK_QSS = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 6px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: #89b4fa;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover { background-color: #45475a; }
QPushButton:pressed { background-color: #585b70; }
QPushButton:disabled { background-color: #2a2a3a; color: #6c7086; }
QLineEdit, QComboBox, QSpinBox {
    background-color: #11111b;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 5px;
    selection-background-color: #89b4fa;
}
QLineEdit:read-only { color: #a6adc8; }
QTableWidget {
    background-color: #11111b;
    alternate-background-color: #181825;
    gridline-color: #313244;
    border: 1px solid #313244;
}
QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    padding: 6px;
    border: none;
    border-right: 1px solid #45475a;
    font-weight: bold;
}
QProgressBar {
    border: 1px solid #45475a;
    border-radius: 6px;
    text-align: center;
    color: #cdd6f4;
    background-color: #11111b;
}
QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 5px;
}
QTextEdit {
    background-color: #11111b;
    color: #a6adc8;
    border: 1px solid #313244;
    border-radius: 6px;
}
QTabWidget::pane {
    border: 1px solid #313244;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    padding: 8px 18px;
    border: 1px solid #313244;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #313244;
    color: #cdd6f4;
    font-weight: bold;
}
QTabBar::tab:hover:!selected { background-color: #252537; }
QScrollArea { border: none; }
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
}
QCheckBox, QRadioButton, QLabel { color: #cdd6f4; }
QScrollBar:vertical {
    background: #181825;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 6px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #181825;
    height: 12px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 6px;
    min-width: 24px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""
