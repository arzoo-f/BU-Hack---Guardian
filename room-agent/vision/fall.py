"""Fall state machine (BUILD_PLAN Section 13; rule form adapted to the tuning clips, DECISIONS D-007).

Per frame, the body is put into one posture class, measured against how long the torso looked
when the person last stood upright (the camera is uncalibrated, so "upright" is the yardstick):

    up       standing or walking
    down     on the floor: the torso is not upright, and this is not a bend
    low      the torso is not upright, but it may be a bend (head hanging, feet under the body)
    resting  down or low with the hip centre inside a safe zone (sofa, bed)
    other    sitting, kneeling, anything else
    unknown / absent

Fast path:  up -> down within fall_window_s makes a candidate; still down fall_confirm_s later
            -> fall_detected (fast_fall). Up again first -> a stumble, no incident.
Slow path:  down or low, outside a safe zone, for slow_path_lying_s -> fall_detected (found_on_floor).
After a fall the detector stays `fallen` until the person is upright again.

Every threshold comes from config/vision.json.
"""
from collections import deque
from dataclasses import dataclass, field

from vision.activity import is_lying
from vision.features import Features
from vision.zones import Zones

IDLE, CANDIDATE, FALLEN = "idle", "candidate", "fallen"
MIN_REF_SAMPLES = 5


@dataclass(frozen=True)
class FallEvent:
    """Something the fall detector noticed in this frame."""

    kind: str                     # fall_detected | stumble | recovered
    t: float
    reason: str | None = None     # fall_detected only: fast_fall | found_on_floor
    features: dict = field(default_factory=dict)


def looks_upright(f: Features, config: dict) -> bool:
    """The shape of a standing or walking person: torso and thighs vertical, head high, narrow."""
    return (f.torso_deg < config["upright_torso_deg"]
            and (f.thigh_deg is None or f.thigh_deg < config["upright_thigh_deg"])
            and f.head_rise is not None and f.head_rise > config["lying_head_rise"]
            and f.bbox_ratio < config["upright_box_ratio"])


class UprightReference:
    """How long the torso looks (pixels) when this person stands upright where they are now."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self._samples: deque[float] = deque(maxlen=config["upright_ref_frames"])
        self._odd_since: float | None = None

    @property
    def value(self) -> float | None:
        if len(self._samples) < MIN_REF_SAMPLES:
            return None
        return sorted(self._samples)[len(self._samples) // 2]

    def reset(self) -> None:
        self._samples.clear()
        self._odd_since = None

    def update(self, f: Features, t: float) -> bool:
        """Feed one frame; True if the person is upright in it (which also refreshes the reference).

        Upright means the shape of a standing person, or a torso still at (nearly) its full
        standing height with the thighs down - for example standing while looking at the floor.

        A body lying along the camera's line of sight can have an upright *shape* but a much
        shorter torso. Such a frame is refused unless that size lasts upright_reanchor_s, which
        means the person really moved (for example crawled, then stood up somewhere else).
        """
        cfg, ref = self.config, self.value
        tall = (ref is not None and f.torso_rise_px / ref >= cfg["standing_torso_ratio"]
                and (f.thigh_deg is None or f.thigh_deg < cfg["sitting_thigh_deg"]))
        if not (tall or looks_upright(f, cfg)):
            self._odd_since = None
            return False
        low, high = cfg["upright_ref_band"]
        if ref is None or low <= f.torso_len_px / ref <= high:
            self._samples.append(f.torso_len_px)
            self._odd_since = None
            return True
        if self._odd_since is None:
            self._odd_since = t
        if t - self._odd_since >= cfg["upright_reanchor_s"]:
            self.reset()
            self._samples.append(f.torso_len_px)
            return True
        return tall


def is_low(f: Features, ref: float | None, config: dict) -> bool:
    """The torso is not upright, in any direction: lying (also towards or away from the camera,
    where the torso looks short rather than tilted) or bending right over."""
    if ref is not None and f.torso_rise_px / ref < config["torso_upright_ratio"]:
        return True
    return is_lying(f, config)


def is_bending(f: Features, config: dict) -> bool:
    """Bent over rather than lying: the body is not wide, the head is not beyond the hips, and
    the feet are still under the body."""
    head_hanging = f.head_rise is None or f.head_rise < config["bend_head_rise"]
    feet_under = f.feet_below_hips_px is None or f.feet_below_hips_px > 0
    return f.bbox_ratio <= config["lying_box_ratio"] and head_hanging and feet_under


@dataclass
class _Candidate:
    start: float
    last_down: float
    peak_speed: float
    frames: int = 1
    down: int = 1


class FallDetector:
    """Feed it the features of every frame; it returns the fall events of that frame."""

    def __init__(self, config: dict, zones: Zones | None = None) -> None:
        self.config = config
        self.zones = zones or Zones()
        self.ref = UprightReference(config)
        self.state = IDLE
        self.posture = "unknown"
        self.zone: str | None = None          # safe zone the hip centre is in right now
        self.torso_ratio: float | None = None  # this frame's torso rise / upright reference
        self._last_up_t: float | None = None
        self._up_since: float | None = None
        self._absent_since: float | None = None
        self._candidate: _Candidate | None = None
        self._low_since: float | None = None
        self._last_low_t = 0.0
        self._speeds: deque[tuple[float, float]] = deque()
        self._last_features: Features | None = None

    @property
    def fallen(self) -> bool:
        return self.state == FALLEN

    def update(self, f: Features | None, t: float, person_seen: bool = True) -> list[FallEvent]:
        """Process one frame (f is None when nobody is seen or the body is unclear)."""
        events: list[FallEvent] = []
        self._classify(f, t, person_seen)
        if self.state == FALLEN:
            self._update_fallen(t, events)
            return events
        self._update_slow_path(t, events)
        if self.state != FALLEN:
            self._update_fast_path(t, events)
        return events

    # -- posture of this frame ------------------------------------------------------------

    def _classify(self, f: Features | None, t: float, person_seen: bool) -> None:
        self.zone = self.torso_ratio = None
        if not person_seen:
            self.posture, self._up_since = "absent", None
            if self._absent_since is None:
                self._absent_since = t
            elif t - self._absent_since >= self.config["absent_reset_s"]:
                self.ref.reset()  # whoever comes back may stand somewhere else
                self._last_up_t = None
            return
        self._absent_since = None
        if f is None or not f.in_view:
            self.posture, self._up_since = "unknown", None
            return
        self._last_features = f
        self._speeds.append((t, f.hip_speed_down))
        while t - self._speeds[0][0] > self.config["fall_window_s"]:
            self._speeds.popleft()
        self.zone = self.zones.at(f.hip_x, f.hip_y)
        if self.ref.update(f, t):
            self.posture = "up"
            self._up_since = t if self._up_since is None else self._up_since
            self._last_up_t = t
            self.torso_ratio = f.torso_rise_px / self.ref.value if self.ref.value else None
            return
        self._up_since = None
        ref = self.ref.value
        self.torso_ratio = f.torso_rise_px / ref if ref else None
        if not is_low(f, ref, self.config):
            self.posture = "other"
        elif self.zone is not None:
            self.posture = "resting"
        else:
            self.posture = "low" if is_bending(f, self.config) else "down"

    def _up_for(self, t: float) -> float:
        return t - self._up_since if self._up_since is not None else 0.0

    # -- fast path ------------------------------------------------------------------------

    def _update_fast_path(self, t: float, events: list[FallEvent]) -> None:
        cfg, c = self.config, self._candidate
        if c is None:
            recently_up = self._last_up_t is not None and t - self._last_up_t <= cfg["fall_window_s"]
            if self.posture == "down" and recently_up:
                self._candidate = _Candidate(start=t, last_down=t, peak_speed=max(v for _, v in self._speeds))
                self.state = CANDIDATE
            return
        c.frames += 1
        if self.posture == "down":
            c.down += 1
            c.last_down = t
        if self.posture == "up" and self._up_for(t) >= cfg["up_confirm_s"]:
            events.append(FallEvent("stumble", t, features={"seconds_low": round(t - c.start, 2),
                                                            "drop_speed": round(c.peak_speed, 2)}))
            self._to_idle()
        elif self.posture == "resting" or t - c.last_down > cfg["down_gap_s"]:
            # moved into a safe zone, or no longer clearly down: not a fast fall
            # (the slow-path timer keeps running on its own)
            self._candidate = None
            self.state = IDLE
        elif t - c.start >= cfg["fall_confirm_s"] and c.down / c.frames >= cfg["fall_confirm_share"]:
            self._confirm("fast_fall", t, t - c.start, c.peak_speed, events)

    # -- slow path ------------------------------------------------------------------------

    def _update_slow_path(self, t: float, events: list[FallEvent]) -> None:
        if self.posture in ("down", "low"):
            if self._low_since is None:
                self._low_since = t
            self._last_low_t = t
            if t - self._low_since >= self.config["slow_path_lying_s"]:
                self._confirm("found_on_floor", t, t - self._low_since, None, events)
        elif self._low_since is not None:
            got_up = self.posture == "up" and self._up_for(t) >= self.config["up_confirm_s"]
            if got_up or self.posture == "resting" or t - self._last_low_t > self.config["low_gap_s"]:
                self._low_since = None

    # -- after a fall ---------------------------------------------------------------------

    def _update_fallen(self, t: float, events: list[FallEvent]) -> None:
        if self.posture == "up" and self._up_for(t) >= self.config["recover_s"]:
            events.append(FallEvent("recovered", t))
            self._to_idle()
        elif (self.posture == "absent" and self._absent_since is not None
              and t - self._absent_since >= self.config["fallen_absent_reset_s"]):
            self._to_idle()  # out of sight for a long time: start afresh

    def _confirm(self, reason: str, t: float, seconds_low: float, drop_speed: float | None,
                 events: list[FallEvent]) -> None:
        f = self._last_features
        events.append(FallEvent("fall_detected", t, reason=reason, features={
            "drop_speed": None if drop_speed is None else round(drop_speed, 2),
            "torso_angle": None if f is None else round(f.torso_deg, 1),
            "torso_ratio": None if self.torso_ratio is None else round(self.torso_ratio, 2),
            "seconds_low": round(seconds_low, 1),
        }))
        self._candidate = None
        self._low_since = None
        self.state = FALLEN

    def _to_idle(self) -> None:
        self._candidate = None
        self._low_since = None
        self.state = IDLE
