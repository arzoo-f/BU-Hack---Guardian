# Guardian - BUHack 2.0
Privacy-first fall detection for elderly people living alone.
Room agent (Python) -> server (FastAPI + SQLite) -> dashboard (React).
Full plan: docs/BUILD_PLAN.md. Live status: docs/PROGRESS.md. Approved changes: docs/DECISIONS.md.

## Who is who
- Claude Code writes and tests all code.
- Person A runs Claude Code, does every physical and account step, and approves
  decisions. Not an experienced engineer: plain words, at most 3 steps at a time.
- Person B does the presentation; send files via docs/handoff/.

## Hard rules
- Raw video frames never leave room-agent. Send keypoints and events only.
- All messages follow contracts/*.json. Do not change a contract without asking.
- Escalation hard rules live in server/escalation.py, not in the AI prompt.
  Never weaken them.
- Secrets come from .env. Never hard-code, print or commit keys.
  Never ask for keys in the chat.
- Stop at every HUMAN CHECKPOINT and wait for Person A.
- Telegram goes only to the team test group.

## Run (Windows, natively - not WSL; Python 3.11 lives in .venv)
- server:     cd server; ..\.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
- room-agent: cd room-agent; ..\.venv\Scripts\python.exe main.py --mock   (or --camera 0, --clip FILE)
- dashboard:  cd dashboard; npm run dev -- --host    (port 5173)
- tests:      .venv\Scripts\python.exe -m pytest
- regression: .venv\Scripts\python.exe scripts\sim_scenarios.py   (from Stage 7)
- PowerShell 5.1 has no `&&`: chain commands with `;`.

## Way of working
- Read this file, docs/BUILD_PLAN.md and docs/PROGRESS.md at the start of every session.
- Plan first, then implement one small step, run it, then continue.
- Commit after every tested step; tag finished stages.
- Update docs/PROGRESS.md after every step.

## Style
- Small functions, type hints, docstrings on public functions.
- Thresholds and timings live in config/*.json.
