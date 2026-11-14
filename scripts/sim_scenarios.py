"""Both demo scenarios end to end, with no person, microphone, OpenAI or Telegram (BUILD_PLAN step 7.1).

A real server runs on a spare port with a throwaway database, the fake AI and a recording stand-in
for Telegram. Recorded clips go through the real vision code; scripted replies stand in for the voice.

  0. Fast sit on the chair (tune_fast_sit_01): no incident.
  1. "I'm okay" (fall clip): "Yes, I slipped" -> gets up -> "Some water, please" -> gentle message,
     resolved, no alert.
  2. "No answer" (fall clip): silence twice -> alert -> Acknowledge (as the dashboard button does)
     -> resolved.

    .venv\\Scripts\\python.exe scripts\\sim_scenarios.py
    .venv\\Scripts\\python.exe scripts\\sim_scenarios.py --fall-clip clips\\tune_fall_sideways_01.mp4

Exit code 0 only if every check passes. Needs the clips in clips/ (they stay on this laptop).
"""
import argparse
import asyncio
import contextlib
import inspect
import logging
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "server"), str(ROOT / "room-agent"), str(ROOT)]

import httpx  # noqa: E402
import uvicorn  # noqa: E402

from agent import FakeAgent  # noqa: E402
from app import create_app  # noqa: E402
from camera_mode import VisionLoop  # noqa: E402
from commands import CommandHandler  # noqa: E402
from server_link import ServerLink, ws_url  # noqa: E402
from settings import load_vision_config  # noqa: E402
from vision.sources import ClipSource  # noqa: E402

FIRST_WORD_LIMIT_S = 6     # BUILD_PLAN CP4.3 / Stage 6: fall -> first spoken word
ALERT_LIMIT_S = 30         # fall -> family alert in Scenario 2
QUIET_AFTER_CLIP_S = 4     # fast sit: wait this long after the clip for an incident that must not come
SCENARIO_LIMIT_S = 90
# Clips are replayed as fast as possible, so the fall confirmation wait (clip time) is added to the timings.
CONFIRM_S = load_vision_config()["fall_confirm_s"]


class RecordingNotifier:
    """Stands in for Telegram and remembers what would have been sent, with the time."""

    def __init__(self) -> None:
        self.alerts: list[tuple[float, str, int]] = []
        self.gentle_messages: list[tuple[float, str, str]] = []
        self.acks: list[tuple[str, str]] = []

    async def alert(self, incident: dict, attempt: int) -> None:
        self.alerts.append((time.monotonic(), incident["incident_id"], attempt))

    async def gentle(self, incident: dict, request: str) -> None:
        self.gentle_messages.append((time.monotonic(), incident["incident_id"], request))

    async def acknowledged(self, incident: dict, by: str) -> None:
        self.acks.append((incident["incident_id"], by))


class ScriptedVoice:
    """Says nothing out loud; 'hears' the next scripted reply after the full listening time."""

    def __init__(self, replies: list[str], after_reply=None) -> None:
        self.replies = list(replies)
        self.after_reply = after_reply        # async callback(number of replies given so far)
        self.spoken: list[tuple[float, str]] = []
        self.answered = 0

    def space_pressed(self) -> None:
        pass

    async def speak(self, text: str) -> None:
        self.spoken.append((time.monotonic(), text))

    async def ask(self, text: str, listen_seconds: float) -> dict:
        await self.speak(text)
        await asyncio.sleep(listen_seconds)
        reply = self.replies.pop(0) if self.replies else ""
        self.answered += 1
        if self.after_reply:
            asyncio.ensure_future(self.after_reply(self.answered))
        return {"transcript": reply, "heard_speech": bool(reply)}


class Report:
    def __init__(self) -> None:
        self.failures = 0

    def check(self, ok: bool, text: str) -> bool:
        print(f"   {'PASS' if ok else 'FAIL'}  {text}")
        self.failures += not ok
        return ok


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Room:
    """A room agent in this process: the clip through the vision code, commands through `voice`."""

    def __init__(self, server: str, clip: Path, voice) -> None:
        self.voice = voice
        self.link = ServerLink(ws_url(server))
        self.link.on_command = CommandHandler(self.link, voice).handle
        self.fall_sent: float | None = None
        self.vision = VisionLoop(ClipSource(clip, *self._size()), load_vision_config(), self._emit,
                                 "living_room", show_window=False)
        self._loop: asyncio.AbstractEventLoop | None = None

    @staticmethod
    def _size() -> tuple[int, int]:
        cfg = load_vision_config()
        return cfg["frame_width"], cfg["frame_height"]

    def _emit(self, message: dict) -> None:
        if message["type"] == "fall_detected":
            self.fall_sent = time.monotonic()
        asyncio.run_coroutine_threadsafe(self.link.send(message), self._loop)

    async def __aenter__(self):
        self._loop = asyncio.get_running_loop()
        self._link_task = asyncio.create_task(self.link.run_forever())
        for _ in range(100):
            if self.link.connected:
                break
            await asyncio.sleep(0.05)
        self.vision_done = asyncio.ensure_future(asyncio.to_thread(self.vision.run))
        return self

    async def __aexit__(self, *exc) -> None:
        self.vision.stop.set()
        with contextlib.suppress(Exception):
            await self.vision_done
        self._link_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._link_task

    async def get_up(self) -> None:
        """The person stands up: what the camera would report once the clip (lying still) is over."""
        await self.vision_done
        incident = self.vision._incident_id
        await self.link.send({"type": "posture_update", "incident_id": incident, "activity": "standing"})


async def incident_of(http: httpx.AsyncClient, room: Room) -> dict | None:
    incident = room.vision._incident_id
    if not incident:
        return None
    r = await http.get(f"/incidents/{incident}")
    return r.json() if r.status_code == 200 else None


async def wait_for(predicate, limit_s: float, step_s: float = 0.2):
    """Poll `predicate` (plain or async) until it gives something truthy; None after limit_s."""
    end = time.monotonic() + limit_s
    while time.monotonic() < end:
        value = predicate()
        if inspect.isawaitable(value):
            value = await value
        if value:
            return value
        await asyncio.sleep(step_s)
    return None


def states(incident: dict) -> list[str]:
    return [e["payload"]["to"] for e in incident["events"] if e["kind"] == "state" and "to" in e["payload"]]


async def scenario_fast_sit(server: str, http, clip: Path, report: Report) -> None:
    print(f"\n0. Fast sit on the chair ({clip.name}): nothing should alert")
    voice = ScriptedVoice([])
    async with Room(server, clip, voice) as room:
        await room.vision_done
        await asyncio.sleep(QUIET_AFTER_CLIP_S)
        report.check(room.fall_sent is None, "no fall detected")
        report.check(not voice.spoken, "Guardian stayed quiet")


async def scenario_okay(server: str, http, clip: Path, notifier: RecordingNotifier, report: Report) -> None:
    print(f"\n1. \"I'm okay\" ({clip.name}): yes, gets up, asks for water")
    room: Room | None = None

    async def after_reply(n: int) -> None:
        if n == 1:
            await room.get_up()

    voice = ScriptedVoice(["Yes, I slipped", "Some water, please"], after_reply)
    async with Room(server, clip, voice) as room:
        if not report.check(await wait_for(lambda: room.fall_sent, 60) is not None, "fall detected"):
            return
        incident = await wait_for(lambda: _resolved(http, room), SCENARIO_LIMIT_S)
        if not report.check(incident is not None, "incident resolved"):
            return
        first = voice.spoken[0][0] - room.fall_sent + CONFIRM_S if voice.spoken else None
        report.check(first is not None and first < FIRST_WORD_LIMIT_S,
                     f"fall -> first question {first:.1f} s with the {CONFIRM_S:.0f} s fall confirmation "
                     f"(under {FIRST_WORD_LIMIT_S} s)" if first is not None else "Guardian asked a question")
        report.check(states(incident) == ["checkin_1", "follow_up", "resolved"],
                     f"states: {' -> '.join(states(incident))}")
        gentle = [g for g in notifier.gentle_messages if g[1] == incident["id"]]
        report.check(len(gentle) == 1 and "water" in gentle[0][2], f"gentle family message: {[g[2] for g in gentle]}")
        report.check(not any(a[1] == incident["id"] for a in notifier.alerts), "no alert")


async def _resolved(http, room: Room) -> dict | None:
    incident = await incident_of(http, room)
    return incident if incident and incident["state"] == "resolved" else None


async def scenario_no_answer(server: str, http, clip: Path, notifier: RecordingNotifier, report: Report) -> None:
    print(f"\n2. \"No answer\" ({clip.name}): silence, alert, Acknowledge")
    voice = ScriptedVoice(["", ""])
    async with Room(server, clip, voice) as room:
        if not report.check(await wait_for(lambda: room.fall_sent, 60) is not None, "fall detected"):
            return
        incident_id = await wait_for(lambda: room.vision._incident_id, 5)
        alert = await wait_for(lambda: next((a for a in notifier.alerts if a[1] == incident_id), None),
                               SCENARIO_LIMIT_S)
        if not report.check(alert is not None, "family alerted"):
            return
        took = alert[0] - room.fall_sent + CONFIRM_S
        report.check(took < ALERT_LIMIT_S, f"fall -> family alert {took:.1f} s with the {CONFIRM_S:.0f} s fall "
                                           f"confirmation (under {ALERT_LIMIT_S} s)")
        r = await http.post(f"/incidents/{incident_id}/ack", json={"by": "sim_scenarios"})
        report.check(r.status_code == 200, f"Acknowledge accepted (HTTP {r.status_code})")
        incident = await wait_for(lambda: _resolved(http, room), 10)
        if not report.check(incident is not None, "incident resolved after Acknowledge"):
            return
        report.check(states(incident) == ["checkin_1", "checkin_2", "escalate", "resolved"],
                     f"states: {' -> '.join(states(incident))}")
        report.check(incident["acknowledged_by"] == "sim_scenarios", f"acknowledged by {incident['acknowledged_by']}")
        report.check((incident_id, "sim_scenarios") in notifier.acks, "family told it was acknowledged")
        said = [text for _, text in voice.spoken]
        report.check(any("family" in s.lower() for s in said), f"told the person: {said[-1]!r}")


async def run(args) -> int:
    for clip in (args.fall_clip, args.sit_clip):
        if not clip.exists():
            print(f"Missing clip {clip}. The clips stay on the demo laptop (clips/ is not in git).")
            return 2
    notifier = RecordingNotifier()
    port = free_port()
    server = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory() as tmp:
        app = create_app(db_path=Path(tmp) / "sim.db", agent=FakeAgent(), notifier=notifier)
        uv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", ws="websockets"))
        thread = threading.Thread(target=uv.run, daemon=True)
        thread.start()
        report = Report()
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(base_url=server, timeout=5) as http:
                await wait_for(lambda: _up(http), 15)
                await scenario_fast_sit(server, http, args.sit_clip, report)
                await scenario_okay(server, http, args.fall_clip, notifier, report)
                await scenario_no_answer(server, http, args.fall_clip, notifier, report)
        finally:
            uv.should_exit = True
            thread.join(timeout=10)
            app.state.hub.db.dispose()   # Windows keeps the file locked otherwise
    verdict = "ALL PASS" if not report.failures else f"{report.failures} FAILED"
    print(f"\n{verdict} ({time.monotonic() - started:.0f} s)")
    return 0 if not report.failures else 1


async def _up(http) -> bool:
    try:
        return (await http.get("/status")).status_code == 200
    except httpx.HTTPError:
        return False


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fall-clip", type=Path, default=ROOT / "clips" / "tune_fall_forward_01.mp4")
    p.add_argument("--sit-clip", type=Path, default=ROOT / "clips" / "tune_fast_sit_01.mp4")
    p.add_argument("-v", "--verbose", action="store_true", help="show the server and room agent logs")
    args = p.parse_args(argv)
    for name in ("httpx", "httpcore"):          # request URLs can carry secrets: never log them
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.ERROR,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
