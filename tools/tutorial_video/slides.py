"""Dark-navy teaching slides cloned from 小東老師電子學 (bN9DOArGQbE)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG = (7, 21, 38)
WHITE = (244, 247, 251)
CYAN = (61, 198, 255)
ORANGE = (255, 122, 46)
GOLD = (232, 196, 106)
MUTED = (138, 160, 184)
NAVY = (11, 39, 68)
FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def _center(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.FreeTypeFont, fill=WHITE) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    x = (W - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)


def badge(draw: ImageDraw.ImageDraw, topic: str, x: int = 70, y: int = 60) -> None:
    font = _font(28)
    draw.rounded_rectangle((x, y, x + 220, y + 70), radius=10, outline=MUTED, width=2)
    draw.text((x + 24, y + 10), topic[:8], font=font, fill=WHITE)
    draw.text((x + 24, y + 40), "小東老師電子學", font=_font(18), fill=MUTED)


def save(img: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")
    return path


def slide_heatmap(topic: str, title: str, caption: str, mode: str) -> Image.Image:
    img, draw = canvas()
    badge(draw, topic)
    _center(draw, title, 120, _font(48))
    cx, cy, r = W // 2, 560, 280
    if mode == "low":
        for i in range(r, 0, -1):
            t = i / r
            color = (int(255 * (0.4 + 0.6 * t)), int(80 + 70 * t), int(20 + 20 * t))
            draw.ellipse((cx - i, cy - i, cx + i, cy + i), fill=color)
    else:
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE)
        draw.ellipse((cx - r + 22, cy - r + 22, cx + r - 22, cy + r - 22), fill=(40, 140, 220))
        draw.ellipse((cx - r + 70, cy - r + 70, cx + r - 70, cy + r - 70), fill=BG)
    draw.rounded_rectangle((80, 980, 360, 1010), radius=4, fill=None)
    draw.rectangle((90, 986, 350, 1004), fill=NAVY)
    for i in range(0, 260, 4):
        t = i / 260
        color = (int(40 + 215 * t), int(40 + 80 * t), int(180 * (1 - t)))
        draw.rectangle((90 + i, 986, 94 + i, 1004), fill=color)
    draw.text((90, 950), "低", font=_font(20), fill=MUTED)
    draw.text((320, 950), "高電流密度", font=_font(20), fill=MUTED)
    _center(draw, caption, 900, _font(36), WHITE)
    return img


def slide_ring(topic: str, title: str, caption: str) -> Image.Image:
    img, draw = canvas()
    badge(draw, topic)
    _center(draw, title, 140, _font(52))
    cx, cy, r = W // 2, 560, 250
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 130, 50))
    draw.ellipse((cx - r + 28, cy - r + 28, cx + r - 28, cy + r - 28), fill=(40, 140, 220))
    draw.ellipse((cx - r + 70, cy - r + 70, cx + r - 70, cy + r - 70), fill=BG)
    _center(draw, caption, 900, _font(32), MUTED)
    return img


def slide_jinju(topic: str, jinju: str, caption: str) -> Image.Image:
    img, draw = canvas()
    badge(draw, topic)
    font = _font(56)
    box = draw.textbbox((0, 0), jinju, font=font)
    tw = box[2] - box[0]
    x = (W - tw) // 2
    draw.text((x, 380), jinju, font=font, fill=WHITE)
    draw.rectangle((x, 460, x + tw, 466), fill=GOLD)
    cx, cy, r = W // 2, 700, 70
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE)
    draw.ellipse((cx - r + 28, cy - r + 28, cx + r - 28, cy + r - 28), fill=BG)
    _center(draw, caption, 860, _font(28), MUTED)
    return img


def slide_title(topic: str, jinju: str, sub: str) -> Image.Image:
    img, draw = canvas()
    draw.rounded_rectangle((1480, 70, 1850, 160), radius=12, outline=GOLD, width=2)
    draw.text((1510, 82), topic, font=_font(32), fill=WHITE)
    draw.text((1510, 118), "Skin Effect" if "膚" in topic else topic, font=_font(20), fill=GOLD)
    draw.text((120, 300), jinju, font=_font(120), fill=WHITE)
    draw.line((120, 470, 420, 470), fill=CYAN, width=8)
    draw.ellipse((420, 454, 452, 486), fill=CYAN)
    draw.text((120, 520), sub, font=_font(56), fill=CYAN)
    cx, cy = 1500, 620
    draw.ellipse((cx - 260, cy - 180, cx + 320, cy + 240), fill=ORANGE)
    draw.ellipse((cx - 160, cy - 120, cx + 220, cy + 180), fill=(30, 90, 140))
    return img


def render_beat(beat: dict[str, Any], dest: Path) -> Path:
    kind = beat["slide"]
    topic = beat.get("topic") or ""
    if kind == "title":
        img = slide_title(topic, beat["jinju"], beat.get("sub") or "")
    elif kind == "heatmap_low":
        img = slide_heatmap(topic, beat.get("title") or "電流密度", beat["caption"], "low")
    elif kind == "heatmap_high":
        img = slide_heatmap(topic, beat.get("title") or "電流密度", beat["caption"], "high")
    elif kind == "ring":
        img = slide_ring(topic, beat.get("title") or "", beat["caption"])
    elif kind == "jinju":
        img = slide_jinju(topic, beat["jinju"], beat.get("caption") or "")
    else:
        img = slide_jinju(topic, beat.get("caption") or beat.get("jinju") or "", "")
    return save(img, dest)
