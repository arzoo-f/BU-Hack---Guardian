"""Daily mobility figures from the activity log (BUILD_PLAN step 3.6): what makes Guardian data-driven.

Each activity row (about every 2 s) lasts until the next one, capped at row_gap_cap_s so that a gap
in the data (laptop off, camera offline) is not counted as hours of sitting. Days are local days
(utc_offset_hours, config/analytics.json).
"""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone


@dataclass
class Row:
    ts: datetime          # timezone-aware
    activity: str
    simulated: bool = False


@dataclass
class DaySummary:
    date: str
    minutes: dict[str, float] = field(default_factory=dict)
    active_minutes: float = 0.0
    sit_to_stand: int = 0
    longest_still_min: float = 0.0
    simulated: bool = False

    def as_dict(self) -> dict:
        return {"date": self.date, "minutes": {k: round(v, 1) for k, v in sorted(self.minutes.items())},
                "active_minutes": round(self.active_minutes, 1), "sit_to_stand": self.sit_to_stand,
                "longest_still_min": round(self.longest_still_min, 1), "simulated": self.simulated}


def local_tz(config: dict) -> timezone:
    return timezone(timedelta(hours=config["utc_offset_hours"]))


def day_bounds(day: date, config: dict) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time(0), tzinfo=local_tz(config))
    return start, start + timedelta(days=1)


def summarise(rows: list[Row], start: datetime, end: datetime, config: dict) -> DaySummary:
    """Figures for the rows with start <= ts < end (rows sorted by time)."""
    cap = timedelta(seconds=config["row_gap_cap_s"])
    active, still = set(config["active_activities"]), set(config["still_activities"])
    summary = DaySummary(date=start.astimezone(local_tz(config)).date().isoformat())
    inside = [r for r in rows if start <= r.ts < end]
    still_run, previous = timedelta(0), None
    for i, row in enumerate(inside):
        nxt = inside[i + 1].ts if i + 1 < len(inside) else end
        lasts = max(min(nxt - row.ts, cap, end - row.ts), timedelta(0))
        minutes = lasts.total_seconds() / 60
        summary.minutes[row.activity] = summary.minutes.get(row.activity, 0.0) + minutes
        if row.activity in active:
            summary.active_minutes += minutes
        if previous == "sitting" and row.activity in active:
            summary.sit_to_stand += 1
        gap_before = row.ts - inside[i - 1].ts if i else timedelta(0)
        if row.activity in still and gap_before <= cap:
            still_run += lasts
        else:
            still_run = lasts if row.activity in still else timedelta(0)
        summary.longest_still_min = max(summary.longest_still_min, still_run.total_seconds() / 60)
        summary.simulated |= row.simulated
        if row.activity != "absent":
            previous = row.activity
    return summary


def timeline(rows: list[Row], start: datetime, end: datetime, config: dict) -> list[dict]:
    """The rows with start <= ts < end merged into segments of one activity, for the Today band.

    A row lasts until the next one, capped at row_gap_cap_s like in summarise(); a longer gap ends
    the segment, so missing data shows as a gap rather than as one long activity.
    """
    cap = timedelta(seconds=config["row_gap_cap_s"])
    inside = [r for r in rows if start <= r.ts < end]
    segments: list[dict] = []
    for i, row in enumerate(inside):
        nxt = inside[i + 1].ts if i + 1 < len(inside) else end
        until = row.ts + max(min(nxt - row.ts, cap, end - row.ts), timedelta(0))
        last = segments[-1] if segments else None
        if last and last["activity"] == row.activity and row.ts <= last["to"]:
            last["to"] = until
            last["simulated"] |= row.simulated
        else:
            segments.append({"from": row.ts, "to": until, "activity": row.activity, "simulated": row.simulated})
    return [{**s, "from": s["from"].isoformat(), "to": s["to"].isoformat()} for s in segments]


def human_duration(minutes: float) -> str:
    """95 -> '1 h 35 min'; 7 -> '7 min'."""
    m = int(round(minutes))
    return f"{m // 60} h {m % 60} min" if m >= 60 else f"{m} min"


def daily(rows: list[Row], now: datetime, config: dict) -> dict:
    """Today, the previous history_days days, today against their average, and insight sentences."""
    tz = local_tz(config)
    today = now.astimezone(tz).date()
    days = [today - timedelta(days=n) for n in range(config["history_days"], -1, -1)]
    summaries = [summarise(rows, *day_bounds(d, config), config) for d in days]
    today_summary = summaries[-1]

    # Fair comparison: today so far against the same hours of the previous days.
    elapsed = now.astimezone(tz) - day_bounds(today, config)[0]
    same_hours = [summarise(rows, day_bounds(d, config)[0], day_bounds(d, config)[0] + elapsed, config)
                  for d in days[:-1]]
    with_data = [s for s in same_hours if s.minutes]
    average = sum(s.active_minutes for s in with_data) / len(with_data) if with_data else None
    change_pct = None
    if average:
        change_pct = round(100 * (today_summary.active_minutes - average) / average)

    insights = []
    if change_pct is not None:
        if abs(change_pct) >= config["insight_change_pct"]:
            word = "less" if change_pct < 0 else "more"
            insights.append(f"Active {abs(change_pct)}% {word} than the {len(with_data)}-day average so far today.")
        else:
            insights.append("Activity today is close to the usual level for this time of day.")
    if today_summary.longest_still_min >= 1:
        insights.append(f"Longest still period today: {human_duration(today_summary.longest_still_min)}.")
    if today_summary.minutes:
        times = "time" if today_summary.sit_to_stand == 1 else "times"
        insights.append(f"Stood up from sitting {today_summary.sit_to_stand} {times} today.")
    return {"today": today_summary.as_dict(), "days": [s.as_dict() for s in summaries],
            "average_active_minutes_same_hours": None if average is None else round(average, 1),
            "change_pct": change_pct, "insights": insights}
