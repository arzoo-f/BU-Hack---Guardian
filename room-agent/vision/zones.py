"""Safe zones (sofa, bed): lying with the hip centre inside a zone means resting, not falling.

Zones are polygons in image fractions (0-1), read from config/zones.json (BUILD_PLAN Section 11).
"""
import json
from pathlib import Path

from settings import ROOT

Polygon = list[tuple[float, float]]


def point_in_polygon(x: float, y: float, polygon: Polygon) -> bool:
    """Ray casting: is (x, y) inside the polygon?"""
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


class Zones:
    """The safe zones of one camera view."""

    def __init__(self, zones: list[dict] | None = None) -> None:
        self.zones: list[tuple[str, Polygon]] = [
            (z["name"], [(float(px), float(py)) for px, py in z["polygon"]]) for z in zones or []]

    def at(self, x: float, y: float) -> str | None:
        """Name of the zone containing the point (image fractions), or None."""
        for name, polygon in self.zones:
            if point_in_polygon(x, y, polygon):
                return name
        return None

    def as_list(self) -> list[dict]:
        return [{"name": name, "polygon": [list(p) for p in polygon]} for name, polygon in self.zones]


def load_zones(config: dict, root: Path = ROOT) -> Zones:
    """Read the zones file named in config/vision.json; no file means no zones."""
    path = root / config["zones_file"]
    if not path.exists():
        return Zones()
    return Zones(json.loads(path.read_text(encoding="utf-8")).get("zones", []))
