"""Load the Guardian message contracts and validate messages against them.

Schemas live next to this file: room/ (room agent -> server), command/ (server -> room agent),
dashboard/ (server -> dashboard) and ai_decision.schema.json (GPT output). Shared field
definitions are in common.schema.json and are referenced by $id.
"""
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
CHANNELS = ("room", "command", "dashboard")


class ContractError(ValueError):
    """A message does not match its contract."""


def _load_schemas() -> dict[Path, dict]:
    return {p: json.loads(p.read_text(encoding="utf-8")) for p in sorted(HERE.rglob("*.schema.json"))}


SCHEMAS = _load_schemas()
_REGISTRY = Registry().with_resources(
    (schema["$id"], Resource.from_contents(schema)) for schema in SCHEMAS.values()
)
_VALIDATORS: dict[tuple[str, str], Draft202012Validator] = {
    (path.parent.name, path.name.removesuffix(".schema.json")): Draft202012Validator(schema, registry=_REGISTRY)
    for path, schema in SCHEMAS.items()
    if path.parent.name in CHANNELS
}
_DECISION = Draft202012Validator(SCHEMAS[HERE / "ai_decision.schema.json"], registry=_REGISTRY)


def message_types(channel: str) -> list[str]:
    """Return the message types defined for a channel, e.g. message_types("room")."""
    return sorted(t for c, t in _VALIDATORS if c == channel)


def _check(validator: Draft202012Validator, data: object, label: str) -> None:
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(map(str, e.absolute_path)) or '(message)'}: {e.message}" for e in errors[:3]
        )
        raise ContractError(f"{label}: {detail}")


def validate(channel: str, message: object) -> dict:
    """Check one message against its contract.

    Returns the message unchanged, or raises ContractError with a short explanation.
    """
    if channel not in CHANNELS:
        raise ValueError(f"unknown channel {channel!r}; expected one of {CHANNELS}")
    if not isinstance(message, dict):
        raise ContractError(f"{channel}: message must be a JSON object")
    mtype = message.get("type")
    validator = _VALIDATORS.get((channel, mtype))
    if validator is None:
        raise ContractError(f"{channel}: unknown message type {mtype!r}")
    _check(validator, message, f"{channel}/{mtype}")
    return message


def validate_decision(decision: object) -> dict:
    """Check a GPT decision against ai_decision.schema.json (schema only, not the per-state rules)."""
    _check(_DECISION, decision, "ai_decision")
    return decision  # type: ignore[return-value]
