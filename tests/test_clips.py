"""Clip recorder and replay tests (BUILD_PLAN step 2.4), using synthetic clips with no person."""
import json
from collections import Counter

import cv2
import numpy as np
import pytest

import record_clips
from camera_mode import VisionLoop
from contracts import validate
from settings import load_vision_config
from vision.sources import ClipSource, LoopingClipSource

CONFIG = load_vision_config()


def write_clip(path, n: int = 30, fps: float = 20.0, times: list[float] | None = None):
    """A small synthetic clip: plain frames whose brightness changes, plus an optional sidecar."""
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (640, 480))
    for i in range(n):
        writer.write(np.full((480, 640, 3), (i * 8) % 256, dtype=np.uint8))
    writer.release()
    if times is not None:
        path.with_suffix(".json").write_text(json.dumps({"label": "bend", "frame_times": times}))
    return path


def read_all(source):
    assert source.open()
    out = []
    while (item := source.read()) is not None:
        out.append(item)
    source.release()
    return out


def test_clip_times_come_from_the_sidecar(tmp_path):
    times = [round(i * 0.047, 3) for i in range(30)]  # an uneven, camera-like 21 FPS
    frames = read_all(ClipSource(write_clip(tmp_path / "a.mp4", times=times), 640, 480))
    assert len(frames) == 30
    assert [t for _, t in frames] == times
    assert frames[0][0].shape == (480, 640, 3)


def test_clip_times_fall_back_to_the_header_fps(tmp_path):
    frames = read_all(ClipSource(write_clip(tmp_path / "b.mp4", n=10, fps=20.0), 640, 480))
    assert [round(t, 3) for _, t in frames] == [round(i / 20, 3) for i in range(10)]


def test_looping_clip_keeps_time_counting_up(tmp_path):
    source = LoopingClipSource(write_clip(tmp_path / "l.mp4", n=4, fps=20.0), 640, 480)
    assert source.open()
    times = [round(source.read()[1], 3) for _ in range(10)]
    source.release()
    assert times == [round(i * 0.05, 3) for i in range(10)] and source.rounds == 2


def test_missing_clip_does_not_open(tmp_path):
    assert ClipSource(tmp_path / "nope.mp4", 640, 480).open() is False


def test_tuning_set_matches_the_plan():
    clips = record_clips.plan_clips("tune")
    counts = Counter(label for label, _ in clips)
    assert sum(counts.values()) == 14
    assert sum(c for label, c in counts.items() if record_clips.is_fall(label)) == 6
    assert clips[0][1].name == "tune_fall_forward_01.mp4"
    assert len(record_clips.plan_clips("tune", only="normal")) == 8
    assert len(record_clips.plan_clips("tune", only="falls")) == 6
    assert len(record_clips.plan_clips("test")) == 12  # CP8.4: 6 falls + 6 normal


def test_every_label_has_an_instruction():
    labels = {label for clips in record_clips.SETS.values() for label, _ in clips}
    assert labels <= set(record_clips.INSTRUCTIONS)


def test_vision_loop_replays_a_clip_with_no_person(tmp_path):
    times = [round(i / 20, 3) for i in range(60)]  # 3 s at 20 FPS
    sent = []
    loop = VisionLoop(ClipSource(write_clip(tmp_path / "c.mp4", n=60, times=times), 640, 480),
                      CONFIG, sent.append, "living_room", show_window=False)
    loop.run()
    for message in sent:
        validate("room", message)
    kinds = Counter(m["type"] for m in sent)
    assert kinds["status"] >= 1 and kinds["activity"] >= 1 and kinds["pose"] == 0
    assert {m["activity"] for m in sent if m["type"] == "activity"} == {"absent"}
    assert 40 <= loop.frames <= 46  # 3 s paced to about 15 FPS


def test_c_makes_the_camera_look_unplugged(tmp_path):
    """CP8.5 with a built-in camera: C in the debug window means no analysis and status 'offline'."""
    times = [round(i / 20, 3) for i in range(60)]
    sent = []
    loop = VisionLoop(ClipSource(write_clip(tmp_path / "off.mp4", n=60, times=times), 640, 480),
                      CONFIG, sent.append, "living_room", show_window=False)
    assert loop.handle_key(ord("c")) is False and loop.camera_off
    loop.run()
    assert loop.frames == 0                                   # nothing was analysed
    assert sent and all(m["type"] == "status" and m["camera"] == "offline" for m in sent)
    loop.handle_key(ord("c"))
    assert not loop.camera_off and loop.handle_key(ord("q")) is True
