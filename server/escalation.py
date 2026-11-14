"""Escalation engine (BUILD_PLAN Section 14): what happens after a fall.

States: monitoring -> checkin_1 -> (checkin_2) -> follow_up -> resolved, or -> escalate -> resolved.

The five hard rules live HERE, in code. The AI can only make an escalation happen sooner:
  1. No answer after two check-ins -> escalate, whatever the AI says.
  2. Help keywords (help, hurt, pain, can't get up, ...) in ANY reply heard during an incident ->
     escalate at once, before any AI call.
  3. Still on the floor (lying or fallen, outside a safe zone) 90 s after the fall, and nobody
     has acknowledged -> escalate, whatever was said.
  4. The AI call fails or takes longer than 5 s -> treated as no answer.
  5. The AI must choose an action allowed in the current state, and may not say "needs help" yet
     choose something else; anything else -> escalate.
Clarification (plan v2): an incident is never Resolved while the person is still on the floor
outside a safe zone, unless family has acknowledged.

Everything outside this file is passed in (room voice, AI, notifier, recorder, clock), so the
tests drive it with fakes. Time-based rules are checked by tick(), called about twice a second.

Locking: every input takes the engine lock, but nothing slow happens while it is held. Calls to
the notifier and the room are queued as "effects" and run after the lock is released, and the AI
is asked outside the lock too; answers that arrive after the incident has moved on are dropped.
"""
import asyncio
import functools
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from contracts import ContractError, validate_decision

log = logging.getLogger("guardian.escalation")

MONITORING, CHECKIN_1, CHECKIN_2 = "monitoring", "checkin_1", "checkin_2"
FOLLOW_UP, ESCALATE, RESOLVED = "follow_up", "escalate", "resolved"
ALLOWED_ACTIONS = {  # Section 12; the AI is never asked in the other states
    CHECKIN_1: {"follow_up", "ask_again", "escalate"},
    CHECKIN_2: {"follow_up", "escalate"},
    FOLLOW_UP: {"resolve", "escalate"},
}
ON_FLOOR = {"lying", "fallen"}
SIDE_CALL_TIMEOUT_S = 6.0   # a stuck notifier or room link is given up on, logged and retried
THINKING_MARGIN_S = 3.0     # if the AI step has not finished this long after its own timeout: no answer
KEYWORD_ENDINGS = "(?:s|es|ed|ing|ful|less)?"   # hurt -> hurts, hurting; pain -> painful


class Room(Protocol):
    async def speak_and_listen(self, incident_id: str, text: str, listen_seconds: float, attempt: int) -> None: ...
    async def speak(self, text: str) -> None: ...


class Agent(Protocol):
    async def decide(self, context: dict) -> dict: ...


class Notifier(Protocol):
    async def alert(self, incident: dict, attempt: int) -> None: ...
    async def gentle(self, incident: dict, request: str) -> None: ...
    async def acknowledged(self, incident: dict, by: str) -> None: ...


class Recorder(Protocol):
    """Stores incidents and their steps, and tells the dashboards."""

    async def opened(self, incident_id: str, reason: str, features: dict, ts: datetime,
                     simulated: bool) -> None: ...
    async def state(self, incident_id: str, old: str, new: str, ts: datetime, **fields) -> None: ...
    async def event(self, incident_id: str, state: str, kind: str, payload: dict, ts: datetime) -> None: ...
    async def decision(self, incident_id: str, state: str, decision: dict, ts: datetime) -> None: ...


class Clock(Protocol):
    def monotonic(self) -> float: ...
    def now(self) -> datetime: ...


class _SafeRecorder:
    """Wraps the recorder so that a storage or dashboard failure can never stop an alert."""

    def __init__(self, inner: Recorder) -> None:
        self._inner = inner

    def __getattr__(self, name: str):
        method = getattr(self._inner, name)

        async def call(*args, **kwargs) -> None:
            try:
                await method(*args, **kwargs)
            except Exception:
                log.exception("recording '%s' failed; the escalation flow continues", name)
        return call


class SystemClock:
    def monotonic(self) -> float:
        return asyncio.get_running_loop().time()

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


@dataclass
class _Listening:
    attempt: int
    deadline: float


@dataclass(eq=False)
class Active:
    """The open incident."""

    id: str
    reason: str
    started: float                        # monotonic time of the fall
    started_at: datetime
    simulated: bool = False
    state: str = CHECKIN_1
    attempts: int = 0                     # questions asked so far; each reply names its question
    listening: _Listening | None = None   # waiting for this voice_reply
    thinking_until: float | None = None   # the AI is deciding; past this time it counts as no answer
    posture: str = "fallen"
    zone: str | None = None
    last_question: str = ""
    last_transcript: str = ""
    last_reason: str = ""
    acked_by: str | None = None
    resolve_when_up: bool = False          # follow-up is done, but the person is still on the floor
    alerts: int = 0                        # family alerts delivered so far
    alert_in_flight: bool = False
    next_realert: float | None = None
    told_sent: bool = False                # said "I have messaged your family. Help is coming."
    told_pending: bool = False             # said "I am trying to reach your family."
    requests: set[str] = field(default_factory=set)
    epoch: int = 0                         # bumped on every state change; stale AI answers are dropped


def _flushes(method):
    """Public entry points: after the lock is released, run the queued notifier and room calls."""
    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        try:
            return await method(self, *args, **kwargs)
        finally:
            await self._flush()
    return wrapper


class EscalationEngine:
    """Runs the escalation flow for one room. Only one incident is open at a time."""

    def __init__(self, config: dict, room: Room, agent: Agent, notifier: Notifier, recorder: Recorder,
                 clock: Clock | None = None, room_name: str = "living_room") -> None:
        self.cfg = config
        self.room = room
        self.agent = agent
        self.notifier = notifier
        self.rec = _SafeRecorder(recorder)
        self.clock = clock or SystemClock()
        self.room_name = room_name
        self.active: Active | None = None
        self.zone: str | None = None       # safe zone from the latest activity message
        self._lock = asyncio.Lock()
        self._effects: list = []           # notifier / room calls waiting to run outside the lock
        self._keywords = [(k, self._keyword_pattern(k)) for k in config["help_keywords"]]

    # -- what the dashboards see ----------------------------------------------------------

    @property
    def incident_id(self) -> str | None:
        return self.active.id if self.active else None

    @property
    def state(self) -> str:
        return self.active.state if self.active else MONITORING

    # -- inputs ---------------------------------------------------------------------------

    @_flushes
    async def on_fall(self, incident_id: str, reason: str, features: dict, simulated: bool = False) -> None:
        """A fall_detected from the room agent (or a simulated fall)."""
        async with self._lock:
            now = self.clock.now()
            a = self.active
            if a is not None and a.simulated and not simulated:
                # a real fall must never be filed under a simulated incident
                await self.rec.event(a.id, a.state, "state", {"event": "closed_by_real_fall",
                                                              "real_incident_id": incident_id}, now)
                await self._resolve("Closed: a real fall was detected during this simulated incident.")
                a = None
            if a is not None:  # a second fall during an open incident is logged on that incident
                a.posture = "fallen"
                await self.rec.event(a.id, a.state, "state", {"event": "fall_detected_again", "reason": reason,
                                                              "room_incident_id": incident_id}, now)
                return
            self.active = Active(id=incident_id, reason=reason, started=self.clock.monotonic(),
                                 started_at=now, simulated=simulated, zone=self.zone)
            await self.rec.opened(incident_id, reason, features, now, simulated)
            log.warning("incident %s opened (%s)", incident_id, reason)
            await self._ask(self.cfg["phrases"]["checkin_1"], self.cfg["checkin1_listen_s"])

    @_flushes
    async def restore(self, incident_id: str, reason: str, started_at: datetime, state: str,
                      simulated: bool = False) -> None:
        """Start-up: a previous run left this incident unfinished. The check-in cannot be resumed,
        so the family is alerted, and re-alerted until someone acknowledges."""
        async with self._lock:
            if self.active is not None:
                return
            self.active = a = Active(id=incident_id, reason=reason, started=self.clock.monotonic(),
                                     started_at=started_at, simulated=simulated, state=state)
            await self.rec.event(a.id, a.state, "state", {"event": "restored_after_restart"}, self.clock.now())
            log.warning("incident %s restored after a restart (was %s)", incident_id, state)
            if a.state == ESCALATE:
                a.last_reason = "Guardian restarted; this alert had not been acknowledged."
                self._queue_alert()
            else:
                await self._escalate("Guardian restarted during this incident, so it is alerting the family "
                                     "to be safe.", rule=None)

    @_flushes
    async def on_posture(self, activity: str) -> None:
        """posture_update from the room agent: did the person get up?"""
        async with self._lock:
            if self.active is not None:
                self.active.posture = activity
            await self._resolve_if_up()

    @_flushes
    async def on_activity(self, activity: str, zone: str | None) -> None:
        """Every activity message: the latest label and safe zone."""
        async with self._lock:
            self.zone = zone
            if self.active is not None:
                self.active.zone = zone
                if activity != "absent":  # out of view: keep the last known posture
                    self.active.posture = activity
            await self._resolve_if_up()

    @_flushes
    async def on_voice_reply(self, incident_id: str, attempt: int, transcript: str, heard_speech: bool) -> None:
        """voice_reply from the room agent: what was heard after a question."""
        async with self._lock:
            a = self.active
            if a is None:
                return
            expected = (incident_id == a.id and a.listening is not None and a.listening.attempt == attempt)
            payload = {"attempt": attempt, "transcript": transcript, "heard_speech": heard_speech}
            if incident_id != a.id:
                payload["for_incident"] = incident_id
            await self.rec.event(a.id, a.state, "reply", payload, self.clock.now())
            keyword = self._help_keyword(transcript)
            if keyword:  # Rule 2: every transcript, whichever question it answers, before any AI call
                a.last_transcript = transcript
                await self._escalate(f'Help keyword heard: "{keyword}".', rule=2, assessment="needs_help")
                return
            if not expected:
                return  # late or unexpected reply: logged, nothing else
            a.listening = None
            a.last_transcript = transcript
            if not heard_speech or not transcript.strip():
                await self._no_answer("No answer was heard.", rule=None)
                return
            epoch = a.epoch
            a.thinking_until = self.clock.monotonic() + self.cfg["ai_timeout_s"] + THINKING_MARGIN_S
            context = {"state": a.state, "attempt": attempt, "question": a.last_question, "transcript": transcript,
                       "posture": a.posture, "in_safe_zone": a.zone is not None,
                       "seconds_since_fall": round(self.clock.monotonic() - a.started)}
        outcome, result = await self._ask_ai(context)  # outside the lock: may take up to 5 s
        async with self._lock:
            if self.active is not a or a.epoch != epoch:  # another incident, or this one moved on
                log.info("AI answer arrived after the incident moved on; ignored")
                return
            a.thinking_until = None
            if outcome == "failed":  # Rule 4
                await self._no_answer(f"The AI did not answer ({result}); treated as no answer.", rule=4)
            elif outcome == "refused":  # Rule 5
                await self._escalate(f"The AI gave {result}; escalating to be safe.", rule=5,
                                     assessment="needs_help")
            else:
                await self._apply(result)

    @_flushes
    async def acknowledge(self, incident_id: str, by: str) -> bool:
        """Family tapped Acknowledge (Telegram or dashboard). Resolves the open incident."""
        async with self._lock:
            a = self.active
            if a is None or incident_id != a.id:
                return False
            a.acked_by = by
            await self.rec.event(a.id, a.state, "ack", {"by": by}, self.clock.now())
            summary = self._summary()
            await self._resolve(f"Acknowledged by {by}.")
            self._effects.append(lambda: self._side_call(self.notifier.acknowledged(summary, by), "acknowledged"))
            return True

    @_flushes
    async def tick(self) -> None:
        """Timers: missing replies, a stuck AI step, Rule 3 (still on the floor), re-alerts."""
        async with self._lock:
            a = self.active
            if a is None:
                return
            now = self.clock.monotonic()
            if a.listening is not None and now >= a.listening.deadline:
                attempt, a.listening = a.listening.attempt, None
                await self.rec.event(a.id, a.state, "reply", {"attempt": attempt, "transcript": "",
                                                              "heard_speech": False, "missing": True},
                                     self.clock.now())
                await self._no_answer("No reply arrived from the room.", rule=None)
            if a is self.active and a.thinking_until is not None and now >= a.thinking_until:
                a.thinking_until = None
                a.epoch += 1  # whatever the AI still answers is too late
                await self._no_answer("The AI step did not finish; treated as no answer.", rule=4)
            if (a is self.active and a.state in (CHECKIN_1, CHECKIN_2, FOLLOW_UP) and a.acked_by is None
                    and now - a.started >= self.cfg["floor_rule_s"] and self._on_floor(a)):
                await self._escalate(f"Still on the floor {self.cfg['floor_rule_s']} s after the fall.",
                                     rule=3, assessment="needs_help")
            if (a is self.active and a.state == ESCALATE and not a.alert_in_flight
                    and a.next_realert is not None and now >= a.next_realert):
                self._queue_alert()

    # -- the flow -------------------------------------------------------------------------

    async def _apply(self, decision: dict) -> None:
        """Act on a validated AI decision (Rule 5 already checked)."""
        a = self.active
        await self.rec.decision(a.id, a.state, {**decision, "source": "ai"}, self.clock.now())
        a.last_reason = decision["reason"]
        await self._gentle(decision.get("request"))
        action = decision["action"]
        if action == "escalate":
            await self._escalate(decision["reason"], rule=None, already_recorded=True)
        elif action == "ask_again":
            await self._set_state(CHECKIN_2)
            await self._ask(self.cfg["phrases"]["checkin_2"], self.cfg["checkin2_listen_s"])
        elif action == "follow_up":
            await self._set_state(FOLLOW_UP)
            question = self._safe_say(decision.get("say")) or self.cfg["phrases"]["follow_up"]
            await self._ask(question, self.cfg["followup_listen_s"])
        elif action == "resolve":
            say = self._safe_say(decision.get("say"))
            if say:
                self._effects.append(lambda: self._side_call(self.room.speak(say), "speak"))
            a.resolve_when_up = True
            await self._resolve_if_up()

    async def _no_answer(self, reason: str, rule: int | None) -> None:
        """Silence, a missing reply or an AI failure, depending on the state (Rules 1 and 4)."""
        a = self.active
        if a.state == CHECKIN_1:
            await self._decide_in_code("no_response", "ask_again", reason + " Asking again.", rule)
            await self._set_state(CHECKIN_2)
            await self._ask(self.cfg["phrases"]["checkin_2"], self.cfg["checkin2_listen_s"])
        elif a.state == CHECKIN_2:  # Rule 1, unless a more specific rule (4) brought us here
            await self._escalate(reason + " No answer after two check-ins.", rule=rule or 1)
        elif a.state == FOLLOW_UP:
            await self._decide_in_code("ok", "resolve", reason + " No request recorded.", rule)
            a.resolve_when_up = True
            await self._resolve_if_up()

    async def _escalate(self, reason: str, rule: int | None, assessment: str = "no_response",
                        already_recorded: bool = False) -> None:
        a = self.active
        if a is None or a.state in (ESCALATE, RESOLVED):
            return
        if not already_recorded:
            await self._decide_in_code(assessment, "escalate", reason, rule)
        a.last_reason = reason
        a.listening = None
        await self._set_state(ESCALATE)
        log.warning("incident %s ESCALATED: %s", a.id, reason)
        self._queue_alert()

    def _queue_alert(self) -> None:
        """Send (or repeat) the family alert once the lock is released."""
        a = self.active
        a.alert_in_flight = True
        a.next_realert = None
        summary, attempt = self._summary(), a.alerts + 1
        self._effects.append(lambda: self._deliver_alert(a, summary, attempt))

    async def _deliver_alert(self, a: Active, summary: dict, attempt: int) -> None:
        """Runs outside the lock. Delivered: repeat every realert_every_s until acknowledged, and
        tell the person help is coming. Failed: retry after alert_retry_s, and say only that
        Guardian is trying - never claim an alert that did not go out."""
        sent = await self._side_call(self.notifier.alert(summary, attempt), "alert")
        phrase = None
        async with self._lock:
            now = self.clock.monotonic()
            step = {"attempt": attempt, "sent": sent}
            if getattr(self.notifier, "channel", None):    # "telegram" or "log", so the dashboard says which
                step["channel"] = self.notifier.channel
            await self.rec.event(a.id, a.state, "alert", step, self.clock.now())
            a.alert_in_flight = False
            if sent:
                a.alerts += 1
            if self.active is a and a.state == ESCALATE:
                a.next_realert = now + (self.cfg["realert_every_s"] if sent else self.cfg["alert_retry_s"])
                if sent and not a.told_sent:
                    phrase = "escalate"
                elif not sent and not a.told_sent and not a.told_pending:
                    phrase = "escalate_pending"
        # A sentence counts as said only if the room could be reached; otherwise the next alert tries again.
        if phrase and await self._side_call(self.room.speak(self.cfg["phrases"][phrase]), "speak"):
            if phrase == "escalate":
                a.told_sent = True
            else:
                a.told_pending = True

    async def _resolve_if_up(self) -> None:
        a = self.active
        if a is not None and a.resolve_when_up and a.state == FOLLOW_UP and not self._on_floor(a):
            await self._resolve("The person is up and has no urgent need.")

    async def _resolve(self, reason: str) -> None:
        a = self.active
        if a is None:
            return
        a.last_reason = reason
        await self._set_state(RESOLVED, resolved_at=self.clock.now(), acknowledged_by=a.acked_by)
        log.info("incident %s resolved: %s", a.id, reason)
        self.active = None

    async def _ask(self, text: str, listen_seconds: float) -> None:
        a = self.active
        a.attempts += 1
        incident_id, attempt = a.id, a.attempts
        a.last_question = text
        a.listening = _Listening(attempt, self.clock.monotonic() + listen_seconds + self.cfg["reply_grace_s"])
        await self.rec.event(a.id, a.state, "speak", {"text": text, "listen_seconds": listen_seconds,
                                                      "attempt": attempt}, self.clock.now())
        self._effects.append(lambda: self._side_call(
            self.room.speak_and_listen(incident_id, text, listen_seconds, attempt), "speak_and_listen"))

    async def _set_state(self, new: str, **fields) -> None:
        a = self.active
        old, a.state = a.state, new
        a.epoch += 1
        a.thinking_until = None
        await self.rec.state(a.id, old, new, self.clock.now(), **fields)

    async def _decide_in_code(self, assessment: str, action: str, reason: str, rule: int | None) -> None:
        decision = {"assessment": assessment, "action": action, "say": "", "request": None, "reason": reason,
                    "source": "hard_rule"}
        if rule is not None:
            decision["rule"] = rule
        await self.rec.decision(self.active.id, self.active.state, decision, self.clock.now())

    async def _gentle(self, request: str | None) -> None:
        """A request from the person goes to family as a non-urgent message (once each)."""
        a = self.active
        wanted = (request or "").strip()
        if not wanted or wanted.lower() in a.requests:
            return
        a.requests.add(wanted.lower())
        await self.rec.event(a.id, a.state, "request", {"request": wanted}, self.clock.now())
        summary = self._summary()
        self._effects.append(lambda: self._side_call(self.notifier.gentle(summary, wanted), "gentle"))

    # -- helpers --------------------------------------------------------------------------

    async def _flush(self) -> None:
        """Run the queued notifier and room calls, in order. Never called with the lock held."""
        while self._effects:
            effect = self._effects.pop(0)
            try:
                await effect()
            except Exception:
                log.exception("a notifier or room call failed")

    async def _ask_ai(self, context: dict) -> tuple[str, dict | str]:
        """("ok", decision) for a valid, consistent answer whose action is allowed in this state;
        ("refused", why) for an invalid, disallowed or inconsistent answer (Rule 5);
        ("failed", why) when the AI errors or takes longer than ai_timeout_s (Rule 4)."""
        try:
            raw = await asyncio.wait_for(self.agent.decide(context), self.cfg["ai_timeout_s"])
        except asyncio.TimeoutError:
            return "failed", f"no answer within {self.cfg['ai_timeout_s']} s"
        except Exception as exc:  # network, key, quota ... (never crash the engine)
            return "failed", type(exc).__name__
        try:
            decision = validate_decision(raw)
        except ContractError as exc:
            return "refused", f"an invalid answer ({exc})"
        if decision["action"] not in ALLOWED_ACTIONS[context["state"]]:
            return "refused", f'the action "{decision["action"]}", which is not allowed in {context["state"]}'
        if decision["assessment"] == "needs_help" and decision["action"] != "escalate":
            return "refused", f'"needs help" together with the action "{decision["action"]}"'
        return "ok", decision

    @staticmethod
    def _keyword_pattern(keyword: str) -> re.Pattern | None:
        """Whole-word matching for Latin keywords ("pain" matches "painful", not "painting" or
        "Spain"); None for other scripts, which are matched as plain text."""
        key = keyword.lower().replace("’", "").replace("'", "")
        if not key.isascii():
            return None
        ending = KEYWORD_ENDINGS if " " not in key else ""
        return re.compile(rf"(?<![a-z]){re.escape(key)}{ending}(?![a-z])")

    def _help_keyword(self, transcript: str) -> str | None:
        text = transcript.lower().replace("’", "").replace("'", "")  # can't / can’t / cant
        for keyword, pattern in self._keywords:
            if pattern.search(text) if pattern else keyword.lower() in text:
                return keyword
        return None

    def _safe_say(self, text: str | None) -> str | None:
        """The AI's own sentence, unless it is empty, too long, or contains a help keyword (asking
        "Do you need any help?" invites "No, I don't need help", which Rule 2 must act on)."""
        say = (text or "").strip()
        if not say or len(say) > self.cfg["max_say_chars"] or self._help_keyword(say):
            return None
        return say

    @staticmethod
    def _on_floor(a: Active) -> bool:
        return a.posture in ON_FLOOR and a.zone is None

    def _summary(self) -> dict:
        a = self.active
        return {"incident_id": a.id, "room": self.room_name, "reason": a.reason,
                "started_at": a.started_at.isoformat(timespec="seconds"), "state": a.state,
                "transcript": a.last_transcript, "ai_reason": a.last_reason, "posture": a.posture,
                "simulated": a.simulated}

    async def _side_call(self, coro, what: str) -> bool:
        """Run a notifier or room call; a failure is logged, never fatal to the flow."""
        try:
            await asyncio.wait_for(coro, SIDE_CALL_TIMEOUT_S)
            return True
        except Exception as exc:
            log.error("%s failed: %s", what, type(exc).__name__)
            return False
