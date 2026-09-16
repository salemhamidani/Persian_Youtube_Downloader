"""تست‌های unit برای downloader.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from downloader import YouTubeDownloader


def _fake_format(**overrides):
    f = {
        "format_id": "18",
        "ext": "mp4",
        "vcodec": "avc1.42001E",
        "acodec": "mp4a.40.2",
        "height": 360,
        "width": 640,
        "tbr": 500.0,
        "abr": None,
        "filesize": None,
        "filesize_approx": 1_000_000,
        "resolution": "640x360",
        "format_note": "360p",
        "fps": 30,
        "language": "en",
    }
    f.update(overrides)
    return f


class TestParseFormats(unittest.TestCase):
    def _info(self, formats, duration=100):
        return {"duration": duration, "formats": formats, "title": "test"}

    def test_parses_basic_fields(self):
        result = YouTubeDownloader.parse_formats(self._info([_fake_format()]))
        self.assertEqual(len(result), 1)
        f = result[0]
        self.assertEqual(f["id"], "18")
        self.assertEqual(f["kind"], "video+audio")
        self.assertEqual(f["resolution"], "640x360")

    def test_kind_video_only(self):
        result = YouTubeDownloader.parse_formats(
            self._info([_fake_format(format_id="137", acodec="none")])
        )
        self.assertEqual(result[0]["kind"], "video")

    def test_kind_audio_only(self):
        result = YouTubeDownloader.parse_formats(
            self._info([_fake_format(format_id="140", vcodec="none")])
        )
        self.assertEqual(result[0]["kind"], "audio")

    def test_size_estimated_from_tbr(self):
        # filesize/filesize_approx ناموجود → از tbr تخمین بزند
        result = YouTubeDownloader.parse_formats(
            self._info([_fake_format(filesize=None, filesize_approx=None, tbr=800.0)])
        )
        # 800 kbps * 1000 * 100s / 8 = 10,000,000 bytes
        self.assertAlmostEqual(result[0]["size_bytes"], 10_000_000, delta=1000)

    def test_language_display(self):
        result = YouTubeDownloader.parse_formats(
            self._info([_fake_format(language="fa")])
        )
        self.assertEqual(result[0]["language"], "فارسی")


class TestEstimateSize(unittest.TestCase):
    def _info(self, formats, duration=1000):
        return {"duration": duration, "formats": formats}

    def test_best_quality(self):
        info = self._info([
            _fake_format(format_id="137", acodec="none", height=1080, filesize_approx=300_000_000),
            _fake_format(format_id="140", vcodec="none", filesize_approx=16_000_000),
        ])
        size = YouTubeDownloader.estimate_size_for_height(info, None)
        self.assertEqual(size, 316_000_000)

    def test_height_limit(self):
        info = self._info([
            _fake_format(format_id="137", acodec="none", height=1080, filesize_approx=300_000_000),
            _fake_format(format_id="136", acodec="none", height=720, filesize_approx=100_000_000),
            _fake_format(format_id="140", vcodec="none", filesize_approx=16_000_000),
        ])
        # برای 720p باید 136 (720p) انتخاب شود نه 137 (1080p)
        size = YouTubeDownloader.estimate_size_for_height(info, 720)
        self.assertEqual(size, 116_000_000)

    def test_audio_only(self):
        info = self._info([
            _fake_format(format_id="140", vcodec="none", filesize_approx=16_000_000),
        ])
        self.assertEqual(YouTubeDownloader.estimate_size_for_height(info, "audio"), 16_000_000)

    def test_no_formats(self):
        self.assertEqual(YouTubeDownloader.estimate_size_for_height({"formats": []}, None), 0)


class TestHumanSize(unittest.TestCase):
    def test_units(self):
        self.assertEqual(YouTubeDownloader._human_size(500), "500.0 B")
        self.assertEqual(YouTubeDownloader._human_size(2048), "2.0 KB")
        self.assertEqual(YouTubeDownloader._human_size(5 * 1024 * 1024), "5.0 MB")

    def test_invalid_input(self):
        self.assertEqual(YouTubeDownloader._human_size("not-a-number"), "?")


if __name__ == "__main__":
    unittest.main()
