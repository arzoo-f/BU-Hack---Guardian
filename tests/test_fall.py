"""Fall state machine tests (BUILD_PLAN step 2.5) with synthetic feature sequences.

The posture numbers are modelled on the tuning clips recorded in the final room (docs/accuracy.md).
"""
import pytest

from settings import load_vision_config
from vision.fall import CANDIDATE, FALLEN, IDLE, FallDetector, UprightReference
from vision.features import Features
from vision.zones import Zones, load_zones, point_in_polygon

CONFIG = load_vision_config()
DT = 1 / 15

STANDING: dict = {}
LOOKING_DOWN = dict(head_rise=1.15)  # standing with the head lowered: not the textbook upright shape
KNEELING = dict(torso_deg=8, bbox_ratio=0.34, head_rise=1.0, thigh_deg=9, torso_len_px=70, torso_rise_px=69,
                feet_below_hips_px=70, hip_y=0.50)
SITTING = dict(torso_deg=15, bbox_ratio=0.55, head_rise=1.4, knee_deg=107, thigh_deg=47, torso_len_px=70,
               torso_rise_px=68, hip_y=0.47)
LYING_ACROSS = dict(torso_deg=63, bbox_ratio=1.55, head_rise=0.74, thigh_deg=56, torso_len_px=60,
                    torso_rise_px=27, feet_below_hips_px=20, hip_y=0.66)
LYING_HEAD_AWAY = dict(torso_deg=3, bbox_ratio=0.70, head_rise=1.27, thigh_deg=23, torso_len_px=38,
                       torso_rise_px=31, feet_below_hips_px=90, hip_y=0.67)
LYING_HEAD_NEAR = dict(torso_deg=10, bbox_ratio=0.70, head_rise=-1.2, knee_deg=None, thigh_deg=None,
                       torso_len_px=40, torso_rise_px=-38, feet_below_hips_px=-80, hip_y=0.60)
BENDING = dict(torso_deg=70, bbox_ratio=0.63, head_rise=-0.8, thigh_deg=None, torso_len_px=65,
               torso_rise_px=-20, feet_below_hips_px=150)
SQUAT_BEND = dict(torso_deg=6, bbox_ratio=0.65, head_rise=0.49, thigh_deg=13, torso_len_px=34,
                  torso_rise_px=36, feet_below_hips_px=40)
SHORT_BUT_UPRIGHT_SHAPE = dict(torso_deg=3, bbox_ratio=0.55, head_rise=1.33, thigh_deg=15, torso_len_px=38,
                               torso_rise_px=36, feet_below_hips_px=90)  # lying along the line of sight
ON_SOFA = {**LYING_ACROSS, "hip_x": 0.45, "hip_y": 0.39}
UNCLEAR = "unclear"   # a person is seen, but not clearly enough for features
NOBODY = "nobody"


def feat(t: float, **overrides) -> Features:
    base = dict(t=t, hip_x=0.35, hip_y=0.40, body_height_px=330.0, ref_height_px=330.0, body_width_px=60.0,
                torso_deg=3.0, bbox_ratio=0.30, head_rise=1.40, knee_deg=176.0, thigh_deg=3.0,
                hip_speed_down=0.0, hip_shift_1s=0.0, torso_len_px=100.0, torso_rise_px=100.0,
                feet_below_hips_px=150.0, in_view=True)
    return Features(**{**base, **overrides})


class Film:
    """Plays scripted postures through a detector at 15 FPS and collects the events."""

    def __init__(self, zones: Zones | None = None) -> None:
        self.detector = FallDetector(CONFIG, zones)
        self.t = 0.0
        self.events = []

    def play(self, seconds: float, posture) -> "Film":
        for _ in range(round(seconds / DT)):
            if posture == NOBODY:
                found = self.detector.update(None, self.t, person_seen=False)
            elif posture == UNCLEAR:
                found = self.detector.update(None, self.t, person_seen=True)
            else:
                found = self.detector.update(feat(self.t, **posture), self.t)
            self.events += found
            self.t += DT
        return self

    def kinds(self) -> list[str]:
        return [e.kind for e in self.events]

    def falls(self) -> list:
        return [e for e in self.events if e.kind == "fall_detected"]


@pytest.mark.parametrize("lying", [LYING_ACROSS, LYING_HEAD_AWAY, LYING_HEAD_NEAR],
                         ids=["across", "head away from camera", "head towards camera"])
def test_fall_in_any_direction_is_detected_3s_after_landing(lying):
    film = Film().play(2, STANDING).play(0.8, KNEELING)   # a safe fall: kneel first, then roll
    landed = film.t
    film.play(2.5, lying)
    assert film.falls() == [] and film.detector.state == CANDIDATE
    film.play(2, lying)
    (fall,) = film.falls()
    assert fall.reason == "fast_fall"
    assert CONFIG["fall_confirm_s"] <= fall.t - landed <= CONFIG["fall_confirm_s"] + 0.2
    assert set(fall.features) == {"drop_speed", "torso_angle", "torso_ratio", "seconds_low"}
    assert film.detector.fallen


def test_up_again_within_3s_is_a_stumble_not_a_fall():
    film = Film().play(2, STANDING).play(1.5, LYING_ACROSS).play(2, STANDING)
    assert film.kinds() == ["stumble"]
    assert film.detector.state == IDLE


@pytest.mark.parametrize("posture", [BENDING, SQUAT_BEND, KNEELING, SITTING],
                         ids=["bend", "squat bend", "kneel", "fast sit"])
def test_normal_movements_are_not_falls(posture):
    film = Film().play(2, STANDING).play(8, posture).play(2, STANDING)
    assert film.falls() == []
    assert "stumble" not in film.kinds()


def test_slow_lie_down_is_found_on_floor_after_60s_not_a_fast_fall():
    film = Film().play(2, STANDING).play(5, KNEELING)   # sits on the mat first, taking 5 s
    lay_down = film.t
    film.play(59, LYING_ACROSS)
    assert film.falls() == []
    film.play(3, LYING_ACROSS)
    (fall,) = film.falls()
    assert fall.reason == "found_on_floor"
    assert 60 <= fall.t - lay_down <= 61
    assert fall.features["drop_speed"] is None and fall.features["seconds_low"] >= 60


def test_bent_over_for_a_whole_minute_is_also_found():
    film = Film().play(2, STANDING).play(62, BENDING)
    assert [f.reason for f in film.falls()] == ["found_on_floor"]


def test_lying_in_a_safe_zone_is_resting():
    zones = Zones([{"name": "sofa", "polygon": [[0.36, 0.32], [0.56, 0.32], [0.56, 0.46], [0.36, 0.46]]}])
    film = Film(zones).play(2, STANDING).play(70, ON_SOFA)
    assert film.events == []
    assert film.detector.posture == "resting" and film.detector.zone == "sofa"
    # the same posture on the floor, outside the zone, is a fall
    assert Film(zones).play(2, STANDING).play(4, LYING_ACROSS).falls() != []


def test_fallen_until_upright_again_then_ready_for_the_next_fall():
    film = Film().play(2, STANDING).play(10, LYING_ACROSS)
    assert len(film.falls()) == 1 and film.detector.state == FALLEN   # no repeats while down
    film.play(0.5, STANDING)
    assert film.detector.fallen                                        # not up for long enough yet
    film.play(1, STANDING)
    assert film.kinds() == ["fall_detected", "recovered"] and film.detector.state == IDLE
    film.play(2, STANDING).play(4, LYING_HEAD_AWAY)
    assert len(film.falls()) == 2


def test_sitting_up_on_the_floor_after_a_fall_is_still_fallen():
    film = Film().play(2, STANDING).play(4, LYING_ACROSS).play(20, KNEELING)
    assert film.detector.fallen and "recovered" not in film.kinds()


def test_standing_with_the_head_down_still_counts_as_upright():
    film = Film().play(2, STANDING).play(6, LOOKING_DOWN)
    assert film.detector.posture == "up"
    film.play(4, LYING_ACROSS)
    assert [f.reason for f in film.falls()] == ["fast_fall"]


def test_short_unclear_gaps_do_not_cancel_a_fall_but_leaving_does():
    film = Film().play(2, STANDING).play(1, LYING_ACROSS).play(0.5, UNCLEAR).play(2, LYING_ACROSS)
    assert len(film.falls()) == 1
    gone = Film().play(2, STANDING).play(1, LYING_ACROSS).play(3, NOBODY).play(1, LYING_ACROSS)
    assert gone.falls() == [] and gone.detector.state == IDLE


def test_body_at_the_image_edge_is_ignored():
    film = Film().play(2, STANDING).play(5, {**LYING_ACROSS, "in_view": False})
    assert film.events == [] and film.detector.posture == "unknown"


def test_lying_along_the_line_of_sight_cannot_pass_as_a_short_standing_person():
    film = Film().play(2, STANDING).play(4, SHORT_BUT_UPRIGHT_SHAPE)
    assert film.detector.ref.value == 100            # reference not dragged down
    assert [f.reason for f in film.falls()] == ["fast_fall"]


def test_reference_re_anchors_when_a_new_size_lasts():
    ref = UprightReference(CONFIG)
    t = 0.0
    for _ in range(30):
        assert ref.update(feat(t), t)
        t += DT
    small = dict(torso_len_px=50.0, torso_rise_px=50.0)   # stood up again much further away
    results = []
    for _ in range(round((CONFIG["upright_reanchor_s"] + 1) / DT)):
        results.append(ref.update(feat(t, **small), t))
        t += DT
    assert results[0] is False and results[-1] is True
    assert ref.value == 50


def test_without_an_upright_reference_the_plain_lying_rules_still_work():
    film = Film().play(62, LYING_ACROSS)   # never seen standing, e.g. Guardian started late
    assert [f.reason for f in film.falls()] == ["found_on_floor"]


def test_point_in_polygon():
    square = [(0.2, 0.2), (0.6, 0.2), (0.6, 0.6), (0.2, 0.6)]
    assert point_in_polygon(0.4, 0.4, square)
    assert not point_in_polygon(0.7, 0.4, square) and not point_in_polygon(0.4, 0.1, square)
    triangle = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    assert point_in_polygon(0.2, 0.2, triangle) and not point_in_polygon(0.8, 0.8, triangle)


def test_configured_zones_cover_the_sofa_but_not_the_mat():
    zones = load_zones(CONFIG)                  # the zone Person A drew in CP8.2
    assert zones.at(0.49, 0.43) == "sofa"       # hip centre while lying on the sofa (Sat test_lie_sofa clips)
    assert zones.at(0.36, 0.56) is None         # hip centre after a fall on the mat (Sat test2 clips)
    assert zones.at(0.35, 0.66) is None         # and where the Friday falls landed
    assert Zones().at(0.49, 0.43) is None
