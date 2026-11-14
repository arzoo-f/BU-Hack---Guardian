"""Where frames come from: the live camera or a recorded clip. Both give (frame, t_seconds).

A clip may have a sidecar JSON (same name, .json) written by scripts/record_clips.py with the
real time of every frame; without it, times come from the frame rate in the video header.
"""
import json
import time
from pathlib import Path

import cv2
import numpy as np

from vision.pose import Camera

Frame = tuple[np.ndarray, float]


class FramePacer:
    """Lets through about target_fps frames per second, whatever rate the source delivers.

    The schedule advances by a fixed step, not from the current time: a naive "skip if less than
    1/fps since the last frame" drops every other frame of a ~22 FPS camera.
    """

    def __init__(self, target_fps: float) -> None:
        self.interval = 1.0 / target_fps
        self._next: float | None = None

    def accept(self, t: float) -> bool:
        """True if the frame with timestamp t should be processed."""
        if self._next is None:
            self._next = t
        if t < self._next:
            return False
        self._next = max(self._next + self.interval, t - self.interval)
        return True


class CameraSource:
    """Live webcam; t is time.monotonic()."""

    live = True

    def __init__(self, index: int, width: int, height: int) -> None:
        self.camera = Camera(index, width, height)
        self.name = f"camera {index}"

    def open(self) -> bool:
        return self.camera.open()

    def read(self) -> Frame | None:
        frame = self.camera.read()
        return None if frame is None else (frame, time.monotonic())

    def release(self) -> None:
        self.camera.release()


def sidecar_path(clip: Path) -> Path:
    return clip.with_suffix(".json")


def read_sidecar(clip: Path) -> dict | None:
    path = sidecar_path(clip)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


class ClipSource:
    """A recorded clip; t is seconds since the clip started. Ends with `finished = True`."""

    live = False

    def __init__(self, path: Path | str, width: int, height: int, realtime: bool = False) -> None:
        self.path = Path(path)
        self.width, self.height = width, height
        self.realtime = realtime
        self.name = self.path.name
        self.finished = False
        self._cap: cv2.VideoCapture | None = None
        self._times: list[float] | None = None
        self._fps = 15.0
        self._index = 0
        self._start = 0.0

    def open(self) -> bool:
        if not self.path.exists():
            return False
        self._cap = cv2.VideoCapture(str(self.path))
        if not self._cap.isOpened():
            return False
        meta = read_sidecar(self.path)
        self._times = meta.get("frame_times") if meta else None
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 15.0
        self._start = time.monotonic()
        return True

    def read(self) -> Frame | None:
        ok, frame = self._cap.read() if self._cap else (False, None)
        if not ok or frame is None:
            self.finished = True
            return None
        i = self._index
        self._index += 1
        t = self._times[i] if self._times and i < len(self._times) else i / self._fps
        if self.realtime:  # play at recorded speed, e.g. to watch it or drive the server live
            wait = self._start + t - time.monotonic()
            if wait > 0:
                time.sleep(wait)
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        return frame, t

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class LoopingClipSource(ClipSource):
    """A clip played again and again, for long runs (BUILD_PLAN step 7.8). Time keeps counting up
    across rounds, so the fall detector sees one long recording."""

    def __init__(self, path: Path | str, width: int, height: int, realtime: bool = False) -> None:
        super().__init__(path, width, height, realtime)
        self.rounds = 0
        self._offset = 0.0
        self._last_t = 0.0

    def read(self) -> Frame | None:
        item = super().read()
        if item is None:
            self.release()
            self._index = 0
            if not self.open():
                return None
            self.finished = False
            self.rounds += 1
            self._offset += self._last_t + 1.0 / self._fps
            item = super().read()
            if item is None:
                return None
        frame, t = item
        self._last_t = t
        return frame, t + self._offset
