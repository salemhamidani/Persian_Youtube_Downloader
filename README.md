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
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

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
| 🎵 **دانلود پلی‌لیست** | Playlist download | استخراج لیست ویدئوها، انتخاب تکی/گروهی و دانلود انتخابی |
| 🎚️ **انتخاب کیفیت پلی‌لیست** | Playlist quality | انتخاب کیفیت (4K/1440p/1080p/720p/…) برای همه ویدئوها |
| 📏 **حجم هر ویدئو** | Per-video size | نمایش حجم تقریبی/واقعی هر ویدئو برای کیفیت انتخابی |
| 💬 **دانلود زیرنویس** | Subtitle download | زیرنویس دستی + خودکار با انتخاب زبان (نیازمند PO Token) |
| 📜 **تاریخچه دانلود** | Download history | ثبت خودکار دانلودهای انجام‌شده + پاک‌کردن |
| 🌐 **پشتیبانی پراکسی** | Proxy support | پروکسی `http` / `socks5` / `socks4` / `https` |
| 🖱️ **رابط راست‌به‌چپ** | RTL interface | کاملاً فارسی با چیدمان راست‌به‌چپ |

---

## 📸 اسکرین‌شات | Screenshot

<div align="center">
  <img src="docs/screenshot.png" alt="رابط کاربری دانلودر یوتیوب فارسی" width="80%" />
  <p><em>رابط کاربری دانلودر یوتیوب فارسی — Persian YouTube Downloader GUI</em></p>
</div>

---

## 📦 پیش‌نیازها | Requirements

| ابزار | Tool | ضروری؟ | نقش |
|-------|------|:------:|-----|
| **Python** | 3.14+ | ✅ بله | اجرای برنامه |
| **yt-dlp** | 2026.8+ | ✅ بله | موتور دانلود |
| **PyQt6** | 6.11+ | ✅ بله | رابط گرافیکی |
| **FFmpeg** | — | ✅ بله | استخراج صدا و ادغام ویدئو/صدا |
| **Node.js** | 22+ | ✅ برای زیرنویس | تولید PO Token (دانلود زیرنویس) |
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

## 🔑 راه‌اندازی PO Token Provider | PO Token Provider Setup

> 📌 **چرا لازم است؟** از سال ۲۰۲۶ یوتیوب برای دانلود زیرنویس به «PO Token» نیاز دارد. بدون آن، دانلود زیرنویس با خطای `Did not get any data blocks` مواجه می‌شود. این راه‌نما را **یک‌بار** انجام دهید.

### ۱) نصب Node.js (الزامی برای زیرنویس)

اگر Node.js نسخه **۲۲ یا بالاتر** نصب نباشد، برنامه هنگام اجرا پیام هشدار نشان می‌دهد.

```bash
# ویندوز (با winget)
winget install OpenJS.NodeJS.LTS
```

### ۲) نصب وابستگی‌های Python

```bash
pip install -r requirements.txt
# شامل: curl_cffi (Impersonation) + bgutil-ytdlp-pot-provider (PO Token)
```

### ۳) راه‌اندازی سرور PO Token

```bash
# کلون ریپو (نسخه 2.0.0) در پوشه خانگی
git clone --single-branch --branch 2.0.0 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git ~/bgutil-ytdlp-pot-provider
cd ~/bgutil-ytdlp-pot-provider/server

# بیلد اسکریپت تولید توکن (با Node.js)
npm ci
npx tsc
```

### ۴) اجبار استفاده از Node.js (اختیاری)

اگر هم Node.js و هم Deno نصب باشند، Deno اولویت می‌گیرد و ممکن است خطا بدهد. برای استفاده از Node.js:

```bash
mv src/generate_once.ts src/generate_once.ts.disabled
```

### ۵) تست

```bash
yt-dlp --write-auto-subs --sub-langs en --skip-download "https://www.youtube.com/watch?v=VIDEO_ID"
```

اگر فایل `.srt` ساخته شد، PO Token درست کار می‌کند. ✅

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

### 🎵 دانلود پلی‌لیست

1. لینک پلی‌لیست (مثل `youtube.com/playlist?list=...` یا `watch?v=...&list=...`) را وارد کنید.
2. روی «استخراج فرمت‌ها» بزنید — لیست ویدئوها با حجم تقریبی نمایش داده می‌شود.
3. **کیفیت دلخواه** را از کامبو انتخاب کنید.
4. ویدئو(های) موردنظر را **تیک** بزنید (یا «انتخاب همه»).
5. روی «دانلود انتخاب‌شده» بزنید.

> 📏 حجم هر ویدئو بر اساس کیفیت انتخابی به‌صورت تدریجی محاسبه و نمایش داده می‌شود.

### 💬 دانلود زیرنویس

1. در بخش «ذخیره‌سازی و دانلود»، تیک **«زیرنویس → دانلود»** را بزنید.
2. زبان‌ها را وارد کنید (مثلاً `fa,en` یا `all`).
3. اگر زیرنویس فقط خودکار است، تیک «خودکار» را هم بزنید.

> ⚠️ زیرنویس نیازمند راه‌اندازی **PO Token Provider** است (بخش بالا). اگر Node.js نصب نباشد، برنامه هشدار می‌دهد.

---

## 📁 ساختار پروژه | Project Structure

```
Persian_Youtube_Downloader/
├── main.py           → نقطه ورود برنامه (entry point)
├── gui.py            → رابط کاربری گرافیکی (PyQt6)
├── downloader.py     → منطق دانلود، زیرنویس و استخراج فرمت‌ها (yt-dlp)
├── cookies.py        → شناسایی مرورگرها و مدیریت فایل کوکی
├── settings.py       → ذخیره/بازیابی تنظیمات و تاریخچه (JSON)
├── requirements.txt  → وابستگی‌های پروژه (شامل PO Token)
├── README.md         → مستند پروژه (فارسی/انگلیسی)
├── LICENSE           → مجوز MIT
├── docs/
│   └── screenshot.png → اسکرین‌شات برنامه
└── .gitignore        → فایل‌های نادیده‌گرفته‌شده (شامل کوکی‌ها)
```

| فایل | File | مسئولیت |
|------|------|---------|
| `main.py` | entry point | اجرای برنامه |
| `gui.py` | UI (PyQt6) | پنجره اصلی، جدول فرمت‌ها، پلی‌لیست، تاریخچه |
| `downloader.py` | download engine | ساخت پارامترهای yt-dlp، دانلود، زیرنویس، پارس فرمت‌ها |
| `cookies.py` | cookie manager | تشخیص مرورگر، اعتبارسنجی کوکی |
| `settings.py` | settings | ذخیره تنظیمات و تاریخچه در `~/.youtube_downloader/config.json` |

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
| «Did not get any data blocks» در زیرنویس | subtitle PO token error | PO Token Provider را راه‌اندازی کنید (بخش راه‌اندازی PO Token) |
| ویدئو بدون زیرنویس دانلود شد | video without subtitle | تیک «خودکار» را بزنید (اکثر ویدئوها فقط زیرنویس خودکار دارند) |

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
