"""Stage 6 timing script: pass/fail and timings from an incident's stored steps."""
from datetime import datetime, timezone

import incident_times


def ev(ts, kind, payload):
    return {"ts": ts, "kind": kind, "payload": payload}


def test_scenario_2_timings_and_pass():
    incident = {"id": "inc_1", "started_at": "2026-11-14T11:00:03Z", "reason": "fast_fall", "acknowledged_by": "Telegram",
                "events": [ev("2026-11-14T11:00:03Z", "state", {"from": "monitoring", "to": "checkin_1",
                                                                 "features": {"seconds_low": 3.0}}),
                           ev("2026-11-14T11:00:03.1Z", "speak", {"text": "Are you okay?"}),
                           ev("2026-11-14T11:00:15Z", "state", {"from": "checkin_1", "to": "checkin_2"}),
                           ev("2026-11-14T11:00:29Z", "state", {"from": "checkin_2", "to": "escalate"}),
                           ev("2026-11-14T11:00:30Z", "alert", {"attempt": 1, "sent": True}),
                           ev("2026-11-14T11:00:50Z", "state", {"from": "escalate", "to": "resolved"})]}
    starts = [datetime(2026, 11, 14, 11, 0, 3, 900000, tzinfo=timezone.utc)]
    r = incident_times.analyse(incident, starts)
    assert r["scenario"] == "2 no answer" and r["passed"]
    assert round(r["first_word_s"], 1) == 3.9 and r["alert_s"] == 30.0


def test_scenario_1_needs_the_request():
    events = [ev("2026-11-14T11:00:03Z", "state", {"from": "monitoring", "to": "checkin_1", "features": {"seconds_low": 3}}),
              ev("2026-11-14T11:00:20Z", "state", {"from": "checkin_1", "to": "follow_up"}),
              ev("2026-11-14T11:00:35Z", "state", {"from": "follow_up", "to": "resolved"})]
    incident = {"id": "inc_2", "started_at": "2026-11-14T11:00:03Z", "reason": "fast_fall", "events": events}
    assert incident_times.analyse(incident, [])["passed"] is False            # no water request
    events.insert(2, ev("2026-11-14T11:00:34Z", "request", {"request": "some water"}))
    assert incident_times.analyse(incident, [])["passed"] is True
