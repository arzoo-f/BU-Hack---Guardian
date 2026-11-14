"""Local debug window: camera image, skeleton and text. Its pixels never leave the laptop."""
import cv2
import numpy as np

WINDOW = "Guardian debug (local only)"

# MediaPipe's 33-point pose skeleton.
CONNECTIONS = [(0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
               (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
               (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20), (11, 23),
               (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28), (27, 29),
               (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)]
MIN_VISIBILITY = 0.3


def draw_skeleton(frame: np.ndarray, keypoints: list[list[float]] | None) -> None:
    """Draw the skeleton in place (green lines, red joints); faint points are skipped."""
    if not keypoints:
        return
    h, w = frame.shape[:2]
    pts = [(int(x * w), int(y * h), v) for x, y, v in keypoints]
    for a, b in CONNECTIONS:
        if pts[a][2] >= MIN_VISIBILITY and pts[b][2] >= MIN_VISIBILITY:
            cv2.line(frame, pts[a][:2], pts[b][:2], (0, 220, 0), 2)
    for x, y, v in pts:
        if v >= MIN_VISIBILITY:
            cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)


def draw_zones(frame: np.ndarray, zones) -> None:
    """Outline the safe zones (blue) with their names."""
    h, w = frame.shape[:2]
    for zone in zones.as_list():
        pts = np.array([[int(x * w), int(y * h)] for x, y in zone["polygon"]], dtype=np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=(255, 128, 0), thickness=2)
        cv2.putText(frame, zone["name"], (int(pts[:, 0].min()) + 4, int(pts[:, 1].min()) + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 128, 0), 1)


def draw_draft(frame: np.ndarray, finished: list[dict], corners: list[tuple[float, float]], name: str) -> None:
    """The zones being drawn (yellow): finished ones closed, the current one open with its corners."""
    h, w = frame.shape[:2]
    for zone in finished:
        pts = np.array([[int(x * w), int(y * h)] for x, y in zone["polygon"]], dtype=np.int32)
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=2)
    pts = [(int(x * w), int(y * h)) for x, y in corners]
    for a, b in zip(pts, pts[1:]):
        cv2.line(frame, a, b, (0, 255, 255), 2)
    for p in pts:
        cv2.circle(frame, p, 5, (0, 255, 255), -1)
    if pts:
        cv2.putText(frame, name, (pts[0][0] + 8, pts[0][1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)


def on_mouse(width: int, height: int, callback) -> None:
    """callback(x_fraction, y_fraction, right_button) for each click on a width x height frame.
    The window must exist already (after the first show())."""
    def handler(event, x, y, _flags, _param):
        if event in (cv2.EVENT_LBUTTONDOWN, cv2.EVENT_RBUTTONDOWN):
            callback(x / width, y / height, event == cv2.EVENT_RBUTTONDOWN)
    cv2.setMouseCallback(WINDOW, handler)


BLUE = (200, 70, 0)          # BGR: the default text colour (nothing in the room is this blue)
ORANGE, RED = (0, 140, 255), (0, 0, 230)


def draw_text(frame: np.ndarray, lines: list[str], origin: tuple[int, int] = (10, 24),
              scale: float = 0.6, colour: tuple[int, int, int] = BLUE) -> None:
    """Draw lines of text once, in one colour, on a light see-through strip, so they stay readable on
    any background. (An outline drawn underneath drifted apart from the letters: OpenCV spaces
    thicker letters wider.)"""
    x, y = origin
    thickness = 1 if scale < 0.8 else 2
    h, w = frame.shape[:2]
    for line in lines:
        (tw, th), base = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
        x1, y1, x2, y2 = max(x - 4, 0), max(y - th - 4, 0), min(x + tw + 4, w), min(y + base + 2, h)
        if x2 > x1 and y2 > y1:
            strip = frame[y1:y2, x1:x2]
            frame[y1:y2, x1:x2] = cv2.addWeighted(strip, 0.35, np.full_like(strip, 255), 0.65, 0)
        cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, colour, thickness, cv2.LINE_AA)
        y += int(30 * scale + 8)


def show(frame: np.ndarray) -> int:
    """Show the frame; return the key pressed (lower-case character code) or -1."""
    cv2.imshow(WINDOW, frame)
    key = cv2.waitKey(1) & 0xFF
    return -1 if key == 255 else ord(chr(key).lower())


def close() -> None:
    cv2.destroyAllWindows()
