"""SQLite storage for the Guardian server (SQLModel), BUILD_PLAN Section 12 data model.

Tables: activity_log, incidents, incident_events, contacts, zones. Pose messages are never stored.
All timestamps are stored as timezone-aware UTC.
"""
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Column, JSON
from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, create_engine, delete, select

DEFAULT_DB = Path(__file__).resolve().parent / "guardian.db"
EVENT_KINDS = ("state", "speak", "reply", "decision", "alert", "ack", "request")


class ActivityLog(SQLModel, table=True):
    """One smoothed activity label from the room agent (about every 2 s)."""

    __tablename__ = "activity_log"
    id: int | None = Field(default=None, primary_key=True)
    ts: datetime = Field(index=True)
    room: str
    activity: str
    confidence: float
    zone: str | None = None
    simulated: bool = False


class Incident(SQLModel, table=True):
    """One fall or found-on-floor event."""

    __tablename__ = "incidents"
    id: str = Field(primary_key=True)
    started_at: datetime = Field(index=True)
    reason: str
    state: str
    features: dict = Field(default_factory=dict, sa_column=Column(JSON))
    resolved_at: datetime | None = None
    acknowledged_by: str | None = None
    simulated: bool = False


class IncidentEvent(SQLModel, table=True):
    """One step of an incident: state change, what was said or heard, a decision, an alert ..."""

    __tablename__ = "incident_events"
    id: int | None = Field(default=None, primary_key=True)
    incident_id: str = Field(index=True, foreign_key="incidents.id")
    ts: datetime
    kind: str
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Contact(SQLModel, table=True):
    """Who gets the alerts. For the demo: the family test group."""

    __tablename__ = "contacts"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    relation: str = ""
    telegram_chat_id: str | None = None


class ZoneRow(SQLModel, table=True):
    """A safe zone (mirror of config/zones.json): polygon in image fractions."""

    __tablename__ = "zones"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    polygon: list = Field(default_factory=list, sa_column=Column(JSON))


def to_utc(ts: str | datetime) -> datetime:
    """Parse an ISO timestamp (or take a datetime) and return it as timezone-aware UTC.

    SQLModel refuses naive datetimes; a timestamp without an offset is taken to be UTC.
    """
    dt = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    """UTC ISO string with a Z suffix (SQLite hands datetimes back without their zone)."""
    if dt is None:
        return None
    return to_utc(dt).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def make_engine(path: Path | str = DEFAULT_DB) -> Engine:
    """Create the SQLite engine and make sure every table exists."""
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


def add(engine: Engine, row: SQLModel) -> None:
    """Insert one row and commit."""
    with Session(engine) as session:
        session.add(row)
        session.commit()


# -- incidents --------------------------------------------------------------------------------

def get_incident(engine: Engine, incident_id: str) -> Incident | None:
    with Session(engine) as session:
        return session.get(Incident, incident_id)


def update_incident(engine: Engine, incident_id: str, **fields) -> None:
    """Change fields of an incident (state, resolved_at, acknowledged_by ...)."""
    with Session(engine) as session:
        row = session.get(Incident, incident_id)
        if row is None:
            raise KeyError(incident_id)
        for key, value in fields.items():
            setattr(row, key, value)
        session.add(row)
        session.commit()


def add_event(engine: Engine, incident_id: str, ts: datetime, kind: str, payload: dict) -> None:
    """Record one step of an incident."""
    if kind not in EVENT_KINDS:
        raise ValueError(f"unknown event kind {kind!r}")
    add(engine, IncidentEvent(incident_id=incident_id, ts=to_utc(ts), kind=kind, payload=payload))


def incident_events(engine: Engine, incident_id: str) -> list[IncidentEvent]:
    with Session(engine) as session:
        query = select(IncidentEvent).where(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.id)
        return list(session.exec(query))


def list_incidents(engine: Engine, limit: int = 50, include_simulated: bool = True) -> list[Incident]:
    """Newest first."""
    with Session(engine) as session:
        query = select(Incident).order_by(Incident.started_at.desc()).limit(limit)
        if not include_simulated:
            query = query.where(Incident.simulated == False)  # noqa: E712 (SQL expression)
        return list(session.exec(query))


def unfinished_incidents(engine: Engine) -> list[Incident]:
    """Incidents that never reached Resolved (for example the server stopped mid-incident), newest first."""
    with Session(engine) as session:
        query = select(Incident).where(Incident.state != "resolved").order_by(Incident.started_at.desc())
        return list(session.exec(query))


def incident_dict(incident: Incident, events: list[IncidentEvent] | None = None) -> dict:
    """An incident as plain JSON-ready data, optionally with its steps."""
    data = {"id": incident.id, "started_at": iso(incident.started_at), "reason": incident.reason,
            "state": incident.state, "features": incident.features, "resolved_at": iso(incident.resolved_at),
            "acknowledged_by": incident.acknowledged_by, "simulated": incident.simulated}
    if events is not None:
        data["events"] = [{"ts": iso(e.ts), "kind": e.kind, "payload": e.payload} for e in events]
    return data


# -- activity ---------------------------------------------------------------------------------

def activity_between(engine: Engine, start: datetime, end: datetime) -> list[ActivityLog]:
    """Activity rows with start <= ts < end, oldest first."""
    with Session(engine) as session:
        query = (select(ActivityLog).where(ActivityLog.ts >= to_utc(start), ActivityLog.ts < to_utc(end))
                 .order_by(ActivityLog.ts))
        return list(session.exec(query))


# -- contacts and zones -----------------------------------------------------------------------

def list_contacts(engine: Engine) -> list[Contact]:
    with Session(engine) as session:
        return list(session.exec(select(Contact).order_by(Contact.id)))


def replace_contacts(engine: Engine, contacts: list[dict]) -> None:
    """Save the full contact list (the old one is replaced)."""
    with Session(engine) as session:
        session.exec(delete(Contact))
        for c in contacts:
            session.add(Contact(name=c["name"], relation=c.get("relation", ""),
                                telegram_chat_id=c.get("telegram_chat_id")))
        session.commit()


def list_zones(engine: Engine) -> list[ZoneRow]:
    with Session(engine) as session:
        return list(session.exec(select(ZoneRow).order_by(ZoneRow.id)))


def replace_zones(engine: Engine, zones: list[dict]) -> None:
    """Save the full zone list (the old one is replaced)."""
    with Session(engine) as session:
        session.exec(delete(ZoneRow))
        for z in zones:
            session.add(ZoneRow(name=z["name"], polygon=[list(p) for p in z["polygon"]]))
        session.commit()
