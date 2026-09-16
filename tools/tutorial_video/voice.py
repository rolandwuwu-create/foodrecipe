"""Taiwanese Mandarin voiceover for 小東老師電子學."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

DEFAULT_VOICE = "zh-TW-YunJheNeural"
FALLBACK_VOICES = (
    "zh-TW-YunJheNeural",
    "zh-TW-HsiaoChenNeural",
    "zh-CN-YunxiNeural",
)
DEFAULT_RATE = "+6%"


class VoiceError(RuntimeError):
    pass


def synthesize(
    text: str,
    dest: Path,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    attempts: int = 5,
) -> Path:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        raise VoiceError("empty narration")
    dest.parent.mkdir(parents=True, exist_ok=True)
    voices = [voice] + [v for v in FALLBACK_VOICES if v != voice]
    last_error = "unknown"

    async def _save(use_voice: str) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(cleaned, use_voice, rate=rate)
        await communicate.save(str(dest))

    for i in range(attempts):
        use_voice = voices[i % len(voices)]
        try:
            asyncio.run(_save(use_voice))
            if dest.exists() and dest.stat().st_size >= 800:
                return dest
            last_error = "empty file"
        except Exception as exc:  # noqa: BLE001 — TTS is flaky; retry then surface
            last_error = str(exc)
            if dest.exists():
                dest.unlink()
        time.sleep(1.2 * (i + 1))
    raise VoiceError(last_error)
