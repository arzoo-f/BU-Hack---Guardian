"""Skeleton picture tests (BUILD_PLAN step 3.7): drawn from keypoints only."""
import json
from io import BytesIO
from pathlib import Path

from PIL import Image

from snapshot import BACKGROUND, BONE, JOINT, SIZE, skeleton_png

POSE = json.loads((Path(__file__).resolve().parents[1] / "contracts" / "examples" / "valid" / "room.pose.json")
                  .read_text(encoding="utf-8"))["keypoints"]


def open_png(data: bytes) -> Image.Image:
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return Image.open(BytesIO(data)).convert("RGB")


def test_skeleton_is_drawn_where_the_keypoints_are():
    image = open_png(skeleton_png(POSE, caption="Living room · 10:07"))
    assert image.size == SIZE
    w, h = SIZE
    hip_x, hip_y = POSE[23][0] * w, POSE[23][1] * h
    assert image.getpixel((int(hip_x), int(hip_y))) == JOINT
    shoulder_mid = ((POSE[11][0] + POSE[23][0]) / 2 * w, (POSE[11][1] + POSE[23][1]) / 2 * h)
    assert image.getpixel((int(shoulder_mid[0]), int(shoulder_mid[1]))) == BONE   # on the left torso line
    assert image.getpixel((5, 5)) == BACKGROUND and image.getpixel((w - 5, 5)) == BACKGROUND


def test_only_keypoint_colours_and_background():
    image = open_png(skeleton_png(POSE))           # no caption: no anti-aliased text
    colours = {c for _, c in image.getcolors(maxcolors=100000)}
    assert BACKGROUND in colours and BONE in colours and JOINT in colours
    blends = colours - {BACKGROUND, BONE, JOINT}
    assert len(blends) < 50                          # only edge blending of lines and dots


def test_faint_points_are_skipped():
    faint = [[x, y, 0.1] for x, y, _ in POSE]
    image = open_png(skeleton_png(faint))
    assert {c for _, c in image.getcolors(maxcolors=100000)} == {BACKGROUND}


def test_no_keypoints_gives_a_note_not_an_error():
    image = open_png(skeleton_png(None, caption="Living room"))
    assert image.size == SIZE and image.getpixel((5, 5)) == BACKGROUND
