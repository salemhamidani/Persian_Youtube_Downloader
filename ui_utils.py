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
