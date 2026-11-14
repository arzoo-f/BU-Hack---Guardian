"""Simulated history and demo reset (BUILD_PLAN steps 7.2 and 7.7)."""
from datetime import date, datetime, timedelta, timezone

import pytest

import analytics
import db
import reset_demo
import seed_history

HKT = timezone(timedelta(hours=8))
TODAY = date(2026, 11, 14)
CONFIG = {"utc_offset_hours": 8, "history_days": 7, "active_activities": ["standing", "walking"],
          "still_activities": ["sitting", "lying"], "row_gap_cap_s": 10, "insight_change_pct": 10}


@pytest.fixture
def engine(tmp_path):
    e = db.make_engine(tmp_path / "demo.db")
    yield e
    e.dispose()


def daily_from(engine, now):
    rows = [analytics.Row(db.to_utc(r.ts), r.activity, r.simulated)
            for r in db.activity_between(engine, now - timedelta(days=9), now)]
    return analytics.daily(rows, now, CONFIG)


def test_seven_simulated_days_with_mobility_dropping_at_the_end(engine):
    result = seed_history.seed(engine, today=TODAY)
    assert result["first_day"] == "2026-11-07" and result["last_day"] == "2026-11-13"
    rows = db.activity_between(engine, datetime(2026, 11, 1, tzinfo=HKT), datetime(2026, 11, 20, tzinfo=HKT))
    assert len(rows) == result["rows"] and all(r.simulated for r in rows)
    assert {r.zone for r in rows if r.activity == "lying"} == {"sofa"}            # naps on the sofa
    days = daily_from(engine, datetime(2026, 11, 14, 12, 0, tzinfo=HKT))["days"]
    by_date = {d["date"]: d for d in days}
    normal = [by_date[f"2026-11-{n:02d}"]["active_minutes"] for n in range(7, 11)]
    low = [by_date[f"2026-11-{n:02d}"]["active_minutes"] for n in range(11, 14)]
    assert min(normal) > max(low)                                                  # the drop is visible
    assert 120 < sum(normal) / 4 < 200 and all(by_date[f"2026-11-{n:02d}"]["sit_to_stand"] >= 2 for n in range(7, 14))
    stands = [by_date[f"2026-11-{n:02d}"]["sit_to_stand"] for n in range(7, 14)]
    assert sum(stands[4:]) / 3 < sum(stands[:4]) / 4                               # fewer stand-ups too
    assert by_date["2026-11-14"]["minutes"] == {}                                  # today is for the camera


def test_insights_find_the_drop(engine):
    seed_history.seed(engine, today=TODAY)
    now = datetime(2026, 11, 14, 12, 0, tzinfo=HKT)
    db.add(engine, db.ActivityLog(ts=now - timedelta(hours=3), room="living_room", activity="walking", confidence=0.9))
    result = daily_from(engine, now)
    assert result["change_pct"] < -50 and result["insights"][0].startswith("Active ")


def test_replace_only_removes_simulated_rows(engine):
    seed_history.seed(engine, today=TODAY)
    db.add(engine, db.ActivityLog(ts=datetime(2026, 11, 14, 9, tzinfo=HKT), room="living_room", activity="sitting",
                                  confidence=0.9))
    first = len(db.activity_between(engine, datetime(2026, 11, 1, tzinfo=HKT), datetime(2026, 11, 20, tzinfo=HKT)))
    seed_history.seed(engine, today=TODAY, replace=True)
    rows = db.activity_between(engine, datetime(2026, 11, 1, tzinfo=HKT), datetime(2026, 11, 20, tzinfo=HKT))
    assert len(rows) == first and sum(not r.simulated for r in rows) == 1


def test_reset_clears_incidents_and_reseeds(engine, monkeypatch):
    db.add(engine, db.Incident(id="inc_1", started_at=datetime(2026, 11, 14, 9, tzinfo=HKT), reason="fast_fall",
                               state="escalate"))
    db.add_event(engine, "inc_1", datetime(2026, 11, 14, 9, tzinfo=HKT), "alert", {"attempt": 1, "sent": True})
    db.add(engine, db.ActivityLog(ts=datetime(2026, 11, 14, 9, tzinfo=HKT), room="living_room", activity="sitting",
                                  confidence=0.9))
    result = reset_demo.reset(engine)
    assert (result["incidents_deleted"], result["steps_deleted"], result["activity_deleted"]) == (1, 1, 1)
    assert db.list_incidents(engine) == [] and result["rows"] > 0


def test_reset_needs_yes(capsys):
    assert reset_demo.main([]) == 1
    assert "--yes" in capsys.readouterr().out


def test_closing_the_open_incident_when_no_server_runs():
    assert reset_demo.close_open_incident("http://127.0.0.1:9") == "server not running"
