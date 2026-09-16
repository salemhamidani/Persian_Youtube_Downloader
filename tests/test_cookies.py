"""تست‌های unit برای cookies.py"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cookies import CookieManager


class TestCookieManager(unittest.TestCase):
    def test_validate_valid_netscape(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t0\tPREF\txyz\n")
            path = f.name
        try:
            self.assertTrue(CookieManager.validate_cookie_file(path))
        finally:
            Path(path).unlink()

    def test_validate_invalid(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("not a cookie file\n")
            path = f.name
        try:
            self.assertFalse(CookieManager.validate_cookie_file(path))
        finally:
            Path(path).unlink()

    def test_validate_nonexistent(self):
        self.assertFalse(CookieManager.validate_cookie_file("/nonexistent/path.txt"))

    def test_validate_empty_string(self):
        self.assertFalse(CookieManager.validate_cookie_file(""))


if __name__ == "__main__":
    unittest.main()
