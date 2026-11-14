"""The vision loop turns fall events into contract messages (no camera: keypoints fed directly)."""
import random

from camera_mode import VisionLoop
from contracts import validate
from mockroom import skeleton
from settings import load_vision_config
from vision.zones import Zones

CONFIG = load_vision_config()
DT = 1 / 15


def play(loop: VisionLoop, t: float, seconds: float, activity: str) -> float:
    rng = random.Random(3)
    for _ in range(round(seconds / DT)):
        loop._analyse(skeleton(activity, t, rng), t, t)
        t += DT
    return t


def make_loop(sent: list, zones: Zones | None = None) -> VisionLoop:
    return VisionLoop(None, CONFIG, sent.append, "living_room", show_window=False, zones=zones or Zones())


def test_fall_then_getting_up_sends_fall_detected_and_posture_updates():
    sent: list[dict] = []
    loop = make_loop(sent)
    t = play(loop, 0.0, 2, "standing")
    t = play(loop, t, 5, "fallen")       # the mock's lying-on-the-floor skeleton
    assert loop.result.label == "fallen" and loop.result.fall_state == "fallen"
    t = play(loop, t, 3, "standing")
    for message in sent:
        validate("room", message)
    assert [m["type"] for m in sent] == ["fall_detected", "posture_update", "posture_update"]
    fall, down, up = sent
    assert fall["reason"] == "fast_fall" and fall["incident_id"].startswith("inc_")
    assert down == {"type": "posture_update", "incident_id": fall["incident_id"], "activity": "fallen"}
    assert up["incident_id"] == fall["incident_id"] and up["activity"] in ("standing", "walking")
    assert loop.result.label != "fallen"


def test_no_posture_updates_without_a_fall():
    sent: list[dict] = []
    loop = make_loop(sent)
    t = play(loop, 0.0, 2, "standing")
    t = play(loop, t, 3, "sitting")
    play(loop, t, 2, "standing")
    assert sent == []


def test_lying_in_a_safe_zone_sends_nothing():
    sent: list[dict] = []
    everywhere = Zones([{"name": "bed", "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]]}])
    loop = make_loop(sent, everywhere)
    t = play(loop, 0.0, 2, "standing")
    play(loop, t, 6, "fallen")
    assert sent == []
    assert loop.result.zone == "bed" and loop.result.label == "lying"
