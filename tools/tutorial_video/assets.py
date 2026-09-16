"""Resolve one visual per shot. Default is Imagine, not web search."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .imagine import ImagineClient, image_data_uri, suffix_from_url
from .planner import BANNED_STOCK_QUERIES, assert_shot_searchable

COMMONS_API = "https://commons.wikimedia.org/w/api.php"


class AssetError(RuntimeError):
    pass


def shot_dir(job_dir: Path, shot_id: str) -> Path:
    path = job_dir / "shots" / shot_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def generate_shot_assets(
    client: ImagineClient,
    shot: dict[str, Any],
    job_dir: Path,
    *,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    generate_audio: bool = True,
) -> dict[str, Any]:
    folder = shot_dir(job_dir, shot["id"])
    still = client.generate_image(shot["image_prompt"], aspect_ratio=aspect_ratio)
    still_path = folder / "still.jpg"
    client.save_bytes(still, still_path)

    request_id = client.start_video(
        shot["video_prompt"],
        image=image_data_uri(still),
        duration=int(shot["duration_sec"]),
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        generate_audio=generate_audio,
    )
    result = client.wait_for_video(request_id)
    url = result["video"]["url"]
    clip = client.download(url)
    clip_path = folder / f"clip{suffix_from_url(url)}"
    client.save_bytes(clip, clip_path)
    record = {
        "shot_id": shot["id"],
        "source": "imagine",
        "still": str(still_path),
        "clip": str(clip_path),
        "request_id": request_id,
        "video_url": url,
    }
    write_json(folder / "asset.json", record)
    return record


def candidate_matches(title: str, description: str, shot: dict[str, Any]) -> list[str]:
    hay = f"{title} {description}".lower()
    errors: list[str] = []
    for term in shot["visual"]["must_include"]:
        if term.lower() not in hay:
            errors.append(f"missing {term!r}")
    for term in shot["visual"]["must_not"]:
        if term.lower() in hay:
            errors.append(f"contains forbidden {term!r}")
    return errors


def search_commons(shot: dict[str, Any], query: str, *, limit: int = 8) -> list[dict[str, str]]:
    assert_shot_searchable(shot, query)
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": str(limit),
        "prop": "imageinfo|info",
        "inprop": "displaytitle",
        "iiprop": "url|extmetadata|mime",
    }
    url = f"{COMMONS_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "foodrecipe-tutorial-video/0.1 (educational)"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    pages = (data.get("query") or {}).get("pages") or {}
    hits: list[dict[str, str]] = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        title = page.get("title") or ""
        desc = (meta.get("ImageDescription") or {}).get("value") or ""
        mime = info.get("mime") or ""
        file_url = info.get("url") or ""
        if not file_url.startswith("http"):
            continue
        if not mime.startswith(("image/", "video/")):
            continue
        hits.append({"title": title, "description": desc, "url": file_url, "mime": mime})
    return hits


def pick_stock(shot: dict[str, Any], query: str) -> dict[str, str]:
    if query.lower().strip() in BANNED_STOCK_QUERIES:
        raise AssetError(f"refusing generic stock query {query!r}")
    hits = search_commons(shot, query)
    accepted: list[dict[str, str]] = []
    rejected: list[str] = []
    for hit in hits:
        errors = candidate_matches(hit["title"], hit["description"], shot)
        if errors:
            rejected.append(f"{hit['title']}: {', '.join(errors)}")
            continue
        accepted.append(hit)
    if not accepted:
        raise AssetError(
            "no stock item matched must_include/must_not; generate with Imagine instead. "
            + "; ".join(rejected[:5])
        )
    return accepted[0]
