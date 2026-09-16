"""Write the episode 腳本, YouTube copy, and subtitles."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def narration_full(board: dict[str, Any]) -> str:
    return "\n\n".join(shot["narration"].strip() for shot in board["shots"] if shot.get("narration"))


def script_markdown(board: dict[str, Any]) -> str:
    lines = [
        f"# {board['jinju']}｜{board['topic']}",
        "",
        f"系列：{board.get('series') or '小東老師電子學'}",
        f"片長目標：約 4–5 分鐘成片（旁白決定每鏡長度）",
        f"金句：{board['jinju']}",
        "",
        "## 旁白全稿（可直接配音）",
        "",
        narration_full(board),
        "",
        "## 分鏡腳本",
        "",
    ]
    for shot in board["shots"]:
        visual = shot.get("title") or shot.get("jinju") or shot.get("caption") or ""
        photo = f" / {shot['photo']}" if shot.get("photo") else ""
        lines += [
            f"### {shot['id']}　{shot['role']}",
            f"- 畫面：`{shot['slide']}`{photo}　{visual}",
            f"- 旁白：{shot['narration']}",
            "",
        ]
    return "\n".join(lines) + "\n"


def youtube_copy(board: dict[str, Any]) -> str:
    title = board.get("youtube_title") or f"{board['jinju']}｜{board['topic']} 5 分鐘搞懂"
    lines = [
        title,
        "",
        board["jinju"],
        "",
        "【這集講什麼】",
        "",
        narration_full(board).split("\n\n")[0],
        "",
        "【分鏡】",
        "",
    ]
    t = 0
    for shot in board["shots"]:
        mm, ss = divmod(int(shot.get("duration_sec") or 0), 60)
        # timestamps filled after render when actual durations exist
        lines.append(f"- {shot['id']} {shot['role']}　{shot.get('title') or shot.get('jinju') or ''}")
        t += int(shot.get("duration_sec") or 0)
    lines += [
        "",
        "#電子學 #鄰近效應 #集膚效應 #小東老師電子學 #高頻",
        "",
    ]
    return "\n".join(lines)


def _srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours, rest = divmod(ms, 3600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def srt_from_timeline(entries: list[tuple[float, float, str]]) -> str:
    blocks = []
    for i, (start, end, text) in enumerate(entries, 1):
        blocks.append(f"{i}\n{_srt_time(start)} --> {_srt_time(end)}\n{text.strip()}\n")
    return "\n".join(blocks)


def write_episode_docs(board: dict[str, Any], job_dir: Path) -> None:
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "SCRIPT.md").write_text(script_markdown(board), encoding="utf-8")
    (job_dir / "YOUTUBE.md").write_text(youtube_copy(board), encoding="utf-8")
