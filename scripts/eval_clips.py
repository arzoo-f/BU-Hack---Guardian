"""Run every recorded clip through the fall detector and print a results table (BUILD_PLAN step 2.6).

    .venv\\Scripts\\python.exe scripts\\eval_clips.py                    # the tuning set
    .venv\\Scripts\\python.exe scripts\\eval_clips.py --set test         # the fresh test set (Stage 8)
    .venv\\Scripts\\python.exe scripts\\eval_clips.py --write            # also update docs/accuracy.md
    .venv\\Scripts\\python.exe scripts\\eval_clips.py --no-zones         # show what the safe zones change
    .venv\\Scripts\\python.exe scripts\\eval_clips.py --trace tune_bend_02   # half-second detail of one clip

Pose detection runs once per clip and is cached in clips/.cache/ (keypoints only).
"""
import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "room-agent"))

from settings import load_vision_config  # noqa: E402
from vision.analyzer import VisionAnalyzer  # noqa: E402
from vision.clipdata import clip_keypoints  # noqa: E402
from vision.zones import Zones, load_zones  # noqa: E402

CLIPS_DIR = ROOT / "clips"
ACCURACY_MD = ROOT / "docs" / "accuracy.md"
SET_TITLES = {"tune": "Tuning set", "test": "Fresh test set",
              "test2": "Second fresh test set (falls only, starting from standing)"}


@dataclass
class ClipResult:
    name: str
    expected: str                 # fall | no_fall
    detected: str | None          # fast_fall | found_on_floor | None
    detect_t: float | None        # seconds into the clip
    after_landing: float | None   # seconds from going down to detection
    stumbles: int
    rested_in: str | None         # safe zone that kept a lying posture from counting (1 s or more)
    final_label: str | None

    @property
    def ok(self) -> bool:
        return (self.detected is not None) == (self.expected == "fall")


def expected_of(clip: Path) -> str:
    sidecar = clip.with_suffix(".json")
    if sidecar.exists():
        return json.loads(sidecar.read_text(encoding="utf-8")).get("expected", "no_fall")
    return "fall" if "_fall_" in clip.stem else "no_fall"


def evaluate(clip: Path, config: dict, zones: Zones, trace: bool = False) -> ClipResult:
    """Feed one clip's keypoints through the same analysis the live camera uses."""
    analyzer = VisionAnalyzer(config, zones)
    fall, stumbles, last, next_trace = None, 0, None, 0.0
    resting: dict[str, int] = {}
    for t, keypoints in clip_keypoints(clip, config):
        last = analyzer.update(keypoints, t)
        if last.posture == "resting":
            resting[last.zone] = resting.get(last.zone, 0) + 1
        for event in last.events:
            if event.kind == "fall_detected" and fall is None:
                fall = event
            stumbles += event.kind == "stumble"
            if trace:
                print(f"    {t:5.2f}s  EVENT {event.kind} {event.reason or ''} {event.features}")
        if trace and t >= next_trace:
            ratio = "  -  " if last.torso_ratio is None else f"{last.torso_ratio:+.2f}"
            f = last.features
            shape = "" if f is None else (f"torso {f.torso_deg:3.0f} box {f.bbox_ratio:4.2f} "
                                          f"head {'-' if f.head_rise is None else format(f.head_rise, '+.2f')}")
            print(f"    {t:5.2f}s  {last.label or '-':9s} posture {last.posture:8s} state {last.fall_state:9s} "
                  f"torso ratio {ratio}  zone {last.zone or '-':5s} {shape}")
            next_trace += 0.5
    return ClipResult(
        name=clip.stem, expected=expected_of(clip), detected=fall.reason if fall else None,
        detect_t=fall.t if fall else None,
        after_landing=fall.features["seconds_low"] if fall else None,
        stumbles=stumbles, final_label=last.label if last else None,
        rested_in=next((z for z, n in resting.items() if n >= config["target_fps"]), None))


def table(results: list[ClipResult]) -> list[str]:
    lines = ["| Clip | Expected | Detected | At (s into clip) | Seconds after landing | Result |",
             "| --- | --- | --- | --- | --- | --- |"]
    for r in results:
        note = "OK" if r.ok else ("MISSED" if r.expected == "fall" else "FALSE ALARM")
        if r.detected is None and r.rested_in:
            note += f" (resting in the {r.rested_in} zone)"
        if r.stumbles:
            note += f" ({r.stumbles} stumble logged)"
        lines.append(f"| {r.name} | {r.expected} | {r.detected or '-'} | "
                     f"{'-' if r.detect_t is None else format(r.detect_t, '.1f')} | "
                     f"{'-' if r.after_landing is None else format(r.after_landing, '.1f')} | {note} |")
    return lines


def summary(results: list[ClipResult]) -> str:
    falls = [r for r in results if r.expected == "fall"]
    normal = [r for r in results if r.expected != "fall"]
    caught = sum(r.detected is not None for r in falls)
    alarms = sum(r.detected is not None for r in normal)
    return f"{caught} of {len(falls)} falls caught; {alarms} false alarms in {len(normal)} normal clips"


def write_accuracy(clip_set: str, results: list[ClipResult], config: dict, zones: Zones) -> None:
    """Replace this set's section in docs/accuracy.md (other sections are kept)."""
    title = SET_TITLES.get(clip_set, clip_set)
    keys = ["model", "target_fps", "torso_upright_ratio", "bend_head_rise", "lying_torso_deg", "lying_box_ratio",
            "lying_head_rise", "fall_window_s", "fall_confirm_s", "fall_confirm_share", "slow_path_lying_s"]
    section = [
        f"## {title}", "",
        f"Evaluated {datetime.now().strftime('%a %d %b %Y, %H:%M')} with `scripts/eval_clips.py --set {clip_set}`.",
        "", f"**{summary(results)}.**", "", *table(results), "",
        "Settings used: " + ", ".join(f"`{k}` = {config[k]}" for k in keys) + ".",
        "Safe zones: " + (", ".join(z["name"] for z in zones.as_list()) or "none") + ".", "",
    ]
    marker = f"## {title}"
    old = ACCURACY_MD.read_text(encoding="utf-8") if ACCURACY_MD.exists() else "# Guardian - fall detection accuracy\n"
    head, _, rest = old.partition(marker)
    after = rest.partition("\n## ")[2]
    text = head.rstrip("\n") + "\n\n" + "\n".join(section) + ("\n## " + after if after else "")
    ACCURACY_MD.write_text(text.rstrip("\n") + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--set", default="tune", dest="clip_set", help="clip name prefix: tune (default), test or test2")
    p.add_argument("--no-zones", action="store_true", help="ignore the safe zones")
    p.add_argument("--write", action="store_true", help="update this set's section in docs/accuracy.md")
    p.add_argument("--trace", metavar="CLIP", help="print half-second detail for one clip (name without .mp4)")
    args = p.parse_args(argv)

    config = load_vision_config()
    zones = Zones() if args.no_zones else load_zones(config)
    if args.trace:
        clip = CLIPS_DIR / f"{args.trace}.mp4"
        if not clip.exists():
            print(f"No such clip: {clip}")
            return 1
        r = evaluate(clip, config, zones, trace=True)
        print(f"{r.name}: expected {r.expected}, detected {r.detected or 'nothing'}")
        return 0
    clips = sorted(CLIPS_DIR.glob(f"{args.clip_set}_*.mp4"))
    if not clips:
        print(f"No clips named {args.clip_set}_*.mp4 in {CLIPS_DIR}")
        return 1
    results = [evaluate(clip, config, zones) for clip in clips]
    print("\n".join(table(results)))
    print("\n" + summary(results))
    if args.write:
        write_accuracy(args.clip_set, results, config, zones)
        print(f"Written to {ACCURACY_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
