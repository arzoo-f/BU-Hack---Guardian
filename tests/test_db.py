"""Database tests (BUILD_PLAN step 3.1): every table can be written and read back."""
from datetime import datetime, timedelta, timezone

import pytest

import db

T0 = datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine(tmp_path):
    e = db.make_engine(tmp_path / "test.db")
    yield e
    e.dispose()


def test_incident_with_its_steps(engine):
    db.add(engine, db.Incident(id="inc_001", started_at=T0, reason="fast_fall", state="checkin_1",
                               features={"torso_angle": 78}))
    db.add_event(engine, "inc_001", T0, "state", {"from": "monitoring", "to": "checkin_1"})
    db.add_event(engine, "inc_001", T0 + timedelta(seconds=2), "speak", {"text": "Are you okay?"})
    db.add_event(engine, "inc_001", T0 + timedelta(seconds=9), "reply", {"transcript": "yes", "attempt": 1})
    db.update_incident(engine, "inc_001", state="resolved", resolved_at=T0 + timedelta(minutes=1),
                       acknowledged_by="Person B")
    incident = db.get_incident(engine, "inc_001")
    data = db.incident_dict(incident, db.incident_events(engine, "inc_001"))
    assert data["state"] == "resolved" and data["acknowledged_by"] == "Person B"
    assert data["started_at"] == "2026-11-14T10:00:00.000Z"
    assert data["resolved_at"] == "2026-11-14T10:01:00.000Z"
    assert data["features"] == {"torso_angle": 78}
    assert [e["kind"] for e in data["events"]] == ["state", "speak", "reply"]
    assert data["events"][2]["payload"]["transcript"] == "yes"


def test_unknown_event_kind_is_refused(engine):
    with pytest.raises(ValueError):
        db.add_event(engine, "inc_001", T0, "selfie", {})


def test_update_of_a_missing_incident_raises(engine):
    with pytest.raises(KeyError):
        db.update_incident(engine, "inc_nope", state="resolved")


def test_incidents_newest_first_and_simulated_filter(engine):
    for i, simulated in enumerate([False, True, False]):
        db.add(engine, db.Incident(id=f"inc_{i}", started_at=T0 + timedelta(minutes=i), reason="fast_fall",
                                   state="resolved", simulated=simulated))
    assert [i.id for i in db.list_incidents(engine)] == ["inc_2", "inc_1", "inc_0"]
    assert [i.id for i in db.list_incidents(engine, include_simulated=False)] == ["inc_2", "inc_0"]
    assert [i.id for i in db.list_incidents(engine, limit=1)] == ["inc_2"]


def test_activity_between(engine):
    for i, label in enumerate(["standing", "walking", "sitting", "lying"]):
        db.add(engine, db.ActivityLog(ts=T0 + timedelta(seconds=2 * i), room="living_room", activity=label,
                                      confidence=0.9))
    rows = db.activity_between(engine, T0 + timedelta(seconds=1), T0 + timedelta(seconds=6))
    assert [r.activity for r in rows] == ["walking", "sitting"]


def test_contacts_and_zones_are_replaced_as_a_whole(engine):
    db.replace_contacts(engine, [{"name": "Family (test)", "relation": "family", "telegram_chat_id": "-100"}])
    db.replace_contacts(engine, [{"name": "Person B", "relation": "daughter"}])
    assert [(c.name, c.relation, c.telegram_chat_id) for c in db.list_contacts(engine)] == [
        ("Person B", "daughter", None)]
    db.replace_zones(engine, [{"name": "sofa", "polygon": [[0.1, 0.2], [0.3, 0.2], [0.3, 0.4]]}])
    (zone,) = db.list_zones(engine)
    assert zone.name == "sofa" and zone.polygon == [[0.1, 0.2], [0.3, 0.2], [0.3, 0.4]]
