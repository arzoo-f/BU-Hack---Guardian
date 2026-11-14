"""Seven days of realistic activity history for the Insights page (BUILD_PLAN step 7.2).

Every row is marked simulated=True and the dashboard labels it "simulated history". Mobility drops
over the last three days, so the insight sentences have something real to find. Rows are 10 s apart
(the analytics count each row up to 10 s). Today is left for the real camera.

    .venv\\Scripts\\python.exe scripts\\seed_history.py                # 7 days before today
    .venv\\Scripts\\python.exe scripts\\seed_history.py --replace      # remove earlier simulated rows first
"""
import argparse
import json
import random
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "server"), str(ROOT)]

from sqlmodel import Session, delete  # noqa: E402

import db  # noqa: E402

ROW_S = 10
# One ordinary day, from 7 am: (activity, minutes, zone). Active blocks shrink on "low" days.
DAY = [
    ("standing", 15, None), ("walking", 20, None), ("sitting", 30, None), ("walking", 25, None),
    ("sitting", 60, None), ("standing", 10, None), ("walking", 15, None), ("sitting", 45, None),
    ("lying", 60, "sofa"), ("walking", 20, None), ("sitting", 90, None), ("standing", 15, None),
    ("walking", 15, None), ("sitting", 60, None), ("standing", 10, None), ("sitting", 90, None),
    ("walking", 10, None),
]
ACTIVE = {"standing", "walking"}


def utc_offset_hours() -> float:
    return json.loads((ROOT / "config" / "analytics.json").read_text(encoding="utf-8"))["utc_offset_hours"]


def day_blocks(active_scale: float, rng: random.Random) -> list[tuple[str, float, str | None]]:
    """One day as (activity, minutes, zone) blocks. active_scale < 1 shortens the active blocks and skips
    some of them (the time goes to sitting), so a less active day also has fewer sit-to-stand moves."""
    blocks: list[list] = []
    carry = 0.0   # active minutes taken away, waiting for the next still block
    for activity, minutes, zone in DAY:
        minutes *= rng.uniform(0.8, 1.2)
        if activity in ACTIVE and active_scale < 1:
            kept = 0.0 if rng.random() < 1 - active_scale else minutes * active_scale
            if blocks and blocks[-1][0] not in ACTIVE:
                blocks[-1][1] += minutes - kept
            else:
                carry += minutes - kept
            minutes = kept
        elif activity not in ACTIVE:
            minutes, carry = minutes + carry, 0.0
        if minutes <= 0:
            continue
        if blocks and blocks[-1][0] == activity and blocks[-1][2] == zone:
            blocks[-1][1] += minutes
        else:
            blocks.append([activity, minutes, zone])
    return [tuple(b) for b in blocks]


def day_rows(day: date, active_scale: float, rng: random.Random, room: str) -> list[db.ActivityLog]:
    """One day of rows, from about 7 am."""
    tz = timezone(timedelta(hours=utc_offset_hours()))
    t = datetime.combine(day, time(7, 0), tzinfo=tz) + timedelta(minutes=rng.randint(-20, 20))
    rows = []
    for activity, minutes, zone in day_blocks(active_scale, rng):
        for _ in range(int(minutes * 60 / ROW_S)):
            rows.append(db.ActivityLog(ts=t.astimezone(timezone.utc), room=room, activity=activity,
                                       confidence=round(rng.uniform(0.8, 0.98), 2), zone=zone, simulated=True))
            t += timedelta(seconds=ROW_S)
    return rows


def seed(engine, days: int = 7, today: date | None = None, low_days: int = 3, low_scale: float = 0.6,
         seed_value: int = 7, room: str = "living_room", replace: bool = False) -> dict:
    """Insert `days` days of simulated history ending yesterday; the last `low_days` are less active."""
    tz = timezone(timedelta(hours=utc_offset_hours()))
    today = today or datetime.now(tz).date()
    rng = random.Random(seed_value)
    with Session(engine) as session:
        if replace:
            session.exec(delete(db.ActivityLog).where(db.ActivityLog.simulated == True))  # noqa: E712
        total = 0
        for back in range(days, 0, -1):
            scale = low_scale if back <= low_days else 1.0
            rows = day_rows(today - timedelta(days=back), scale, rng, room)
            session.add_all(rows)
            total += len(rows)
        session.commit()
    return {"days": days, "rows": total, "first_day": str(today - timedelta(days=days)),
            "last_day": str(today - timedelta(days=1)), "low_days": low_days}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--replace", action="store_true", help="delete earlier simulated rows first")
    p.add_argument("--db", default=str(db.DEFAULT_DB), help="database file (default: the server's)")
    args = p.parse_args(argv)
    engine = db.make_engine(args.db)
    result = seed(engine, days=args.days, replace=args.replace)
    engine.dispose()
    print(f"Seeded {result['rows']} simulated activity rows: {result['first_day']} to {result['last_day']} "
          f"(the last {result['low_days']} days less active).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
