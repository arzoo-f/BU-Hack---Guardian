"""Activity label tests (BUILD_PLAN step 2.3): rules, majority vote, tracker, CP2.2 guide."""
import random

from guide import Guide
from mockroom import skeleton
from settings import load_vision_config
from vision.activity import ActivityTracker, ActivityVoter, classify
from vision.features import Features, FeatureTracker

CONFIG = load_vision_config()
DT = 1 / 15


def pose(activity: str, dx: float = 0.0):
    return [[x + dx, y, v] for x, y, v in skeleton(activity, t=0.0, rng=random.Random(2))]


def label_of(activity: str) -> str | None:
    return classify(FeatureTracker(CONFIG).update(pose(activity), 0.0), True, CONFIG)


def test_rules_per_frame():
    assert label_of("standing") == "standing"
    assert label_of("sitting") == "sitting"
    assert label_of("lying") == "lying"
    assert classify(None, False, CONFIG) == "absent"
    assert classify(None, True, CONFIG) is None  # person seen, but not clearly


def features(**overrides) -> Features:
    base = dict(t=0.0, hip_x=0.5, hip_y=0.5, body_height_px=300.0, ref_height_px=300.0, body_width_px=60.0,
                torso_deg=3.0, bbox_ratio=0.3, head_rise=1.45, knee_deg=178.0, thigh_deg=3.0,
                hip_speed_down=0.0, hip_shift_1s=0.0)
    return Features(**{**base, **overrides})


def test_lying_towards_or_away_from_the_camera():
    # CP2.2 in the final room: head away from the camera, torso only 51-59 deg in the image
    assert classify(features(torso_deg=59, bbox_ratio=1.39, head_rise=0.78), True, CONFIG) == "lying"
    assert classify(features(torso_deg=51, bbox_ratio=1.18, head_rise=1.01, knee_deg=95), True, CONFIG) == "lying"
    assert classify(features(torso_deg=40, bbox_ratio=1.3, head_rise=None), True, CONFIG) == "lying"


def test_wide_but_upright_is_not_lying():
    # arms spread wide: the box is wide, but the head is high above the hips
    assert classify(features(bbox_ratio=1.2, head_rise=1.45), True, CONFIG) == "standing"
    assert classify(features(torso_deg=15, bbox_ratio=0.55, head_rise=1.43, knee_deg=107), True, CONFIG) == "sitting"


def test_sitting_from_the_thighs_when_the_knee_looks_straight_or_ankles_are_hidden():
    # final room: knee looked 130+ deg from this angle, but thighs pointed 46-49 deg from straight down
    assert classify(features(torso_deg=13, knee_deg=135, thigh_deg=46, head_rise=1.4), True, CONFIG) == "sitting"
    assert classify(features(torso_deg=13, knee_deg=None, thigh_deg=49, head_rise=1.4), True, CONFIG) == "sitting"
    assert classify(features(thigh_deg=4, knee_deg=173), True, CONFIG) == "standing"  # walking stride
    assert classify(features(thigh_deg=None, knee_deg=None), True, CONFIG) == "standing"


def test_walking_needs_sideways_movement():
    tracker, label = FeatureTracker(CONFIG), None
    for i in range(16):  # 0.2 image widths in one second, well over 0.3 body-widths
        label = classify(tracker.update(pose("standing", dx=0.2 * i * DT), i * DT), True, CONFIG)
    assert label == "walking"


def test_vote_is_a_majority_and_ignores_unclear_frames():
    voter = ActivityVoter(5)
    for lab in ["standing"] * 3 + [None, None]:
        voter.add(lab)
    assert voter.add("lying") == ("standing", 0.75)
    voter.add("lying")
    label, share = voter.add("lying")  # window: standing x2, lying x3
    assert (label, share) == ("lying", 0.6)


def test_vote_keeps_the_current_label_on_a_tie():
    voter = ActivityVoter(4)
    for lab in ["sitting", "sitting", "standing", "standing"]:
        voter.add(lab)
    assert voter.label == "sitting"


def test_tracker_switches_after_about_half_a_second():
    tracker = ActivityTracker(CONFIG)
    t = 0.0
    for _ in range(20):
        result = tracker.update(pose("standing"), t)
        t += DT
    assert result.label == "standing"
    switched_after = None
    for i in range(20):
        result = tracker.update(pose("lying"), t)
        t += DT
        if result.label == "lying" and switched_after is None:
            switched_after = i + 1
    assert result.label == "lying" and result.confidence == 1.0
    assert 6 <= switched_after <= 9  # majority of 15 frames: about half a second


def test_tracker_absent_when_nobody_is_there():
    tracker = ActivityTracker(CONFIG)
    result = None
    for i in range(20):
        result = tracker.update(None, i * DT)
    assert result.label == "absent" and result.features is None


def test_guide_judges_each_step_on_its_later_part():
    steps = [(10, "1/2  STAND STILL", "standing"), (10, "2/2  SIT", "sitting"), (5, "done", None)]
    guide = Guide(steps)
    assert guide.total == 25 and guide.step_at(12) == 1 and guide.step_at(30) is None
    for i in range(250):
        t = i * 0.1
        label = "standing" if t < 13 else "sitting"  # slow to sit down: still standing early in step 2
        guide.record(t, label)
    rows = guide.summary()
    assert [(r[1], r[2], r[4]) for r in rows] == [("standing", "standing", True), ("sitting", "sitting", True)]
    assert rows[1][3] == 1.0  # the transition at 10-13 s falls before the judged part
