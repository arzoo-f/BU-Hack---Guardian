"""Per-frame body features from 33 pose keypoints (BUILD_PLAN Section 13).

Speeds are measured in body-heights (or body-widths) per second, so they do not depend on how
far the person is from the camera. Image y grows downwards, so a positive hip speed means
the hips are moving towards the floor.
"""
import math
from collections import deque
from dataclasses import dataclass

# MediaPipe landmark numbers.
NOSE, L_SHOULDER, R_SHOULDER, L_HIP, R_HIP = 0, 11, 12, 23, 24
L_KNEE, R_KNEE, L_ANKLE, R_ANKLE = 25, 26, 27, 28
CORE = (L_SHOULDER, R_SHOULDER, L_HIP, R_HIP)


@dataclass(frozen=True)
class Features:
    """What the body is doing in one frame."""

    t: float                  # time in seconds (monotonic)
    hip_x: float              # hip centre, fraction of image width
    hip_y: float              # hip centre, fraction of image height (0 = top, 1 = bottom)
    body_height_px: float     # head-to-ankle skeleton length in this frame
    ref_height_px: float      # longest body length seen in the last scale_window_s (speed scale)
    body_width_px: float      # shoulder or hip width, whichever is larger
    torso_deg: float          # torso angle from vertical: 0 upright, 90 horizontal
    bbox_ratio: float         # width / height of the box around the visible keypoints
    head_rise: float | None   # how far the nose is above the hips, in current torso lengths
                              # (about 1.4 upright, under 1 lying in any direction); None if no nose
    knee_deg: float | None    # the more bent knee (180 = straight); None if legs are not visible
    thigh_deg: float | None   # hips->knees direction from straight down (about 3 standing, 45+ sitting);
                              # needs no ankles. None if the knees are not visible
    hip_speed_down: float     # body-heights per second; + = hips moving down
    hip_shift_1s: float       # sideways hip movement over the last second, in body-widths
    torso_len_px: float = 1.0           # shoulder midpoint to hip midpoint
    torso_rise_px: float = 1.0          # how far the shoulders are above the hips in the image
                                        # (small or negative when the torso is not upright)
    feet_below_hips_px: float | None = None  # ankles (else knees) below the hips in the image;
                                             # negative = above; None if no leg point is visible
    in_view: bool = True                # shoulders and hips inside the image, away from its edge


def _mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle(a, b, c) -> float:
    """Angle at b (degrees) between b->a and b->c."""
    v1, v2 = (a[0] - b[0], a[1] - b[1]), (c[0] - b[0], c[1] - b[1])
    n = math.hypot(*v1) * math.hypot(*v2)
    if n == 0:
        return 180.0
    cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / n))
    return math.degrees(math.acos(cos))


class FeatureTracker:
    """Turns a stream of keypoints into Features; keeps the short history speeds need."""

    def __init__(self, config: dict) -> None:
        self.w = config["frame_width"]
        self.h = config["frame_height"]
        self.min_vis = config["min_keypoint_visibility"]
        # From a camera up high, knees and ankles are found less confidently than the torso.
        self.min_leg_vis = config["min_leg_visibility"]
        self.speed_window = config["speed_window_s"]
        self.scale_window = config["scale_window_s"]
        self.edge = config["edge_margin"]
        self._history: deque[tuple[float, float, float, float]] = deque()  # t, hip_x_px, hip_y_px, height

    def reset(self) -> None:
        self._history.clear()

    def update(self, keypoints: list[list[float]] | None, t: float) -> Features | None:
        """Features for this frame, or None if shoulders and hips are not clearly visible."""
        if not keypoints or min(keypoints[i][2] for i in CORE) < self.min_vis:
            return None
        px = [(x * self.w, y * self.h) for x, y, _ in keypoints]
        leg_points = (L_KNEE, R_KNEE, L_ANKLE, R_ANKLE)
        vis = [v >= (self.min_leg_vis if i in leg_points else self.min_vis)
               for i, (_, _, v) in enumerate(keypoints)]
        shoulders, hips = _mid(px[L_SHOULDER], px[R_SHOULDER]), _mid(px[L_HIP], px[R_HIP])

        dx, dy = shoulders[0] - hips[0], shoulders[1] - hips[1]
        torso_deg = math.degrees(math.atan2(abs(dx), abs(dy)))

        legs = [(h, k, a) for h, k, a in ((L_HIP, L_KNEE, L_ANKLE), (R_HIP, R_KNEE, R_ANKLE))
                if vis[k] and vis[a]]
        knee_deg = min(_angle(px[h], px[k], px[a]) for h, k, a in legs) if legs else None
        thigh_deg = None
        if vis[L_KNEE] and vis[R_KNEE]:
            knees_mid = _mid(px[L_KNEE], px[R_KNEE])
            thigh_deg = math.degrees(math.atan2(abs(knees_mid[0] - hips[0]), knees_mid[1] - hips[1]))

        # Skeleton length head -> shoulders -> hips -> knees -> ankles (works in any orientation).
        height = _dist(px[NOSE], shoulders) + _dist(shoulders, hips)
        if vis[L_KNEE] and vis[R_KNEE]:
            knees = _mid(px[L_KNEE], px[R_KNEE])
            height += _dist(hips, knees)
            if vis[L_ANKLE] and vis[R_ANKLE]:
                height += _dist(knees, _mid(px[L_ANKLE], px[R_ANKLE]))
        width = max(_dist(px[L_SHOULDER], px[R_SHOULDER]), _dist(px[L_HIP], px[R_HIP]), 0.15 * height)

        shown = [p for p, ok in zip(px, vis) if ok]
        xs, ys = [p[0] for p in shown], [p[1] for p in shown]
        bbox_ratio = (max(xs) - min(xs)) / max(max(ys) - min(ys), 1.0)
        torso_len = max(_dist(shoulders, hips), 1.0)
        head_rise = (hips[1] - px[NOSE][1]) / torso_len if vis[NOSE] else None
        feet = [px[i][1] for i in (L_ANKLE, R_ANKLE) if vis[i]] or [px[i][1] for i in (L_KNEE, R_KNEE) if vis[i]]
        feet_below_hips = sum(feet) / len(feet) - hips[1] if feet else None
        in_view = all(self.edge <= p[0] / self.w <= 1 - self.edge and self.edge <= p[1] / self.h <= 1 - self.edge
                      for p in (shoulders, hips))

        self._history.append((t, hips[0], hips[1], height))
        while self._history and t - self._history[0][0] > max(self.scale_window, 1.0):
            self._history.popleft()
        ref_height = max(h for ht, _, _, h in self._history if t - ht <= self.scale_window)

        hip_speed_down = 0.0
        recent = [s for s in self._history if t - s[0] <= self.speed_window and s[0] < t]
        if recent:
            t0, _, y0, _ = recent[0]
            hip_speed_down = (hips[1] - y0) / (t - t0) / ref_height

        hip_shift = 0.0
        last_second = [s for s in self._history if t - s[0] <= 1.0]
        if len(last_second) > 1:
            xs1 = [s[1] for s in last_second]
            hip_shift = (max(xs1) - min(xs1)) / width

        return Features(t=t, hip_x=hips[0] / self.w, hip_y=hips[1] / self.h, body_height_px=height,
                        ref_height_px=ref_height, body_width_px=width, torso_deg=torso_deg,
                        bbox_ratio=bbox_ratio, head_rise=head_rise, knee_deg=knee_deg, thigh_deg=thigh_deg,
                        hip_speed_down=hip_speed_down, hip_shift_1s=hip_shift, torso_len_px=torso_len,
                        torso_rise_px=hips[1] - shoulders[1], feet_below_hips_px=feet_below_hips,
                        in_view=in_view)
