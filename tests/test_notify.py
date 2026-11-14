"""Telegram notifier tests (BUILD_PLAN step 4.4) against a fake Telegram API (httpx.MockTransport)."""
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

import app as server_app
from agent import FakeAgent
from notify import LogNotifier, TelegramError, TelegramNotifier, alert_caption, make_notifier

TOKEN = "123456:THIS-IS-A-FAKE-TOKEN-FOR-TESTS-ONLY"
CHAT = "-1004458009229"
POSE = json.loads(open("contracts/examples/valid/room.pose.json", encoding="utf-8").read())["keypoints"]
INCIDENT = {"incident_id": "inc_001", "room": "living_room", "reason": "fast_fall",
            "started_at": "2026-11-14T02:07:10+00:00", "state": "escalate", "transcript": "",
            "ai_reason": "No answer after two check-ins.", "posture": "fallen", "simulated": False}


class FakeTelegram:
    """Answers Bot API calls like Telegram; remembers what was asked."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict | bytes]] = []
        self.updates: list[list[dict]] = []
        self.next_id = 100
        self.fail_with: Exception | None = None

    def handler(self, request: httpx.Request) -> httpx.Response:
        if self.fail_with:
            raise self.fail_with
        method = request.url.path.rsplit("/", 1)[-1]
        assert TOKEN in str(request.url)
        body = request.content
        params = json.loads(body) if request.headers.get("content-type", "").startswith("application/json") else body
        self.calls.append((method, params))
        if method in ("sendPhoto", "sendMessage"):
            self.next_id += 1
            return httpx.Response(200, json={"ok": True, "result": {"message_id": self.next_id}})
        if method == "getUpdates":
            return httpx.Response(200, json={"ok": True, "result": self.updates.pop(0) if self.updates else []})
        if method == "badMethod":
            return httpx.Response(200, json={"ok": False, "error_code": 400, "description": "Bad Request"})
        return httpx.Response(200, json={"ok": True, "result": True})

    def made(self, method: str) -> list:
        return [params for m, params in self.calls if m == method]


def make(fake: FakeTelegram) -> TelegramNotifier:
    client = httpx.AsyncClient(transport=httpx.MockTransport(fake.handler))
    return TelegramNotifier(TOKEN, CHAT, keypoints=lambda: POSE, utc_offset_hours=8, client=client)


def press(update_id: int, chat: int, incident_id: str = "inc_001", first: str = "Ayesha", last: str = "B") -> dict:
    return {"update_id": update_id, "callback_query": {
        "id": f"cb{update_id}", "data": f"ack:{incident_id}", "from": {"first_name": first, "last_name": last},
        "message": {"message_id": 101, "chat": {"id": chat}}}}


# -- messages ---------------------------------------------------------------------------------------

def test_caption_says_what_happened_in_plain_words():
    text = alert_caption(INCIDENT, 1, 8)
    assert "Guardian alert: possible fall" in text and "Room: living room · Sat 10:07" in text
    assert "Heard: no answer" in text and "Why: No answer after two check-ins." in text
    assert "Acknowledge" in text and "Reminder" not in text
    reminder = alert_caption({**INCIDENT, "transcript": "help", "simulated": True}, 3, 8)
    assert reminder.startswith("🔔 Reminder 2") and "[TEST]" in reminder and 'Heard: "help"' in reminder
    assert "found on the floor" in alert_caption({**INCIDENT, "reason": "found_on_floor"}, 1, 8)


async def test_alert_is_a_skeleton_picture_with_an_acknowledge_button():
    fake = FakeTelegram()
    await make(fake).alert(INCIDENT, 1)
    (body,) = fake.made("sendPhoto")
    assert b"image/png" in body and b"\x89PNG" in body                 # the skeleton picture
    assert CHAT.encode() in body and b"ack:inc_001" in body            # the test group, the button
    assert "Guardian alert".encode() in body


async def test_acknowledging_edits_every_alert_and_removes_the_button():
    fake = FakeTelegram()
    notifier = make(fake)
    await notifier.alert(INCIDENT, 1)
    await notifier.alert(INCIDENT, 2)
    await notifier.acknowledged(INCIDENT, "dashboard")
    edits = fake.made("editMessageCaption")
    assert [e["message_id"] for e in edits] == [101, 102]
    assert all("✅ Acknowledged by dashboard" in e["caption"] for e in edits)
    assert all(e["reply_markup"] == {"inline_keyboard": []} for e in edits)
    await notifier.acknowledged(INCIDENT, "dashboard")                 # nothing left to edit
    assert len(fake.made("editMessageCaption")) == 2


async def test_gentle_message_for_a_request():
    fake = FakeTelegram()
    await make(fake).gentle(INCIDENT, "a glass of water")
    (sent,) = fake.made("sendMessage")
    assert sent["chat_id"] == int(CHAT) and "Not urgent" in sent["text"] and "a glass of water" in sent["text"]


# -- the Acknowledge button -------------------------------------------------------------------------------

async def test_button_press_in_the_family_group_acknowledges():
    fake, acks = FakeTelegram(), []
    notifier = make(fake)

    async def on_ack(incident_id, by):
        acks.append((incident_id, by))
        return True

    notifier.on_ack = on_ack
    fake.updates = [[press(7, int(CHAT))]]
    assert await notifier.poll_once() == 1
    assert acks == [("inc_001", "Telegram: Ayesha B")]
    (answer,) = fake.made("answerCallbackQuery")
    assert answer["callback_query_id"] == "cb7" and answer["text"].startswith("Thank you, Ayesha")
    await notifier.poll_once()
    assert fake.made("getUpdates")[-1]["offset"] == 8                 # the press is not delivered twice


async def test_button_press_from_another_chat_is_ignored():
    fake, acks = FakeTelegram(), []
    notifier = make(fake)

    async def on_ack(incident_id, by):
        acks.append(incident_id)
        return True

    notifier.on_ack = on_ack
    fake.updates = [[press(9, -999)]]
    await notifier.poll_once()
    assert acks == [] and "not for this chat" in fake.made("answerCallbackQuery")[0]["text"]


async def test_press_on_an_old_alert_says_already_handled():
    fake = FakeTelegram()
    notifier = make(fake)

    async def on_ack(incident_id, by):
        return False

    notifier.on_ack = on_ack
    fake.updates = [[press(11, int(CHAT))]]
    await notifier.poll_once()
    assert fake.made("answerCallbackQuery")[0]["text"].startswith("Already handled")


async def test_polling_never_spins_when_answers_come_back_at_once():
    import asyncio

    fake = FakeTelegram()                                              # always answers "no updates" at once
    task = asyncio.create_task(make(fake).poll_forever())
    await asyncio.sleep(1.5)
    task.cancel()
    assert len(fake.made("getUpdates")) <= 3                           # about one call per second, not thousands


# -- safety -------------------------------------------------------------------------------------------------

async def test_errors_never_contain_the_token():
    fake = FakeTelegram()
    fake.fail_with = httpx.ConnectError(f"cannot reach https://api.telegram.org/bot{TOKEN}/sendPhoto")
    with pytest.raises(TelegramError) as caught:
        await make(fake).alert(INCIDENT, 1)
    assert TOKEN not in str(caught.value) and caught.value.__cause__ is None and caught.value.__suppress_context__
    fake.fail_with = None
    with pytest.raises(TelegramError, match="400 Bad Request"):
        await make(fake)._call("badMethod")


def test_make_notifier_falls_back_to_the_log(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TOKEN)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", CHAT)
    monkeypatch.setenv("GUARDIAN_FAKE_TELEGRAM", "1")
    assert isinstance(make_notifier(lambda: None), LogNotifier)
    monkeypatch.delenv("GUARDIAN_FAKE_TELEGRAM")
    assert isinstance(make_notifier(lambda: None), TelegramNotifier)
    monkeypatch.delenv("TELEGRAM_CHAT_ID")
    assert isinstance(make_notifier(lambda: None), LogNotifier)


# -- through the real server ----------------------------------------------------------------------------------

def test_alert_and_acknowledge_through_the_server(tmp_path):
    fake = FakeTelegram()
    notifier = make(fake)
    app = server_app.create_app(tmp_path / "t.db", agent=FakeAgent(), notifier=notifier)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/room") as room:
            room.send_json(json.loads(open("contracts/examples/valid/room.pose.json", encoding="utf-8").read()))
            room.send_json(json.loads(open("contracts/examples/valid/room.fall_detected.json", encoding="utf-8").read()))
            room.receive_json()
            room.send_json({"type": "voice_reply", "incident_id": "inc_001", "attempt": 1,
                            "transcript": "help me", "heard_speech": True})
            for _ in range(50):
                if fake.made("sendPhoto"):
                    break
                time.sleep(0.05)
        assert len(fake.made("sendPhoto")) == 1 and client.get("/status").json()["state"] == "escalate"
        fake.updates = [[press(1, int(CHAT))]]
        client.portal.call(notifier.poll_once)                         # family taps Acknowledge
        assert client.get("/status").json()["state"] == "monitoring"
        assert client.get("/incidents/inc_001").json()["acknowledged_by"] == "Telegram: Ayesha B"
        (edit,) = fake.made("editMessageCaption")
        assert "Acknowledged by Telegram: Ayesha B" in edit["caption"]
    app.state.hub.db.dispose()


def test_the_bot_token_never_reaches_the_log():
    """httpx logs request URLs at INFO and Telegram puts the token in the URL (found Sat 6:23 pm)."""
    import logging

    import app as server_app  # noqa: F401  (importing the server sets the levels)

    for name in ("httpx", "httpcore"):
        assert logging.getLogger(name).getEffectiveLevel() >= logging.WARNING
