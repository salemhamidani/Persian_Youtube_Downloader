# -*- mode: python ; coding: utf-8 -*-
"""فایل پیکربندی PyInstaller برای ساخت exe قابل حمل

نحوه ساخت:
    pyinstaller Persian_Youtube_Downloader.spec
"""
import shutil

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# جمع‌آوری کامل پکیج‌ها (شامل داده‌ها، DLL ها و submodule های پنهان)
for pkg in ["yt_dlp", "curl_cffi", "yt_dlp_plugins"]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# ابزارهای خارجی: ffmpeg، ffprobe و aria2c (در کنار exe قرار می‌گیرند)
for tool in ["ffmpeg", "ffprobe", "aria2c"]:
    path = shutil.which(tool)
    if path:
        binaries.append((path, "."))
        print(f"[spec] باندل کردن {tool}: {path}")
    else:
        print(f"[spec] ⚠️ {tool} یافت نشد — باندل نمی‌شود")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "unittest", "pydoc", "doctest",
        "test", "tests", "setuptools", "pip",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Persian_Youtube_Downloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # برنامه GUI — بدون پنجره کنسول
    disable_windowed_traceback=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Persian_Youtube_Downloader",
)
