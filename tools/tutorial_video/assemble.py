"""Concatenate shot clips and burn Chinese titles."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"


class AssembleError(RuntimeError):
    pass


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssembleError(proc.stderr.strip() or proc.stdout.strip() or "ffmpeg failed")


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def make_placeholder(path: Path, text: str, duration: int, size: str = "1280x720") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    draw = f"drawtext=fontfile={FONT}:text='{_escape_drawtext(text)}':fontsize=36:fontcolor=white:x=60:y=h-120"
    _run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x191512:s={size}:d={duration}",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-vf",
            draw,
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ]
    )
    return path


def still_to_clip(
    png: Path,
    output: Path,
    duration: int,
    size: str = "1920x1080",
    zoom: bool = False,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    w, h = size.split("x")
    if zoom:
        frames = max(int(duration) * 25, 25)
        vf = (
            f"scale={w}:{h},"
            f"zoompan=z='min(1.0+0.0009*on,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps=25"
        )
    else:
        vf = (
            f"scale={size}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
        )
    _run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(png),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-vf",
            vf,
            "-t",
            str(duration),
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(output),
        ]
    )
    return output


def concat_clips(clips: list[Path], output: Path) -> Path:
    if not clips:
        raise AssembleError("no clips to assemble")
    if not shutil.which("ffmpeg"):
        raise AssembleError("ffmpeg is required")
    output.parent.mkdir(parents=True, exist_ok=True)
    listing = output.with_suffix(".concat.txt")
    lines = [f"file '{clip.resolve()}'" for clip in clips]
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            str(output),
        ]
    )
    return output


def assemble_job(storyboard: dict[str, Any], job_dir: Path) -> Path:
    clips: list[Path] = []
    for shot in storyboard["shots"]:
        folder = job_dir / "shots" / shot["id"]
        found = sorted(folder.glob("clip.*"))
        if not found:
            raise AssembleError(f"missing clip for {shot['id']}")
        clips.append(found[0])
    return concat_clips(clips, job_dir / "tutorial.mp4")
