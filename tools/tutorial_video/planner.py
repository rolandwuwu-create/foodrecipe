"""Build a locked shot list. Stock-search keywords are not a plan."""

from __future__ import annotations

from typing import Any

STYLE_LOCK = (
    "photorealistic Taiwan home kitchen, warm tungsten light, slightly used wok, "
    "same cook's hands throughout, handheld cookbook tutorial, no on-screen text, "
    "no logo, no watermark, no stock-video lower third"
)

BANNED_STOCK_QUERIES = frozenset(
    {
        "cooking",
        "kitchen",
        "food",
        "recipe",
        "chef",
        "dinner",
        "cooking video",
        "food video",
        "做菜",
        "廚房",
        "美食",
        "料理",
        "教學",
        "烹飪",
        "食譜",
    }
)


def style_lock(dish: str) -> str:
    return f"{STYLE_LOCK}, continuous tutorial about {dish}"


def _ingredient_names(recipe: dict[str, Any], limit: int = 8) -> list[str]:
    names: list[str] = []
    for item in recipe.get("ingredients") or []:
        name = item.get("name") if isinstance(item, dict) else str(item)
        if name and name not in names:
            names.append(name)
        if len(names) >= limit:
            break
    return names


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
    dish: str,
) -> dict[str, Any]:
    image_prompt = (
        f"{subject}. {camera}. {style_lock(dish)}. "
        f"Must show: {', '.join(must_include)}. Do not show: {', '.join(must_not)}."
    )
    video_prompt = (
        f"{motion}. Keep the same framing and the same {dish} ingredients. "
        f"{style_lock(dish)}. No jump cuts to unrelated food."
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


def plan_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    dish = recipe["name"]
    equipment = recipe.get("equipment") or "炒鍋"
    minutes = recipe.get("minutes")
    ingredients = _ingredient_names(recipe)
    must_not = [
        "unrelated restaurant plating",
        "western brunch",
        "random grocery b-roll",
        "talking-head influencer",
        "stock footage kitchen montage",
    ]
    shots: list[dict[str, Any]] = []
    shots.append(
        _shot(
            "s00",
            "title",
            f"今天做{dish}，大概 {minutes} 分鐘，用{equipment}就夠。",
            f"title-worthy hero still of finished {dish} on a Taiwanese home table",
            [dish, equipment, "finished plate"],
            must_not,
            "tight 3/4 hero, shallow depth of field",
            "slow push-in over the plated dish, steam drifting",
            5,
            dish,
        )
    )
    if ingredients:
        shots.append(
            _shot(
                "s01",
                "mise",
                "材料先備好：" + "、".join(ingredients) + "。",
                f"mise en place for {dish}: {', '.join(ingredients)} in small bowls",
                [dish, *ingredients[:4]],
                must_not + ["cooked leftover from another dish"],
                "overhead looking down at the cutting board",
                "hands adjust bowls, no cutting yet",
                6,
                dish,
            )
        )
    for index, step in enumerate(recipe.get("steps") or [], start=1):
        text = step["text"]
        shots.append(
            _shot(
                f"s{index + 1:02d}",
                "step",
                text,
                f"{dish} cooking step: {text}",
                [dish, equipment],
                must_not + ["a different recipe"],
                "over-the-shoulder into the wok, close enough to see the food",
                f"perform only this action: {text}",
                7,
                dish,
            )
        )
    tip = (recipe.get("tip") or "").strip()
    if tip:
        shots.append(
            _shot(
                f"s{len(shots):02d}",
                "tip",
                tip,
                f"close detail that illustrates the tip for {dish}: {tip}",
                [dish],
                must_not,
                "macro insert on the critical detail",
                "hold the detail, tiny handheld drift",
                6,
                dish,
            )
        )
    shots.append(
        _shot(
            f"s{len(shots):02d}",
            "plate",
            f"{dish}完成，趁熱吃。",
            f"finished {dish} plated family-style, ready to eat",
            [dish, "plated serving"],
            must_not,
            "table-level three-quarter",
            "set chopsticks down, faint steam",
            5,
            dish,
        )
    )
    return {
        "kind": "recipe_tutorial",
        "topic": dish,
        "recipe_id": recipe["id"],
        "style_lock": style_lock(dish),
        "asset_policy": "generate_per_shot",
        "shots": shots,
    }


def plan_topic(topic: str, steps: list[str]) -> dict[str, Any]:
    if not topic.strip():
        raise ValueError("topic is required")
    if not steps:
        raise ValueError("tutorial steps are required; do not invent stock b-roll")
    must_not = [
        "unrelated stock footage",
        "generic office montage",
        "random food close-up",
        "celebrity talking head",
    ]
    shots = [
        _shot(
            "s00",
            "title",
            topic.strip(),
            f"hero visual that is specifically about: {topic}",
            [topic.strip()],
            must_not,
            "clean instructional wide",
            "slow push-in on the actual subject of the lesson",
            5,
            topic.strip(),
        )
    ]
    for index, step in enumerate(steps, start=1):
        text = step.strip()
        if not text:
            continue
        shots.append(
            _shot(
                f"s{index:02d}",
                "step",
                text,
                f"tutorial step for {topic}: {text}",
                [topic.strip(), text],
                must_not,
                "clear view of the action being taught",
                f"perform only: {text}",
                7,
                topic.strip(),
            )
        )
    shots.append(
        _shot(
            f"s{len(shots):02d}",
            "recap",
            f"重點就是這樣做{topic}。",
            f"recap still that still shows {topic}, not a generic end card",
            [topic.strip()],
            must_not,
            "same location as the lesson",
            "hold, then fade",
            5,
            topic.strip(),
        )
    )
    return {
        "kind": "topic_tutorial",
        "topic": topic.strip(),
        "style_lock": style_lock(topic.strip()),
        "asset_policy": "generate_per_shot",
        "shots": shots,
    }


def assert_shot_searchable(shot: dict[str, Any], query: str) -> None:
    """Reject the generic searches that make tutorial footage look wrong."""
    cleaned = " ".join(query.lower().split())
    if cleaned in BANNED_STOCK_QUERIES:
        raise ValueError(f"generic stock query is blocked: {query!r}")
    hay = cleaned
    must = [m.lower() for m in shot["visual"]["must_include"]]
    if not any(term in hay for term in must):
        raise ValueError(
            f"stock query {query!r} does not contain any must_include term {must}"
        )
