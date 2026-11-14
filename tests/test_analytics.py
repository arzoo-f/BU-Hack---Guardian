"""Daily mobility figures (BUILD_PLAN step 3.6) on synthetic activity rows."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from analytics import Row, daily, human_duration, summarise, timeline

CONFIG = json.loads((Path(__file__).resolve().parents[1] / "config" / "analytics.json").read_text("utf-8"))
HKT = timezone(timedelta(hours=8))
STEP = 10  # seconds between synthetic rows (= row_gap_cap_s, so each row counts 10 s)


def run(start: datetime, minutes: float, activity: str, simulated: bool = False) -> list[Row]:
    return [Row(start + timedelta(seconds=STEP * i), activity, simulated) for i in range(int(minutes * 60 / STEP))]


def test_minutes_per_activity_and_active_minutes():
    t0 = datetime(2026, 11, 14, 9, 0, tzinfo=HKT)
    rows = run(t0, 2, "standing") + run(t0 + timedelta(minutes=2), 1, "sitting") + \
        run(t0 + timedelta(minutes=3), 0.5, "walking")
    s = summarise(rows, t0, t0 + timedelta(hours=1), CONFIG)
    assert s.minutes == pytest.approx({"standing": 2.0, "sitting": 1.0, "walking": 0.5})
    assert s.active_minutes == pytest.approx(2.5)
    assert s.date == "2026-11-14"


def test_gaps_in_the_data_are_not_counted_as_hours():
    t0 = datetime(2026, 11, 14, 9, 0, tzinfo=HKT)
    rows = [Row(t0, "sitting"), Row(t0 + timedelta(hours=2), "sitting")]   # laptop off in between
    s = summarise(rows, t0, t0 + timedelta(hours=3), CONFIG)
    assert s.minutes["sitting"] == pytest.approx(2 * CONFIG["row_gap_cap_s"] / 60)
    assert s.longest_still_min == pytest.approx(CONFIG["row_gap_cap_s"] / 60)


def test_sit_to_stand_and_longest_still_period():
    t0 = datetime(2026, 11, 14, 9, 0, tzinfo=HKT)
    rows, t = [], t0
    for activity, minutes in [("sitting", 5), ("standing", 1), ("sitting", 20), ("absent", 0.5), ("walking", 2),
                              ("lying", 30), ("sitting", 10), ("standing", 1)]:
        rows += run(t, minutes, activity)
        t += timedelta(minutes=minutes)
    s = summarise(rows, t0, t, CONFIG)
    assert s.sit_to_stand == 3          # sitting->standing, sitting->(absent)->walking, sitting->standing
    assert s.longest_still_min == pytest.approx(40)   # lying 30 + sitting 10 without a break


def test_daily_compares_today_with_the_same_hours_of_the_last_7_days():
    now = datetime(2026, 11, 14, 12, 0, tzinfo=HKT)
    rows = []
    for back in range(1, 8):
        day = now - timedelta(days=back)
        rows += run(day.replace(hour=8), 60, "walking", simulated=True)    # a morning walk every day
        rows += run(day.replace(hour=15), 120, "walking", simulated=True)  # after 12:00: not compared
    rows += run(now.replace(hour=8), 30, "walking") + run(now.replace(hour=8, minute=30), 90, "sitting")
    result = daily(rows, now, CONFIG)
    assert result["average_active_minutes_same_hours"] == pytest.approx(60)
    assert result["change_pct"] == -50
    assert result["insights"][0] == "Active 50% less than the 7-day average so far today."
    assert result["insights"][1] == "Longest still period today: 1 h 30 min."
    assert len(result["days"]) == 8 and result["days"][0]["simulated"] is True
    assert result["days"][-1] == result["today"] and result["today"]["simulated"] is False
    assert result["today"]["minutes"]["walking"] == pytest.approx(30)


def test_daily_without_history_has_no_comparison():
    now = datetime(2026, 11, 14, 12, 0, tzinfo=HKT)
    result = daily(run(now.replace(hour=11), 10, "sitting"), now, CONFIG)
    assert result["change_pct"] is None and result["average_active_minutes_same_hours"] is None
    assert result["insights"] == ["Longest still period today: 10 min.", "Stood up from sitting 0 times today."]


def test_day_boundaries_are_local_time():
    late = datetime(2026, 11, 14, 23, 59, tzinfo=HKT)
    rows = [Row(late.astimezone(timezone.utc), "walking")]       # stored in UTC: still the 14th in Hong Kong
    result = daily(rows, datetime(2026, 11, 15, 0, 30, tzinfo=HKT), CONFIG)
    assert result["days"][-2]["date"] == "2026-11-14" and result["days"][-2]["active_minutes"] > 0
    assert result["today"]["minutes"] == {}


@pytest.mark.parametrize("minutes, text", [(7, "7 min"), (60, "1 h 0 min"), (130.4, "2 h 10 min")])
def test_human_duration(minutes, text):
    assert human_duration(minutes) == text


def test_timeline_merges_rows_into_segments_and_keeps_gaps():
    t0 = datetime(2026, 11, 14, 9, 0, tzinfo=HKT)
    rows = run(t0, 2, "walking") + run(t0 + timedelta(minutes=2), 3, "sitting") + \
        run(t0 + timedelta(minutes=30), 1, "sitting", simulated=True)       # 25 minutes with no data before
    got = timeline(rows, t0, t0 + timedelta(hours=1), CONFIG)
    assert [(s["activity"], s["from"][11:16], s["to"][11:19]) for s in got] == [
        ("walking", "09:00", "09:02:00"), ("sitting", "09:02", "09:05:00"), ("sitting", "09:30", "09:31:00")]
    assert [s["simulated"] for s in got] == [False, False, True]
    assert timeline(rows, t0, t0 + timedelta(minutes=1), CONFIG)[-1]["to"] == "2026-11-14T09:01:00+08:00"
