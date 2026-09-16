"""Built-in 電學小知識 lessons. Add more JSON files beside this module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent / "data" / "lessons.json"


def load_lessons() -> list[dict[str, Any]]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def get_lesson(key: str) -> dict[str, Any]:
    for lesson in load_lessons():
        if lesson["id"] == key or lesson["title"] == key:
            return lesson
    known = ", ".join(item["id"] for item in load_lessons())
    raise KeyError(f"unknown lesson {key!r}. known ids: {known}")
