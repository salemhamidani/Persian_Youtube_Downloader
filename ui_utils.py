"""توابع و ثابت‌های کمکی رابط کاربری (مستقل از MainWindow)"""
import re

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableWidgetItem,
)


# نقش سفارشی برای علامت‌گذاری ویدئوهای دانلودشده در پلی‌لیست
DONE_ROLE = Qt.ItemDataRole.UserRole + 100


class GreenCheckDelegate(QStyledItemDelegate):
    """delegate برای نمایش تیک سبز ویدئوهای دانلودشده در جدول پلی‌لیست"""

    def paint(self, painter, option, index):
        if index.data(DONE_ROLE) == "done":
            opt = QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            style = option.widget.style() if option.widget else QApplication.style()
            style.drawPrimitive(
                QStyle.PrimitiveElement.PE_PanelItemViewItem, opt, painter, option.widget
            )
            # رسم دستی تیک سبز
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor("#4caf50"))
            pen.setWidthF(2.6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            cx = option.rect.center().x()
            cy = option.rect.center().y()
            painter.drawLine(QPointF(cx - 5.0, cy), QPointF(cx - 1.5, cy + 3.5))
            painter.drawLine(QPointF(cx - 1.5, cy + 3.5), QPointF(cx + 6.0, cy - 4.5))
            painter.restore()
            return
        super().paint(painter, option, index)


YOUTUBE_URL_RE = re.compile(
    r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/.+$",
    re.IGNORECASE,
)


def is_playlist_url(url: str) -> bool:
    """تشخیص لینک پلی‌لیست از لینک تک‌ویدئو"""
    u = (url or "").strip().lower()
    # هر لینکی که پارامتر list= داشته باشد (حتی watch?v=...&list=...) پلی‌لیست است
    return "/playlist" in u or "list=" in u


# گزینه‌های کیفیت دانلود: (برچسب، selector یت-dlp، حداکثر ارتفاع یا 'audio'، (کدک صدا, کیفیت) یا None)
# 🎬 = ویدئو، 🎵 = فقط صدا
QUALITY_OPTIONS = [
    # ---- ویدئو ----
    ("🎬 بهترین کیفیت (خودکار)", "bestvideo+bestaudio/best", None, None),
    ("🎬 2160p — 4K", "bestvideo[height<=2160]+bestaudio/best[height<=2160]", 2160, None),
    ("🎬 1440p — 2K", "bestvideo[height<=1440]+bestaudio/best[height<=1440]", 1440, None),
    ("🎬 1080p — Full HD", "bestvideo[height<=1080]+bestaudio/best[height<=1080]", 1080, None),
    ("🎬 720p — HD", "bestvideo[height<=720]+bestaudio/best[height<=720]", 720, None),
    ("🎬 480p", "bestvideo[height<=480]+bestaudio/best[height<=480]", 480, None),
    ("🎬 360p", "bestvideo[height<=360]+bestaudio/best[height<=360]", 360, None),
    # ---- فقط صدا (فرمت‌های مختلف) ----
    ("🎵 فقط صدا — بهترین (بدون تبدیل)", "bestaudio/best", "audio", None),
    ("🎵 فقط صدا — MP3 128 kbps", "bestaudio/best", "audio", ("mp3", "128")),
    ("🎵 فقط صدا — MP3 192 kbps", "bestaudio/best", "audio", ("mp3", "192")),
    ("🎵 فقط صدا — MP3 320 kbps", "bestaudio/best", "audio", ("mp3", "320")),
    ("🎵 فقط صدا — M4A (AAC)", "bestaudio/best", "audio", ("m4a", "192")),
    ("🎵 فقط صدا — Opus", "bestaudio/best", "audio", ("opus", None)),
    ("🎵 فقط صدا — FLAC (بی‌اتلاف)", "bestaudio/best", "audio", ("flac", None)),
    ("🎵 فقط صدا — WAV", "bestaudio/best", "audio", ("wav", None)),
]


def quality_data(item_data):
    """دادهٔ گزینهٔ کیفیت را به (selector, ارتفاع, کدک صدا) تبدیل می‌کند.

    با هر دو قالب (رشتهٔ ساده یا tuple چهارتایی) سازگار است.
    """
    if isinstance(item_data, (tuple, list)):
        sel = item_data[0] if len(item_data) > 0 else None
        height = item_data[1] if len(item_data) > 1 else None
        audio = item_data[2] if len(item_data) > 2 else None
        return sel, height, audio
    return item_data, None, None


# نگاشت selector به ارتفاع برای برآورد حجم
QUALITY_HEIGHT = {s: h for (_label, s, h, _a) in QUALITY_OPTIONS}


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
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected { background-color: #313244; }
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
}
QMenu::item { padding: 6px 24px; }
QMenu::item:selected { background-color: #313244; }
QMenu::separator { height: 1px; background: #313244; margin: 4px 8px; }
"""
