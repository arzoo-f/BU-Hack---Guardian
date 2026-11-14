"""Camera capture and MediaPipe pose detection. Frames stay in this process; only keypoints go on."""
import contextlib
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("GLOG_minloglevel", "2")

import cv2  # noqa: E402
import mediapipe as mp  # noqa: E402
import numpy as np  # noqa: E402
from mediapipe.tasks.python import BaseOptions  # noqa: E402
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode  # noqa: E402

Keypoints = list[list[float]]  # 33 x [x, y, visibility], x and y as fractions of the image


@contextlib.contextmanager
def quiet_native_stderr():
    """Hide the C++ start-up chatter MediaPipe writes straight to stderr."""
    try:
        fd = sys.stderr.fileno()
    except (AttributeError, OSError, ValueError):
        yield
        return
    saved = os.dup(fd)
    with open(os.devnull, "w") as devnull:
        os.dup2(devnull.fileno(), fd)
        try:
            yield
        finally:
            os.dup2(saved, fd)
            os.close(saved)


class Camera:
    """A webcam delivering BGR frames at the configured size."""

    def __init__(self, index: int, width: int = 640, height: int = 480) -> None:
        self.index, self.width, self.height = index, width, height
        self.cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        self.release()
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)  # DirectShow opens fast on Windows
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return self.cap.isOpened()

    def read(self) -> np.ndarray | None:
        """Next frame resized to width x height, or None if the camera gave nothing."""
        if self.cap is None:
            return None
        ok, frame = self.cap.read()
        if not ok or frame is None:
            return None
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        return frame

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class PoseDetector:
    """MediaPipe Pose Landmarker in video mode: one person, 33 keypoints per frame."""

    def __init__(self, model_file: Path) -> None:
        options = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(model_file)),
                                        running_mode=RunningMode.VIDEO, num_poses=1)
        with quiet_native_stderr():
            self._landmarker = PoseLandmarker.create_from_options(options)
        self._last_ts = -1

    def detect(self, frame_bgr: np.ndarray, ts_ms: int | None = None) -> Keypoints | None:
        """Keypoints of the person in the frame, or None if nobody is found."""
        if ts_ms is None:
            ts_ms = int(time.monotonic() * 1000)
        ts_ms = max(ts_ms, self._last_ts + 1)  # video mode needs strictly increasing timestamps
        self._last_ts = ts_ms
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        result = self._landmarker.detect_for_video(image, ts_ms)
        if not result.pose_landmarks:
            return None
        return [[round(p.x, 4), round(p.y, 4), round(min(max(p.visibility, 0.0), 1.0), 3)]
                for p in result.pose_landmarks[0]]

    def close(self) -> None:
        self._landmarker.close()
