"""AI agent tests (BUILD_PLAN step 3.5): no network - the OpenAI client is a fake."""
import json
from types import SimpleNamespace

import pytest

import agent as agent_mod
from agent import FakeAgent, OpenAIAgent, decision_schema, make_agent, user_message
from contracts import validate_decision

CONTEXT = {"state": "checkin_1", "attempt": 1, "transcript": "I'm okay, I just slipped", "posture": "fallen",
           "in_safe_zone": False, "seconds_since_fall": 8}


class FakeCompletions:
    def __init__(self, content: str, refusal: str | None = None) -> None:
        self.content, self.refusal, self.kwargs = content, refusal, None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        message = SimpleNamespace(content=self.content, refusal=self.refusal)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def fake_client(content: str, refusal: str | None = None):
    completions = FakeCompletions(content, refusal)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


@pytest.mark.parametrize("state, actions", [("checkin_1", ["follow_up", "ask_again", "escalate"]),
                                            ("checkin_2", ["follow_up", "escalate"]),
                                            ("follow_up", ["escalate", "resolve"])])
def test_schema_only_offers_the_actions_allowed_in_the_state(state, actions):
    schema = decision_schema(state)
    assert sorted(schema["properties"]["action"]["enum"]) == sorted(actions)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])   # strict mode needs every field required


def test_user_message_carries_the_facts_and_the_allowed_actions():
    data = json.loads(user_message(CONTEXT))
    assert data["transcript"] == CONTEXT["transcript"] and data["posture"] == "fallen"
    assert data["allowed_actions"] == ["follow_up", "ask_again", "escalate"]


async def test_openai_agent_sends_a_strict_schema_and_returns_the_decision():
    answer = {"assessment": "ok", "action": "follow_up", "say": "Glad you're okay. Do you need anything?",
              "request": None, "reason": "Clear yes."}
    client, completions = fake_client(json.dumps(answer))
    got = await OpenAIAgent("gpt-5.4-mini", client=client).decide(CONTEXT)
    assert got == answer
    sent = completions.kwargs
    assert sent["model"] == "gpt-5.4-mini" and sent["reasoning_effort"] == "none"
    fmt = sent["response_format"]["json_schema"]
    assert fmt["strict"] is True and fmt["schema"] == decision_schema("checkin_1")
    assert sent["messages"][0]["role"] == "system" and "escalate" in sent["messages"][0]["content"]


async def test_openai_agent_skips_reasoning_effort_for_older_models():
    client, completions = fake_client(json.dumps({"assessment": "ok", "action": "follow_up", "say": "",
                                                  "request": None, "reason": "x"}))
    await OpenAIAgent("gpt-4o-mini", client=client).decide(CONTEXT)
    assert "reasoning_effort" not in completions.kwargs


async def test_openai_agent_raises_on_refusal_or_bad_json():
    client, _ = fake_client("", refusal="I can't help with that")
    with pytest.raises(RuntimeError):
        await OpenAIAgent("gpt-5.4-mini", client=client).decide(CONTEXT)
    client, _ = fake_client("{not json")
    with pytest.raises(json.JSONDecodeError):
        await OpenAIAgent("gpt-5.4-mini", client=client).decide(CONTEXT)


@pytest.mark.parametrize("state, transcript, action, wanted", [
    ("checkin_1", "Yes, I'm okay", "follow_up", None),
    ("checkin_1", "what?", "ask_again", None),
    ("checkin_2", "hmm", "escalate", None),
    ("follow_up", "No thanks", "resolve", None),
    ("follow_up", "Some water, please", "resolve", "some water, please"),
])
async def test_fake_agent_rules(state, transcript, action, wanted):
    got = await FakeAgent().decide({**CONTEXT, "state": state, "transcript": transcript})
    validate_decision(got)
    assert got["action"] == action and got["request"] == wanted


def test_make_agent_chooses_fake_without_a_key_or_when_forced(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert isinstance(make_agent(), FakeAgent)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    monkeypatch.setenv("GUARDIAN_FAKE_AI", "1")
    assert isinstance(make_agent(), FakeAgent)
    monkeypatch.delenv("GUARDIAN_FAKE_AI")
    monkeypatch.setattr(agent_mod, "OpenAIAgent", lambda model: ("openai", model))
    assert make_agent() == ("openai", "gpt-5.4-mini")
