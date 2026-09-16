import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.tutorial_video.assemble import assemble_job, still_to_clip
from tools.tutorial_video.lessons import get_lesson
from tools.tutorial_video.planner import (
    BANNED_STOCK_QUERIES,
    assert_shot_searchable,
    plan_lesson,
    plan_topic,
)
from tools.tutorial_video.slides import render_beat


class SkinEffectLessonTests(unittest.TestCase):
    def test_matches_xiaodong_episode_grammar(self):
        board = plan_lesson(get_lesson("skin-effect"))
        self.assertEqual(board["kind"], "xiaodong_explainer")
        self.assertEqual(board["jinju"], "高頻世界裡，粗電線的心是空的。")
        self.assertEqual(board["asset_policy"], "imagine_hero_then_slides")
        self.assertEqual(board["shots"][0]["source"], "imagine+overlay")
        self.assertIn("no text", board["hero_prompt"])
        self.assertIn("no lightning", board["hero_prompt"])
        roles = [s["role"] for s in board["shots"]]
        self.assertEqual(roles[0], "title")
        self.assertEqual(roles[-1], "jinju")
        for shot in board["shots"][1:]:
            self.assertEqual(shot["source"], "slide")


class PlannerTests(unittest.TestCase):
    def test_topic_requires_beats(self):
        with self.assertRaises(ValueError):
            plan_topic("集膚效應", [])
        board = plan_topic("集膚效應", ["低頻整根跑", "高頻只走皮"], jinju="粗電線的心是空的")
        self.assertEqual(board["jinju"], "粗電線的心是空的")

    def test_blocks_generic_electricity_queries(self):
        shot = plan_lesson(get_lesson("skin-effect"))["shots"][0]
        for query in ("electricity", "lightning", "電工"):
            self.assertIn(query, BANNED_STOCK_QUERIES)
            with self.assertRaises(ValueError):
                assert_shot_searchable(shot, query)


class SlideTests(unittest.TestCase):
    def test_renders_1080p_pngs(self):
        board = plan_lesson(get_lesson("skin-effect"))
        with tempfile.TemporaryDirectory() as tmp:
            for shot in board["shots"]:
                path = render_beat(shot, Path(tmp) / f"{shot['id']}.png")
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 8000)


class AssembleTests(unittest.TestCase):
    def test_slides_concat_to_mp4(self):
        board = plan_lesson(get_lesson("skin-effect"))
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            for shot in board["shots"]:
                still = render_beat(shot, job / "shots" / shot["id"] / "still.png")
                still_to_clip(still, job / "shots" / shot["id"] / "clip.mp4", 1)
            out = assemble_job(board, job)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 5000)


if __name__ == "__main__":
    unittest.main()
