"""Mock room for --mock mode: a scripted person with a fake skeleton and a fake fall every minute.

Timeline (seconds since start): standing 10 s -> walking 10 s -> sitting 10 s, repeating;
every `fall_every` seconds the person 'falls' and stays down for `fallen_for` seconds, then
stands up again. No camera is used.
"""
import asyncio
import logging
import math
import random
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

log = logging.getLogger("guardian.room.mock")

# A person standing about 2.5 m from the camera; MediaPipe's 33 points as (x, y, visibility),
# x and y as fractions of the image.
STANDING = [
    (0.500, 0.150, 0.99), (0.510, 0.135, 0.98), (0.515, 0.135, 0.98), (0.520, 0.135, 0.97),
    (0.490, 0.135, 0.98), (0.485, 0.135, 0.98), (0.480, 0.135, 0.97), (0.530, 0.145, 0.95),
    (0.470, 0.145, 0.95), (0.510, 0.170, 0.98), (0.490, 0.170, 0.98), (0.560, 0.250, 0.99),
    (0.440, 0.250, 0.99), (0.580, 0.370, 0.97), (0.420, 0.370, 0.97), (0.590, 0.480, 0.95),
    (0.410, 0.480, 0.95), (0.595, 0.500, 0.90), (0.405, 0.500, 0.90), (0.590, 0.510, 0.90),
    (0.410, 0.510, 0.90), (0.585, 0.495, 0.90), (0.415, 0.495, 0.90), (0.540, 0.520, 0.99),
    (0.460, 0.520, 0.99), (0.545, 0.700, 0.97), (0.455, 0.700, 0.97), (0.550, 0.870, 0.95),
    (0.450, 0.870, 0.95), (0.545, 0.890, 0.90), (0.455, 0.890, 0.90), (0.565, 0.900, 0.90),
    (0.435, 0.900, 0.90),
]
HIP_CENTRE = (0.50, 0.52)
ASPECT = 640 / 480  # one unit of image height is 0.75 units of image width
CYCLE = (("standing", 10.0), ("walking", 10.0), ("sitting", 10.0))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def skeleton(activity: str, t: float, rng: random.Random | None = None) -> list[list[float]]:
    """Fake keypoints for an activity at time t (small jitter so the drawing looks alive)."""
    rng = rng or random.Random()
    pts = []
    for i, (x, y, v) in enumerate(STANDING):
        if activity == "walking":  # drift left and right across the room
            x += 0.15 * math.sin(2 * math.pi * t / 8)
            if i >= 25:  # legs swing a little
                x += (0.02 if i % 2 else -0.02) * math.sin(2 * math.pi * t)
        elif activity == "sitting":  # upper body lower, thighs forward: knees bent about 90 degrees
            if i <= 24:
                y += 0.12
            elif i in (25, 26):
                x, y = x + 0.10, 0.64
            else:
                x += 0.10
        elif activity in ("lying", "fallen"):  # rotate the standing body to horizontal, low down
            dx, dy = x - HIP_CENTRE[0], y - HIP_CENTRE[1]
            x, y = 0.50 + dy / ASPECT, 0.80 + dx * ASPECT * 0.3
        pts.append([round(x + rng.uniform(-0.003, 0.003), 4),
                    round(y + rng.uniform(-0.003, 0.003), 4), v])
    return pts


class MockRoom:
    """The scripted person: what they are doing at time t, and the messages that go with it."""

    def __init__(self, room: str, fall_every: float = 60.0, fallen_for: float = 10.0) -> None:
        self.room = room
        self.fall_every = fall_every
        self.fallen_for = fallen_for
        self._stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self._rng = random.Random(7)

    def fall_index(self, t: float) -> int | None:
        """Which fake fall is happening at time t (1, 2, ...), or None."""
        if self.fall_every <= 0 or t < self.fall_every:
            return None
        k = int(t // self.fall_every)
        return k if t - k * self.fall_every < self.fallen_for else None

    def activity_at(self, t: float) -> str:
        if self.fall_index(t) is not None:
            return "fallen"
        period = sum(d for _, d in CYCLE)
        phase = t % period
        for label, duration in CYCLE:
            if phase < duration:
                return label
            phase -= duration
        return CYCLE[-1][0]

    def incident_id(self, k: int) -> str:
        return f"inc_mock_{self._stamp}_{k}"

    async def run(self, link, until: float | None = None,
                  clock: Callable[[], float] = time.monotonic,
                  sleep: Callable[[float], Awaitable[None]] = asyncio.sleep) -> None:
        """Send pose at 5 Hz, activity every 2 s, a heartbeat every 5 s, and the fake falls."""
        start = clock()
        next_activity = next_status = 0.0
        current_fall: int | None = None
        last_label = None
        while until is None or clock() - start < until:
            t = clock() - start
            label = self.activity_at(t)
            fall = self.fall_index(t)
            if fall != current_fall:
                if current_fall is not None:
                    await link.send({"type": "posture_update", "incident_id": self.incident_id(current_fall),
                                     "activity": "standing"})
                    log.info("mock person got up (incident %s)", self.incident_id(current_fall))
                if fall is not None:
                    await link.send({"type": "fall_detected", "ts": now_iso(),
                                     "incident_id": self.incident_id(fall), "reason": "fast_fall",
                                     "features": {"drop_speed": 1.8, "torso_angle": 82.0, "seconds_low": 3.0}})
                    log.info("mock FALL sent (incident %s)", self.incident_id(fall))
                current_fall = fall
            if label != last_label:
                log.info("mock person is %s", label)
                last_label = label
            await link.send({"type": "pose", "ts": now_iso(), "keypoints": skeleton(label, t, self._rng)})
            if t >= next_activity:
                await link.send({"type": "activity", "ts": now_iso(), "room": self.room, "activity": label,
                                 "confidence": round(self._rng.uniform(0.82, 0.96), 2), "zone": None})
                next_activity += 2.0
            if t >= next_status:
                await link.send({"type": "status", "ts": now_iso(), "camera": "ok", "fps": 15.0})
                next_status += 5.0
            await sleep(0.2)
