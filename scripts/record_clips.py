"""Record tuning or test clips for fall detection (BUILD_PLAN step 2.4, CP2.3 and CP8.4).

For each clip the window says what to do next, gives time to get into position, counts down
and records 10 s. It saves clips/<set>_<label>_<nn>.mp4 plus a .json with the time of every
frame. Clips that already exist are skipped, so an interrupted session can simply be restarted.
Clips stay on this laptop: clips/ is git-ignored and never uploaded.

    .venv\\Scripts\\python.exe scripts\\record_clips.py --set tune                 # all 14 tuning clips
    .venv\\Scripts\\python.exe scripts\\record_clips.py --set tune --only normal   # the 8 no-fall clips
    .venv\\Scripts\\python.exe scripts\\record_clips.py --set test                 # fresh test set (Stage 8)
    .venv\\Scripts\\python.exe scripts\\record_clips.py --set tune --only normal --max 1   # one clip as a test

Keys in the window: SPACE start now, P pause, R redo the last clip, S skip this clip, Q quit.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "room-agent"))

import cv2  # noqa: E402

from vision import debug_view  # noqa: E402
from vision.pose import Camera  # noqa: E402

CLIPS_DIR = ROOT / "clips"
RECORD_S = 10.0
COUNTDOWN_S = 5.0
PREPARE_S = {"first": 12.0, "after_fall": 25.0, "after_normal": 12.0}

INSTRUCTIONS = {
    # "Stand until GO!": in the first fresh set 4 of 6 falls began already kneeling, so the camera
    # never saw the person upright (docs/accuracy.md).
    "fall_forward": "STAND until GO! Then SAFE FALL FORWARD onto the mat - kneel, then roll. Stay down 5 s.",
    "fall_backward": "STAND until GO! Then SAFE FALL BACKWARD onto the mat - sit/kneel, roll back. Stay down 5 s.",
    "fall_sideways": "STAND until GO! Then SAFE FALL SIDEWAYS onto the mat - kneel, then roll. Stay down 5 s.",
    "fast_sit": "SIT DOWN FAST on the chair, then stay seated.",
    "lie_sofa": "LIE DOWN on the sofa or bed, then stay there.",
    "bend": "BEND DOWN to pick something up, then stand up.",
    "kneel": "KNEEL on the floor for a few seconds, then stand up.",
}
SETS = {  # BUILD_PLAN CP2.3 (tuning) and CP8.4 (fresh test set)
    "tune": [("fall_forward", 2), ("fall_backward", 2), ("fall_sideways", 2),
             ("fast_sit", 2), ("lie_sofa", 2), ("bend", 2), ("kneel", 2)],
    "test2": [("fall_forward", 2), ("fall_backward", 2), ("fall_sideways", 2)],   # falls only, see above
    "test": [("fall_forward", 2), ("fall_backward", 2), ("fall_sideways", 2),
             ("fast_sit", 2), ("lie_sofa", 2), ("bend", 1), ("kneel", 1)],
}


def is_fall(label: str) -> bool:
    return label.startswith("fall_")


def plan_clips(clip_set: str, only: str | None = None) -> list[tuple[str, Path]]:
    """(label, path) for every clip in the set, falls first, optionally only falls or normal."""
    clips = []
    for label, count in SETS[clip_set]:
        if only == "falls" and not is_fall(label) or only == "normal" and is_fall(label):
            continue
        clips += [(label, CLIPS_DIR / f"{clip_set}_{label}_{n:02d}.mp4") for n in range(1, count + 1)]
    return clips


class Recorder:
    """Shows instructions on the live image and records clips without the text burned in."""

    def __init__(self, camera: Camera) -> None:
        self.camera = camera
        self.paused = False

    def wait(self, seconds: float, lines: list[str], colour=debug_view.BLUE) -> str | None:
        """Show the live image with text for `seconds`; returns a key action or None."""
        end = time.monotonic() + seconds
        while time.monotonic() < end or self.paused:
            frame = self.camera.read()
            if frame is None:
                continue
            left = max(end - time.monotonic(), 0)
            shown = ["PAUSED - press P to continue"] if self.paused else [*lines, f"{left:.0f} s"]
            debug_view.draw_text(frame, shown, origin=(10, 40), scale=0.7, colour=colour)
            key = debug_view.show(frame)
            if key == ord("p"):
                self.paused = not self.paused
                end = time.monotonic() + seconds if not self.paused else end
            elif key == ord(" "):
                return "start"
            elif key in (ord("q"), ord("r"), ord("s")):
                return {"q": "quit", "r": "redo", "s": "skip"}[chr(key)]
        return None

    def record(self, path: Path, label: str, clip_set: str) -> int:
        """Record RECORD_S seconds to path (+ .json with frame times). Returns frames written."""
        frames, times = [], []
        start = time.monotonic()
        while (now := time.monotonic()) - start < RECORD_S:
            frame = self.camera.read()
            if frame is None:
                continue
            frames.append(frame)
            times.append(round(now - start, 4))
            shown = frame.copy()  # the saved frame never carries the text
            debug_view.draw_text(shown, ["GO!"], origin=(10, 60), scale=1.6, colour=debug_view.RED)
            debug_view.draw_text(shown, [INSTRUCTIONS[label], f"RECORDING  {RECORD_S - (now - start):.0f} s"],
                                 origin=(10, 110), scale=0.7, colour=debug_view.RED)
            if debug_view.show(shown) == ord("q"):
                break
        fps = (len(times) - 1) / (times[-1] - times[0]) if len(times) > 1 else 15.0
        path.parent.mkdir(exist_ok=True)
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps,
                                 (self.camera.width, self.camera.height))
        for frame in frames:
            writer.write(frame)
        writer.release()
        path.with_suffix(".json").write_text(json.dumps({
            "set": clip_set, "label": label, "expected": "fall" if is_fall(label) else "no_fall",
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fps_measured": round(fps, 2), "frame_times": times,
        }, indent=1), encoding="utf-8")
        return len(frames)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--set", choices=sorted(SETS), default="tune", dest="clip_set")
    p.add_argument("--only", choices=["falls", "normal"], help="record only the falls or only the normal clips")
    p.add_argument("--max", type=int, help="record at most this many clips this time")
    p.add_argument("--camera", type=int, default=0)
    args = p.parse_args(argv)

    todo = [(label, path) for label, path in plan_clips(args.clip_set, args.only) if not path.exists()]
    todo = todo[:args.max] if args.max else todo
    if not todo:
        print("All clips in this set are already recorded.")
        return 0
    camera = Camera(args.camera)
    if not camera.open():
        print(f"Camera {args.camera} could not be opened.")
        return 1
    recorder, done, i, previous = Recorder(camera), [], 0, None
    print(f"{len(todo)} clips to record. Safe falls: kneel first, then roll onto the mat. Stop if anything hurts.")
    try:
        while i < len(todo):
            label, path = todo[i]
            prepare = PREPARE_S["first" if previous is None else "after_fall" if is_fall(previous) else "after_normal"]
            header = f"Clip {i + 1} of {len(todo)}: {path.stem}"
            safety = ["Kneel first, then roll. Stop if anything hurts."] if is_fall(label) else []
            action = recorder.wait(prepare, [header, "GET READY for: " + INSTRUCTIONS[label], *safety,
                                             "Get into position - wait for GO, do not start yet"])
            if action is None or action == "start":
                action = recorder.wait(COUNTDOWN_S, [header, "GET READY for: " + INSTRUCTIONS[label],
                                                     "GO in..."], colour=debug_view.ORANGE)
            if action == "quit":
                break
            if action == "skip":
                print(f"skipped {path.name}")
                i += 1
                continue
            if action == "redo" and done:
                i -= 1  # go back to the clip just recorded and overwrite it
                done.pop()
                continue
            n = recorder.record(path, label, args.clip_set)
            print(f"saved {path.name} ({n} frames)")
            done.append(path)
            previous = label
            i += 1
        recorder.wait(3, ["All done - thank you!"] if i >= len(todo) else ["Stopped"])
    finally:
        camera.release()
        debug_view.close()
    print(f"Recorded {len(done)} clip(s) in {CLIPS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
