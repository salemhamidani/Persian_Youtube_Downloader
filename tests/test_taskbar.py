"""تست‌های unit برای taskbar.py (پیشرفت تسک‌بار ویندوز)"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from taskbar import TBPF_NOPROGRESS, TBPF_NORMAL, TaskbarProgress


class TestTaskbarProgress(unittest.TestCase):
    def test_construct_without_crash(self):
        # با hwnd نامعتبر هم نباید خطا بدهد؛ روی ویندوز interface ساخته می‌شود
        tp = TaskbarProgress(0)
        self.assertIsInstance(tp, TaskbarProgress)

    def test_methods_without_crash(self):
        tp = TaskbarProgress(0)
        tp.show()
        tp.set_value(42, 100)
        tp.hide()
        tp.set_state(TBPF_NORMAL)
        tp.set_state(TBPF_NOPROGRESS)

    def test_value_out_of_range_does_not_crash(self):
        # مقادیر خارج از بازه نباید باعث خطا شوند (clamp در gui انجام می‌شود)
        tp = TaskbarProgress(0)
        tp.set_value(150, 100)
        tp.set_value(-10, 100)


if __name__ == "__main__":
    unittest.main()
