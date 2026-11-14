"""Contract tests (BUILD_PLAN step 1.3): every example message is checked against its schema."""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from contracts import ContractError, message_types, validate, validate_decision
from contracts.validate import SCHEMAS

EXAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "examples"
VALID = sorted((EXAMPLES / "valid").glob("*.json"))
INVALID = sorted((EXAMPLES / "invalid").glob("*.json"))

# Every message type named in BUILD_PLAN Section 12.
EXPECTED = {
    "room": ["activity", "fall_detected", "pose", "posture_update", "status", "voice_reply"],
    "command": ["speak", "speak_and_listen"],
    "dashboard": ["activity", "decision", "incident_update", "pose", "status"],
}


def _check(path: Path) -> dict:
    """Validate an example file; the channel is the first part of its name."""
    channel = path.name.split(".")[0]
    message = json.loads(path.read_text(encoding="utf-8"))
    return validate_decision(message) if channel == "decision" else validate(channel, message)


@pytest.mark.parametrize("path", list(SCHEMAS), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_schema_files_are_valid_json_schema(path):
    Draft202012Validator.check_schema(SCHEMAS[path])


def test_every_message_type_has_a_schema():
    for channel, types in EXPECTED.items():
        assert message_types(channel) == types


def test_every_message_type_has_a_valid_example():
    covered = {tuple(p.name.split(".")[:2]) for p in VALID}
    missing = [(c, t) for c, types in EXPECTED.items() for t in types if (c, t) not in covered]
    assert not missing, f"no valid example for {missing}"
    assert any(p.name.startswith("decision.") for p in VALID)


@pytest.mark.parametrize("path", VALID, ids=lambda p: p.name)
def test_valid_examples_pass(path):
    _check(path)


@pytest.mark.parametrize("path", INVALID, ids=lambda p: p.name)
def test_invalid_examples_are_rejected(path):
    with pytest.raises(ContractError):
        _check(path)


def test_error_message_names_the_bad_field():
    bad = {"type": "status", "ts": "2026-11-14T10:02:05Z", "camera": "ok", "fps": -1}
    with pytest.raises(ContractError, match="fps"):
        validate("room", bad)


def test_non_object_and_unknown_channel():
    with pytest.raises(ContractError):
        validate("room", ["not", "an", "object"])
    with pytest.raises(ValueError):
        validate("radio", {"type": "status"})
