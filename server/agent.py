"""AI decisions for voice check-ins (BUILD_PLAN step 3.5).

The agent only PROPOSES what happens next. server/escalation.py validates every answer, applies the
five hard rules and has the final say. Two agents:
  FakeAgent   - simple word rules, no network; for tests and mock runs
  OpenAIAgent - GPT with a strict JSON schema (model from OPENAI_MODEL in .env)
"""
import json
import logging
import os
from pathlib import Path

log = logging.getLogger("guardian.agent")

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"checkin_1": ["follow_up", "ask_again", "escalate"],
           "checkin_2": ["follow_up", "escalate"],
           "follow_up": ["resolve", "escalate"]}

SYSTEM_PROMPT = """\
You are the voice check-in assistant of Guardian, a fall-detection safety aid for an older person \
who lives alone. A possible fall was just detected and the person was asked `question` out loud. \
`transcript` is their reply. Choose what happens next.

A fall was just detected, so the person saying they fell, slipped or tripped is expected and is \
NOT by itself a sign of injury. Judge how they say they are.

Choose ONLY from the allowed actions you are given:
- follow_up: the person says they are okay, fine or alright - including a plain "yes" to "Are you \
okay?" or "Can you hear me? Say yes if you are okay." `say` = one short, kind question asking \
whether they need anything, e.g. "Glad you're okay. Do you need anything?".
- ask_again: (check-in 1 only) the reply is unclear, off-topic or cut off.
- escalate: any sign of pain, injury, bleeding, dizziness, confusion or distress; any request for \
help; "no" or "not really" to "Are you okay?"; or a still-unclear answer at check-in 2. When in \
doubt about their safety, escalate.
- resolve: (follow-up only) the person says they need nothing, or names something they would like. \
Put that thing in `request`, e.g. "a glass of water".

`request` is null unless the person asks for something. `reason` is one short sentence for the \
family explaining your choice. Keep `say` under 15 words, calm and plain; it may be empty for \
escalate and resolve. Do not use the words "help", "hurt" or "pain" in `say`. Never promise \
medical help and never diagnose. If you judge that the person needs help, the action must be \
escalate."""


def _enums() -> dict:
    common = json.loads((ROOT / "contracts" / "common.schema.json").read_text(encoding="utf-8"))["$defs"]
    return {"assessment": common["assessment"]["enum"], "action": common["action"]["enum"]}


def decision_schema(state: str) -> dict:
    """Strict JSON schema for OpenAI structured output; the action list is limited to `state`."""
    enums = _enums()
    return {
        "type": "object", "additionalProperties": False,
        "required": ["assessment", "action", "say", "request", "reason"],
        "properties": {
            "assessment": {"type": "string", "enum": enums["assessment"]},
            "action": {"type": "string", "enum": [a for a in enums["action"] if a in ALLOWED[state]]},
            "say": {"type": "string"},
            "request": {"type": ["string", "null"]},
            "reason": {"type": "string"},
        },
    }


def user_message(context: dict) -> str:
    """The facts the AI decides on, as JSON."""
    return json.dumps({**context, "allowed_actions": ALLOWED[context["state"]]}, ensure_ascii=False)


class FakeAgent:
    """Word rules standing in for GPT. Never use it as a safety judgement."""

    OK_WORDS = ("okay", "ok", "fine", "yes", "alright", "all right", "i'm good")

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def decide(self, context: dict) -> dict:
        self.calls.append(context)
        text, state = context["transcript"].lower(), context["state"]
        if state == "follow_up":
            wants = "please" in text or "could" in text or "can i have" in text
            return {"assessment": "ok", "action": "resolve", "say": "", "request": text.strip() if wants else None,
                    "reason": "Fake AI: follow-up answered."}
        if any(w in text for w in self.OK_WORDS):
            return {"assessment": "ok", "action": "follow_up", "say": "Glad you're okay. Do you need anything?",
                    "request": None, "reason": "Fake AI: the person said they are okay."}
        if state == "checkin_1":
            return {"assessment": "unclear", "action": "ask_again", "say": "", "request": None,
                    "reason": "Fake AI: the reply was unclear."}
        return {"assessment": "unclear", "action": "escalate", "say": "", "request": None,
                "reason": "Fake AI: still unclear at the second check-in."}


class OpenAIAgent:
    """GPT decisions with structured output. Raises on any problem; the engine treats that as
    "no answer" (Rule 4) and validates every answer itself (Rule 5)."""

    def __init__(self, model: str, client=None, timeout_s: float = 6.0) -> None:
        self.model = model
        if client is None:
            from openai import AsyncOpenAI  # imported here so tests and mock mode need no key
            client = AsyncOpenAI(timeout=timeout_s, max_retries=0)  # a retry would blow the 5 s limit
        self.client = client

    async def decide(self, context: dict) -> dict:
        extra = {"reasoning_effort": "none"} if self.model.startswith("gpt-5") else {}
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": user_message(context)}],
            response_format={"type": "json_schema", "json_schema": {
                "name": "guardian_decision", "strict": True, "schema": decision_schema(context["state"])}},
            **extra,
        )
        message = response.choices[0].message
        if getattr(message, "refusal", None):
            raise RuntimeError("the model refused to answer")
        return json.loads(message.content)


def make_agent() -> FakeAgent | OpenAIAgent:
    """OpenAIAgent when a key and model are configured, otherwise the FakeAgent (with a warning).
    GUARDIAN_FAKE_AI=1 forces the fake, e.g. for mock-only work."""
    model = os.environ.get("OPENAI_MODEL", "")
    if os.environ.get("GUARDIAN_FAKE_AI") == "1" or not os.environ.get("OPENAI_API_KEY") or not model:
        log.warning("using the FAKE AI agent (word rules, no OpenAI)")
        return FakeAgent()
    log.info("using OpenAI model %s for check-in decisions", model)
    return OpenAIAgent(model)
