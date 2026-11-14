"""Replay a recorded clip through the room agent pipeline (thin wrapper around main.py --clip).

    .venv\\Scripts\\python.exe scripts\\replay_clip.py clips\\tune_fall_forward_01.mp4
    .venv\\Scripts\\python.exe scripts\\replay_clip.py clips\\tune_bend_01.mp4 --fast --no-window

Any extra options are passed to room-agent/main.py (for example --server, --log-frames).
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("clip", help="path to an .mp4 recorded by record_clips.py")
    args, extra = p.parse_known_args()
    clip = Path(args.clip).resolve()
    if not clip.exists():
        print(f"No such clip: {clip}")
        return 1
    cmd = [sys.executable, str(ROOT / "room-agent" / "main.py"), "--clip", str(clip), *extra]
    return subprocess.call(cmd, cwd=ROOT / "room-agent")


if __name__ == "__main__":
    sys.exit(main())
