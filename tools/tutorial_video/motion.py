"""Real motion graphics — current crowding, field rings, not Ken Burns."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Any, Iterator

import numpy as np
from PIL import Image, ImageDraw

from .assemble import AssembleError, probe_duration
from .slides import (
    BG,
    H,
    MUTED,
    NAVY,
    ORANGE,
    W,
    WHITE,
    _center,
    _font,
    badge,
    paint_subtitle,
)

FPS = 18


def clip_length(
    duration: float,
    audio: Path | None,
    pad_head: float = 0.35,
    pad_tail: float = 0.55,
) -> tuple[float, float, float]:
    if audio:
        adur = probe_duration(audio)
        pad_tail = max(pad_tail, float(duration) - adur - pad_head)
        total = adur + pad_head + pad_tail
    else:
        total = float(duration)
    return max(total, 1.2), pad_head, pad_tail


def _ease(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def _encode(
    frames: Iterator[np.ndarray],
    n_frames: int,
    output: Path,
    *,
    audio: Path | None,
    pad_head: float,
    pad_tail: float,
    total: float,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
    ]
    if audio:
        delay_ms = int(pad_head * 1000)
        cmd += [
            "-i",
            str(audio),
            "-filter_complex",
            f"[1:a]adelay={delay_ms}|{delay_ms},apad=pad_dur={pad_tail:.2f},"
            "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
        ]
    else:
        cmd += [
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
        ]
    cmd += [
        "-frames:v",
        str(n_frames),
        "-t",
        f"{total:.3f}",
        "-shortest",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        str(output),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for frame in frames:
            proc.stdin.write(np.ascontiguousarray(frame, dtype=np.uint8).tobytes())
        proc.stdin.close()
    except BrokenPipeError as exc:
        err = (proc.stderr.read() if proc.stderr else b"").decode("utf-8", errors="replace")
        raise AssembleError(err or "ffmpeg pipe broke") from exc
    err_bytes = proc.stderr.read() if proc.stderr else b""
    if proc.stderr:
        proc.stderr.close()
    code = proc.wait()
    if code != 0:
        raise AssembleError(err_bytes.decode("utf-8", errors="replace") or "ffmpeg motion encode failed")
    return output


def _heatmap_disk(mode: str, t: float) -> np.ndarray:
    """Return HxWx3 disk on navy, t=0..1."""
    cx, cy, r = W // 2, 560, 280
    yy, xx = np.ogrid[0:H, 0:W]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    rgb = np.zeros((H, W, 3), dtype=np.uint8)
    rgb[:, :] = BG
    inside = dist <= r
    if mode == "low":
        pulse = 0.85 + 0.15 * math.sin(t * math.pi * 2)
        tn = np.clip(1 - dist / r, 0, 1)
        rgb[..., 0][inside] = np.clip(255 * (0.35 + 0.65 * tn[inside]) * pulse, 0, 255).astype(
            np.uint8
        )
        rgb[..., 1][inside] = np.clip((70 + 90 * tn[inside]) * pulse, 0, 255).astype(np.uint8)
        rgb[..., 2][inside] = np.clip(20 + 30 * tn[inside], 0, 255).astype(np.uint8)
    else:
        hole = 40 + _ease(t) * 210
        skin = dist <= r
        rim = dist >= hole
        core = dist < hole - 18
        mid = inside & rim
        rgb[..., 0][mid] = 255
        rgb[..., 1][mid] = 122
        rgb[..., 2][mid] = 46
        blue = inside & (~rim) & (~core)
        rgb[..., 0][blue] = 40
        rgb[..., 1][blue] = 140
        rgb[..., 2][blue] = 220
        rgb[core] = BG
    return rgb


def _chrome_heatmap(shot: dict[str, Any]) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    topic = shot.get("topic") or ""
    badge(draw, topic)
    _center(draw, shot.get("title") or "電流密度", 120, _font(48))
    _center(draw, shot.get("caption") or "", 760, _font(36), WHITE)
    draw.rectangle((90, 866, 350, 884), fill=NAVY)
    for i in range(0, 260, 4):
        u = i / 260
        color = (int(40 + 215 * u), int(40 + 80 * u), int(180 * (1 - u)))
        draw.rectangle((90 + i, 866, 94 + i, 884), fill=color)
    draw.text((90, 830), "低", font=_font(20), fill=MUTED)
    draw.text((320, 830), "高電流密度", font=_font(20), fill=MUTED)
    if shot.get("narration"):
        img = paint_subtitle(img, shot["narration"])
    return img


def _frame_heatmap(shot: dict[str, Any], t: float, chrome: Image.Image) -> np.ndarray:
    disk = _heatmap_disk("low" if shot["slide"] == "heatmap_low" else "high", t)
    chrome_a = np.array(chrome)
    # keep chrome (non-navy-ish text areas): where chrome differs from BG a lot
    diff = np.abs(chrome_a.astype(np.int16) - np.array(BG, dtype=np.int16)).sum(axis=2)
    out = disk.copy()
    out[diff > 18] = chrome_a[diff > 18]
    return out


def _orange_mask(arr: np.ndarray) -> np.ndarray:
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    return (r > 130) & (g > 35) & (g < 210) & (b < 110) & (r > g) & (r > b + 20)


def _pulse_photo(base: np.ndarray, mask: np.ndarray, t: float) -> np.ndarray:
    boost = 0.22 * (0.5 + 0.5 * math.sin(t * math.pi * 2))
    out = base.astype(np.float32)
    out[mask, 0] = np.clip(out[mask, 0] * (1.05 + boost), 0, 255)
    out[mask, 1] = np.clip(out[mask, 1] * (1.0 + boost * 0.6), 0, 255)
    return out.astype(np.uint8)


def _field_rings(img: Image.Image, cx: float, cy: float, t: float) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(5):
        rad = (t * 420 + i * 70) % 420 + 40
        alpha = int(max(0, 140 - rad * 0.28))
        d.ellipse(
            (cx - rad, cy - rad, cx + rad, cy + rad),
            outline=(255, 140, 50, alpha),
            width=3,
        )
    # traveling current ticks along a horizontal band through the centroid
    for p in range(10):
        u = (t * 1.4 + p / 10) % 1
        x = cx - 280 + 560 * u
        y = cy + 8 * math.sin(u * math.pi * 4 + t * 8)
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 180, 60, 200))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _frame_photo(base: np.ndarray, mask: np.ndarray, cx: float, cy: float, t: float) -> np.ndarray:
    pulsed = _pulse_photo(base, mask, t)
    img = Image.fromarray(pulsed)
    return np.array(_field_rings(img, cx, cy, t))


def _frame_jinju(still: Image.Image, t: float) -> np.ndarray:
    img = still.copy()
    draw = ImageDraw.Draw(img)
    e = _ease(min(t * 1.4, 1))
    # growing gold underline approximation: brighten center ring
    cx, cy, r = W // 2, 700, int(40 + 40 * (0.5 + 0.5 * math.sin(t * math.pi * 2)))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ORANGE, width=6)
    draw.ellipse((cx - r + 22, cy - r + 22, cx + r - 22, cy + r - 22), outline=BG, width=8)
    fade = Image.new("RGB", img.size, BG)
    return np.array(Image.blend(fade, img, e if t < 0.25 else 1.0))


def _frame_cards(still: Image.Image, t: float) -> np.ndarray:
    e = _ease(min(t * 2.2, 1))
    fade = Image.new("RGB", still.size, BG)
    return np.array(Image.blend(fade, still, e if t < 0.5 else 1.0))


def animate_shot(
    shot: dict[str, Any],
    still: Path,
    output: Path,
    duration: float,
    audio: Path | None = None,
) -> Path:
    total, pad_head, pad_tail = clip_length(duration, audio)
    n = max(int(round(total * FPS)), FPS)
    kind = shot.get("slide") or ""
    still_img = Image.open(still).convert("RGB")
    base = np.array(still_img)
    mask = _orange_mask(base)
    if mask.any():
        ys, xs = np.where(mask)
        cx, cy = float(xs.mean()), float(ys.mean())
    else:
        cx, cy = W * 0.72, H * 0.55

    chrome = None
    if kind in {"heatmap_low", "heatmap_high"}:
        chrome = _chrome_heatmap(shot)

    def gen() -> Iterator[np.ndarray]:
        for i in range(n):
            t = i / max(n - 1, 1)
            if kind in {"heatmap_low", "heatmap_high"} and chrome is not None:
                yield _frame_heatmap(shot, t, chrome)
            elif kind in {"photo_title", "photo_caption"}:
                yield _frame_photo(base, mask, cx, cy, t)
            elif kind == "jinju":
                yield _frame_jinju(still_img, t)
            elif kind in {"bullets", "compare", "text", "end", "title"}:
                yield _frame_cards(still_img, t)
            else:
                yield _frame_photo(base, mask, cx, cy, t)

    return _encode(
        gen(),
        n,
        output,
        audio=audio,
        pad_head=pad_head,
        pad_tail=pad_tail,
        total=total,
    )
