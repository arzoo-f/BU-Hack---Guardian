"""Room agent settings: config/vision.json plus paths. Thresholds never live in the code."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = Path(__file__).resolve().parent
MODELS_DIR = AGENT_DIR / "models"


def load_vision_config(path: Path | None = None) -> dict:
    """Read config/vision.json (BUILD_PLAN Section 11)."""
    return json.loads((path or ROOT / "config" / "vision.json").read_text(encoding="utf-8"))


def model_path(config: dict) -> Path:
    """Full path of the MediaPipe model file named in the config."""
    return MODELS_DIR / config["model"]
