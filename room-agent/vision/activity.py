"""Activity labels (BUILD_PLAN Section 13): simple rules per frame, then a majority vote over
the last vote_frames frames (about 1 s at 15 FPS). 'fallen' is set later by the fall state
machine (step 2.5), never by these rules.
"""
from collections import Counter, deque
from dataclasses import dataclass

from vision.features import Features, FeatureTracker


def is_lying(f: Features, config: dict) -> bool:
    """Lying in any direction: the torso is clearly tilted, OR the body is wider than tall with the
    head low. The second test catches someone lying towards or away from the camera, whose torso
    looks short and only partly tilted from a camera up high."""
    if f.torso_deg > config["lying_torso_deg"]:
        return True
    head_low = f.head_rise is None or f.head_rise < config["lying_head_rise"]
    return f.bbox_ratio > config["lying_box_ratio"] and head_low


def is_sitting(f: Features, config: dict) -> bool:
    """Knees clearly bent, or thighs pointing well away from straight down. The thigh test needs no
    ankles and does not depend on the knee looking bent from this camera angle."""
    if f.knee_deg is not None and f.knee_deg < config["sitting_knee_deg"]:
        return True
    return f.thigh_deg is not None and f.thigh_deg > config["sitting_thigh_deg"]


def classify(features: Features | None, person_seen: bool, config: dict) -> str | None:
    """Label for one frame; None when a person is seen but not clearly enough to judge."""
    if not person_seen:
        return "absent"
    if features is None:
        return None
    if is_lying(features, config):
        return "lying"
    if is_sitting(features, config):
        return "sitting"
    if features.hip_shift_1s > config["walking_hip_shift_bodywidths_per_s"]:
        return "walking"
    return "standing"


class ActivityVoter:
    """Majority vote over the last n frame labels; unclear frames (None) do not vote."""

    def __init__(self, n: int) -> None:
        self._labels: deque[str] = deque(maxlen=n)
        self.label: str | None = None

    def add(self, label: str | None) -> tuple[str | None, float]:
        """Add one frame's label; return the smoothed label and its share of the votes."""
        if label is not None:
            self._labels.append(label)
        if not self._labels:
            return None, 0.0
        counts = Counter(self._labels)
        best = max(counts.values())
        leaders = [lab for lab, c in counts.items() if c == best]
        if self.label not in leaders:  # on a tie, keep the current label; otherwise the newest leader
            self.label = next(lab for lab in reversed(self._labels) if lab in leaders)
        return self.label, counts[self.label] / len(self._labels)


@dataclass(frozen=True)
class ActivityResult:
    label: str | None        # smoothed label (None until the first clear frame)
    confidence: float        # share of the recent votes for that label
    raw: str | None          # this frame's own label
    features: Features | None


class ActivityTracker:
    """Keypoints in, smoothed activity out."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.features = FeatureTracker(config)
        self.voter = ActivityVoter(config["vote_frames"])

    def update(self, keypoints: list[list[float]] | None, t: float) -> ActivityResult:
        if keypoints is None:
            self.features.reset()  # speeds must not jump across a gap
        feats = self.features.update(keypoints, t)
        raw = classify(feats, keypoints is not None, self.config)
        label, confidence = self.voter.add(raw)
        return ActivityResult(label, confidence, raw, feats)
