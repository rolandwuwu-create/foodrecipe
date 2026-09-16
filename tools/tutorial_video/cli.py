"""CLI: plan a 電學小知識 short, then render it with Grok Imagine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .assemble import assemble_job, still_to_clip, probe_duration
from .assets import write_json
from .imagine import ImagineClient, ImagineError
from .lessons import get_lesson, load_lessons
from .planner import plan_lesson, plan_topic
from .script import srt_from_timeline, write_episode_docs
from .slides import render_beat
from .voice import VoiceError, synthesize

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "tutorial_video"


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text).strip("-")[:48] or "lesson"


def _job_dir(slug: str) -> Path:
    return OUT / slug


def _write_storyboard(storyboard: dict, job_dir: Path) -> Path:
    job_dir.mkdir(parents=True, exist_ok=True)
    return write_json(job_dir / "storyboard.json", storyboard)


def cmd_list(_: argparse.Namespace) -> int:
    for lesson in load_lessons():
        print(f"{lesson['id']:18}  {lesson['title']}")
    return 0


def _plan_from_args(args: argparse.Namespace) -> tuple[dict, Path]:
    if args.lesson:
        board = plan_lesson(get_lesson(args.lesson))
        slug = board["lesson_id"]
    elif args.topic:
        steps = [s.strip() for s in (args.steps or "").split("|") if s.strip()]
        board = plan_topic(args.topic, steps, hook=args.hook or "", jinju=getattr(args, "jinju", "") or "")
        slug = _slug(args.topic)
    else:
        raise SystemExit("plan needs --lesson or --topic")
    job_dir = Path(args.out) if getattr(args, "out", None) else _job_dir(slug)
    return board, job_dir


def cmd_plan(args: argparse.Namespace) -> int:
    board, job_dir = _plan_from_args(args)
    path = _write_storyboard(board, job_dir)
    write_episode_docs(board, job_dir)
    print(path)
    print(job_dir / "SCRIPT.md")
    print(f"{len(board['shots'])} shots  policy={board['asset_policy']}  {board['topic']}")
    for shot in board["shots"]:
        print(f"  {shot['id']}  {shot['role']:6}  {shot['narration']}")
    return 0


def _load_board(args: argparse.Namespace) -> tuple[dict, Path]:
    if args.job:
        job_dir = Path(args.job)
        board = json.loads((job_dir / "storyboard.json").read_text(encoding="utf-8"))
        return board, job_dir
    if args.lesson or args.topic:
        board, job_dir = _plan_from_args(args)
        _write_storyboard(board, job_dir)
        return board, job_dir
    raise SystemExit("render needs --lesson, --topic, or --job")


def cmd_render(args: argparse.Namespace) -> int:
    board, job_dir = _load_board(args)
    write_episode_docs(board, job_dir)
    print(job_dir / "SCRIPT.md")
    client = None
    if args.imagine:
        client = ImagineClient(
            poll_interval=args.poll_interval,
            poll_timeout=args.poll_timeout,
        )
    timeline: list[tuple[float, float, str]] = []
    t = 0.0
    for shot in board["shots"]:
        folder = job_dir / "shots" / shot["id"]
        still = render_beat(shot, folder / "still.png")
        if args.imagine and shot.get("source") == "imagine+overlay" and shot.get("image_prompt"):
            print(f"imagine hero {shot['id']} …", flush=True)
            try:
                hero = client.generate_image(shot["image_prompt"])
                client.save_bytes(hero, folder / "hero.jpg")
            except ImagineError as exc:
                print(f"  skip hero: {exc}")
        audio = None
        if not args.no_voice and shot.get("narration"):
            existing = folder / "vo.mp3"
            if existing.exists() and existing.stat().st_size >= 800:
                audio = existing
                print(f"  vo {shot['id']} reuse")
            else:
                print(f"  vo {shot['id']} …", flush=True)
                try:
                    audio = synthesize(shot["narration"], existing, voice=args.voice)
                except VoiceError as exc:
                    print(f"  voice failed: {exc}", file=sys.stderr)
                    return 1
        clip = folder / "clip.mp4"
        still_to_clip(
            still,
            clip,
            float(shot["duration_sec"]),
            zoom=shot.get("slide") in {"photo_title", "photo_caption"},
            audio=audio,
        )
        dur = probe_duration(clip)
        timeline.append((t, t + dur, shot["narration"]))
        t += dur
        print(f"  {shot['id']} {shot['role']}  {dur:.1f}s")
    (job_dir / "captions.srt").write_text(srt_from_timeline(timeline), encoding="utf-8")
    out = assemble_job(board, job_dir)
    print(out)
    print(f"total {t:.1f}s  script={job_dir / 'SCRIPT.md'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan and render 電學小知識 shorts with Grok Imagine."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="list built-in electrical lessons")
    p_list.set_defaults(func=cmd_list)

    p_plan = sub.add_parser("plan", help="write a locked shot list and 腳本, do not search stock")
    p_plan.add_argument("--lesson", help="built-in lesson id, e.g. skin-effect")
    p_plan.add_argument("--topic", help="new topic in 小東老師電子學 grammar")
    p_plan.add_argument("--hook", default="", help="opening line")
    p_plan.add_argument("--jinju", default="", help="金句")
    p_plan.add_argument("--steps", help="pipe-separated beats")
    p_plan.add_argument("--out", help="job directory")
    p_plan.set_defaults(func=cmd_plan)

    p_render = sub.add_parser("render", help="generate each shot with Imagine and concat")
    p_render.add_argument("--lesson", help="plan + render a built-in lesson")
    p_render.add_argument("--topic", help="plan + render a new topic")
    p_render.add_argument("--hook", default="")
    p_render.add_argument("--jinju", default="")
    p_render.add_argument("--steps", help="pipe-separated beats when using --topic")
    p_render.add_argument("--job", help="existing job directory with storyboard.json")
    p_render.add_argument("--out", help="job directory")
    p_render.add_argument("--resolution", default="720p")
    p_render.add_argument("--imagine", action="store_true", help="also generate Imagine hero (needs XAI_API_KEY)")
    p_render.add_argument("--no-voice", action="store_true", help="skip TTS (silent picture-in-picture)")
    p_render.add_argument("--voice", default="zh-TW-YunJheNeural", help="edge-tts voice")
    p_render.add_argument("--placeholders", action="store_true", help="deprecated; slides are the default")
    p_render.add_argument("--poll-interval", type=float, default=5)
    p_render.add_argument("--poll-timeout", type=float, default=600)
    p_render.set_defaults(func=cmd_render)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "plan" and not args.lesson and not args.topic:
        print("plan needs --lesson or --topic", file=sys.stderr)
        return 2
    return args.func(args)
