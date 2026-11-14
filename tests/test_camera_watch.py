"""Camera-offline alert: the family is told when Guardian cannot see the room for 2 minutes."""
from datetime import datetime, timedelta, timezone

from camera_watch import CameraWatch

LIMIT, RETRY = 120, 15


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def monotonic(self) -> float:
        return self.t

    def now(self) -> datetime:
        return datetime(2026, 11, 14, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=self.t)


class Notifier:
    def __init__(self) -> None:
        self.sent: list[tuple] = []
        self.fail = False

    async def camera_offline(self, room, since):
        if self.fail:
            raise ConnectionError("telegram down")
        self.sent.append(("offline", room, since))

    async def camera_back(self, room):
        self.sent.append(("back", room))


def watch_seeing():
    clock, notifier = Clock(), Notifier()
    watch = CameraWatch(notifier, clock, LIMIT, RETRY, "living_room")
    watch.update(True)
    return watch, clock, notifier


async def run_until(watch, clock, t):
    while clock.t < t:
        clock.t += 1
        await watch.tick()


async def test_two_minutes_without_the_camera_tells_the_family_once_then_says_when_it_is_back():
    watch, clock, notifier = watch_seeing()
    clock.t = 10
    watch.update(False)
    await run_until(watch, clock, 10 + LIMIT - 1)
    assert notifier.sent == []                               # not yet
    await run_until(watch, clock, 10 + LIMIT + 300)
    assert notifier.sent == [("offline", "living_room", clock.now().replace(minute=0, second=10))]
    watch.update(False)                                      # still offline: no repeat
    watch.update(True)
    await watch.tick()
    assert notifier.sent[-1] == ("back", "living_room") and len(notifier.sent) == 2


async def test_a_short_gap_says_nothing():
    watch, clock, notifier = watch_seeing()
    watch.update(False)
    await run_until(watch, clock, LIMIT - 30)
    watch.update(True)
    await run_until(watch, clock, LIMIT + 60)
    assert notifier.sent == []


async def test_nothing_seen_since_start_up_also_counts():
    clock, notifier = Clock(), Notifier()
    watch = CameraWatch(notifier, clock, LIMIT, RETRY, "living_room")   # room agent never connected
    await run_until(watch, clock, LIMIT + 1)
    assert [m[0] for m in notifier.sent] == ["offline"]


async def test_a_failed_message_is_retried():
    watch, clock, notifier = watch_seeing()
    watch.update(False)
    notifier.fail = True
    await run_until(watch, clock, LIMIT + 5)
    assert notifier.sent == [] and not watch.alerted
    notifier.fail = False
    await run_until(watch, clock, LIMIT + RETRY + 2)
    assert [m[0] for m in notifier.sent] == ["offline"] and watch.alerted


async def test_a_notifier_without_these_messages_is_fine():
    clock = Clock()
    watch = CameraWatch(object(), clock, LIMIT, RETRY, "living_room")
    await run_until(watch, clock, LIMIT + 1)
    assert watch.alerted
