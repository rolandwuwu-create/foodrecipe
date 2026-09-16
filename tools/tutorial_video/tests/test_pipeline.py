import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.tutorial_video.assets import candidate_matches, pick_stock
from tools.tutorial_video.imagine import ImagineClient, ImagineError
from tools.tutorial_video.planner import (
    BANNED_STOCK_QUERIES,
    assert_shot_searchable,
    plan_recipe,
    plan_topic,
)
from tools.tutorial_video.recipes import get_recipe, parse_recipes


class RecipeParseTests(unittest.TestCase):
    def test_parses_tomato_egg(self):
        recipes = parse_recipes()
        self.assertGreaterEqual(len(recipes), 10)
        dish = get_recipe("tomatoegg")
        self.assertEqual(dish["name"], "番茄炒蛋")
        self.assertTrue(dish["steps"])
        self.assertTrue(any("番茄" in i["name"] for i in dish["ingredients"]))


class PlannerTests(unittest.TestCase):
    def test_recipe_shots_lock_the_dish(self):
        board = plan_recipe(get_recipe("tomatoegg"))
        self.assertEqual(board["asset_policy"], "generate_per_shot")
        self.assertGreaterEqual(len(board["shots"]), 5)
        for shot in board["shots"]:
            self.assertEqual(shot["source"], "imagine")
            self.assertIn("番茄炒蛋", " ".join(shot["visual"]["must_include"]))
            self.assertIn("番茄炒蛋", shot["image_prompt"])

    def test_topic_requires_real_steps(self):
        with self.assertRaises(ValueError):
            plan_topic("怎麼用這個網站", [])
        board = plan_topic("怎麼用冰箱篩晚餐", ["勾選食材", "看推薦"])
        self.assertEqual(board["shots"][1]["narration"], "勾選食材")

    def test_blocks_generic_stock_queries(self):
        shot = plan_recipe(get_recipe("tomatoegg"))["shots"][0]
        for query in ("cooking", "kitchen", "美食", "cooking video"):
            self.assertIn(query, BANNED_STOCK_QUERIES)
            with self.assertRaises(ValueError):
                assert_shot_searchable(shot, query)
        with self.assertRaises(ValueError):
            assert_shot_searchable(shot, "chef plating pasta")
        assert_shot_searchable(shot, "番茄炒蛋 成品 家常")


class AssetPolicyTests(unittest.TestCase):
    def test_stock_must_mention_the_dish(self):
        shot = plan_recipe(get_recipe("tomatoegg"))["shots"][0]
        self.assertTrue(candidate_matches("Random pasta night", "stock dinner", shot))
        self.assertEqual(
            candidate_matches(
                "番茄炒蛋 炒鍋 finished plate 家常",
                "home cooked 番茄炒蛋",
                shot,
            ),
            [],
        )

    def test_pick_stock_refuses_when_nothing_matches(self):
        shot = plan_recipe(get_recipe("tomatoegg"))["shots"][0]
        fake_hits = [
            {
                "title": "File:Kitchen.jpg",
                "description": "A generic kitchen",
                "url": "https://example.com/k.jpg",
                "mime": "image/jpeg",
            }
        ]
        with patch("tools.tutorial_video.assets.search_commons", return_value=fake_hits):
            with self.assertRaises(Exception) as ctx:
                pick_stock(shot, "番茄炒蛋 家常")
        self.assertIn("Imagine", str(ctx.exception))


class ImagineClientTests(unittest.TestCase):
    def test_start_video_reads_request_id(self):
        client = ImagineClient(api_key="test-key")

        def fake_request(method, path, body=None, accept="application/json"):
            self.assertEqual(method, "POST")
            self.assertEqual(path, "/videos/generations")
            self.assertEqual(body["model"], "grok-imagine-video-1.5")
            self.assertIn("image", body)
            return {"request_id": "abc-123"}

        with patch.object(client, "_request", side_effect=fake_request):
            self.assertEqual(
                client.start_video("move", image="data:image/jpeg;base64,xx", duration=6),
                "abc-123",
            )

    def test_wait_for_video_handles_failure(self):
        client = ImagineClient(api_key="test-key", poll_interval=0, poll_timeout=1)
        with patch.object(client, "get_video", return_value={"status": "failed"}):
            with self.assertRaises(ImagineError):
                client.wait_for_video("abc")

    def test_generate_image_requires_key(self):
        client = ImagineClient(api_key="")
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ImagineError):
                client.generate_image("x")


class PlaceholderAssembleTests(unittest.TestCase):
    def test_placeholders_concat(self):
        from tools.tutorial_video.assemble import assemble_job, make_placeholder

        board = plan_topic("測試", ["第一步"])
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "storyboard.json").write_text(json.dumps(board), encoding="utf-8")
            for shot in board["shots"]:
                make_placeholder(
                    job / "shots" / shot["id"] / "clip.mp4",
                    shot["id"],
                    1,
                )
            out = assemble_job(board, job)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
