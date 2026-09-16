"""تست‌های unit برای settings.py"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from settings import SettingsManager


def _make_settings(tmpdir):
    sm = SettingsManager.__new__(SettingsManager)
    sm.config_dir = Path(tmpdir)
    sm.config_file = Path(tmpdir) / "config.json"
    sm.defaults = {"download_path": str(tmpdir), "history": []}
    sm.data = sm.load()
    return sm


class TestSettingsManager(unittest.TestCase):
    def test_defaults_when_empty(self):
        with tempfile.TemporaryDirectory() as d:
            sm = _make_settings(d)
            self.assertEqual(sm.get("history"), [])

    def test_set_and_persist(self):
        with tempfile.TemporaryDirectory() as d:
            sm = _make_settings(d)
            sm.set("download_path", "/tmp/foo")
            # بازخوانی از فایل
            sm2 = _make_settings(d)
            self.assertEqual(sm2.get("download_path"), "/tmp/foo")

    def test_get_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as d:
            sm = _make_settings(d)
            self.assertEqual(sm.get("retries", 5), 5)

    def test_history_newest_first(self):
        with tempfile.TemporaryDirectory() as d:
            sm = _make_settings(d)
            sm.add_history({"title": "a"})
            sm.add_history({"title": "b"})
            h = sm.get_history()
            self.assertEqual(len(h), 2)
            self.assertEqual(h[0]["title"], "b")

    def test_history_capped_at_500(self):
        with tempfile.TemporaryDirectory() as d:
            sm = _make_settings(d)
            for i in range(505):
                sm.add_history({"title": str(i)})
            self.assertEqual(len(sm.get_history()), 500)


if __name__ == "__main__":
    unittest.main()
