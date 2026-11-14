"""Feature tests (BUILD_PLAN step 2.2) with synthetic keypoints: standing, sitting, lying, motion."""
import random

import pytest

from mockroom import skeleton
from settings import load_vision_config
from vision.features import CORE, FeatureTracker

CONFIG = load_vision_config()
DT = 1 / 15


def pose(activity: str) -> list[list[float]]:
    return skeleton(activity, t=0.0, rng=random.Random(1))


def shifted(pts, dx: float = 0.0, dy: float = 0.0):
    return [[x + dx, y + dy, v] for x, y, v in pts]


def single(activity: str):
    return FeatureTracker(CONFIG).update(pose(activity), t=0.0)


def test_standing():
    f = single("standing")
    assert f.torso_deg < 10
    assert f.knee_deg > 160
    assert f.thigh_deg < 10
    assert f.bbox_ratio < 1
    assert 0.4 < f.hip_y < 0.6


def test_sitting():
    f = single("sitting")
    assert f.torso_deg < 30
    assert f.knee_deg < CONFIG["sitting_knee_deg"]
    assert f.thigh_deg > CONFIG["sitting_thigh_deg"]


@pytest.mark.parametrize("activity", ["lying", "fallen"])
def test_lying(activity):
    f = single(activity)
    assert f.torso_deg > CONFIG["lying_torso_deg"]
    assert f.bbox_ratio > 1
    assert f.hip_y > 0.7


def test_still_person_has_no_speed():
    tracker, f = FeatureTracker(CONFIG), None
    for i in range(15):
        f = tracker.update(pose("standing"), t=i * DT)
    assert abs(f.hip_speed_down) < 0.05 and f.hip_shift_1s < 0.05


def test_hip_speed_is_measured_in_body_heights_per_second():
    tracker, base = FeatureTracker(CONFIG), pose("standing")
    ref = tracker.update(base, t=0.0).body_height_px
    drop = 0.3  # image heights per second
    f = None
    for i in range(1, 10):
        f = tracker.update(shifted(base, dy=drop * i * DT), t=i * DT)
    assert f.hip_speed_down == pytest.approx(drop * CONFIG["frame_height"] / ref, rel=0.05)
    assert f.hip_speed_down > 0  # moving down


def test_rising_gives_negative_speed():
    tracker, base, f = FeatureTracker(CONFIG), pose("standing"), None
    for i in range(10):
        f = tracker.update(shifted(base, dy=-0.2 * i * DT), t=i * DT)
    assert f.hip_speed_down < 0


def test_walking_shift_in_body_widths():
    tracker, base, f = FeatureTracker(CONFIG), pose("standing"), None
    for i in range(16):  # 0.2 image widths in one second
        f = tracker.update(shifted(base, dx=0.2 * i * DT), t=i * DT)
    assert f.hip_shift_1s == pytest.approx(0.2 * CONFIG["frame_width"] / f.body_width_px, rel=0.1)
    assert f.hip_shift_1s > CONFIG["walking_hip_shift_bodywidths_per_s"]


def test_reference_height_remembers_the_standing_body():
    tracker = FeatureTracker(CONFIG)
    standing = tracker.update(pose("standing"), t=0.0)
    shrunk = [[0.5 + (x - 0.5) * 0.5, 0.5 + (y - 0.5) * 0.5, v] for x, y, v in pose("standing")]
    f = tracker.update(shrunk, t=1.0)  # foreshortened frame: shorter skeleton
    assert f.body_height_px < standing.body_height_px
    assert f.ref_height_px == pytest.approx(standing.body_height_px)
    later = tracker.update(shrunk, t=1.0 + CONFIG["scale_window_s"] + 0.1)
    assert later.ref_height_px == pytest.approx(later.body_height_px)


def test_hidden_core_or_no_person_gives_none():
    tracker = FeatureTracker(CONFIG)
    assert tracker.update(None, t=0.0) is None
    pts = pose("standing")
    pts[CORE[0]][2] = 0.1
    assert tracker.update(pts, t=0.1) is None


def test_less_certain_legs_still_count_but_torso_must_be_clear():
    between = (CONFIG["min_leg_visibility"] + CONFIG["min_keypoint_visibility"]) / 2
    pts = pose("sitting")
    for i in (25, 26, 27, 28):
        pts[i][2] = between
    f = FeatureTracker(CONFIG).update(pts, t=0.0)
    assert f.knee_deg is not None and f.knee_deg < CONFIG["sitting_knee_deg"]
    pts[CORE[0]][2] = between
    assert FeatureTracker(CONFIG).update(pts, t=0.0) is None


def test_hidden_legs_give_no_knee_angle():
    pts = pose("standing")
    for i in (25, 26, 27, 28):
        pts[i][2] = 0.1
    f = FeatureTracker(CONFIG).update(pts, t=0.0)
    assert f is not None and f.knee_deg is None
