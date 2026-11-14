"""Guardian server: live connections, REST API, SQLite storage and the escalation engine.

WebSockets: /ws/room (room agent: events in, voice commands out) and /ws/dashboard (live updates).
REST: GET /status, /incidents, /incidents/{id}, /activity, /analytics/daily, /analytics/timeline,
      /zones, /contacts, /settings;
      POST /incidents/{id}/ack, /zones, /contacts, /simulate/fall (BUILD_PLAN Section 12).
Every message in or out is checked against contracts/. The check-in flow and the five hard
rules live in escalation.py; this file only wires it to the outside world.

Run from this folder:  ..\\.venv\\Scripts\\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000
The database is server/guardian.db unless GUARDIAN_DB names another file (long test runs).
"""
import asyncio
import contextlib
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import analytics  # noqa: E402
import db  # noqa: E402
from agent import make_agent  # noqa: E402
from camera_watch import CameraWatch  # noqa: E402
from contracts import ContractError, validate  # noqa: E402
from escalation import EscalationEngine  # noqa: E402
from notify import make_notifier  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# httpx logs every request URL at INFO, and Telegram puts the bot token in the URL: never log it.
for _name in ("httpx", "httpcore"):
    logging.getLogger(_name).setLevel(logging.WARNING)
log = logging.getLogger("guardian.server")

SEND_TIMEOUT_S = 1.0  # a stuck dashboard must not hold up the room agent
TICK_S = 0.5          # how often the engine checks its timers


def now_iso() -> str:
    """Current UTC time as an ISO 8601 string with a Z suffix."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_escalation_config() -> dict:
    return json.loads((ROOT / "config" / "escalation.json").read_text(encoding="utf-8"))


def load_analytics_config() -> dict:
    return json.loads((ROOT / "config" / "analytics.json").read_text(encoding="utf-8"))


class Hub:
    """Live connections and the latest state of the room."""

    def __init__(self, engine_db) -> None:
        self.db = engine_db
        self.engine: EscalationEngine | None = None   # set by create_app
        self.watch: CameraWatch | None = None          # camera-offline alert, set by create_app
        self.dashboards: set[WebSocket] = set()
        self.room_ws: WebSocket | None = None
        self.room: str | None = None
        self.activity: dict | None = None
        self.camera: str | None = None
        self.fps: float | None = None
        self.pose: list | None = None                  # latest keypoints (for the alert picture)
        self.last_seen: str | None = None
        self.rejected = 0
        self.errors = 0

    def incident_fields(self) -> dict:
        """The incident_id and state that every dashboard message carries."""
        return {"incident_id": self.engine.incident_id, "state": self.engine.state}

    def status_message(self) -> dict:
        """A dashboard 'status' message describing the room right now."""
        return {"type": "status", "ts": now_iso(), "camera": self.camera or "offline",
                "fps": self.fps or 0.0, **self.incident_fields()}

    async def broadcast(self, message: dict) -> None:
        """Validate a dashboard message and send it to every connected dashboard."""
        validate("dashboard", message)
        dead = []
        for ws in list(self.dashboards):
            try:
                await asyncio.wait_for(ws.send_json(message), SEND_TIMEOUT_S)
            except Exception as exc:  # closed, broken or too slow: drop it, it will reconnect
                log.warning("dropping dashboard after failed send: %r", exc)
                dead.append(ws)
        for ws in dead:
            self.dashboards.discard(ws)

    async def send_command(self, command: dict) -> None:
        """Send a voice command to the room agent (raises if it is not connected)."""
        validate("command", command)
        if self.room_ws is None:
            raise ConnectionError("room agent not connected")
        await self.room_ws.send_json(command)

    async def handle_room_message(self, message: dict) -> None:
        """Act on one validated message from the room agent."""
        kind, engine = message["type"], self.engine
        self.last_seen = now_iso()
        if kind == "activity":
            self.room = message["room"]
            self.activity = {k: message[k] for k in ("activity", "confidence", "zone", "ts")}
            db.add(self.db, db.ActivityLog(ts=db.to_utc(message["ts"]), room=message["room"],
                                           activity=message["activity"], confidence=message["confidence"],
                                           zone=message["zone"]))
            await engine.on_activity(message["activity"], message["zone"])
            log.info("activity %s (%.2f)", message["activity"], message["confidence"])
            await self.broadcast({**message, **self.incident_fields()})
        elif kind == "pose":
            self.pose = message["keypoints"]
            await self.broadcast({**message, **self.incident_fields()})  # forwarded, never stored
        elif kind == "status":
            self.camera, self.fps = message["camera"], message["fps"]
            self.watch.update(message["camera"] == "ok")
            await self.broadcast({**message, **self.incident_fields()})
        elif kind == "fall_detected":
            await engine.on_fall(message["incident_id"], message["reason"], message["features"])
        elif kind == "posture_update":
            await engine.on_posture(message["activity"])
        elif kind == "voice_reply":
            await engine.on_voice_reply(message["incident_id"], message["attempt"], message["transcript"],
                                        message["heard_speech"])

    def status_snapshot(self) -> dict:
        """Body of GET /status."""
        latest = db.list_incidents(self.db, limit=1)
        return {
            "room": self.room, "room_connected": self.room_ws is not None,
            "activity": self.activity, "camera": self.camera, "fps": self.fps, "last_seen": self.last_seen,
            "open_incident": self.engine.incident_id, "state": self.engine.state,
            "last_incident": db.incident_dict(latest[0]) if latest else None,
            "dashboards": len(self.dashboards), "rejected_messages": self.rejected, "handler_errors": self.errors,
        }


class DbRecorder:
    """The engine's recorder: every step goes into SQLite and out to the dashboards."""

    def __init__(self, hub: Hub) -> None:
        self.hub = hub

    async def _update(self, incident_id: str, state: str, kind: str, payload: dict, ts: datetime,
                      **extra) -> None:
        db.add_event(self.hub.db, incident_id, ts, kind, payload)
        await self.hub.broadcast({"type": "incident_update", "ts": db.iso(ts), "incident_id": incident_id,
                                  "state": state, "kind": kind, "payload": payload, **extra})

    async def opened(self, incident_id: str, reason: str, features: dict, ts: datetime, simulated: bool) -> None:
        db.add(self.hub.db, db.Incident(id=incident_id, started_at=ts, reason=reason, state="checkin_1",
                                        features=features, simulated=simulated))
        await self._update(incident_id, "checkin_1", "state",
                           {"from": "monitoring", "to": "checkin_1", "features": features}, ts,
                           reason=reason, simulated=simulated)

    async def state(self, incident_id: str, old: str, new: str, ts: datetime, **fields) -> None:
        db.update_incident(self.hub.db, incident_id, state=new, **fields)
        await self._update(incident_id, new, "state", {"from": old, "to": new}, ts)

    async def event(self, incident_id: str, state: str, kind: str, payload: dict, ts: datetime) -> None:
        await self._update(incident_id, state, kind, payload, ts)

    async def decision(self, incident_id: str, state: str, decision: dict, ts: datetime) -> None:
        db.add_event(self.hub.db, incident_id, ts, "decision", decision)
        await self.hub.broadcast({"type": "decision", "ts": db.iso(ts), "incident_id": incident_id,
                                  "state": state, **decision})


class RoomVoice:
    """The engine's voice: commands to the room agent over /ws/room."""

    def __init__(self, hub: Hub) -> None:
        self.hub = hub

    async def speak_and_listen(self, incident_id: str, text: str, listen_seconds: float, attempt: int) -> None:
        await self.hub.send_command({"type": "speak_and_listen", "incident_id": incident_id, "text": text,
                                     "listen_seconds": listen_seconds, "attempt": attempt})

    async def speak(self, text: str) -> None:
        await self.hub.send_command({"type": "speak", "text": text})


class AckBody(BaseModel):
    by: str = Field(default="dashboard", min_length=1, max_length=80)


class ZonesBody(BaseModel):
    zones: list[dict]


class ContactsBody(BaseModel):
    contacts: list[dict]


def create_app(db_path: Path | str | None = None, agent=None, notifier=None, clock=None,
               escalation_config: dict | None = None) -> FastAPI:
    """Build the app; tests pass their own database, AI, notifier and clock."""
    hub = Hub(db.make_engine(db_path or os.environ.get("GUARDIAN_DB") or db.DEFAULT_DB))
    notifier = notifier or make_notifier(lambda: hub.pose, load_analytics_config()["utc_offset_hours"])
    esc_config = escalation_config or load_escalation_config()
    room_name = os.getenv("ROOM_NAME", "living_room")
    engine = EscalationEngine(esc_config, RoomVoice(hub), agent or make_agent(), notifier, DbRecorder(hub),
                              clock, room_name=room_name)
    hub.engine = engine
    hub.watch = CameraWatch(notifier, engine.clock, esc_config["camera_offline_alert_s"],
                            esc_config["alert_retry_s"], room_name)
    if hasattr(notifier, "on_ack"):
        notifier.on_ack = engine.acknowledge        # the Telegram Acknowledge button
    background: set[asyncio.Task] = set()

    async def tick_forever() -> None:
        while True:
            try:
                await engine.tick()
            except Exception:
                log.exception("escalation tick failed")
            try:
                await hub.watch.tick()
            except Exception:
                log.exception("camera watch tick failed")
            await asyncio.sleep(TICK_S)

    def run_in_background(coro, what: str) -> None:
        """Voice replies can wait seconds for the AI: handle them beside the receive loop."""
        async def guarded():
            try:
                await coro
            except Exception:
                hub.errors += 1
                log.exception("error while handling %s", what)
        task = asyncio.create_task(guarded())
        background.add(task)
        task.add_done_callback(background.discard)

    async def restore_unfinished() -> None:
        """Incidents a previous run left open. The newest real one is re-opened as an alert (the
        check-in cannot be resumed and nobody acknowledged); the rest are closed with a note."""
        unfinished = db.unfinished_incidents(hub.db)   # newest first
        keep = next((i for i in unfinished if not i.simulated), None)
        now = datetime.now(timezone.utc)
        for incident in unfinished:
            if incident is keep:
                continue
            db.add_event(hub.db, incident.id, now, "state", {"from": incident.state, "to": "resolved",
                                                             "note": "closed at start-up (unfinished)"})
            db.update_incident(hub.db, incident.id, state="resolved", resolved_at=now)
            log.info("unfinished incident %s closed at start-up", incident.id)
        if keep is not None:
            await engine.restore(keep.id, keep.reason, db.to_utc(keep.started_at), keep.state)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            await restore_unfinished()
        except Exception:
            log.exception("restoring unfinished incidents failed")
        tasks = [asyncio.create_task(tick_forever())]
        if hasattr(notifier, "poll_forever"):
            tasks.append(asyncio.create_task(notifier.poll_forever()))   # Acknowledge button presses
        yield
        for task in tasks:
            task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks)

    app = FastAPI(title="Guardian server", lifespan=lifespan)
    app.state.hub = hub
    app.state.engine = engine
    app.state.notifier = notifier
    app.state.camera_watch = hub.watch
    # The dashboard runs on port 5173, on this laptop or opened from a phone on the same Wi-Fi.
    app.add_middleware(CORSMiddleware, allow_origin_regex=r"^https?://[^/]+:5173$",
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/status")
    def get_status() -> dict:
        return hub.status_snapshot()

    @app.get("/incidents")
    def get_incidents(limit: int = Query(50, ge=1, le=500), include_simulated: bool = True) -> list[dict]:
        return [db.incident_dict(i) for i in db.list_incidents(hub.db, limit, include_simulated)]

    @app.get("/incidents/{incident_id}")
    def get_incident(incident_id: str) -> dict:
        incident = db.get_incident(hub.db, incident_id)
        if incident is None:
            raise HTTPException(404, "no such incident")
        return db.incident_dict(incident, db.incident_events(hub.db, incident_id))

    @app.post("/incidents/{incident_id}/ack")
    async def ack_incident(incident_id: str, body: AckBody | None = None) -> dict:
        by = body.by if body else "dashboard"
        if await engine.acknowledge(incident_id, by):
            return {"incident_id": incident_id, "state": "resolved", "acknowledged_by": by}
        incident = db.get_incident(hub.db, incident_id)
        if incident is None:
            raise HTTPException(404, "no such incident")
        raise HTTPException(409, f"incident is not open (state: {incident.state})")

    @app.get("/activity")
    def get_activity(start: str | None = Query(None, alias="from"), end: str | None = Query(None, alias="to")) -> list:
        try:
            to = db.to_utc(end) if end else datetime.now(timezone.utc)
            frm = db.to_utc(start) if start else to - timedelta(hours=24)
        except ValueError:
            raise HTTPException(422, "from/to must be ISO 8601 times")
        return [{"ts": db.iso(r.ts), "room": r.room, "activity": r.activity, "confidence": r.confidence,
                 "zone": r.zone, "simulated": r.simulated} for r in db.activity_between(hub.db, frm, to)]

    @app.get("/analytics/daily")
    def get_daily(now: str | None = Query(None, description="for tests and demos: pretend it is this time")) -> dict:
        cfg = load_analytics_config()
        try:
            moment = db.to_utc(now) if now else datetime.now(timezone.utc)
        except ValueError:
            raise HTTPException(422, "now must be an ISO 8601 time")
        start = moment - timedelta(days=cfg["history_days"] + 1)
        rows = [analytics.Row(db.to_utc(r.ts), r.activity, r.simulated)
                for r in db.activity_between(hub.db, start, moment + timedelta(seconds=1))]
        return analytics.daily(rows, moment, cfg)

    @app.get("/analytics/timeline")
    def get_timeline(day: str | None = Query(None, alias="date", description="local date YYYY-MM-DD; default today"),
                     now: str | None = Query(None, description="for tests and demos: pretend it is this time")) -> dict:
        """One local day as activity segments (the Today band), cut off at now for today."""
        cfg = load_analytics_config()
        try:
            moment = db.to_utc(now) if now else datetime.now(timezone.utc)
            local_day = date.fromisoformat(day) if day else moment.astimezone(analytics.local_tz(cfg)).date()
        except ValueError:
            raise HTTPException(422, "date must be YYYY-MM-DD and now an ISO 8601 time")
        start, end = analytics.day_bounds(local_day, cfg)
        until = min(end, max(start, moment))
        rows = [analytics.Row(db.to_utc(r.ts), r.activity, r.simulated)
                for r in db.activity_between(hub.db, start, until)]
        return {"date": local_day.isoformat(), "from": start.isoformat(), "to": end.isoformat(),
                "now": until.isoformat(), "segments": analytics.timeline(rows, start, until, cfg)}

    @app.get("/zones")
    def get_zones() -> dict:
        """Saved zones; until the room agent saves some (Stage 8), the ones in config/zones.json."""
        saved = [{"name": z.name, "polygon": z.polygon} for z in db.list_zones(hub.db)]
        if saved:
            return {"zones": saved, "source": "saved"}
        config = json.loads((ROOT / "config" / "zones.json").read_text(encoding="utf-8"))
        return {"zones": config.get("zones", []), "source": "config"}

    @app.get("/settings")
    def get_settings() -> dict:
        """Read-only summary for the dashboard's Settings page (editing is OPTIONAL in the plan)."""
        esc = engine.cfg
        vision = json.loads((ROOT / "config" / "vision.json").read_text(encoding="utf-8"))
        return {
            "check_in": {"first_listen_s": esc["checkin1_listen_s"], "second_listen_s": esc["checkin2_listen_s"],
                         "floor_rule_s": esc["floor_rule_s"], "realert_every_s": esc["realert_every_s"],
                         "ai_timeout_s": esc["ai_timeout_s"], "help_keywords": esc["help_keywords"]},
            "fall_detection": {"confirm_after_s": vision["fall_confirm_s"], "window_s": vision["fall_window_s"],
                               "found_on_floor_after_s": vision["slow_path_lying_s"],
                               "torso_upright_ratio": vision["torso_upright_ratio"], "model": vision["model"]},
            "alerts": {"telegram": type(notifier).__name__ == "TelegramNotifier",
                       "ai": type(engine.agent).__name__},
            "room": os.getenv("ROOM_NAME", "living_room"),
        }

    @app.post("/zones")
    def post_zones(body: ZonesBody) -> dict:
        for z in body.zones:
            points = z.get("polygon")
            if not z.get("name") or not isinstance(points, list) or len(points) < 3 or not all(
                    isinstance(p, list) and len(p) == 2 and all(0 <= c <= 1 for c in p) for p in points):
                raise HTTPException(422, "each zone needs a name and 3+ corners as [x, y] fractions (0-1)")
        db.replace_zones(hub.db, body.zones)
        log.info("safe zones saved: %s", ", ".join(z["name"] for z in body.zones) or "none")
        return {"zones": [{"name": z.name, "polygon": z.polygon} for z in db.list_zones(hub.db)]}

    @app.get("/contacts")
    def get_contacts() -> dict:
        return {"contacts": [{"name": c.name, "relation": c.relation, "telegram_chat_id": c.telegram_chat_id}
                             for c in db.list_contacts(hub.db)]}

    @app.post("/contacts")
    def post_contacts(body: ContactsBody) -> dict:
        if any(not c.get("name") for c in body.contacts):
            raise HTTPException(422, "each contact needs a name")
        db.replace_contacts(hub.db, body.contacts)
        return get_contacts()

    @app.post("/simulate/fall")
    async def simulate_fall() -> dict:
        incident_id = "inc_sim_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        await engine.on_fall(incident_id, "fast_fall", {}, simulated=True)
        return {"incident_id": engine.incident_id, "state": engine.state}

    @app.websocket("/ws/room")
    async def ws_room(ws: WebSocket) -> None:
        await ws.accept()
        hub.room_ws = ws
        log.info("room agent connected")
        try:
            while True:
                text = await ws.receive_text()
                try:
                    message = validate("room", json.loads(text))
                except (json.JSONDecodeError, ContractError) as exc:
                    hub.rejected += 1
                    log.warning("rejected room message: %s", exc)
                    continue
                if message["type"] == "voice_reply":
                    run_in_background(hub.handle_room_message(message), "voice_reply")
                    continue
                try:
                    await hub.handle_room_message(message)
                except Exception:  # one bad message must never cut off the room agent
                    hub.errors += 1
                    log.exception("error while handling a %s message", message["type"])
        except WebSocketDisconnect:
            pass
        finally:
            if hub.room_ws is ws:
                hub.room_ws = None
                hub.camera = None
                hub.watch.update(False)    # no room agent: Guardian cannot see the room
                with contextlib.suppress(Exception):
                    await hub.broadcast(hub.status_message())   # dashboards show "Camera offline" now
            log.info("room agent disconnected")

    @app.websocket("/ws/dashboard")
    async def ws_dashboard(ws: WebSocket) -> None:
        await ws.accept()
        hub.dashboards.add(ws)
        log.info("dashboard connected (%d open)", len(hub.dashboards))
        try:
            await ws.send_json(hub.status_message())
            while True:
                await ws.receive_text()  # dashboards only listen; ignore anything they send
        except WebSocketDisconnect:
            pass
        finally:
            hub.dashboards.discard(ws)
            log.info("dashboard disconnected (%d open)", len(hub.dashboards))

    return app


app = create_app()
