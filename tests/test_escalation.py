"""Escalation engine tests (BUILD_PLAN step 3.4): the ten required tests plus edge cases.

Fakes replace the room voice, the AI, the notifier, the recorder and the clock, so 90-second and
2-minute timers run instantly.
"""
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from escalation import CHECKIN_1, CHECKIN_2, ESCALATE, FOLLOW_UP, RESOLVED, EscalationEngine

CONFIG = json.loads((Path(__file__).resolve().parents[1] / "config" / "escalation.json").read_text("utf-8"))
PHRASES = CONFIG["phrases"]


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0
        self.base = datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc)

    def monotonic(self) -> float:
        return self.t

    def now(self) -> datetime:
        return self.base + timedelta(seconds=self.t)


class FakeRoom:
    def __init__(self) -> None:
        self.said: list[tuple] = []
        self.attempts: list[int] = []     # the question numbers the server sent
        self.offline = False              # the room agent is not connected

    async def speak_and_listen(self, incident_id, text, listen_seconds, attempt):
        if self.offline:
            raise ConnectionError("room agent not connected")
        self.said.append(("ask", text, listen_seconds))
        self.attempts.append(attempt)

    def spoken(self) -> list[str]:
        """Sentences said without listening afterwards."""
        return [s[1] for s in self.said if s[0] == "say"]

    async def speak(self, text):
        if self.offline:
            raise ConnectionError("room agent not connected")
        self.said.append(("say", text))


class FakeAgent:
    """Answers with scripted decisions (dicts), raises scripted exceptions, or waits on a gate."""

    def __init__(self, *answers) -> None:
        self.answers = list(answers)
        self.calls: list[dict] = []
        self.gate: asyncio.Event | None = None

    async def decide(self, context):
        self.calls.append(context)
        if self.gate is not None:
            await self.gate.wait()
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        if answer == "hang":
            await asyncio.sleep(10)
        return answer


class FakeNotifier:
    """Records alerts; can fail (Telegram down) or hang on a gate (Telegram slow)."""

    def __init__(self, fail: bool = False) -> None:
        self.alerts: list[int] = []
        self.gentle_requests: list[str] = []
        self.acks: list[str] = []
        self.fail = fail
        self.tries = 0
        self.gate: asyncio.Event | None = None

    async def alert(self, incident, attempt):
        self.tries += 1
        if self.gate is not None:
            await self.gate.wait()
        if self.fail:
            raise ConnectionError("telegram down")
        self.alerts.append(attempt)

    async def gentle(self, incident, request):
        self.gentle_requests.append(request)

    async def acknowledged(self, incident, by):
        self.acks.append(by)


class FakeRecorder:
    def __init__(self) -> None:
        self.incidents: list[str] = []
        self.states: list[tuple] = []
        self.events: list[tuple] = []
        self.decisions: list[dict] = []
        self.fields: dict = {}

    async def opened(self, incident_id, reason, features, ts, simulated):
        self.incidents.append(incident_id)

    async def state(self, incident_id, old, new, ts, **fields):
        self.states.append((old, new))
        self.fields.update(fields)

    async def event(self, incident_id, state, kind, payload, ts):
        self.events.append((kind, payload))

    async def decision(self, incident_id, state, decision, ts):
        self.decisions.append(decision)


def ai(action: str, assessment: str = "ok", say: str = "", request=None, reason: str = "test") -> dict:
    return {"assessment": assessment, "action": action, "say": say, "request": request, "reason": reason}


class World:
    """An engine wired to fakes, with helpers to play a scenario."""

    def __init__(self, *answers, config: dict | None = None, notifier: FakeNotifier | None = None) -> None:
        self.clock, self.room, self.agent = FakeClock(), FakeRoom(), FakeAgent(*answers)
        self.notifier, self.rec = notifier or FakeNotifier(), FakeRecorder()
        self.engine = EscalationEngine(config or CONFIG, self.room, self.agent, self.notifier, self.rec, self.clock)

    async def fall(self, incident_id: str = "inc_001") -> None:
        await self.engine.on_fall(incident_id, "fast_fall", {"torso_angle": 70})

    async def reply(self, transcript: str, heard: bool = True) -> None:
        attempt = self.engine.active.listening.attempt
        await self.engine.on_voice_reply(self.engine.active.id, attempt, transcript, heard)

    async def at(self, seconds: float) -> None:
        """Move the clock to `seconds` after the start, ticking twice a second on the way."""
        while self.clock.t < seconds:
            self.clock.t = min(self.clock.t + 0.5, seconds)
            await self.engine.tick()

    @property
    def path(self) -> list[str]:
        return [new for _, new in self.rec.states]

    def rules(self) -> list:
        return [d.get("rule") for d in self.rec.decisions if d["action"] == "escalate"]


# -- the ten tests required by BUILD_PLAN Section 14 ---------------------------------------------

async def test_ok_and_up_goes_to_followup_and_resolves():
    w = World(ai("follow_up", say="Glad you're okay. Do you need anything?"), ai("resolve"))
    await w.fall()
    assert w.engine.state == CHECKIN_1 and w.room.said == [("ask", PHRASES["checkin_1"], 6)]
    await w.engine.on_posture("standing")
    await w.reply("I'm okay, I just slipped")
    assert w.engine.state == FOLLOW_UP
    assert w.room.said[-1] == ("ask", "Glad you're okay. Do you need anything?", CONFIG["followup_listen_s"])
    await w.reply("No thank you")
    assert w.path == [FOLLOW_UP, RESOLVED] and w.engine.active is None
    assert w.notifier.alerts == [] and w.notifier.gentle_requests == []
    assert [c["state"] for c in w.agent.calls] == [CHECKIN_1, FOLLOW_UP]


async def test_request_sends_gentle_message():
    w = World(ai("follow_up"), ai("resolve", request="a glass of water"))
    await w.fall()
    await w.engine.on_posture("standing")
    await w.reply("Yes, I slipped")
    assert w.room.said[-1][1] == PHRASES["follow_up"]   # the AI gave no say text: fixed phrase
    await w.reply("Some water, please")
    assert w.notifier.gentle_requests == ["a glass of water"]
    assert ("request", {"request": "a glass of water"}) in w.rec.events
    assert w.engine.state == "monitoring" and w.notifier.alerts == []


async def test_silence_twice_escalates():  # Rule 1
    w = World()
    await w.fall()
    await w.reply("", heard=False)
    assert w.engine.state == CHECKIN_2 and w.room.said[-1] == ("ask", PHRASES["checkin_2"], 8)
    await w.reply("", heard=False)
    assert w.engine.state == ESCALATE and w.rules() == [1]
    assert w.notifier.alerts == [1] and ("say", PHRASES["escalate"]) in w.room.said
    assert w.agent.calls == []                          # silence never needs the AI


@pytest.mark.parametrize("words", ["help me, I can't get up", "My hip HURTS", "cannot get up", "救命",
                                   "I can’t get up"])
async def test_help_keyword_escalates_without_ai_call(words):  # Rule 2
    w = World(ai("follow_up"))
    await w.fall()
    await w.reply(words)
    assert w.engine.state == ESCALATE and w.rules() == [2]
    assert w.agent.calls == []                          # decided before any AI call
    assert w.rec.decisions[-1]["source"] == "hard_rule"


async def test_ok_but_still_on_floor_escalates_at_90s():  # Rule 3
    w = World(ai("follow_up"), ai("resolve"))
    await w.fall()
    await w.reply("I'm okay")
    await w.reply("No, nothing")                        # says okay, but never gets up
    assert w.engine.state == FOLLOW_UP                  # cannot resolve while on the floor
    await w.at(CONFIG["floor_rule_s"] - 0.5)
    assert w.engine.state == FOLLOW_UP
    await w.at(CONFIG["floor_rule_s"])
    assert w.engine.state == ESCALATE and w.rules() == [3] and w.notifier.alerts == [1]


async def test_ai_timeout_counts_as_no_answer():  # Rule 4
    fast = {**CONFIG, "ai_timeout_s": 0.05}
    w = World("hang", RuntimeError("invalid api key"), config=fast)
    await w.fall()
    await w.reply("yes I think so")                     # AI too slow: counts as no answer
    assert w.engine.state == CHECKIN_2 and w.rec.decisions[-1]["rule"] == 4
    await w.reply("yes")                                # AI errors: no answer again
    assert w.engine.state == ESCALATE and w.rules() == [4]


@pytest.mark.parametrize("bad, state", [
    (ai("resolve"), CHECKIN_1),                         # not allowed in check-in 1
    (ai("call_ambulance"), CHECKIN_1),                  # not an action at all
    ({"action": "follow_up", "say": "ok"}, CHECKIN_1),  # fields missing
    ("not even a dict", CHECKIN_1),
    (ai("ask_again"), CHECKIN_2),                       # not allowed in check-in 2
], ids=["resolve-in-checkin1", "unknown-action", "missing-fields", "not-json", "ask_again-in-checkin2"])
async def test_invalid_or_disallowed_action_escalates(bad, state):  # Rule 5
    w = World(bad) if state == CHECKIN_1 else World(ai("ask_again"), bad)
    await w.fall()
    if state == CHECKIN_2:
        await w.reply("what?")
        assert w.engine.state == CHECKIN_2
    await w.reply("hmm")
    assert w.engine.state == ESCALATE and w.rules() == [5]
    assert w.rec.decisions[-1]["source"] == "hard_rule"


async def test_realert_every_2_min_until_ack():
    w = World()
    await w.fall()
    await w.reply("", heard=False)
    await w.reply("", heard=False)
    escalated = w.clock.t
    await w.at(escalated + CONFIG["realert_every_s"] - 1)
    assert w.notifier.alerts == [1]
    await w.at(escalated + CONFIG["realert_every_s"])
    assert w.notifier.alerts == [1, 2]
    await w.at(escalated + 2 * CONFIG["realert_every_s"])
    assert w.notifier.alerts == [1, 2, 3]
    assert await w.engine.acknowledge("inc_001", "Person B")
    await w.at(escalated + 10 * CONFIG["realert_every_s"])
    assert w.notifier.alerts == [1, 2, 3]


@pytest.mark.parametrize("by", ["dashboard", "telegram: Person B"])
async def test_ack_from_dashboard_or_telegram_resolves(by):
    w = World()
    await w.fall()
    await w.reply("", heard=False)
    await w.reply("", heard=False)
    assert w.engine.state == ESCALATE
    assert await w.engine.acknowledge("inc_001", by) is True
    assert w.path[-1] == RESOLVED and w.rec.fields["acknowledged_by"] == by
    assert w.notifier.acks == [by]                      # updates the other place (Telegram message)
    assert ("ack", {"by": by}) in w.rec.events
    assert await w.engine.acknowledge("inc_001", by) is False   # already closed


async def test_cannot_resolve_while_on_floor():
    w = World(ai("follow_up"), ai("resolve"))
    await w.fall()
    await w.reply("yes")
    await w.reply("I don't need anything")
    assert w.engine.state == FOLLOW_UP                  # still lying there
    await w.engine.on_posture("sitting")                # on a chair / up from the floor
    assert w.path[-1] == RESOLVED and w.notifier.alerts == []


# -- edge cases -----------------------------------------------------------------------------------

async def test_missing_replies_count_as_no_answer():
    """The room agent is offline: no voice_reply ever arrives."""
    w = World()
    await w.fall()
    await w.at(CONFIG["checkin1_listen_s"] + CONFIG["reply_grace_s"])
    assert w.engine.state == CHECKIN_2
    await w.at(CONFIG["floor_rule_s"] - 1)
    assert w.engine.state == ESCALATE and w.rules() == [1]


async def test_second_fall_is_logged_on_the_open_incident():
    w = World()
    await w.fall("inc_001")
    await w.fall("inc_002")
    assert w.engine.incident_id == "inc_001"
    assert ("state", {"event": "fall_detected_again", "reason": "fast_fall", "room_incident_id": "inc_002"}) \
        in w.rec.events


async def test_late_ai_answer_is_ignored_once_rule_3_has_fired():
    w = World(ai("follow_up"))
    w.agent.gate = asyncio.Event()
    await w.fall()
    w.clock.t = CONFIG["floor_rule_s"] - 2
    task = asyncio.create_task(w.reply("I'm fine"))
    while not w.agent.calls:
        await asyncio.sleep(0)
    await w.at(CONFIG["floor_rule_s"] + 1)              # Rule 3 fires while the AI is thinking
    assert w.engine.state == ESCALATE
    w.agent.gate.set()
    await task
    assert w.engine.state == ESCALATE and w.path == [ESCALATE]


async def test_lying_in_a_safe_zone_is_not_on_the_floor():
    w = World(ai("follow_up"), ai("resolve"))
    await w.fall()
    await w.engine.on_activity("lying", "sofa")         # moved onto the sofa
    await w.reply("I'm okay")
    await w.reply("No thanks")
    assert w.path[-1] == RESOLVED and w.rules() == []


async def test_the_ai_gets_the_context_it_needs():
    w = World(ai("ask_again"))
    await w.fall()
    w.clock.t = 9.0
    await w.reply("what?")
    (context,) = w.agent.calls
    assert context == {"state": CHECKIN_1, "attempt": 1, "question": PHRASES["checkin_1"], "transcript": "what?",
                       "posture": "fallen", "in_safe_zone": False, "seconds_since_fall": 9}


async def test_the_alert_step_names_the_channel_when_the_notifier_has_one():
    notifier = FakeNotifier()
    notifier.channel = "log"                            # e.g. Telegram switched off: the dashboard must say so
    w = World(notifier=notifier)
    await w.fall()
    await w.reply("", heard=False)
    await w.reply("", heard=False)
    assert ("alert", {"attempt": 1, "sent": True, "channel": "log"}) in w.rec.events


async def test_failed_alert_is_retried_quickly_and_never_claims_help_is_coming():
    w = World(notifier=FakeNotifier(fail=True))
    await w.fall()
    await w.reply("", heard=False)
    await w.reply("", heard=False)
    assert w.engine.state == ESCALATE                   # a failing notifier does not stop the escalation
    assert ("alert", {"attempt": 1, "sent": False}) in w.rec.events
    assert w.room.spoken() == [PHRASES["escalate_pending"]]   # honest: nothing has gone out yet
    await w.at(CONFIG["alert_retry_s"])
    assert w.notifier.tries == 2                        # retried after 15 s, not after 2 minutes
    w.notifier.fail = False                             # Telegram is back
    await w.at(2 * CONFIG["alert_retry_s"])
    assert w.notifier.alerts == [1]
    assert w.room.spoken() == [PHRASES["escalate_pending"], PHRASES["escalate"]]
    await w.at(2 * CONFIG["alert_retry_s"] + CONFIG["realert_every_s"])
    assert w.notifier.alerts == [1, 2]                  # then reminders every 2 minutes
    assert w.room.spoken() == [PHRASES["escalate_pending"], PHRASES["escalate"]]   # each said once


# -- problems found in the Stage 3 review (each failed before its fix) ----------------------------

async def test_help_keyword_escalates_even_in_an_unexpected_reply():  # Rule 2 on EVERY transcript
    w = World(ai("follow_up"))
    await w.fall()
    await w.engine.on_posture("standing")
    await w.reply("yes")                                # now waiting for reply number 2
    await w.engine.on_voice_reply("inc_001", 1, "help me, I can't get up", True)   # numbered 1
    assert w.engine.state == ESCALATE and w.rules() == [2] and w.notifier.alerts == [1]

    w = World()                                         # a reply tagged with another incident's id
    await w.fall("inc_002")
    await w.engine.on_voice_reply("inc_001", 1, "help", True)
    assert w.engine.state == ESCALATE and w.rules() == [2]

    w = World(ai("follow_up"))                          # an unexpected reply without a keyword: only logged
    await w.fall()
    await w.engine.on_voice_reply("inc_001", 7, "yes", True)
    assert w.engine.state == CHECKIN_1 and w.agent.calls == []


async def test_help_keyword_at_the_second_checkin_and_in_follow_up():
    w = World(ai("ask_again"))
    await w.fall()
    await w.reply("what?")
    await w.reply("I think I hurt my arm")
    assert w.engine.state == ESCALATE and w.rules() == [2] and len(w.agent.calls) == 1

    w = World(ai("follow_up"))
    await w.fall()
    await w.engine.on_posture("standing")
    await w.reply("yes")
    await w.reply("actually I need help")
    assert w.engine.state == ESCALATE and w.rules() == [2] and len(w.agent.calls) == 1


@pytest.mark.parametrize("words, hit", [
    ("it's painful", True), ("HELP!", True), ("my leg is hurting", True), ("I cant get up", True),
    ("I can’t get up", True), ("救命啊", True), ("my hip hurts", True),
    ("I was painting", False), ("I went to Spain", False), ("no thanks", False), ("", False),
])
def test_help_keywords_match_words_not_fragments(words, hit):
    assert bool(World().engine._help_keyword(words)) is hit


async def test_questions_are_numbered_so_a_lost_question_cannot_put_the_two_sides_out_of_step():
    w = World(ai("follow_up"))
    await w.fall()
    assert w.room.attempts == [1]
    await w.at(CONFIG["checkin1_listen_s"] + CONFIG["reply_grace_s"])   # question 1 never reached the room
    assert w.engine.state == CHECKIN_2 and w.room.attempts == [1, 2]
    await w.engine.on_voice_reply("inc_001", 2, "Yes, I'm okay", True)  # the room echoes the number it was given
    assert w.engine.state == FOLLOW_UP and w.notifier.alerts == []


async def test_old_ai_answer_cannot_touch_a_new_incident():
    w = World(ai("follow_up"))
    w.agent.gate = asyncio.Event()
    await w.fall("inc_001")
    task = asyncio.create_task(w.reply("yes I'm fine"))  # the AI is thinking about incident 1
    while not w.agent.calls:
        await asyncio.sleep(0)
    await w.engine.acknowledge("inc_001", "dashboard")
    await w.fall("inc_002")                              # a new fall; nobody has answered yet
    w.agent.gate.set()
    await task
    assert w.engine.incident_id == "inc_002" and w.engine.state == CHECKIN_1
    assert w.engine.active.listening is not None


async def test_slow_alert_does_not_block_other_events():
    w = World()
    w.notifier.gate = asyncio.Event()                    # Telegram hangs
    await w.fall()
    await w.reply("", heard=False)
    task = asyncio.create_task(w.reply("", heard=False))  # escalates; the alert is stuck in flight
    while not w.notifier.tries:
        await asyncio.sleep(0)
    assert w.engine.state == ESCALATE
    await asyncio.wait_for(w.engine.on_activity("fallen", None), 0.5)
    await asyncio.wait_for(w.engine.tick(), 0.5)
    assert await asyncio.wait_for(w.engine.acknowledge("inc_001", "dashboard"), 0.5) is True
    w.notifier.gate.set()
    await task
    assert w.notifier.alerts == [1] and w.room.spoken() == []   # resolved meanwhile: nothing is said


async def test_ai_step_that_dies_counts_as_no_answer():
    w = World(ai("follow_up"))
    w.agent.gate = asyncio.Event()
    await w.fall()
    task = asyncio.create_task(w.reply("yes"))
    while not w.agent.calls:
        await asyncio.sleep(0)
    task.cancel()                                        # the AI step is lost (crash, shutdown ...)
    with pytest.raises(asyncio.CancelledError):
        await task
    assert w.engine.state == CHECKIN_1 and w.engine.active.listening is None
    await w.at(CONFIG["ai_timeout_s"] + 3)
    assert w.engine.state == CHECKIN_2 and w.rec.decisions[-1]["rule"] == 4


async def test_needs_help_with_any_other_action_escalates():  # Rule 5: the AI contradicts itself
    w = World(ai("follow_up", assessment="needs_help"))
    await w.fall()
    await w.reply("my chest feels tight")
    assert w.engine.state == ESCALATE and w.rules() == [5]


@pytest.mark.parametrize("say", ["Do you need any help?", "x" * 200, "   "],
                         ids=["contains a help word", "too long", "blank"])
async def test_unsuitable_ai_sentence_is_replaced_by_the_fixed_phrase(say):
    w = World(ai("follow_up", say=say))
    await w.fall()
    await w.reply("yes I'm okay")
    assert w.room.said[-1][1] == PHRASES["follow_up"]


@pytest.mark.parametrize("state", [CHECKIN_1, FOLLOW_UP, ESCALATE])
async def test_incident_left_open_by_a_restart_alerts_until_acknowledged(state):
    w = World()
    await w.engine.restore("inc_old", "fast_fall", w.clock.now(), state)
    assert w.engine.state == ESCALATE and w.notifier.alerts == [1]
    await w.at(CONFIG["realert_every_s"])
    assert w.notifier.alerts == [1, 2]
    assert await w.engine.acknowledge("inc_old", "dashboard")
    assert w.engine.state == "monitoring"


async def test_help_is_coming_is_said_later_if_the_room_could_not_be_reached():
    w = World()
    await w.fall()
    w.room.offline = True                                # the room agent drops out (or the server restarted)
    await w.at(CONFIG["floor_rule_s"])                   # no replies arrive: escalates
    assert w.engine.state == ESCALATE and w.notifier.alerts == [1] and w.room.spoken() == []
    escalated = w.clock.t
    w.room.offline = False
    await w.at(escalated + CONFIG["realert_every_s"])
    assert w.notifier.alerts == [1, 2] and w.room.spoken() == [PHRASES["escalate"]]
    await w.at(escalated + 2 * CONFIG["realert_every_s"])
    assert w.room.spoken() == [PHRASES["escalate"]]      # said once


async def test_real_fall_closes_an_open_simulated_incident():
    w = World()
    await w.engine.on_fall("inc_sim_1", "fast_fall", {}, simulated=True)
    await w.reply("", heard=False)
    await w.reply("", heard=False)                       # the simulated incident is left un-acknowledged
    await w.engine.on_fall("inc_real_1", "fast_fall", {"torso_angle": 70})
    assert w.engine.incident_id == "inc_real_1" and w.engine.state == CHECKIN_1
    assert w.engine.active.simulated is False and w.room.said[-1] == ("ask", PHRASES["checkin_1"], 6)
    await w.engine.on_fall("inc_sim_2", "fast_fall", {}, simulated=True)   # never the other way round
    assert w.engine.incident_id == "inc_real_1"


# -- coverage the review asked for ------------------------------------------------------------------

async def test_rules_4_and_5_in_follow_up():
    w = World(ai("follow_up"), RuntimeError("boom"))
    await w.fall()
    await w.engine.on_posture("standing")
    await w.reply("yes")
    await w.reply("erm")                                 # the AI fails: recorded as "no request"
    assert w.path[-1] == RESOLVED and w.rec.decisions[-1]["rule"] == 4 and w.notifier.alerts == []

    w = World(ai("follow_up"), ai("ask_again"))          # ask_again is not allowed in follow-up
    await w.fall()
    await w.engine.on_posture("standing")
    await w.reply("yes")
    await w.reply("erm")
    assert w.engine.state == ESCALATE and w.rules() == [5]


async def test_acknowledge_during_a_checkin_resolves_without_alerting():
    w = World()
    await w.fall()
    assert await w.engine.acknowledge("inc_001", "dashboard")
    assert w.path == [RESOLVED] and w.notifier.acks == ["dashboard"]
    await w.at(300)
    assert w.notifier.alerts == []


async def test_out_of_view_keeps_the_last_known_posture():
    w = World(ai("follow_up"), ai("resolve"))
    await w.fall()
    await w.engine.on_activity("absent", None)           # the camera lost the person
    await w.reply("yes")
    await w.reply("no thanks")
    assert w.engine.state == FOLLOW_UP                   # still counted as on the floor
    await w.at(CONFIG["floor_rule_s"])
    assert w.engine.state == ESCALATE and w.rules() == [3]


async def test_storage_failure_never_stops_an_alert():
    class BrokenRecorder(FakeRecorder):
        async def event(self, *a):
            raise OSError("disk full")

        async def state(self, *a, **k):
            raise OSError("disk full")

        async def decision(self, *a):
            raise OSError("disk full")

    w = World()
    w.engine.rec._inner = BrokenRecorder()
    await w.fall()
    await w.reply("", heard=False)
    await w.reply("", heard=False)
    assert w.engine.state == "escalate" and w.notifier.alerts == [1]


async def test_silence_in_follow_up_means_no_request():
    w = World(ai("follow_up"))
    await w.fall()
    await w.engine.on_posture("standing")
    await w.reply("yes")
    await w.reply("", heard=False)
    assert w.path[-1] == RESOLVED and len(w.agent.calls) == 1
