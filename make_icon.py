"""تولید آیکون برنامه (دانلودر یوتیوب) — یک بار اجرا می‌شود"""
from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPen

SIZE = 256
img = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
img.fill(Qt.GlobalColor.transparent)

p = QPainter(img)
p.setRenderHint(QPainter.RenderHint.Antialiasing)

# پس‌زمینه: گرادیان قرمز یوتیوب
grad = QLinearGradient(QPointF(0, 0), QPointF(SIZE, SIZE))
grad.setColorAt(0.0, QColor("#FF3B30"))
grad.setColorAt(1.0, QColor("#CC0000"))
p.setBrush(grad)
p.setPen(Qt.PenStyle.NoPen)
p.drawRoundedRect(QRectF(8, 8, SIZE - 16, SIZE - 16), 52, 52)

# فلش دانلود سفید (بدنه + سر فلش + سینی)
pen = QPen(QColor("#FFFFFF"))
pen.setWidth(16)
pen.setCapStyle(Qt.PenCapStyle.RoundCap)
pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
p.setPen(pen)

cx = SIZE / 2  # 128
# بدنه فلش
p.drawLine(QPointF(cx, 68), QPointF(cx, 150))
# سر فلش
p.drawLine(QPointF(cx - 44, 108), QPointF(cx, 154))
p.drawLine(QPointF(cx + 44, 108), QPointF(cx, 154))
# سینی (خط افقی پایین)
p.drawLine(QPointF(cx - 48, 182), QPointF(cx + 48, 182))

p.end()

assets = Path(__file__).resolve().parent / "assets"
assets.mkdir(exist_ok=True)
img.save(str(assets / "icon.png"), "PNG")
img.save(str(assets / "icon.ico"), "ICO")
print("icon saved ->", assets / "icon.png", "and icon.ico")
