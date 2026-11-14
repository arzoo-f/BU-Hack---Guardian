"""Keypoints of a recorded clip, exactly as the live pipeline would see them (same frame pacing).

Pose detection is the slow part of replaying a clip, so the result is cached next to the clips
in clips/.cache/ (git-ignored like the clips; keypoints only, never pixels). The cache is
ignored when the clip, the pose model or the frame settings change.
"""
import json
from pathlib import Path

from settings import model_path
from vision.pose import Keypoints, PoseDetector
from vision.sources import ClipSource, FramePacer

TimedKeypoints = list[tuple[float, Keypoints | None]]


def _cache_key(clip: Path, config: dict) -> dict:
    stat = clip.stat()
    return {"model": config["model"], "target_fps": config["target_fps"],
            "size": [config["frame_width"], config["frame_height"]],
            "clip_bytes": stat.st_size, "clip_mtime": int(stat.st_mtime)}


def clip_keypoints(clip: Path | str, config: dict, use_cache: bool = True) -> TimedKeypoints:
    """(t, keypoints or None) for every frame the live pipeline would process."""
    clip = Path(clip)
    cache = clip.parent / ".cache" / f"{clip.stem}.json"
    key = _cache_key(clip, config)
    if use_cache and cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("key") == key:
            return [(t, kp) for t, kp in data["frames"]]

    source = ClipSource(clip, config["frame_width"], config["frame_height"])
    if not source.open():
        raise FileNotFoundError(f"cannot open clip {clip}")
    detector = PoseDetector(model_path(config))
    pacer = FramePacer(config["target_fps"])
    frames: TimedKeypoints = []
    try:
        while (item := source.read()) is not None:
            frame, t = item
            if pacer.accept(t):
                frames.append((t, detector.detect(frame, int(t * 1000))))
    finally:
        source.release()
        detector.close()
    cache.parent.mkdir(exist_ok=True)
    cache.write_text(json.dumps({"key": key, "frames": frames}), encoding="utf-8")
    return frames
