"""Taiwanese Mandarin voiceover for 小東老師電子學."""

from __future__ import annotations

import asyncio
from pathlib import Path

DEFAULT_VOICE = "zh-TW-YunJheNeural"
DEFAULT_RATE = "+6%"


class VoiceError(RuntimeError):
    pass


def synthesize(
    text: str,
    dest: Path,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
) -> Path:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        raise VoiceError("empty narration")
    dest.parent.mkdir(parents=True, exist_ok=True)

    async def _run() -> None:
        import edge_tts

        communicate = edge_tts.Communicate(cleaned, voice, rate=rate)
        await communicate.save(str(dest))

    try:
        asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001 — surface any TTS failure to the renderer
        raise VoiceError(str(exc)) from exc
    if not dest.exists() or dest.stat().st_size < 800:
        raise VoiceError(f"tts produced no audio: {dest}")
    return dest
