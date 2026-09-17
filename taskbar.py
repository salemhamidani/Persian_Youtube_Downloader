"""پیشرفت در تسک‌بار ویندوز (ITaskbarList3) بدون وابستگی خارجی.

PyQt6 دیگر ماژول QtWinExtras را ندارد (این ماژول در Qt6 حذف شد)، بنابراین برای
نمایش درصد پیشرفت روی آیکون تسک‌بار ویندوز، مستقیماً با ctypes از COM API
ویندوز (ITaskbarList3) استفاده می‌کنیم. این همان چیزی است که QWinTaskbarProgress
در Qt5 زیر پوستش انجام می‌داد.

استفاده:
    tp = TaskbarProgress(hwnd)   # hwnd = عدد دستگیره پنجره (int)
    tp.show()                    # نمایش نوار پیشرفت (وضعیت عادی)
    tp.set_value(42, 100)        # ۴۲٪
    tp.hide()                    # پنهان‌کردن (بدون پیشرفت)
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

__all__ = ["TaskbarProgress"]


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    def __init__(self, a: int, b: int, c: int, d: tuple):
        super().__init__(a, b, c, (ctypes.c_ubyte * 8)(*d))


# CLSID مربوط به ITaskbarList (سرویس تسک‌بار ویندوز)
_CLSID_TaskbarList = _GUID(
    0x56FDF344, 0xFD6D, 0x11D0,
    (0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90),
)
# IID مربوط به رابط ITaskbarList3
_IID_ITaskbarList3 = _GUID(
    0xEA1AFB91, 0x9E28, 0x4B86,
    (0x90, 0xE9, 0x9E, 0x9F, 0x8A, 0x5E, 0xEF, 0xAF),
)

_CLSCTX_INPROC_SERVER = 0x1

# ---- پرچم‌های وضعیت پیشرفت (TBPFLAG) ----
TBPF_NOPROGRESS = 0x00000000      # بدون نوار پیشرفت
TBPF_INDETERMINATE = 0x00000001   # پیشرفت نامشخص (لوپ)
TBPF_NORMAL = 0x00000002          # پیشرفت عادی (سبز)
TBPF_ERROR = 0x00000004           # خطا (قرمز)
TBPF_PAUSED = 0x00000008          # توقف (زرد)

# ---- امضای توابع COM ----
# HRESULT SetProgressValue(HWND hwnd, ULONGLONG ullCompleted, ULONGLONG ullTotal)
_SetProgressValue = ctypes.WINFUNCTYPE(
    ctypes.c_long,          # HRESULT
    ctypes.c_void_p,        # this
    wintypes.HWND,          # hwnd
    ctypes.c_ulonglong,     # ullCompleted
    ctypes.c_ulonglong,     # ullTotal
)
# HRESULT SetProgressState(HWND hwnd, TBPFLAG tbpFlags)
_SetProgressState = ctypes.WINFUNCTYPE(
    ctypes.c_long,          # HRESULT
    ctypes.c_void_p,        # this
    wintypes.HWND,          # hwnd
    ctypes.c_int,           # tbpFlags
)


class TaskbarProgress:
    """نمایش درصد پیشرفت روی آیکون تسک‌بار ویندوز (فقط ویندوز)."""

    def __init__(self, hwnd: int):
        self._hwnd = wintypes.HWND(hwnd)
        self._itaskbar3 = self._create_interface()

    @staticmethod
    def _create_interface():
        """ساخت نمونه ITaskbarList3؛ در صورت شکست None برمی‌گرداند."""
        if sys.platform != "win32":
            return None
        try:
            ole32 = ctypes.windll.ole32
            # COM را در این thread مقداردهی کن (اگر قبلاً شده باشد، نتیجه نادیده گرفته می‌شود)
            ole32.CoInitialize(None)

            ppv = ctypes.c_void_p()
            hr = ole32.CoCreateInstance(
                ctypes.byref(_CLSID_TaskbarList),
                None,
                _CLSCTX_INPROC_SERVER,
                ctypes.byref(_IID_ITaskbarList3),
                ctypes.byref(ppv),
            )
            if hr < 0 or not ppv.value:
                return None
            return ppv
        except Exception:
            return None

    def _call(self, index: int, func_type, *args) -> None:
        """فراخوانی متد COM از طریق جدول مجازی (vtable) با ایندکس مشخص."""
        if self._itaskbar3 is None:
            return
        try:
            vtable = ctypes.cast(
                self._itaskbar3, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
            )[0]
            func = func_type(vtable[index])
            func(self._itaskbar3, *args)
        except Exception:
            pass

    def set_state(self, flags: int) -> None:
        """تنظیم وضعیت نوار پیشرفت (NORMAL / ERROR / PAUSED / NOPROGRESS / ...)."""
        # ایندکس 10 در vtable = ITaskbarList3::SetProgressState
        self._call(10, _SetProgressState, self._hwnd, int(flags))

    def set_value(self, completed: int, total: int = 100) -> None:
        """تنظیم مقدار پیشرفت (completed از total)."""
        # ایندکس 9 در vtable = ITaskbarList3::SetProgressValue
        self._call(9, _SetProgressValue, self._hwnd, completed, total)

    def show(self) -> None:
        """نمایش نوار پیشرفت با وضعیت عادی (سبز)."""
        self.set_state(TBPF_NORMAL)

    def hide(self) -> None:
        """پنهان‌کردن نوار پیشرفت."""
        self.set_state(TBPF_NOPROGRESS)
