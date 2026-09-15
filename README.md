<div align="center">

# 🎬 دانلودر یوتیوب فارسی
### Persian YouTube Downloader

**یک دانلودر گرافیکی سریع، زیبا و حرفه‌ای برای یوتیوب** — ساخته‌شده با `Python` ،`PyQt6` و `yt-dlp`

*A fast, beautiful & professional GUI YouTube downloader — built with `Python`, `PyQt6` & `yt-dlp`*

<br>

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.11-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://www.qt.io/)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-2026.8-red?style=for-the-badge)](https://github.com/yt-dlp/yt-dlp)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)](https://github.com/salemhamidani/Persian_Youtube_Downloader)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)](https://github.com/salemhamidani/Persian_Youtube_Downloader)

<br>

| 🇮🇷 فارسی | 🇬🇧 English |
|:---:|:---:|
| دانلود ویدئو و صوت از یوتیوب با رابط کاربری گرافیکی | Download YouTube video & audio with a GUI |

</div>

---

## ✨ معرفی | Overview

**فارسی:** این پروژه یک دانلودر دسکتاپ یوتیوب با رابط گرافیکی (GUI) است که بر پایه موتور قدرتمند `yt-dlp` ساخته شده. شما لینک ویدئو را وارد می‌کنید، برنامه تمام فرمت‌های موجود (کیفیت، کدک، زبان، بیت‌ریت و حجم) را در یک جدول حرفه‌ای نمایش می‌دهد و می‌توانید دقیقاً همان کیفیت یا ترکیب دلخواه (مثل `137+140`) را دانلود کنید.

**English:** This is a desktop YouTube downloader with a graphical interface (GUI) built on the powerful `yt-dlp` engine. Paste a video link, browse every available format (quality, codec, language, bitrate & size) in a professional table, and download exactly the quality or combination you want (e.g. `137+140`).

> 💡 **چرا این پروژه؟** چون اکثر دانلودرهای موجود یا CLI هستند یا رابط کاربری ضعیفی دارند. این پروژه تجربه‌ای **کاملاً فارسی، راست‌به‌چپ و بصری** ارائه می‌دهد.

---

## 🚀 ویژگی‌ها | Features

| ✨ ویژگی | Feature | توضیح |
|---------|---------|-------|
| 📋 **تشخیص خودکار لینک** | Auto clipboard detection | لینک یوتیوب را کپی کنید؛ برنامه خودش آن را بارگذاری می‌کند |
| 🎚️ **استخراج همه فرمت‌ها** | Full format extraction | کیفیت، FPS، زبان، کدک ویدئو/صدا، بیت‌ریت و حجم |
| 🔍 **فیلتر هوشمند** | Smart filtering | فقط ویدئو / فقط صدا / ویدئو+صدا / بالاترین کیفیت هر رزولوشن |
| 🎵 **دانلود فقط صدا** | Audio-only mode | استخراج با FFmpeg در قالب `mp3` ،`m4a` ،`opus` ،`flac` ،`wav` |
| 🍪 **پشتیبانی کوکی** | Cookie support | کوکی مرورگر (Chrome/Firefox/Edge/…) یا فایل `cookies.txt` |
| ⚡ **سرعت بالا** | High-speed download | دانلود همزمان ۸ قطعه + چانک ۱۰MB + دانلودر خارجی `aria2c` |
| 📊 **پیشرفت زنده** | Live progress | سرعت، زمان باقی‌مانده، حجم و لاگ لحظه‌ای |
| 🖱️ **رابط راست‌به‌چپ** | RTL interface | کاملاً فارسی با چیدمان راست‌به‌چپ |

---

## 📸 اسکرین‌شات | Screenshot

> 📌 *به‌زودی اضافه می‌شود — کافیست یک اسکرین‌شات در مسیر `docs/` بگذارید و اینجا لینک کنید.*

```text
┌─────────────────────────────────────────────────────────┐
│  ۱) لینک ویدئو      [____________________________] 🔍   │
│  ۲) کوکی‌ها         ◉ مرورگر  ○ فایل cookies.txt        │
│  ۳) فرمت‌های موجود   [جدول ۱۰ ستونه کیفیت/کدک/حجم/زبان]  │
│  ۴) ذخیره و دانلود   [مسیر] [تلاش مجدد] [⬇️ دانلود]      │
│  ۵) وضعیت و پیشرفت   [████████░░░░] سرعت / ETA / حجم     │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 پیش‌نیازها | Requirements

| ابزار | Tool | ضروری؟ | نقش |
|-------|------|:------:|-----|
| **Python** | 3.14+ | ✅ بله | اجرای برنامه |
| **yt-dlp** | 2026.8+ | ✅ بله | موتور دانلود |
| **PyQt6** | 6.11+ | ✅ بله | رابط گرافیکی |
| **FFmpeg** | — | ✅ بله | استخراج صدا و ادغام ویدئو/صدا |
| **aria2c** | — | ⭕ اختیاری | دانلود موازی سریع‌تر |

> ⚠️ **FFmpeg ضروری است.** برای دانلود صدا (mp3) و ادغام ویدئو+صدا به FFmpeg نیاز دارید. راهنمای نصب:
> ```bash
> # ویندوز (با winget)
> winget install Gyan.FFmpeg
>
> # لینوکس
> sudo apt install ffmpeg
>
> # مک
> brew install ffmpeg
> ```

---

## 🛠️ نصب | Installation

### فارسی

```bash
# ۱) کلون کردن مخزن
git clone https://github.com/salemhamidani/Persian_Youtube_Downloader.git
cd Persian_Youtube_Downloader

# ۲) ساخت محیط مجازی (پیشنهادی)
python -m venv venv

# ۳) فعال‌سازی محیط مجازی
# ویندوز:
venv\Scripts\activate
# لینوکس/مک:
source venv/bin/activate

# ۴) نصب وابستگی‌ها
pip install -r requirements.txt

# ۵) اجرای برنامه
python main.py
```

### English

```bash
git clone https://github.com/salemhamidani/Persian_Youtube_Downloader.git
cd Persian_Youtube_Downloader
python -m venv venv
# Windows: venv\Scripts\activate   |   Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 🎯 نحوه استفاده | Usage

1. **لینک را کپی کنید** — برنامه به‌طور خودکار لینک را از کلیپ‌بورد تشخیص می‌دهد (یا دستی وارد کنید).
2. **روی «استخراج فرمت‌ها» بزنید** — جدول کامل فرمت‌ها نمایش داده می‌شود.
3. **فرمت دلخواه را انتخاب کنید** — یا از جدول، یا ID مستقیم (مثل `137+140`).
4. **مسیر ذخیره و تعداد تلاش مجدد را تنظیم کنید.**
5. **روی «شروع دانلود» بزنید** — پیشرفت زنده را تماشا کنید! 🎉

> 💡 **نکته:** برای دانلود فقط صدا، تیک «فقط صدا (استخراج با FFmpeg)» را بزنید و قالب دلخواه (mp3 و…) را انتخاب کنید.

---

## 📁 ساختار پروژه | Project Structure

```
Persian_Youtube_Downloader/
├── main.py           → نقطه ورود برنامه (entry point)
├── gui.py            → رابط کاربری گرافیکی (PyQt6) + مدیریت thread ها
├── downloader.py     → منطق دانلود و استخراج فرمت‌ها (yt-dlp)
├── cookies.py        → شناسایی مرورگرها و مدیریت فایل کوکی
├── settings.py       → ذخیره/بازیابی تنظیمات کاربر (JSON)
├── requirements.txt  → وابستگی‌های پروژه
├── .gitignore        → فایل‌های نادیده‌گرفته‌شده (شامل کوکی‌ها)
└── مستند-پروژه.md     → مستند کامل تحلیل و نقاط ضعف/بهبود
```

| فایل | File | مسئولیت |
|------|------|---------|
| `main.py` | entry point | اجرای برنامه |
| `gui.py` | UI (711 خط) | پنجره اصلی، جدول فرمت‌ها، پیشرفت زنده |
| `downloader.py` | download engine | ساخت پارامترهای yt-dlp، دانلود، پارس فرمت‌ها |
| `cookies.py` | cookie manager | تشخیص مرورگر، اعتبارسنجی کوکی |
| `settings.py` | settings | ذخیره تنظیمات در `~/.youtube_downloader/config.json` |

---

## 🔒 نکات امنیتی | Security Notes

> 🚨 **مهم:** فایل `cookies.txt` حاوی **توکن‌های ورود حساب گوگل/یوتیوب شما** است. این فایل **هرگز نباید** commit یا به اشتراک گذاشته شود — به همین دلیل در `.gitignore` قرار گرفته است.

| ✅ امن | ❌ ناامن |
|-------|---------|
| استفاده از کوکی مرورگر (`cookiesfrombrowser`) | قرار دادن `cookies.txt` در مخزن |
| `.gitignore` شامل کوکی و فایل‌های حساس | به‌اشتراک‌گذاری کوکی با دیگران |
| اعتبارسنجی SSL فعال (`nocheckcertificate: False`) | غیرفعال‌کردن بررسی گواهی SSL |

---

## 🧪 عیب‌یابی | Troubleshooting

| مشکل | Problem | راه‌حل |
|------|---------|--------|
| «ffmpeg not found» | ffmpeg missing | FFmpeg را نصب کنید (بخش پیش‌نیازها) |
| دانلود کند | slow download | `aria2c` را نصب کنید تا دانلود موازی فعال شود |
| خطای کوکی | cookie error | مرورگر را ببندید یا از فایل `cookies.txt` تازه استفاده کنید |
| فرمت نمایش داده نمی‌شود | formats not shown | از کوکی معتبر استفاده کنید (YouTube محدودیت اعمال می‌کند) |

---

## 🤝 مشارکت | Contributing

از مشارکت شما استقبال می‌کنیم! 🎉

1. مخزن را **Fork** کنید.
2. یک شاخه جدید بسازید: `git checkout -b feature/amazing-feature`
3. تغییرات را commit کنید: `git commit -m "Add amazing feature"`
4. به شاخه خود push کنید: `git push origin feature/amazing-feature`
5. یک **Pull Request** باز کنید.

---

## ⭐ حمایت | Support

اگر این پروژه برایتان مفید بود، با یک **ستاره ⭐** از آن حمایت کنید!

<br>

<div align="center">

**ساخته‌شده با ❤️ برای جامعه فارسی‌زبان**

*Made with ❤️ for the Persian-speaking community*

</div>
