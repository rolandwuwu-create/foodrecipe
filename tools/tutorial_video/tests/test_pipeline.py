import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.tutorial_video.assemble import assemble_job, probe_duration, still_to_clip
from tools.tutorial_video.lessons import get_lesson
from tools.tutorial_video.planner import (
    BANNED_STOCK_QUERIES,
    assert_shot_searchable,
    plan_lesson,
    plan_topic,
)
from tools.tutorial_video.script import narration_full, script_markdown
from tools.tutorial_video.slides import render_beat
from tools.tutorial_video.voice import VoiceError, synthesize


class SkinEffectLessonTests(unittest.TestCase):
    def test_matches_xiaodong_episode_grammar(self):
        board = plan_lesson(get_lesson("skin-effect"))
        self.assertEqual(board["kind"], "xiaodong_explainer")
        self.assertEqual(board["jinju"], "高頻世界裡，粗電線的心是空的。")
        self.assertEqual(board["asset_policy"], "imagine_hero_then_slides")
        self.assertEqual(board["shots"][0]["source"], "imagine+overlay")
        self.assertEqual(board["shots"][0]["slide"], "photo_title")
        self.assertEqual(board["shots"][0]["photo"], "copper_hero_right.png")
        self.assertIn("no text", board["hero_prompt"])
        self.assertIn("no lightning", board["hero_prompt"])
        roles = [s["role"] for s in board["shots"]]
        self.assertEqual(roles[0], "title")
        self.assertIn("jinju", roles)
        self.assertEqual(roles[-1], "end")
        self.assertGreaterEqual(len(board["shots"]), 10)
        self.assertGreater(len(narration_full(board)), 400)


class ProximityLessonTests(unittest.TestCase):
    def test_is_a_full_episode_script(self):
        board = plan_lesson(get_lesson("proximity-effect"))
        self.assertEqual(board["jinju"], "旁邊那根線，也在偷你的電流。")
        self.assertEqual(board["shots"][0]["slide"], "photo_title")
        self.assertEqual(board["shots"][0]["photo"], "proximity_hero_right.png")
        photos = {s.get("photo") for s in board["shots"] if s.get("photo")}
        self.assertIn("proximity_section.png", photos)
        self.assertIn("transformer_pack.png", photos)
        self.assertGreaterEqual(len(board["shots"]), 12)
        script = script_markdown(board)
        self.assertIn("旁白全稿", script)
        self.assertIn("旁邊那根線，也在偷你的電流。", script)
        self.assertGreater(len(narration_full(board)), 700)


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

    def test_photo_title_is_cinematic_overlay(self):
        from PIL import Image

        board = plan_lesson(get_lesson("proximity-effect"))
        with tempfile.TemporaryDirectory() as tmp:
            path = render_beat(board["shots"][0], Path(tmp) / "title.png")
            with Image.open(path) as img:
                self.assertEqual(img.size, (1920, 1080))
            self.assertGreater(path.stat().st_size, 40000)

    def test_new_slide_kinds(self):
        from PIL import Image

        board = plan_lesson(get_lesson("proximity-effect"))
        kinds = {s["slide"] for s in board["shots"]}
        self.assertIn("bullets", kinds)
        self.assertIn("compare", kinds)
        self.assertIn("end", kinds)
        with tempfile.TemporaryDirectory() as tmp:
            for shot in board["shots"]:
                if shot["slide"] in {"bullets", "compare", "end", "text"}:
                    path = render_beat(shot, Path(tmp) / f"{shot['id']}.png")
                    with Image.open(path) as img:
                        self.assertEqual(img.size, (1920, 1080))


class AssembleTests(unittest.TestCase):
    def test_slides_concat_to_mp4(self):
        board = plan_lesson(get_lesson("skin-effect"))
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            for shot in board["shots"][:3]:
                still = render_beat(shot, job / "shots" / shot["id"] / "still.png")
                still_to_clip(still, job / "shots" / shot["id"] / "clip.mp4", 1)
            short = {
                **board,
                "shots": board["shots"][:3],
            }
            out = assemble_job(short, job)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 5000)

    def test_muxes_voice_track(self):
        board = plan_lesson(get_lesson("proximity-effect"))
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            shot = board["shots"][0]
            still = render_beat(shot, job / "still.png")
            wav = job / "vo.wav"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=1.2",
                    str(wav),
                ],
                check=True,
                capture_output=True,
            )
            clip = still_to_clip(still, job / "clip.mp4", 2, audio=wav)
            self.assertGreater(probe_duration(clip), 1.4)


class VoiceTests(unittest.TestCase):
    def test_empty_narration_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(VoiceError):
                synthesize("   ", Path(tmp) / "x.mp3")


if __name__ == "__main__":
    unittest.main()
