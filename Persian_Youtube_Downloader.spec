# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller config for building the portable EXE.

Build:
    pyinstaller Persian_Youtube_Downloader.spec
"""
import shutil

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# Collect the packages that ship data files / native DLLs / hidden submodules
for pkg in ["yt_dlp", "curl_cffi", "yt_dlp_plugins"]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# External tools: ffmpeg, ffprobe and aria2c (placed next to the exe)
# NOTE: keep every print() ASCII-only - the GitHub Actions Windows runner uses a
# cp1252 console and crashes on non-encodable characters.
for tool in ["ffmpeg", "ffprobe", "aria2c"]:
    path = shutil.which(tool)
    if path:
        binaries.append((path, "."))
        print(f"[spec] bundling {tool}: {path}")
    else:
        print(f"[spec] WARNING: {tool} not found - not bundled")

# Application icon (window icon + EXE icon)
datas.append(("assets/icon.png", "assets"))
datas.append(("assets/icon.ico", "assets"))

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
    console=False,  # GUI app - no console window
    disable_windowed_traceback=False,
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Persian_Youtube_Downloader",
)
