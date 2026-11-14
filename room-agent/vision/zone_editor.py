"""Draw the safe zones in the debug window (BUILD_PLAN step 8.1).

Z starts a zone (the first Z after a save starts again from no zones; Z while drawing finishes the
current zone and starts the next), each left click adds a corner, a right click or Backspace
removes the last one, S saves, Esc cancels. The first zone is called "sofa", the second "bed".
Saved zones are written to config/zones.json; the vision loop applies them at once and sends them
to the server, so the dashboard shows them.
"""
import json
from datetime import datetime
from pathlib import Path

from vision.zones import Zones

NAMES = ["sofa", "bed"]


class ZoneEditor:
    """The drawing state; positions are image fractions (0-1). Knows nothing about OpenCV."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.drawing = False
        self.finished: list[dict] = []                   # zones completed in this drawing session
        self.corners: list[tuple[float, float]] = []     # the zone being drawn
        self.message = ""                                # last outcome, shown in the window

    @property
    def name(self) -> str:
        """Name of the zone being drawn."""
        n = len(self.finished)
        return NAMES[n] if n < len(NAMES) else f"zone {n + 1}"

    def start(self) -> None:
        """Z: start drawing, or finish the current zone and start the next one."""
        if self.drawing:
            self._finish_current()
        else:
            self.drawing, self.finished = True, []
        self.corners = []
        self.message = ""

    def click(self, x: float, y: float) -> None:
        if self.drawing:
            self.corners.append((round(min(max(x, 0.0), 1.0), 3), round(min(max(y, 0.0), 1.0), 3)))

    def undo(self) -> None:
        if self.drawing and self.corners:
            self.corners.pop()

    def cancel(self) -> None:
        """Esc: forget the drawing; the saved zones stay as they were."""
        if self.drawing:
            self.drawing, self.finished, self.corners = False, [], []
            self.message = "Cancelled - the saved zones are unchanged"

    def save(self) -> Zones | None:
        """S: write config/zones.json and return the new zones (None when there is nothing to save)."""
        if not self.drawing:
            return None
        self._finish_current()
        if not self.finished:
            self.message = "A zone needs at least 3 corners - keep clicking, then press S"
            return None
        data = {"note": f"Drawn in the debug window on {datetime.now():%a %d %b %Y %H:%M} (BUILD_PLAN 8.1).",
                "zones": self.finished}
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        zones = Zones(self.finished)
        self.message = "Saved: " + ", ".join(z["name"] for z in self.finished)
        self.drawing, self.finished, self.corners = False, [], []
        return zones

    def _finish_current(self) -> None:
        if len(self.corners) >= 3:
            self.finished.append({"name": self.name, "polygon": [list(c) for c in self.corners]})
        self.corners = []
