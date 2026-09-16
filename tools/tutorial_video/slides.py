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
    draw.rounded_rectangle((80, 860, 360, 890), radius=4, fill=None)
    draw.rectangle((90, 866, 350, 884), fill=NAVY)
    for i in range(0, 260, 4):
        t = i / 260
        color = (int(40 + 215 * t), int(40 + 80 * t), int(180 * (1 - t)))
        draw.rectangle((90 + i, 866, 94 + i, 884), fill=color)
    draw.text((90, 830), "低", font=_font(20), fill=MUTED)
    draw.text((320, 830), "高電流密度", font=_font(20), fill=MUTED)
    _center(draw, caption, 760, _font(36), WHITE)
    return img


def slide_ring(topic: str, title: str, caption: str) -> Image.Image:
    img, draw = canvas()
    badge(draw, topic)
    _center(draw, title, 140, _font(52))
    cx, cy, r = W // 2, 560, 250
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 130, 50))
    draw.ellipse((cx - r + 28, cy - r + 28, cx + r - 28, cy + r - 28), fill=(40, 140, 220))
    draw.ellipse((cx - r + 70, cy - r + 70, cx + r - 70, cy + r - 70), fill=BG)
    _center(draw, caption, 820, _font(32), MUTED)
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


TOPIC_EN = {
    "集膚效應": "Skin Effect",
    "鄰近效應": "Proximity Effect",
    "繼電器黏死": "Relay Weld",
}


def _english(topic: str) -> str:
    return TOPIC_EN.get(topic, topic)


def _topic_badge(draw: ImageDraw.ImageDraw, topic: str) -> None:
    draw.rounded_rectangle((1480, 70, 1850, 160), radius=12, outline=GOLD, width=2)
    draw.text((1510, 82), topic, font=_font(32), fill=WHITE)
    draw.text((1510, 118), _english(topic), font=_font(20), fill=GOLD)


def slide_title(topic: str, jinju: str, sub: str) -> Image.Image:
    img, draw = canvas()
    _topic_badge(draw, topic)
    draw.text((120, 300), jinju, font=_font(120), fill=WHITE)
    draw.line((120, 470, 420, 470), fill=CYAN, width=8)
    draw.ellipse((420, 454, 452, 486), fill=CYAN)
    draw.text((120, 520), sub, font=_font(56), fill=CYAN)
    cx, cy = 1500, 620
    draw.ellipse((cx - 260, cy - 180, cx + 320, cy + 240), fill=ORANGE)
    draw.ellipse((cx - 160, cy - 120, cx + 220, cy + 180), fill=(30, 90, 140))
    return img


HEROES = Path(__file__).resolve().parent / "data" / "heroes"


def _fit_hero(name: str) -> Image.Image:
    src = Image.open(HEROES / Path(name).name).convert("RGB")
    if src.size == (W, H):
        return src
    return src.resize((W, H), Image.Resampling.LANCZOS)


def slide_photo_title(photo: str, topic: str, jinju: str, sub: str) -> Image.Image:
    img = _fit_hero(photo).convert("RGBA")
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(shade)
    for x in range(0, 1040):
        alpha = int(230 * (1 - x / 1040))
        d.line([(x, 0), (x, H)], fill=(7, 21, 38, alpha))
    img = Image.alpha_composite(img, shade).convert("RGB")
    draw = ImageDraw.Draw(img)
    _topic_badge(draw, topic)
    size = 108
    font = _font(size)
    box = draw.textbbox((0, 0), jinju, font=font)
    while size > 56 and (box[2] - box[0]) > 980:
        size -= 8
        font = _font(size)
        box = draw.textbbox((0, 0), jinju, font=font)
    draw.text((90, 300), jinju, font=font, fill=WHITE)
    draw.line((120, 470, 420, 470), fill=CYAN, width=8)
    draw.ellipse((420, 454, 452, 486), fill=CYAN)
    draw.text((120, 520), sub, font=_font(48), fill=CYAN)
    return img


def slide_photo_caption(photo: str, topic: str, title: str, caption: str) -> Image.Image:
    img = _fit_hero(photo)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 120), fill=BG)
    badge(draw, topic)
    _center(draw, title, 18, _font(34))
    if caption:
        _center(draw, caption, 70, _font(26), MUTED)
    return img


def wrap_zh(text: str, width: int = 22) -> list[str]:
    text = " ".join((text or "").split())
    if not text:
        return []
    lines: list[str] = []
    buf = ""
    breaks = set("，。；、！？,.;!? ")
    for ch in text:
        buf += ch
        if len(buf) >= width and ch in breaks:
            lines.append(buf.strip())
            buf = ""
        elif len(buf) >= width + 8:
            lines.append(buf.strip())
            buf = ""
    if buf.strip():
        lines.append(buf.strip())
    return lines[:4]


def slide_bullets(topic: str, title: str, bullets: list[str]) -> Image.Image:
    img, draw = canvas()
    badge(draw, topic)
    _center(draw, title, 140, _font(52))
    y = 300
    for item in bullets[:5]:
        draw.ellipse((160, y + 16, 196, y + 52), fill=ORANGE)
        draw.text((230, y), item, font=_font(40), fill=WHITE)
        y += 110
    return img


def slide_compare(
    topic: str,
    title: str,
    left_title: str,
    left_body: str,
    right_title: str,
    right_body: str,
) -> Image.Image:
    img, draw = canvas()
    badge(draw, topic)
    _center(draw, title, 140, _font(52))
    cards = [
        (120, left_title, left_body),
        (1020, right_title, right_body),
    ]
    for x, heading, body in cards:
        draw.rounded_rectangle((x, 280, x + 780, 820), radius=18, fill=NAVY)
        draw.text((x + 48, 320), heading, font=_font(44), fill=GOLD)
        y = 420
        for line in wrap_zh(body, 14):
            draw.text((x + 48, y), line, font=_font(36), fill=WHITE)
            y += 64
    return img


def slide_text(topic: str, title: str, caption: str) -> Image.Image:
    img, draw = canvas()
    badge(draw, topic)
    _center(draw, title, 200, _font(56))
    y = 380
    for line in wrap_zh(caption, 16):
        _center(draw, line, y, _font(44), WHITE)
        y += 72
    return img


def slide_end(topic: str, jinju: str, caption: str) -> Image.Image:
    img, draw = canvas()
    _center(draw, "小東老師電子學", 280, _font(40), MUTED)
    _center(draw, caption or topic, 380, _font(64), GOLD)
    y = 520
    for line in wrap_zh(jinju, 16) or [jinju]:
        _center(draw, line, y, _font(48), WHITE)
        y += 70
    return img


def paint_subtitle(img: Image.Image, text: str) -> Image.Image:
    lines = wrap_zh(text, 26)
    if not lines:
        return img
    bar_h = 36 + 44 * len(lines)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    y0 = H - bar_h
    d.rectangle((0, y0, W, H), fill=(7, 21, 38, 210))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    y = y0 + 12
    for line in lines:
        _center(draw, line, y, _font(30), WHITE)
        y += 44
    return img


def render_beat(beat: dict[str, Any], dest: Path) -> Path:
    kind = beat["slide"]
    topic = beat.get("topic") or ""
    if kind == "photo_title":
        img = slide_photo_title(beat["photo"], topic, beat["jinju"], beat.get("sub") or "")
    elif kind == "photo_caption":
        img = slide_photo_caption(
            beat["photo"], topic, beat.get("title") or "", beat.get("caption") or ""
        )
    elif kind == "title":
        img = slide_title(topic, beat["jinju"], beat.get("sub") or "")
    elif kind == "heatmap_low":
        img = slide_heatmap(topic, beat.get("title") or "電流密度", beat["caption"], "low")
    elif kind == "heatmap_high":
        img = slide_heatmap(topic, beat.get("title") or "電流密度", beat["caption"], "high")
    elif kind == "ring":
        img = slide_ring(topic, beat.get("title") or "", beat["caption"])
    elif kind == "bullets":
        img = slide_bullets(topic, beat.get("title") or "", list(beat.get("bullets") or []))
    elif kind == "compare":
        img = slide_compare(
            topic,
            beat.get("title") or "",
            beat.get("left_title") or "",
            beat.get("left_body") or "",
            beat.get("right_title") or "",
            beat.get("right_body") or "",
        )
    elif kind == "text":
        img = slide_text(topic, beat.get("title") or "", beat.get("caption") or "")
    elif kind == "end":
        img = slide_end(topic, beat.get("jinju") or "", beat.get("caption") or topic)
    elif kind == "jinju":
        img = slide_jinju(topic, beat["jinju"], beat.get("caption") or "")
    else:
        img = slide_jinju(topic, beat.get("caption") or beat.get("jinju") or "", "")
    if beat.get("narration") and kind not in {"photo_title", "jinju", "end"}:
        img = paint_subtitle(img, beat["narration"])
    return save(img, dest)
