"""Pre-demo check: the parts that need no network, camera or running Guardian."""
from datetime import date, datetime, timedelta, timezone

import db
import preflight
import seed_history


def test_secrets_are_checked_but_never_shown():
    secret = "placeholder-value-for-the-preflight-test"
    ok = preflight.check_env({"OPENAI_API_KEY": secret, "TELEGRAM_BOT_TOKEN": "123:abc", "TELEGRAM_CHAT_ID": "-1"})
    assert ok[0] == preflight.OK and secret not in ok[1]
    missing = preflight.check_env({"OPENAI_API_KEY": secret, "TELEGRAM_BOT_TOKEN": " ", "TELEGRAM_CHAT_ID": "-1"})
    assert missing[0] == preflight.FAIL and "TELEGRAM_BOT_TOKEN" in missing[1] and secret not in missing[1]
    assert preflight.check_env({})[0] == preflight.FAIL


def test_database_open_incident_and_simulated_history(tmp_path):
    path = tmp_path / "demo.db"
    assert preflight.check_database(path)[0][0] == preflight.WARN          # no database yet
    engine = db.make_engine(path)
    seed_history.seed(engine, today=datetime.now(timezone(timedelta(hours=8))).date())
    db.add(engine, db.Incident(id="inc_1", started_at=datetime.now(timezone.utc), reason="fast_fall",
                               state="escalate"))
    engine.dispose()
    (incidents, history) = preflight.check_database(path)
    assert incidents[0] == preflight.FAIL and "reset_demo" in incidents[1]
    assert history[0] == preflight.OK


def test_old_history_is_flagged(tmp_path):
    engine = db.make_engine(tmp_path / "old.db")
    seed_history.seed(engine, today=date(2026, 1, 1))
    engine.dispose()
    assert preflight.check_database(tmp_path / "old.db")[1][0] == preflight.WARN


def test_not_running_is_a_warning_not_a_failure(monkeypatch):
    monkeypatch.setattr(preflight, "SERVER", "http://127.0.0.1:9")
    assert preflight.check_running() == [(preflight.WARN, preflight.check_running()[0][1])]
    assert "start.bat" in preflight.check_running()[0][1]
