"""Parse cooking recipes from the site's index.html."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = ROOT / "index.html"

_RECIPE_HEAD = re.compile(
    r'\{id:"(?P<id>[^"]+)",n:"(?P<n>[^"]+)",c:"(?P<c>[^"]+)",e:"(?P<e>[^"]+)",t:(?P<t>\d+)'
)
_STEP = re.compile(r'\[(\d+),"([^"\\]*(?:\\.[^"\\]*)*)"\]')
_TIP = re.compile(r'tip:"([^"\\]*(?:\\.[^"\\]*)*)"')
_ING_ROW = re.compile(r'\["([^"]+)",(.*?),"(.*?)"\]')


def _unescape(text: str) -> str:
    return text.replace(r"\"", '"').replace(r"\n", "\n").replace(r"\\", "\\")


def _block_for(html: str, start: int) -> str:
    depth = 0
    for i, ch in enumerate(html[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return html[start : i + 1]
    raise ValueError("unbalanced recipe object")


def parse_recipes(html: str | None = None) -> list[dict[str, Any]]:
    source = html if html is not None else INDEX_HTML.read_text(encoding="utf-8")
    marker = source.find("const R=[")
    if marker < 0:
        raise ValueError("recipe list not found in index.html")
    chunk = source[marker:]
    recipes: list[dict[str, Any]] = []
    for match in _RECIPE_HEAD.finditer(chunk):
        block = _block_for(chunk, match.start())
        steps = [
            {"at": int(minute), "text": _unescape(text)}
            for minute, text in _STEP.findall(block)
        ]
        tip_match = _TIP.search(block)
        ingredients = [
            {"name": name, "amount": amount.strip(), "unit": unit}
            for name, amount, unit in _ING_ROW.findall(block)
        ]
        recipes.append(
            {
                "id": match.group("id"),
                "name": match.group("n"),
                "cuisine": match.group("c"),
                "equipment": match.group("e"),
                "minutes": int(match.group("t")),
                "ingredients": ingredients,
                "steps": steps,
                "tip": _unescape(tip_match.group(1)) if tip_match else "",
            }
        )
    if not recipes:
        raise ValueError("no recipes parsed")
    return recipes


def get_recipe(recipe_id: str) -> dict[str, Any]:
    for recipe in parse_recipes():
        if recipe["id"] == recipe_id or recipe["name"] == recipe_id:
            return recipe
    known = ", ".join(r["id"] for r in parse_recipes())
    raise KeyError(f"unknown recipe {recipe_id!r}. known ids: {known}")


def dump_catalog(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(parse_recipes(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
