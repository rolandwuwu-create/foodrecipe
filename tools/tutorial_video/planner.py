"""Build a locked shot list for 電學小知識. Stock keywords are not a plan."""

from __future__ import annotations

from typing import Any

STYLE_LOCK = (
    "consistent 電學小知識 educational series: dark slate desk, clean vector "
    "circuit diagrams, subtle electron-flow dots, high-school physics aesthetic, "
    "same color language (amber voltage, teal current, coral resistor), "
    "no on-screen channel logo, no watermark, no YouTube end screen"
)

BANNED_STOCK_QUERIES = frozenset(
    {
        "electricity",
        "electric",
        "power",
        "energy",
        "lightning",
        "spark",
        "electrician",
        "power plant",
        "science",
        "education",
        "電",
        "電力",
        "閃電",
        "電工",
        "科普",
        "教學",
        "電路",
        "cooking",
        "kitchen",
        "food",
        "美食",
    }
)

GENERIC_MUST_NOT = [
    "lightning bolt stock footage",
    "power-plant cooling towers",
    "electrician in a hard hat",
    "tesla coil sparks",
    "generic glowing earth",
    "unrelated kitchen or food",
    "random gadget unboxing",
]


def style_lock(topic: str) -> str:
    return f"{STYLE_LOCK}, one continuous explainer about {topic}"


def _shot(
    shot_id: str,
    role: str,
    narration: str,
    subject: str,
    must_include: list[str],
    must_not: list[str],
    camera: str,
    motion: str,
    duration: int,
    topic: str,
) -> dict[str, Any]:
    image_prompt = (
        f"{subject}. {camera}. {style_lock(topic)}. "
        f"Must show: {', '.join(must_include)}. Do not show: {', '.join(must_not)}."
    )
    video_prompt = (
        f"{motion}. Stay on this exact concept: {topic}. "
        f"{style_lock(topic)}. No cutaway to unrelated electricity b-roll."
    )
    return {
        "id": shot_id,
        "role": role,
        "duration_sec": duration,
        "narration": narration,
        "source": "imagine",
        "visual": {
            "subject": subject,
            "must_include": must_include,
            "must_not": must_not,
            "camera": camera,
            "motion": motion,
        },
        "image_prompt": image_prompt,
        "video_prompt": video_prompt,
    }


def _title_shot(topic: str, hook: str) -> dict[str, Any]:
    return _shot(
        "s00",
        "title",
        hook or topic,
        f"title card visual that is only about {topic}: a specific diagram, not generic electricity",
        [topic],
        GENERIC_MUST_NOT,
        "centered educational wide, diagram occupies most of the frame",
        f"slow push-in on the {topic} diagram",
        5,
        topic,
    )


def _recap_shot(topic: str, index: int) -> dict[str, Any]:
    return _shot(
        f"s{index:02d}",
        "recap",
        f"記住：這一則電學小知識只講{topic}。",
        f"recap of the same {topic} diagram used in the lesson, not a generic end card",
        [topic],
        GENERIC_MUST_NOT,
        "same desk and same diagram as the lesson",
        "hold the final diagram, then fade",
        5,
        topic,
    )


def plan_topic(topic: str, steps: list[str] | list[dict[str, str]], hook: str = "") -> dict[str, Any]:
    if not str(topic).strip():
        raise ValueError("topic is required")
    cleaned: list[dict[str, str]] = []
    for step in steps:
        if isinstance(step, str):
            text = step.strip()
            if text:
                cleaned.append({"text": text, "visual": f"diagram that shows only: {text}"})
        else:
            text = (step.get("text") or "").strip()
            if not text:
                continue
            cleaned.append(
                {
                    "text": text,
                    "visual": (step.get("visual") or f"diagram that shows only: {text}").strip(),
                }
            )
    if not cleaned:
        raise ValueError("tutorial steps are required; do not invent stock b-roll")

    topic = topic.strip()
    shots = [_title_shot(topic, hook.strip() or topic)]
    for index, step in enumerate(cleaned, start=1):
        shots.append(
            _shot(
                f"s{index:02d}",
                "step",
                step["text"],
                f"{topic}: {step['visual']}",
                [topic, step["text"]],
                GENERIC_MUST_NOT,
                "clear view of this one electrical idea, large readable diagram",
                f"animate only this idea: {step['text']}",
                7,
                topic,
            )
        )
    shots.append(_recap_shot(topic, len(shots)))
    return {
        "kind": "electrical_short",
        "series": "電學小知識",
        "topic": topic,
        "style_lock": style_lock(topic),
        "asset_policy": "generate_per_shot",
        "shots": shots,
    }


def plan_lesson(lesson: dict[str, Any]) -> dict[str, Any]:
    board = plan_topic(lesson["title"], lesson.get("steps") or [], hook=lesson.get("hook") or "")
    board["lesson_id"] = lesson["id"]
    board["series"] = lesson.get("series") or "電學小知識"
    return board


def assert_shot_searchable(shot: dict[str, Any], query: str) -> None:
    """Reject the generic searches that make 電學 footage look like lightning reels."""
    cleaned = " ".join(query.lower().split())
    if cleaned in BANNED_STOCK_QUERIES:
        raise ValueError(f"generic stock query is blocked: {query!r}")
    hay = cleaned
    must = [m.lower() for m in shot["visual"]["must_include"]]
    if not any(term in hay for term in must):
        raise ValueError(
            f"stock query {query!r} does not contain any must_include term {must}"
        )
