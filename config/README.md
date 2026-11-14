# config

Thresholds and timings, so tuning never needs code changes (BUILD_PLAN Section 11).

- `vision.json` - activity and fall thresholds (starting values; the clips decide the real ones).
- `escalation.json` - check-in timings and help keywords. Keywords may be extended, never shortened.
- `zones.json` - safe-zone polygons (sofa, bed). Corners are fractions (0-1) of image width and height.

Secrets and machine settings live in `.env` (see `.env.example`), not here.
