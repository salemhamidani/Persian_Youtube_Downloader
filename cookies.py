import os
import platform
from pathlib import Path


class CookieManager:
    """شناسایی و مدیریت کوکی‌های مرورگرها"""

    SUPPORTED_BROWSERS = {
        "Chrome": "chrome",
        "Firefox": "firefox",
        "Edge": "edge",
        "Opera": "opera",
        "Brave": "brave",
        "Chromium": "chromium",
        "Vivaldi": "vivaldi",
        "Safari": "safari",
    }

    @staticmethod
    def detect_installed_browsers() -> list:
        """تشخیص مرورگرهای نصب‌شده روی سیستم"""
        system = platform.system()
        home = Path.home()
        installed = []

        browser_paths = {}

        if system == "Windows":
            local = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
            appdata = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
            browser_paths = {
                "Chrome": [
                    local / "Google/Chrome/User Data",
                    Path("C:/Program Files/Google/Chrome/Application"),
                    Path("C:/Program Files (x86)/Google/Chrome/Application"),
                ],
                "Firefox": [
                    appdata / "Mozilla/Firefox",
                    Path("C:/Program Files/Mozilla Firefox"),
                ],
                "Edge": [
                    local / "Microsoft/Edge/User Data",
                    Path("C:/Program Files (x86)/Microsoft/Edge/Application"),
                ],
                "Opera": [
                    appdata / "Opera Software/Opera Stable",
                    local / "Programs/Opera",
                ],
                "Brave": [
                    local / "BraveSoftware/Brave-Browser/User Data",
                ],
            }
        elif system == "Darwin":
            browser_paths = {
                "Chrome": [home / "Library/Application Support/Google/Chrome"],
                "Firefox": [home / "Library/Application Support/Firefox"],
                "Edge": [home / "Library/Application Support/Microsoft Edge"],
                "Opera": [home / "Library/Application Support/com.operasoftware.Opera"],
                "Safari": [home / "Library/Safari"],
                "Brave": [home / "Library/Application Support/BraveSoftware/Brave-Browser"],
            }
        else:
            browser_paths = {
                "Chrome": [home / ".config/google-chrome"],
                "Firefox": [home / ".mozilla/firefox"],
                "Edge": [home / ".config/microsoft-edge"],
                "Opera": [home / ".config/opera"],
                "Brave": [home / ".config/BraveSoftware/Brave-Browser"],
                "Chromium": [home / ".config/chromium"],
            }

        for browser, paths in browser_paths.items():
            for p in paths:
                if p.exists():
                    installed.append(browser)
                    break

        return installed

    @staticmethod
    def validate_cookie_file(path: str) -> bool:
        """اعتبارسنجی فایل cookies.txt"""
        if not path or not os.path.isfile(path):
            return False
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                first_lines = f.read(2048)
            if "# Netscape HTTP Cookie File" in first_lines or "# HTTP Cookie File" in first_lines:
                return True
            if "\t" in first_lines:
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def normalize_cookie_file(path: str) -> str:
        """
        نرمال‌سازی فایل کوکی:
        - حذف BOM
        - تبدیل CRLF به LF
        - اطمینان از وجود هدر Netscape
        """
        if not path or not os.path.isfile(path):
            return path

        try:
            with open(path, "rb") as f:
                data = f.read()

            original = data

            # حذف BOM UTF-8
            if data.startswith(b"\xef\xbb\xbf"):
                data = data[3:]

            # تبدیل CRLF به LF
            data = data.replace(b"\r\n", b"\n")

            # اطمینان از هدر صحیح
            if not data.startswith(b"# Netscape HTTP Cookie File") and \
               not data.startswith(b"# HTTP Cookie File"):
                # اگر هدر نیست، اضافه کن
                data = b"# Netscape HTTP Cookie File\n" + data

            if data != original:
                with open(path, "wb") as f:
                    f.write(data)
                print(f"[info] فایل کوکی نرمال‌سازی شد: {path}")

        except Exception as e:
            print(f"[warn] خطا در نرمال‌سازی کوکی: {e}")

        return path