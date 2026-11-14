# server

FastAPI server: receives events from the room agent, stores them in SQLite, runs the escalation
flow (check-ins, AI decisions, the five hard rules) and pushes live updates to dashboards.

Run (from this folder):

```
..\.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Set `GUARDIAN_FAKE_AI=1` to use the word-rule fake instead of OpenAI, and `GUARDIAN_FAKE_TELEGRAM=1`
to write family alerts to the log instead of Telegram (mock-only work; the tests set both).
With `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`, alerts go to the family test group as a
skeleton picture with an Acknowledge button; button presses come back by long polling.

| Endpoint | Purpose |
| --- | --- |
| `WS /ws/room` | room agent <-> server (contracts/room, contracts/command) |
| `WS /ws/dashboard` | server -> dashboards (contracts/dashboard) |
| `GET /status` | current activity, camera, open incident and state, connection counts |
| `GET /incidents`, `GET /incidents/{id}` | incident list; one incident with every step |
| `POST /incidents/{id}/ack` | acknowledge from the dashboard (body `{"by": "..."}`, optional) |
| `GET /activity?from=&to=` | activity log (ISO times; default the last 24 h) |
| `GET/POST /zones`, `GET/POST /contacts` | safe zones and contacts |
| `POST /simulate/fall` | start a simulated incident (testing and rehearsals) |

| File | Purpose |
| --- | --- |
| `app.py` | API, live connections, wiring of the engine to the database, room and dashboards |
| `escalation.py` | the check-in flow and the five hard rules (Section 14) |
| `agent.py` | AI decisions: `OpenAIAgent` (strict JSON schema) and `FakeAgent` |
| `notify.py` | family notifications: Telegram (alerts, reminders, Acknowledge, gentle messages) or log |
| `snapshot.py` | skeleton picture for the alert, drawn from keypoints only |
| `analytics.py` | daily mobility figures and insight sentences |
| `db.py` | SQLite tables and queries |

The database file `guardian.db` is created here and is git-ignored.

**Restarting during an incident:** on start-up the newest unfinished real incident is re-opened as
an alert and re-alerts until acknowledged (D-010); other unfinished incidents are closed with a
note. While developing, acknowledge open incidents before restarting, or expect an alert.
