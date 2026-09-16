import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.tutorial_video.assets import candidate_matches, pick_stock
from tools.tutorial_video.imagine import ImagineClient, ImagineError
from tools.tutorial_video.lessons import get_lesson
from tools.tutorial_video.planner import (
    BANNED_STOCK_QUERIES,
    assert_shot_searchable,
    plan_lesson,
    plan_topic,
)


class LessonTests(unittest.TestCase):
    def test_ohms_law_is_locked_to_the_concept(self):
        board = plan_lesson(get_lesson("ohms-law"))
        self.assertEqual(board["series"], "電學小知識")
        self.assertEqual(board["asset_policy"], "generate_per_shot")
        self.assertGreaterEqual(len(board["shots"]), 6)
        for shot in board["shots"]:
            self.assertEqual(shot["source"], "imagine")
            self.assertIn("歐姆定律", shot["visual"]["must_include"])
            self.assertIn("lightning bolt stock footage", shot["visual"]["must_not"])
            self.assertIn("歐姆定律", shot["image_prompt"])


class PlannerTests(unittest.TestCase):
    def test_topic_requires_real_steps(self):
        with self.assertRaises(ValueError):
            plan_topic("電容器", [])
        board = plan_topic("電容器為什麼能通交流", ["平行板結構", "交流正負對調"])
        self.assertEqual(board["shots"][1]["narration"], "平行板結構")

    def test_blocks_generic_electricity_queries(self):
        shot = plan_lesson(get_lesson("ohms-law"))["shots"][0]
        for query in ("electricity", "lightning", "電工", "電力"):
            self.assertIn(query, BANNED_STOCK_QUERIES)
            with self.assertRaises(ValueError):
                assert_shot_searchable(shot, query)
        with self.assertRaises(ValueError):
            assert_shot_searchable(shot, "cool sparks tesla coil")
        assert_shot_searchable(shot, "歐姆定律 V=IR 電路圖")


class AssetPolicyTests(unittest.TestCase):
    def test_stock_must_mention_the_concept(self):
        shot = plan_lesson(get_lesson("ohms-law"))["shots"][0]
        self.assertTrue(candidate_matches("Lightning over a city", "stock electricity", shot))
        self.assertEqual(candidate_matches("歐姆定律 電路圖", "V=IR 歐姆定律", shot), [])

    def test_pick_stock_refuses_when_nothing_matches(self):
        shot = plan_lesson(get_lesson("ohms-law"))["shots"][0]
        fake_hits = [
            {
                "title": "File:Lightning.jpg",
                "description": "A thunderstorm",
                "url": "https://example.com/k.jpg",
                "mime": "image/jpeg",
            }
        ]
        with patch("tools.tutorial_video.assets.search_commons", return_value=fake_hits):
            with self.assertRaises(Exception) as ctx:
                pick_stock(shot, "歐姆定律 電路圖")
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

        board = plan_topic("測試歐姆", ["第一步"])
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
