"""Put Guardian back to a clean demo state (BUILD_PLAN step 7.7): no incidents, no activity except
seven days of simulated history.

If the server is running, an open incident is first acknowledged through the server (so its
in-memory state is cleared too). ALL incidents and activity rows in the database are then deleted -
this is for the demo database, so it asks for --yes.

    .venv\\Scripts\\python.exe scripts\\reset_demo.py --yes
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "server"), str(ROOT / "scripts"), str(ROOT)]

from sqlmodel import Session, delete  # noqa: E402

import db  # noqa: E402
import seed_history  # noqa: E402


def close_open_incident(server: str) -> str:
    """Acknowledge the open incident through a running server; returns what happened."""
    try:
        with urllib.request.urlopen(f"{server}/status", timeout=2) as r:
            status = json.loads(r.read())
    except Exception:
        return "server not running"
    incident = status.get("open_incident")
    if not incident:
        return "server running, no open incident"
    request = urllib.request.Request(f"{server}/incidents/{incident}/ack", method="POST",
                                     data=json.dumps({"by": "reset_demo"}).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=5):
        pass
    return f"open incident {incident} acknowledged"


def reset(engine) -> dict:
    """Delete every incident, incident step and activity row; then seed the simulated history."""
    with Session(engine) as session:
        steps = session.exec(delete(db.IncidentEvent)).rowcount
        incidents = session.exec(delete(db.Incident)).rowcount
        activity = session.exec(delete(db.ActivityLog)).rowcount
        session.commit()
    seeded = seed_history.seed(engine)
    return {"incidents_deleted": incidents, "steps_deleted": steps, "activity_deleted": activity, **seeded}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--yes", action="store_true", help="really delete all incidents and activity")
    p.add_argument("--db", default=str(db.DEFAULT_DB))
    p.add_argument("--server", default="http://127.0.0.1:8000")
    args = p.parse_args(argv)
    if not args.yes:
        print("This deletes ALL incidents and activity in the demo database. Run again with --yes.")
        return 1
    print(close_open_incident(args.server))
    engine = db.make_engine(args.db)
    result = reset(engine)
    engine.dispose()
    print(f"Deleted {result['incidents_deleted']} incidents ({result['steps_deleted']} steps) and "
          f"{result['activity_deleted']} activity rows.")
    print(f"Seeded {result['rows']} simulated rows: {result['first_day']} to {result['last_day']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
