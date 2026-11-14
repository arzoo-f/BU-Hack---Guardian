"""One object for the whole analysis of a frame: keypoints in; activity label, safe zone and fall
events out. The live loop and the clip evaluation both use it, so they cannot drift apart."""
from dataclasses import dataclass, field

from vision.activity import ActivityTracker
from vision.fall import FallDetector, FallEvent
from vision.features import Features
from vision.zones import Zones


@dataclass(frozen=True)
class FrameAnalysis:
    label: str | None            # smoothed activity; "fallen" after a confirmed fall until up again
    confidence: float
    raw: str | None              # this frame's own label
    features: Features | None
    zone: str | None             # safe zone the hip centre is in, if any
    posture: str                 # fall detector's posture class for this frame
    fall_state: str              # idle | candidate | fallen
    torso_ratio: float | None
    events: list[FallEvent] = field(default_factory=list)


class VisionAnalyzer:
    """Activity labels plus the fall state machine."""

    def __init__(self, config: dict, zones: Zones | None = None) -> None:
        self.activity = ActivityTracker(config)
        self.fall = FallDetector(config, zones)

    def set_zones(self, zones: Zones) -> None:
        """New safe zones (drawn in the debug window), used from the next frame on."""
        self.fall.zones = zones

    def update(self, keypoints: list[list[float]] | None, t: float) -> FrameAnalysis:
        result = self.activity.update(keypoints, t)
        events = self.fall.update(result.features, t, person_seen=keypoints is not None)
        label = result.label
        if self.fall.fallen and label not in (None, "absent"):
            label = "fallen"
        return FrameAnalysis(label, result.confidence, result.raw, result.features, self.fall.zone,
                             self.fall.posture, self.fall.state, self.fall.torso_ratio, events)
