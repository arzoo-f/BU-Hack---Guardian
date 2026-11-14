"""Check check-in decisions against the real OpenAI model (BUILD_PLAN steps 3.10 and 3.11).

For each sample reply it shows:
  - what Guardian does: a fall, then the reply played through the real escalation engine
    (hard rules first, then the AI), with fake voice, notifier and recorder
  - what the AI alone would say, and how long it took (every answer is checked against the schema)

    .venv\\Scripts\\python.exe scripts\\ai_check.py               # the six sample replies (CP3.3)
    .venv\\Scripts\\python.exe scripts\\ai_check.py --wrong-key   # invalid key for this run only (3.11)

The API key is read from .env and never printed. --wrong-key never touches .env.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "server"), str(ROOT)]

from dotenv import load_dotenv  # noqa: E402

from agent import OpenAIAgent  # noqa: E402
from contracts import ContractError, validate_decision  # noqa: E402
from escalation import EscalationEngine  # noqa: E402

SAMPLES = ["I'm okay, I just slipped", "", "help me, I can't get up", "my hip hurts", "yes", "what?"]
CHECKIN_1 = "Are you okay? Please say yes or no."
FOLLOW_UP = "Glad you're okay. Do you need anything?"
EXTRA = [  # (state, question, reply, acceptable actions) - a guard against the prompt drifting
    ("checkin_1", CHECKIN_1, "no", {"escalate"}),
    ("checkin_1", CHECKIN_1, "I'm okay but I feel a bit dizzy", {"escalate"}),
    ("checkin_1", CHECKIN_1, "yeah yeah I'm alright, just embarrassed", {"follow_up"}),
    ("checkin_1", CHECKIN_1, "I fell but I'm fine", {"follow_up"}),
    ("checkin_2", "Can you hear me? Say yes if you are okay.", "yes", {"follow_up"}),
    ("checkin_2", "Can you hear me? Say yes if you are okay.", "uh... what happened", {"escalate"}),
    ("follow_up", FOLLOW_UP, "No thank you", {"resolve"}),
    ("follow_up", FOLLOW_UP, "Some water, please", {"resolve"}),
    ("follow_up", FOLLOW_UP, "Actually my wrist is swelling up", {"escalate"}),
]
WRONG_KEY = "deliberately-invalid-key-for-the-wrong-key-test"  # not key-shaped: keeps secret scans clean


class Quiet:
    """Fake room, notifier and recorder: remember what happened, send nothing."""

    def __init__(self) -> None:
        self.decisions, self.alerts = [], []

    async def speak_and_listen(self, *a): ...
    async def speak(self, *a): ...
    async def alert(self, incident, attempt): self.alerts.append(attempt)
    async def gentle(self, *a): ...
    async def acknowledged(self, *a): ...
    async def opened(self, *a): ...
    async def state(self, *a, **k): ...
    async def event(self, *a): ...
    async def decision(self, incident_id, state, decision, ts): self.decisions.append(decision)


class Clock:
    def monotonic(self) -> float:
        return time.monotonic()

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def make_engine(agent) -> tuple[EscalationEngine, Quiet]:
    config = json.loads((ROOT / "config" / "escalation.json").read_text(encoding="utf-8"))
    quiet = Quiet()
    return EscalationEngine(config, quiet, agent, quiet, quiet, Clock()), quiet


async def guardian_does(agent, transcript: str) -> str:
    """Fall, then this reply to check-in 1: what Guardian decides and the next state."""
    engine, quiet = make_engine(agent)
    await engine.on_fall("inc_check", "fast_fall", {})
    await engine.on_voice_reply("inc_check", 1, transcript, bool(transcript))
    d = quiet.decisions[-1]
    who = f"hard rule {d['rule']}" if d.get("source") == "hard_rule" and d.get("rule") else (
        "code (no speech)" if d.get("source") == "hard_rule" else "AI")
    return f"{d['action']} ({who}) -> {engine.state}"


async def ai_alone(agent, transcript: str) -> tuple[str, str, float]:
    context = {"state": "checkin_1", "attempt": 1, "question": "Are you okay? Please say yes or no.",
               "transcript": transcript, "posture": "fallen", "in_safe_zone": False, "seconds_since_fall": 9}
    start = time.perf_counter()
    try:
        decision = validate_decision(await agent.decide(context))
        return decision["action"], decision["reason"], time.perf_counter() - start
    except ContractError as exc:
        return "INVALID", str(exc)[:60], time.perf_counter() - start
    except Exception as exc:
        return "ERROR", type(exc).__name__, time.perf_counter() - start


async def extra_checks(agent) -> int:
    """The AI alone on EXTRA; returns the number of answers outside the acceptable set."""
    print(f"\n{'State':10s} | {'Reply':42s} | {'AI says':10s} | {'request':20s} | ok?")
    print("-" * 100)
    wrong = 0
    for state, question, transcript, acceptable in EXTRA:
        context = {"state": state, "attempt": 1, "question": question, "transcript": transcript,
                   "posture": "standing" if state == "follow_up" else "fallen", "in_safe_zone": False,
                   "seconds_since_fall": 20}
        try:
            decision = validate_decision(await agent.decide(context))
            action, request = decision["action"], decision["request"] or "-"
        except Exception as exc:
            action, request = "ERROR", type(exc).__name__
        ok = action in acceptable
        wrong += not ok
        print(f"{state:10s} | {transcript:42s} | {action:10s} | {request[:20]:20s} | {'yes' if ok else 'NO'}")
    return wrong


async def silent_scenario(agent) -> str:
    """Two check-ins with no usable answer must end in an escalation."""
    engine, quiet = make_engine(agent)
    await engine.on_fall("inc_silent", "fast_fall", {})
    await engine.on_voice_reply("inc_silent", 1, "yes", True)       # the AI fails -> Rule 4 -> ask again
    await engine.on_voice_reply("inc_silent", 2, "", False)         # silence -> Rule 1
    rules = [d.get("rule") for d in quiet.decisions]
    return f"states end in {engine.state}, rules {rules}, alerts sent {quiet.alerts}"


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wrong-key", action="store_true", help="use an invalid key for this run only")
    p.add_argument("--more", action="store_true", help="also check extra replies against expected actions")
    args = p.parse_args()
    load_dotenv(ROOT / ".env")
    model = os.environ.get("OPENAI_MODEL", "")
    if not model or not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_MODEL and OPENAI_API_KEY must be set in .env")
        return 1
    from openai import AsyncOpenAI
    key = WRONG_KEY if args.wrong_key else os.environ["OPENAI_API_KEY"]
    agent = OpenAIAgent(model, client=AsyncOpenAI(api_key=key, timeout=6.0, max_retries=0))
    print(f"Model: {model}{'   (DELIBERATELY WRONG KEY)' if args.wrong_key else ''}\n")
    print(f"{'Reply':28s} | {'Guardian does':40s} | {'AI alone would say':18s} | {'time':>5s} | AI's reason")
    print("-" * 140)
    worst = 0.0
    for transcript in SAMPLES:
        does = await guardian_does(agent, transcript)
        action, reason, seconds = await ai_alone(agent, transcript)
        worst = max(worst, seconds)
        shown = f'"{transcript}"' if transcript else "(silence)"
        print(f"{shown:28s} | {does:40s} | {action:18s} | {seconds:4.1f}s | {reason}")
    print(f"\nSlowest AI answer: {worst:.1f} s (limit {json.loads((ROOT / 'config' / 'escalation.json').read_text())['ai_timeout_s']} s)")
    if args.wrong_key:
        print("Silent scenario with the wrong key:", await silent_scenario(agent))
    if args.more:
        wrong = await extra_checks(agent)
        print(f"\n{len(EXTRA) - wrong} of {len(EXTRA)} extra replies handled as expected")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
