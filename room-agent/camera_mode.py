"""Vision loop: frames (live camera or recorded clip) -> pose -> activity and falls -> server,
with the local debug window.

Runs in a worker thread; messages are handed to the asyncio side through `emit`. All timing
uses the source's clock (monotonic for the camera, clip time for a clip), so a replayed clip
behaves exactly as it did live.
"""
import csv
import json
import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone

from guide import Guide
from settings import AGENT_DIR, ROOT, model_path
from vision import debug_view
from vision.analyzer import FrameAnalysis, VisionAnalyzer
from vision.fall import FallEvent
from vision.pose import PoseDetector
from vision.sources import FramePacer
from vision.zone_editor import ZoneEditor
from vision.zones import Zones, load_zones

log = logging.getLogger("guardian.room.camera")

STATUS_EVERY_S = 5.0
ACTIVITY_EVERY_S = 2.0
READ_FAILURES_BEFORE_OFFLINE = 30
POSTURE_UPDATES_FOR_S = 1800.0  # after a fall, keep telling the server about posture changes
LOG_DIR = AGENT_DIR / "logs"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def feature_line(result: FrameAnalysis) -> str:
    f = result.features
    if f is None:
        return "features: -"
    knee = f"{f.knee_deg:3.0f}" if f.knee_deg is not None else "  -"
    return (f"torso {f.torso_deg:3.0f}  knee {knee}  hip v {f.hip_speed_down:+.2f} bh/s  "
            f"shift {f.hip_shift_1s:.2f} bw  box {f.bbox_ratio:.2f}")


class VisionLoop:
    """Reads frames, finds the pose, activity and falls, and sends the room messages."""

    def __init__(self, source, config: dict, emit: Callable[[dict], None], room: str,
                 show_window: bool = True, seconds: float | None = None,
                 guide: Guide | None = None, frame_log: bool = False,
                 zones: Zones | None = None, on_space: Callable[[], None] | None = None,
                 on_zones_saved: Callable[[list[dict]], None] | None = None) -> None:
        self.source = source
        self.config = config
        self.emit = emit
        self.room = room
        self.show_window = show_window
        self.guide = guide
        self.seconds = guide.total if guide else seconds
        self.frame_log = frame_log or guide is not None
        self.stop = threading.Event()
        self.on_space = on_space          # Space in the debug window = "I'm okay" during a check-in
        self.zones = load_zones(config) if zones is None else zones
        self.analyzer = VisionAnalyzer(config, self.zones)
        self.zone_editor = ZoneEditor(ROOT / config["zones_file"])   # Z / clicks / S in the debug window
        self.on_zones_saved = on_zones_saved                          # e.g. send them to the server
        self._mouse_ready = False
        self.camera_off = False                                       # C in the debug window
        self._status_due = False
        self.result: FrameAnalysis | None = None
        self.frames = 0
        self.frames_with_person = 0
        self.fps = 0.0
        self._label: str | None = None
        self._csv = None
        self._session = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self._falls = 0
        self._incident_id: str | None = None
        self._incident_t = 0.0

    def run(self) -> None:
        cfg, source = self.config, self.source
        if not source.open():
            log.error("%s could not be opened", source.name)
            self.emit({"type": "status", "ts": now_iso(), "camera": "offline", "fps": 0.0})
            return
        detector = PoseDetector(model_path(cfg))
        log.info("%s open, model %s, up to %s FPS", source.name, cfg["model"], cfg["target_fps"])
        self._open_frame_log()
        pacer = FramePacer(cfg["target_fps"])  # about target_fps, so vote_frames covers about 1 s
        pose_interval = 1.0 / cfg["pose_send_hz"]
        stamps: deque[float] = deque(maxlen=30)
        t0 = next_pose = next_status = next_activity = None
        failures = 0
        camera_ok = True
        try:
            while not self.stop.is_set():
                item = source.read()
                if item is None:
                    if not source.live:
                        break  # end of the clip
                    failures += 1
                    if failures >= READ_FAILURES_BEFORE_OFFLINE and camera_ok:
                        camera_ok = False
                        log.warning("camera stopped delivering frames")
                    now = time.monotonic()
                    if next_status is None or now >= next_status:
                        self.emit({"type": "status", "ts": now_iso(), "camera": "offline", "fps": 0.0})
                        next_status = now + STATUS_EVERY_S
                    time.sleep(0.05)
                    continue
                frame, t = item
                if not camera_ok:
                    log.info("camera is back")
                failures, camera_ok = 0, True
                if t0 is None:
                    t0 = next_pose = next_status = next_activity = t
                elapsed = t - t0
                if self.seconds is not None and elapsed >= self.seconds:
                    break
                if self._status_due:                   # C was pressed: say so at once
                    next_status, self._status_due = t, False
                if self.camera_off:                    # C: behave exactly like a dead camera
                    if t >= next_status:
                        self.emit({"type": "status", "ts": now_iso(), "camera": "offline", "fps": 0.0})
                        next_status = t + STATUS_EVERY_S
                    if self.show_window and self.handle_key(self._draw_camera_off(frame)):
                        break
                    continue
                if not pacer.accept(t):
                    continue
                stamps.append(t)
                self.fps = (len(stamps) - 1) / (stamps[-1] - stamps[0]) if len(stamps) > 1 else 0.0

                keypoints = detector.detect(frame, int(t * 1000))
                self.frames += 1
                self._analyse(keypoints, t, elapsed)

                if keypoints and t >= next_pose:
                    self.emit({"type": "pose", "ts": now_iso(), "keypoints": keypoints})
                    next_pose = t + pose_interval
                if self._label and t >= next_activity:
                    self.emit({"type": "activity", "ts": now_iso(), "room": self.room, "activity": self._label,
                               "confidence": round(self.result.confidence, 2), "zone": self.result.zone})
                    next_activity = t + ACTIVITY_EVERY_S
                if t >= next_status:
                    self.emit({"type": "status", "ts": now_iso(), "camera": "ok", "fps": round(self.fps, 1)})
                    next_status = t + STATUS_EVERY_S
                if self.show_window and self.handle_key(self._draw(frame, keypoints, elapsed)):
                    break
        finally:
            source.release()
            detector.close()
            if self.show_window:
                debug_view.close()
            if self._csv:
                self._csv[0].close()
            log.info("%s stopped: %d frames, %.1f FPS, person in %.0f%% of frames", source.name,
                     self.frames, self.fps, 100 * self.frames_with_person / max(self.frames, 1))

    def _analyse(self, keypoints, t: float, elapsed: float) -> None:
        """Activity and falls for this frame; sends fall and posture messages, feeds guide and CSV."""
        if keypoints:
            self.frames_with_person += 1
        self.result = r = self.analyzer.update(keypoints, t)
        for event in r.events:
            self._on_fall_event(event, t, elapsed)
        label = r.label
        if label and label != self._label:
            log.info("activity -> %s (%.0f%%) at %.1f s", label, 100 * r.confidence, elapsed)
            self._label = label
            if self._incident_id and t - self._incident_t <= POSTURE_UPDATES_FOR_S:
                self.emit({"type": "posture_update", "incident_id": self._incident_id, "activity": label})
        if self.guide:
            self.guide.record(elapsed, label)
        if self._csv:
            f = r.features
            self._csv[1].writerow([f"{elapsed:.3f}", label, f"{r.confidence:.2f}", r.raw,
                                   *(("", "", "", "", "") if f is None else (
                                       f"{f.torso_deg:.1f}", "" if f.knee_deg is None else f"{f.knee_deg:.1f}",
                                       f"{f.hip_speed_down:.3f}", f"{f.hip_shift_1s:.3f}", f"{f.bbox_ratio:.2f}")),
                                   r.posture, r.fall_state, "" if r.torso_ratio is None else f"{r.torso_ratio:.2f}",
                                   json.dumps(keypoints) if keypoints else ""])  # points only, never pixels

    def _on_fall_event(self, event: FallEvent, t: float, elapsed: float) -> None:
        if event.kind == "fall_detected":
            self._falls += 1
            self._incident_id = f"inc_{self._session}_{self._falls}"
            self._incident_t = t
            self.emit({"type": "fall_detected", "ts": now_iso(), "incident_id": self._incident_id,
                       "reason": event.reason, "features": event.features})
            log.warning("FALL DETECTED (%s) at %.1f s, incident %s: %s", event.reason, elapsed,
                        self._incident_id, event.features)
        elif event.kind == "stumble":
            log.info("stumble at %.1f s (up again, no incident): %s", elapsed, event.features)
        elif event.kind == "recovered":
            log.info("person is up again at %.1f s", elapsed)

    def handle_key(self, key: int) -> bool:
        """A key in the debug window; True means quit (Q)."""
        if key == ord("q"):
            return True
        if key == ord(" ") and self.on_space is not None:
            log.info("space bar pressed")
            self.on_space()
        elif key == ord("c"):
            self.toggle_camera_off()
        else:
            self.zone_key(key)
        return False

    def toggle_camera_off(self) -> None:
        """C: pretend the camera is unplugged (for testing the camera-offline alert with a built-in
        camera, BUILD_PLAN CP8.5): no pictures are analysed and the status says "offline"."""
        self.camera_off = not self.camera_off
        self._status_due = True
        log.warning("camera %s (simulated with C)", "OFF" if self.camera_off else "back ON")

    def _draw_camera_off(self, frame) -> int:
        blank = frame * 0                              # nothing of the room is shown or analysed
        debug_view.draw_text(blank, ["CAMERA OFF (simulated for testing)", "Press C to turn it back on"],
                             origin=(10, 200), scale=0.8, colour=debug_view.ORANGE)
        return debug_view.show(blank)

    def zone_key(self, key: int) -> None:
        """Z starts a zone (or the next one), S saves, Esc cancels, Backspace removes a corner."""
        editor = self.zone_editor
        if key == ord("z"):
            editor.start()
        elif key == 8:
            editor.undo()
        elif key == 27:
            editor.cancel()
        elif key == ord("s"):
            zones = editor.save()
            if zones is not None:
                self.set_zones(zones)

    def zone_click(self, x: float, y: float, right: bool = False) -> None:
        """A click in the debug window (image fractions): a corner, or (right button) undo."""
        if right:
            self.zone_editor.undo()
        else:
            self.zone_editor.click(x, y)

    def set_zones(self, zones: Zones) -> None:
        """Use new safe zones at once, and pass them on (to the server, for the dashboard)."""
        self.zones = zones
        self.analyzer.set_zones(zones)
        log.info("safe zones saved: %s", zones.as_list())
        if self.on_zones_saved is not None:
            self.on_zones_saved(zones.as_list())

    def _draw(self, frame, keypoints, elapsed: float) -> int:
        editor = self.zone_editor
        if not editor.drawing:
            debug_view.draw_zones(frame, self.zones)
        debug_view.draw_skeleton(frame, keypoints)
        if editor.drawing:
            debug_view.draw_draft(frame, editor.finished, editor.corners, editor.name)
            debug_view.draw_text(frame, [f"Drawing '{editor.name}': click its corners",
                                         "Z = next zone   S = save   Esc = cancel   right click = undo"],
                                 origin=(10, 400), scale=0.6)
        elif editor.message:
            debug_view.draw_text(frame, [editor.message], origin=(10, 430), scale=0.6)
        r = self.result
        label = (r.label or "-").upper() if r else "-"
        conf = f" ({r.confidence:.0%})" if r and r.label else ""
        colour = debug_view.BLUE
        if r and r.fall_state == "fallen":
            colour = debug_view.RED    # red: confirmed fall
        elif r and r.fall_state == "candidate":
            label, conf, colour = "POSSIBLE FALL...", "", debug_view.ORANGE  # orange: waiting to confirm
        debug_view.draw_text(frame, [f"{self.fps:4.1f} FPS   Q = quit   Space = I'm okay   Z = safe zone"
                                     "   C = camera off (test)"], scale=0.45)
        debug_view.draw_text(frame, [f"{label}{conf}"], origin=(10, 62), scale=1.0, colour=colour)
        if r:
            ratio = "-" if r.torso_ratio is None else f"{r.torso_ratio:.2f}"
            state = f"posture {r.posture}  torso ratio {ratio}  zone {r.zone or '-'}"
            debug_view.draw_text(frame, [feature_line(r), state], origin=(10, 92), scale=0.5)
        if self.guide:
            debug_view.draw_text(frame, [self.guide.instruction(elapsed)], origin=(10, 455),
                                 scale=0.8)
        key = debug_view.show(frame)
        if not self._mouse_ready:                      # the window exists only after the first show()
            debug_view.on_mouse(frame.shape[1], frame.shape[0], self.zone_click)
            self._mouse_ready = True
        return key

    def _open_frame_log(self) -> None:
        if not self.frame_log:
            return
        LOG_DIR.mkdir(exist_ok=True)
        path = LOG_DIR / f"frames_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        handle = open(path, "w", newline="", encoding="utf-8")
        writer = csv.writer(handle)
        writer.writerow(["t_s", "label", "confidence", "raw", "torso_deg", "knee_deg",
                         "hip_speed_down", "hip_shift_1s", "bbox_ratio",
                         "posture", "fall_state", "torso_ratio", "keypoints"])
        self._csv = (handle, writer)
        log.info("writing per-frame log to %s", path)
