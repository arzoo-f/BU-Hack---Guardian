"""Times and pass/fail of the real incidents (BUILD_PLAN step 6.1): one line per run.

Landing = the fall message minus the seconds the person was already down (the fall is confirmed
~3 s after landing). First spoken word = when the room agent started playing the first question
(logs/room-agent.log, written by start.bat). Phone alert = when Telegram accepted the alert.

    .venv\\Scripts\\python.exe scripts\\incident_times.py                 # incidents of the last 3 hours
    .venv\\Scripts\\python.exe scripts\\incident_times.py --since 19:00   # from 7 pm today
"""
import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = "http://127.0.0.1:8000"
AGENT_LOG = ROOT / "logs" / "room-agent.log"
PLAYING = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) INFO guardian\.room\.tts: playing")


def get(path: str):
    with urllib.request.urlopen(f"{SERVER}{path}", timeout=5) as r:
        return json.loads(r.read())


def ts(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def playback_starts(log: Path = AGENT_LOG) -> list[datetime]:
    """When each spoken sentence started, from the room agent's log (local time -> UTC)."""
    if not log.exists():
        return []
    starts = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = PLAYING.match(line)
        if m:
            local = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f").astimezone()
            starts.append(local.astimezone(timezone.utc))
    return starts


def analyse(incident: dict, starts: list[datetime]) -> dict:
    """Scenario, pass/fail and the timings of one incident."""
    events = incident["events"]
    states = [e["payload"]["to"] for e in events if e["kind"] == "state" and "to" in e["payload"]]
    fall = next(e for e in events if e["kind"] == "state" and e["payload"].get("from") == "monitoring")
    landing = ts(fall["ts"]) - timedelta(seconds=(fall["payload"].get("features") or {}).get("seconds_low") or 0)
    first_speak = next((ts(e["ts"]) for e in events if e["kind"] == "speak"), None)
    spoken = next((s for s in starts if first_speak and s >= first_speak - timedelta(seconds=1)), None)
    alert = next((ts(e["ts"]) for e in events if e["kind"] == "alert" and e["payload"].get("sent")), None)
    requests = [e["payload"]["request"] for e in events if e["kind"] == "request"]
    heard = [e["payload"].get("transcript") or "-" for e in events if e["kind"] == "reply"]
    if "escalate" in states:
        scenario = "2 no answer"
        passed = (states[:3] == ["checkin_1", "checkin_2", "escalate"] and states[-1] == "resolved"
                  and alert is not None and bool(incident.get("acknowledged_by")))
    else:
        scenario = "1 I'm okay"
        passed = "follow_up" in states and states[-1] == "resolved" and bool(requests)
    return {"id": incident["id"], "started": ts(incident["started_at"]), "scenario": scenario, "passed": passed,
            "first_word_s": (spoken - landing).total_seconds() if spoken else None,
            "alert_s": (alert - landing).total_seconds() if alert else None,
            "states": states, "heard": heard, "requests": requests, "reason": incident["reason"]}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--since", help="HH:MM today (local time); default: the last 3 hours")
    args = p.parse_args(argv)
    now = datetime.now().astimezone()
    since = (now.replace(hour=int(args.since[:2]), minute=int(args.since[3:5]), second=0, microsecond=0)
             if args.since else now - timedelta(hours=3))
    starts = playback_starts()
    rows = [analyse(get(f"/incidents/{i['id']}"), starts) for i in get("/incidents?limit=100")
            if not i["simulated"] and ts(i["started_at"]) >= since.astimezone(timezone.utc)]
    for r in sorted(rows, key=lambda r: r["started"]):
        word = f"{r['first_word_s']:.1f} s" if r["first_word_s"] is not None else "-"
        alert = f"{r['alert_s']:.1f} s" if r["alert_s"] is not None else "-"
        print(f"{r['started'].astimezone():%H:%M:%S}  {r['scenario']:12s} {'PASS' if r['passed'] else 'FAIL'}  "
              f"first word {word:7s} phone alert {alert:7s} heard {r['heard']}"
              + (f"  asked for {r['requests']}" if r["requests"] else ""))
    if not rows:
        print("No real incidents in this period.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
