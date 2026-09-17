"""تست‌های unit برای توابع کمکی gui.py (بدون نیاز به اجرای GUI)"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui_utils import QUALITY_OPTIONS, YOUTUBE_URL_RE, is_playlist_url, quality_data


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


class TestQualityData(unittest.TestCase):
    def test_legacy_string(self):
        self.assertEqual(quality_data("bestvideo+bestaudio/best"), ("bestvideo+bestaudio/best", None, None))

    def test_video_tuple(self):
        sel, h, a = quality_data(("bestvideo[height<=1080]+bestaudio/best[height<=1080]", 1080, None))
        self.assertEqual(sel, "bestvideo[height<=1080]+bestaudio/best[height<=1080]")
        self.assertEqual(h, 1080)
        self.assertIsNone(a)

    def test_audio_tuple(self):
        sel, h, a = quality_data(("bestaudio/best", "audio", ("mp3", "320")))
        self.assertEqual(sel, "bestaudio/best")
        self.assertEqual(h, "audio")
        self.assertEqual(a, ("mp3", "320"))

    def test_none(self):
        self.assertEqual(quality_data(None), (None, None, None))


class TestQualityOptions(unittest.TestCase):
    def test_all_entries_are_4_tuples(self):
        for opt in QUALITY_OPTIONS:
            self.assertEqual(len(opt), 4, opt)

    def test_has_audio_formats(self):
        audio_codecs = [opt[3][0] for opt in QUALITY_OPTIONS if opt[3]]
        for expected in ("mp3", "m4a", "opus", "flac", "wav"):
            self.assertIn(expected, audio_codecs, expected)

    def test_has_video_options(self):
        heights = [opt[2] for opt in QUALITY_OPTIONS if opt[2] not in ("audio", None)]
        self.assertIn(1080, heights)
        self.assertIn(720, heights)


if __name__ == "__main__":
    unittest.main()
