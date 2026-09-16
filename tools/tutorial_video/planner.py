"""Episode grammar cloned from 小東老師電子學 Grok Bot videos."""

from __future__ import annotations

from typing import Any

BANNED_STOCK_QUERIES = frozenset(
    {
        "electricity",
        "electric",
        "lightning",
        "spark",
        "electrician",
        "power plant",
        "電力",
        "閃電",
        "電工",
        "科普",
        "教學",
        "電路",
        "cooking",
        "food",
        "美食",
    }
)

GENERIC_MUST_NOT = [
    "lightning bolt",
    "power-plant cooling towers",
    "electrician hard hat",
    "tesla coil",
    "generic glowing earth",
    "unrelated kitchen",
]


def plan_lesson(lesson: dict[str, Any]) -> dict[str, Any]:
    topic = lesson["title"]
    jinju = lesson["jinju"]
    shots = []
    for index, beat in enumerate(lesson["beats"]):
        shot = {
            "id": f"s{index:02d}",
            "role": beat["role"],
            "duration_sec": int(beat.get("duration_sec") or 6),
            "narration": beat["narration"],
            "source": "slide",
            "slide": beat["slide"],
            "topic": topic,
            "jinju": beat.get("jinju") or jinju,
            "title": beat.get("title") or "",
            "caption": beat.get("caption") or beat.get("sub") or "",
            "sub": beat.get("sub") or lesson.get("sub") or "",
            "photo": beat.get("photo") or "",
            "visual": {
                "must_include": [topic, jinju],
                "must_not": GENERIC_MUST_NOT,
            },
        }
        if beat["role"] == "title":
            shot["source"] = "imagine+overlay"
            shot["image_prompt"] = lesson["hero_prompt"]
            shot["video_prompt"] = (
                "Slow cinematic push-in on this exact object, current glow on the skin only, "
                "no new objects, no text, no lightning."
            )
        shots.append(shot)
    return {
        "kind": "xiaodong_explainer",
        "series": lesson.get("series") or "小東老師電子學",
        "topic": topic,
        "lesson_id": lesson["id"],
        "jinju": jinju,
        "reference": lesson.get("reference"),
        "hero_prompt": lesson.get("hero_prompt"),
        "asset_policy": "imagine_hero_then_slides",
        "shots": shots,
    }


def plan_topic(topic: str, steps: list[str], hook: str = "", jinju: str = "") -> dict[str, Any]:
    if not topic.strip():
        raise ValueError("topic is required")
    cleaned = [s.strip() for s in steps if str(s).strip()]
    if not cleaned:
        raise ValueError("beats are required")
    jinju = (jinju or hook or topic).strip()
    lesson = {
        "id": "custom",
        "title": topic.strip(),
        "series": "小東老師電子學",
        "jinju": jinju,
        "sub": cleaned[0],
        "hero_prompt": (
            f"Photoreal cinematic 3D hero of the exact mechanism: {topic}. "
            "Dark navy studio, no people, no lightning, no power lines, no text."
        ),
        "beats": [
            {
                "role": "title",
                "slide": "title",
                "jinju": jinju,
                "sub": cleaned[0],
                "duration_sec": 5,
                "narration": hook or jinju,
            }
        ],
    }
    kinds = ["heatmap_low", "heatmap_high", "ring", "ring"]
    for i, text in enumerate(cleaned):
        lesson["beats"].append(
            {
                "role": "step",
                "slide": kinds[i % len(kinds)],
                "title": topic,
                "caption": text,
                "duration_sec": 7,
                "narration": text,
            }
        )
    lesson["beats"].append(
        {
            "role": "jinju",
            "slide": "jinju",
            "jinju": jinju,
            "caption": topic,
            "duration_sec": 6,
            "narration": jinju,
        }
    )
    return plan_lesson(lesson)


def assert_shot_searchable(shot: dict[str, Any], query: str) -> None:
    cleaned = " ".join(query.lower().split())
    if cleaned in BANNED_STOCK_QUERIES:
        raise ValueError(f"generic stock query is blocked: {query!r}")
    must = [m.lower() for m in shot["visual"]["must_include"]]
    if not any(term.lower() in cleaned for term in must):
        raise ValueError(f"stock query {query!r} missing must_include {must}")
