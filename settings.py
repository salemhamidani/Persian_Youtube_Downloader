import json
import os
import platform
from pathlib import Path


class SettingsManager:
    """مدیریت ذخیره و بازیابی تنظیمات برنامه"""

    def __init__(self):
        self.config_dir = Path.home() / ".youtube_downloader"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.defaults = {
            "download_path": self.get_default_download_path(),
            "browser": "Chrome",
            "retries": 5,
            "use_custom_cookie": False,
            "custom_cookie_path": "",
            "proxy_enabled": False,
            "proxy_host": "",
            "proxy_port": 8080,
            "proxy_proto": "http",
        }
        self.data = self.load()

    @staticmethod
    def get_default_download_path() -> str:
        system = platform.system()
        home = Path.home()

        if system == "Windows":
            path = home / "Downloads"
        elif system == "Darwin":
            path = home / "Downloads"
        else:
            path = home / "Downloads"

        if not path.exists():
            path = home
        return str(path)

    def load(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {**self.defaults, **data}
            except Exception:
                return dict(self.defaults)
        return dict(self.defaults)

    def save(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطا در ذخیره تنظیمات: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default if default is not None else self.defaults.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()