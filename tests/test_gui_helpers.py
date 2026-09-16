"""تست‌های unit برای توابع کمکی gui.py (بدون نیاز به اجرای GUI)"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui_utils import YOUTUBE_URL_RE, is_playlist_url


class TestUrlValidation(unittest.TestCase):
    def test_valid_urls(self):
        valid = [
            "https://www.youtube.com/watch?v=abc123",
            "https://youtu.be/abc123",
            "https://music.youtube.com/watch?v=abc",
            "https://www.youtube-nocookie.com/watch?v=abc",
            "https://youtube.com/shorts/abc",
        ]
        for u in valid:
            self.assertTrue(YOUTUBE_URL_RE.match(u), u)

    def test_invalid_urls(self):
        invalid = [
            "https://example.com/watch?v=abc",
            "not a url",
            "https://youtube.com",
        ]
        for u in invalid:
            self.assertFalse(YOUTUBE_URL_RE.match(u), u)


class TestPlaylistDetection(unittest.TestCase):
    def test_playlist_url(self):
        self.assertTrue(is_playlist_url("https://www.youtube.com/playlist?list=PLabc"))

    def test_video_with_list_param(self):
        # ویدئویی که عضوی از پلی‌لیست است
        self.assertTrue(is_playlist_url("https://www.youtube.com/watch?v=x&list=PLabc"))

    def test_single_video(self):
        self.assertFalse(is_playlist_url("https://www.youtube.com/watch?v=abc123"))
        self.assertFalse(is_playlist_url("https://youtu.be/abc123"))


if __name__ == "__main__":
    unittest.main()
