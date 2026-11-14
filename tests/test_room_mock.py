"""Room agent mock-mode tests (BUILD_PLAN step 1.5): fake skeleton, timeline, commands, link."""
import math
from collections import Counter

import pytest

from commands import CommandHandler
from contracts import validate
from mockroom import MockRoom, skeleton
from server_link import ServerLink, ws_url
from voice.stub import StubVoice


class FakeClock:
    """Time that only moves when the code under test sleeps."""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    async def sleep(self, seconds: float) -> None:
        self.t += seconds


class FakeLink:
    """Collects messages instead of sending them; checks each against the contract."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, message: dict) -> None:
        self.sent.append(validate("room", message))


def torso_angle(pts) -> float:
    sx, sy = (pts[11][0] + pts[12][0]) / 2 * 640, (pts[11][1] + pts[12][1]) / 2 * 480
    hx, hy = (pts[23][0] + pts[24][0]) / 2 * 640, (pts[23][1] + pts[24][1]) / 2 * 480
    return math.degrees(math.atan2(abs(sx - hx), abs(sy - hy)))


@pytest.mark.parametrize("activity", ["standing", "walking", "sitting", "lying", "fallen"])
def test_fake_skeleton_is_a_valid_pose(activity):
    pts = skeleton(activity, t=3.3)
    validate("room", {"type": "pose", "ts": "2026-11-14T10:00:00Z", "keypoints": pts})


def test_fake_skeleton_is_upright_or_horizontal():
    assert torso_angle(skeleton("standing", 0)) < 20
    assert torso_angle(skeleton("fallen", 0)) > 60


def test_timeline():
    room = MockRoom("living_room", fall_every=60)
    assert [room.activity_at(t) for t in (5, 15, 25, 35)] == ["standing", "walking", "sitting", "standing"]
    assert room.fall_index(59.9) is None and room.fall_index(60) == 1
    assert room.activity_at(65) == "fallen"
    assert room.fall_index(70.1) is None and room.activity_at(71) == "walking"
    assert room.fall_index(120.5) == 2


async def test_run_sends_the_planned_messages():
    clock, link = FakeClock(), FakeLink()
    room = MockRoom("living_room", fall_every=60)
    await room.run(link, until=75, clock=clock, sleep=clock.sleep)
    counts = Counter(m["type"] for m in link.sent)
    assert counts["fall_detected"] == 1 and counts["posture_update"] == 1
    assert counts["status"] == 15            # every 5 s
    assert 37 <= counts["activity"] <= 38    # every 2 s
    assert 370 <= counts["pose"] <= 376      # 5 per second
    fall = next(m for m in link.sent if m["type"] == "fall_detected")
    up = next(m for m in link.sent if m["type"] == "posture_update")
    assert up["incident_id"] == fall["incident_id"] and up["activity"] == "standing"
    assert link.sent.index(fall) < link.sent.index(up)
    labels = [m["activity"] for m in link.sent if m["type"] == "activity"]
    assert "fallen" in labels and "walking" in labels and "sitting" in labels


async def test_commands_speak_and_number_the_attempts():
    clock, link = FakeClock(), FakeLink()
    voice = StubVoice(sleep=clock.sleep)
    handler = CommandHandler(link, voice)
    ask = {"type": "speak_and_listen", "incident_id": "inc_001",
           "text": "Are you okay? Please say yes or no.", "listen_seconds": 6}
    await handler.handle(validate("command", ask))
    await handler.handle(validate("command", {**ask, "listen_seconds": 8}))
    await handler.handle(validate("command", {"type": "speak", "text": "Help is coming."}))
    replies = [m for m in link.sent if m["type"] == "voice_reply"]
    assert [r["attempt"] for r in replies] == [1, 2]
    assert replies[0]["transcript"] == "I'm okay" and replies[0]["heard_speech"] is True
    assert clock.t == 14  # listened 6 s, then 8 s
    assert voice.spoken[-1] == "Help is coming."


async def test_reply_carries_the_question_number_the_server_sent():
    clock, link = FakeClock(), FakeLink()
    handler = CommandHandler(link, StubVoice(sleep=clock.sleep))
    numbered = {"type": "speak_and_listen", "incident_id": "inc_001", "listen_seconds": 8, "attempt": 2,
                "text": "Can you hear me? Say yes if you are okay."}
    await handler.handle(validate("command", numbered))   # the agent missed question 1: it still answers no. 2
    assert link.sent[-1]["attempt"] == 2


def test_ws_url():
    assert ws_url("http://localhost:8000") == "ws://localhost:8000/ws/room"
    assert ws_url("http://192.168.1.20:8000/") == "ws://192.168.1.20:8000/ws/room"


async def test_offline_link_keeps_incident_messages_and_drops_live_data():
    link = ServerLink("ws://127.0.0.1:9/ws/room")
    await link.send({"type": "pose", "ts": "2026-11-14T10:00:00Z", "keypoints": skeleton("standing", 0)})
    await link.send({"type": "fall_detected", "ts": "2026-11-14T10:00:01Z", "incident_id": "inc_001",
                     "reason": "fast_fall", "features": {}})
    assert [m["type"] for m in link._pending] == ["fall_detected"]


async def test_link_refuses_messages_that_break_the_contract():
    link = ServerLink("ws://127.0.0.1:9/ws/room")
    with pytest.raises(Exception):
        await link.send({"type": "activity", "activity": "running"})
