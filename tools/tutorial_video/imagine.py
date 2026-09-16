"""Minimal Grok Imagine REST client (image + video)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

def load_dotenv() -> None:
    for path in (Path("/workspace/.env"), Path.cwd() / ".env"):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()
DEFAULT_BASE = "https://api.x.ai/v1"
IMAGE_MODEL = "grok-imagine-image-2.0"
VIDEO_MODEL = "grok-imagine-video-1.5"


class ImagineError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("XAI_API_KEY", "").strip()
    if not key:
        raise ImagineError(
            "XAI_API_KEY is not set. Add it to the environment before rendering."
        )
    return key


@dataclass
class ImagineClient:
    api_key: str | None = None
    base_url: str = DEFAULT_BASE
    timeout: float = 60
    poll_interval: float = 5
    poll_timeout: float = 600

    def _key(self) -> str:
        return self.api_key or _api_key()

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        accept: str = "application/json",
    ) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self._key()}",
                "Accept": accept,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                ctype = resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ImagineError(f"{method} {path} failed ({exc.code}): {detail}") from exc
        if "application/json" in ctype or raw[:1] in (b"{", b"["):
            return json.loads(raw.decode("utf-8"))
        return raw

    def generate_image(
        self,
        prompt: str,
        *,
        aspect_ratio: str = "16:9",
        resolution: str = "1k",
        quality: str = "medium",
    ) -> bytes:
        payload = {
            "model": IMAGE_MODEL,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "quality": quality,
            "response_format": "b64_json",
            "n": 1,
        }
        data = self._request("POST", "/images/generations", payload)
        items = data.get("data") or []
        if not items:
            raise ImagineError(f"image response missing data: {data}")
        item = items[0]
        if item.get("b64_json"):
            import base64

            return base64.b64decode(item["b64_json"])
        url = item.get("url")
        if not url:
            raise ImagineError(f"image response missing url/b64: {data}")
        return self.download(url)

    def start_video(
        self,
        prompt: str,
        *,
        image: str | None = None,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        generate_audio: bool = False,
    ) -> str:
        payload: dict[str, Any] = {
            "model": VIDEO_MODEL,
            "prompt": prompt,
            "duration": max(1, min(int(duration), 15)),
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "generate_audio": generate_audio,
        }
        if image:
            payload["image"] = image
        data = self._request("POST", "/videos/generations", payload)
        request_id = data.get("request_id")
        if not request_id:
            raise ImagineError(f"video start missing request_id: {data}")
        return str(request_id)

    def get_video(self, request_id: str) -> dict[str, Any]:
        return self._request("GET", f"/videos/{request_id}")

    def wait_for_video(self, request_id: str) -> dict[str, Any]:
        deadline = time.time() + self.poll_timeout
        while time.time() < deadline:
            data = self.get_video(request_id)
            status = data.get("status")
            if status == "done":
                video = data.get("video") or {}
                if not video.get("url"):
                    raise ImagineError(f"done without url: {data}")
                return data
            if status in {"failed", "expired"}:
                raise ImagineError(f"video {request_id} {status}: {data}")
            time.sleep(self.poll_interval)
        raise ImagineError(f"timed out waiting for video {request_id}")

    def download(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "foodrecipe-imagine/0.1"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read()

    def save_bytes(self, data: bytes, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path


def image_data_uri(image_bytes: bytes, mime: str = "image/jpeg") -> str:
    import base64

    return f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def suffix_from_url(url: str, default: str = ".mp4") -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix
    return suffix or default
