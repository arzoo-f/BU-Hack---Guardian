"""Server tests (BUILD_PLAN steps 1.4 and 3.2): REST routes, WebSockets, storage, CORS, and the
escalation flow driven end to end through the room WebSocket (fake AI, recording notifier)."""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

import app as server_app
import db
from agent import FakeAgent
from contracts import validate

EXAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "examples" / "valid"
PHRASES = server_app.load_escalation_config()["phrases"]


def example(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


class CaptureNotifier:
    def __init__(self) -> None:
        self.alerts, self.gentle_requests, self.acks = [], [], []

    async def alert(self, incident, attempt):
        self.alerts.append(attempt)

    async def gentle(self, incident, request):
        self.gentle_requests.append(request)

    async def acknowledged(self, incident, by):
        self.acks.append(by)


@pytest.fixture
def notifier():
    return CaptureNotifier()


@pytest.fixture
def client(tmp_path, notifier):
    app = server_app.create_app(tmp_path / "test.db", agent=FakeAgent(), notifier=notifier)
    with TestClient(app) as c:
        yield c
    app.state.hub.db.dispose()


def rows(client, model) -> list:
    with Session(client.app.state.hub.db) as s:
        return list(s.exec(select(model)))


def next_message(ws, type_: str, kind: str | None = None, limit: int = 30) -> dict:
    """Read dashboard messages until one of the wanted type (and incident step kind) arrives."""
    for _ in range(limit):
        msg = validate("dashboard", ws.receive_json())
        if msg["type"] == type_ and (kind is None or msg.get("kind") == kind):
            return msg
    raise AssertionError(f"no {type_}/{kind} message")


def reply(room, attempt: int, transcript: str, heard: bool = True) -> None:
    room.send_json({"type": "voice_reply", "incident_id": "inc_001", "attempt": attempt,
                    "transcript": transcript, "heard_speech": heard})


# -- basics (Stage 1) -----------------------------------------------------------------------------

def test_status_starts_empty(client):
    body = client.get("/status").json()
    assert body["room_connected"] is False and body["activity"] is None and body["last_incident"] is None
    assert body["state"] == "monitoring" and body["open_incident"] is None and body["rejected_messages"] == 0


def test_dashboard_gets_a_status_message_on_connect(client):
    with client.websocket_connect("/ws/dashboard") as dash:
        msg = validate("dashboard", dash.receive_json())
        assert msg["type"] == "status" and msg["camera"] == "offline" and msg["incident_id"] is None


def test_room_events_reach_dashboard_and_database(client):
    with client.websocket_connect("/ws/dashboard") as dash:
        dash.receive_json()
        with client.websocket_connect("/ws/room") as room:
            room.send_json(example("room.activity.json"))
            msg = next_message(dash, "activity")
            assert msg["activity"] == "sitting" and msg["state"] == "monitoring"
            room.send_json(example("room.status.json"))
            msg = next_message(dash, "status")
            assert msg["camera"] == "ok" and msg["fps"] == 14.8
            room.send_json(example("room.fall_detected.json"))
            msg = next_message(dash, "incident_update", "state")
            assert msg["incident_id"] == "inc_001" and msg["reason"] == "fast_fall" and msg["state"] == "checkin_1"
            status = client.get("/status").json()
            assert status["room_connected"] is True and status["open_incident"] == "inc_001"
            assert status["activity"]["activity"] == "sitting" and status["camera"] == "ok"
            assert status["last_incident"]["id"] == "inc_001"
    assert [r.activity for r in rows(client, db.ActivityLog)] == ["sitting"]
    (incident,) = rows(client, db.Incident)
    assert (incident.id, incident.reason, incident.features["torso_angle"]) == ("inc_001", "fast_fall", 78)
    assert client.get("/status").json()["room_connected"] is False


def test_the_camera_watch_follows_the_room(client):
    watch = client.app.state.camera_watch
    with client.websocket_connect("/ws/dashboard") as dash:
        dash.receive_json()
        with client.websocket_connect("/ws/room") as room:
            room.send_json(example("room.status.json"))
            next_message(dash, "status")
            assert watch.blind_since is None                     # camera ok: Guardian can see
            room.send_json({**example("room.status.json"), "camera": "offline", "fps": 0.0})
            next_message(dash, "status")
            assert watch.blind_since is not None
            room.send_json(example("room.status.json"))
            next_message(dash, "status")
            assert watch.blind_since is None
        msg = next_message(dash, "status")                       # the room agent left: told at once
        assert msg["camera"] == "offline" and watch.blind_since is not None


def test_pose_is_forwarded_but_never_stored(client):
    with client.websocket_connect("/ws/dashboard") as dash:
        dash.receive_json()
        with client.websocket_connect("/ws/room") as room:
            room.send_json(example("room.pose.json"))
            msg = next_message(dash, "pose")
            assert len(msg["keypoints"]) == 33
    assert rows(client, db.ActivityLog) == [] and rows(client, db.Incident) == []


def test_invalid_room_message_is_rejected_and_counted(client):
    with client.websocket_connect("/ws/dashboard") as dash:
        dash.receive_json()
        with client.websocket_connect("/ws/room") as room:
            room.send_text("not json")
            room.send_json({"type": "selfie", "ts": "2026-11-14T10:02:05Z"})
            room.send_json(example("room.status.json"))
            assert dash.receive_json()["type"] == "status"
    assert client.get("/status").json()["rejected_messages"] == 2


def test_handler_error_does_not_drop_the_room_agent(client, monkeypatch):
    real_add, calls = db.add, []

    def flaky_add(engine, row):
        calls.append(row)
        if len(calls) == 1:
            raise RuntimeError("disk full")
        real_add(engine, row)

    monkeypatch.setattr(db, "add", flaky_add)
    with client.websocket_connect("/ws/dashboard") as dash:
        dash.receive_json()
        with client.websocket_connect("/ws/room") as room:
            room.send_json(example("room.activity.json"))  # storing fails: logged, not forwarded
            room.send_json(example("room.status.json"))
            assert dash.receive_json()["type"] == "status"
            assert client.get("/status").json()["room_connected"] is True
    assert client.get("/status").json()["handler_errors"] == 1


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://192.168.1.20:5173"])
def test_cors_allows_the_dashboard(client, origin):
    assert client.get("/status", headers={"Origin": origin}).headers.get("access-control-allow-origin") == origin


def test_cors_refuses_other_sites(client):
    r = client.get("/status", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in r.headers


# -- the escalation flow over the real connections (Stage 3) -------------------------------------

def test_help_keyword_escalates_and_ack_resolves(client, notifier):
    with client.websocket_connect("/ws/dashboard") as dash:
        dash.receive_json()
        with client.websocket_connect("/ws/room") as room:
            room.send_json(example("room.fall_detected.json"))
            ask = validate("command", room.receive_json())
            assert ask == {"type": "speak_and_listen", "incident_id": "inc_001",
                           "text": PHRASES["checkin_1"], "listen_seconds": 6, "attempt": 1}
            reply(room, 1, "help me, I can't get up")
            decision = next_message(dash, "decision")
            assert decision["action"] == "escalate" and decision["source"] == "hard_rule" and decision["rule"] == 2
            assert next_message(dash, "incident_update", "state")["state"] == "escalate"
            assert validate("command", room.receive_json()) == {"type": "speak", "text": PHRASES["escalate"]}
            assert notifier.alerts == [1]

            r = client.post("/incidents/inc_001/ack", json={"by": "dashboard"})
            assert r.status_code == 200 and r.json()["state"] == "resolved"
            assert next_message(dash, "incident_update", "ack")["payload"] == {"by": "dashboard"}
    assert notifier.acks == ["dashboard"]
    assert client.post("/incidents/inc_001/ack", json={"by": "dashboard"}).status_code == 409
    assert client.post("/incidents/inc_nope/ack").status_code == 404
    detail = client.get("/incidents/inc_001").json()
    assert detail["state"] == "resolved" and detail["acknowledged_by"] == "dashboard"
    assert [e["kind"] for e in detail["events"]][:4] == ["state", "speak", "reply", "decision"]
    assert client.get("/status").json()["state"] == "monitoring"


def test_scenario_1_okay_then_a_request(client, notifier):
    with client.websocket_connect("/ws/room") as room:
        room.send_json(example("room.fall_detected.json"))
        room.receive_json()                                   # "Are you okay?"
        reply(room, 1, "Yes, I'm okay, I slipped")
        follow = validate("command", room.receive_json())
        assert follow["type"] == "speak_and_listen" and follow["listen_seconds"] == 8
        room.send_json({"type": "posture_update", "incident_id": "inc_001", "activity": "standing"})
        reply(room, 2, "Some water, please")
        for _ in range(50):
            if client.get("/status").json()["state"] == "monitoring":
                break
            time.sleep(0.05)
    assert notifier.gentle_requests == ["some water, please"] and notifier.alerts == []
    assert client.get("/incidents/inc_001").json()["state"] == "resolved"


def test_simulated_fall_starts_a_simulated_incident(client):
    with client.websocket_connect("/ws/dashboard") as dash:
        dash.receive_json()
        incident_id = client.post("/simulate/fall").json()["incident_id"]
        msg = next_message(dash, "incident_update", "state")
        assert msg["incident_id"] == incident_id and msg["simulated"] is True
    status = client.get("/status").json()
    assert status["open_incident"] == incident_id and status["state"] == "checkin_1"
    listed = client.get("/incidents").json()
    assert [i["id"] for i in listed] == [incident_id] and listed[0]["simulated"] is True
    assert client.get("/incidents", params={"include_simulated": "false"}).json() == []
    assert client.post("/simulate/fall").json()["incident_id"] == incident_id   # logged on the open one
    assert client.get("/incidents/inc_nope").status_code == 404


def test_unfinished_incidents_are_restored_or_closed_at_start_up(tmp_path, notifier):
    path = tmp_path / "restart.db"
    before = db.make_engine(path)                        # what a server that stopped mid-incident leaves behind
    t = datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc)
    for incident_id, started, state, simulated in [
            ("inc_newest_real", t, "checkin_2", False),
            ("inc_older_real", t - timedelta(hours=1), "follow_up", False),
            ("inc_sim_x", t + timedelta(minutes=5), "escalate", True),
            ("inc_done", t, "resolved", False)]:
        db.add(before, db.Incident(id=incident_id, started_at=started, reason="fast_fall", state=state,
                                   simulated=simulated))
    before.dispose()

    app = server_app.create_app(path, agent=FakeAgent(), notifier=notifier)
    with TestClient(app) as client:
        status = client.get("/status").json()
        assert status["open_incident"] == "inc_newest_real" and status["state"] == "escalate"
        assert notifier.alerts == [1]                    # the family is alerted about the interrupted incident
        states = {i["id"]: i["state"] for i in client.get("/incidents").json()}
        assert states == {"inc_newest_real": "escalate", "inc_older_real": "resolved",
                          "inc_sim_x": "resolved", "inc_done": "resolved"}
        steps = client.get("/incidents/inc_newest_real").json()["events"]
        assert steps[0]["payload"] == {"event": "restored_after_restart"}
        assert client.post("/incidents/inc_newest_real/ack", json={"by": "dashboard"}).status_code == 200
        assert client.get("/status").json()["state"] == "monitoring"
    app.state.hub.db.dispose()


# -- other routes ---------------------------------------------------------------------------------

def test_activity_range(client):
    with client.websocket_connect("/ws/room") as room:
        for i, label in enumerate(["standing", "walking", "sitting"]):
            room.send_json({**example("room.activity.json"), "ts": f"2026-11-14T10:00:0{2 * i}Z", "activity": label})
        room.send_json(example("room.status.json"))
    got = client.get("/activity", params={"from": "2026-11-14T10:00:01Z", "to": "2026-11-14T10:00:05Z"}).json()
    assert [r["activity"] for r in got] == ["walking", "sitting"]
    assert got[0]["ts"] == "2026-11-14T10:00:02.000Z"
    assert client.get("/activity", params={"from": "yesterday"}).status_code == 422


def test_analytics_daily(client):
    with client.websocket_connect("/ws/room") as room:
        for i in range(30):   # 1 minute of walking, 10:00-10:01 Hong Kong time
            room.send_json({**example("room.activity.json"), "activity": "walking",
                            "ts": f"2026-11-14T02:00:{2 * i:02d}Z"})
        room.send_json(example("room.status.json"))
    body = client.get("/analytics/daily", params={"now": "2026-11-14T12:00:00+08:00"}).json()
    assert body["today"]["date"] == "2026-11-14"
    # 29 rows x 2 s, and the last row counts up to row_gap_cap_s (10 s): 68 s
    assert body["today"]["active_minutes"] == pytest.approx(68 / 60, abs=0.05)
    assert len(body["days"]) == 8 and isinstance(body["insights"], list)
    assert client.get("/analytics/daily", params={"now": "noon"}).status_code == 422
    band = client.get("/analytics/timeline", params={"now": "2026-11-14T12:00:00+08:00"}).json()
    assert (band["date"], band["from"], band["now"]) == ("2026-11-14", "2026-11-14T00:00:00+08:00",
                                                         "2026-11-14T04:00:00+00:00")
    assert [s["activity"] for s in band["segments"]] == ["walking"]
    assert band["segments"][0]["from"].startswith("2026-11-14T02:00:00")
    yesterday = client.get("/analytics/timeline", params={"date": "2026-11-13", "now": "2026-11-14T12:00:00+08:00"})
    assert yesterday.json()["segments"] == []
    assert client.get("/analytics/timeline", params={"date": "14/11"}).status_code == 422


def test_zones_and_contacts(client):
    fallback = client.get("/zones").json()
    assert fallback["source"] == "config" and fallback["zones"][0]["name"] == "sofa"   # config/zones.json
    sofa = {"name": "sofa", "polygon": [[0.4, 0.33], [0.52, 0.33], [0.52, 0.45], [0.4, 0.45]]}
    assert client.post("/zones", json={"zones": [sofa]}).json() == {"zones": [sofa]}
    assert client.get("/zones").json() == {"zones": [sofa], "source": "saved"}
    bad = {"name": "bed", "polygon": [[0.1, 0.1], [1.5, 0.1], [0.2, 0.2]]}
    assert client.post("/zones", json={"zones": [bad]}).status_code == 422
    settings = client.get("/settings").json()
    assert settings["check_in"]["floor_rule_s"] == 90 and settings["alerts"] == {"telegram": False, "ai": "FakeAgent"}
    assert settings["fall_detection"]["confirm_after_s"] == 3.0
    family = {"name": "Guardian Family (Test)", "relation": "family", "telegram_chat_id": "-100123"}
    assert client.post("/contacts", json={"contacts": [family]}).json() == {"contacts": [family]}
    assert client.post("/contacts", json={"contacts": [{"relation": "x"}]}).status_code == 422
