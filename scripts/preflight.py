"""Pre-demo check (BUILD_PLAN step 9.3 and Appendix C): a green / red list before every rehearsal,
recording and the live demo. Keys are only checked for being present: their values are never shown.

    .venv\\Scripts\\python.exe scripts\\preflight.py               files, keys, OpenAI, Telegram, and the
                                                                   running Guardian (start.bat first)
    .venv\\Scripts\\python.exe scripts\\preflight.py --hardware    also listen to the microphone for 1 s
                                                                   (in memory only) to catch a muted mic
    .venv\\Scripts\\python.exe scripts\\preflight.py --offline     no OpenAI or Telegram calls

Exit code 0 when nothing is red. Nothing is sent to Telegram: it only asks who the bot is and
whether it can see the family group.
"""
import argparse
import json
import os
import sys
import urllib.request
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "server"), str(ROOT / "room-agent"), str(ROOT)]

from dotenv import dotenv_values  # noqa: E402

OK, WARN, FAIL = "OK", "WARN", "FAIL"
SERVER, DASHBOARD = "http://127.0.0.1:8000", "http://127.0.0.1:5173"
SECRETS = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
REMINDERS = [  # Appendix C - the things a script cannot see
    "Laptop on power; sleep, screen saver and notifications off.",
    "Windows microphone Input volume at 100; speaker loud enough to hear from the mat.",
    "Room lit, mat in place; camera angle and the sofa zone checked on the Live page.",
    "Telegram open on Person B's phone (the family test group).",
    "Demo mode on in the dashboard (button at the top right).",
    "Phone hotspot ready; ProtonVPN off if a phone must open the dashboard.",
]

Result = tuple[str, str]


def get_json(url: str, timeout: float = 3) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except Exception:
        return None


# -- files and settings ----------------------------------------------------------------------------

def check_env(env: dict) -> Result:
    """The secrets are filled in (never printed)."""
    missing = [k for k in SECRETS if not (env.get(k) or "").strip()]
    if not env:
        return FAIL, ".env not found: copy .env.example to .env and fill it in"
    if missing:
        return FAIL, f".env is missing a value for: {', '.join(missing)}"
    return OK, ".env has the OpenAI key, the Telegram token and the chat ID (values not shown)"


def check_model() -> Result:
    from settings import load_vision_config, model_path

    path = model_path(load_vision_config())
    return (OK, f"pose model {path.name} present") if path.exists() else (FAIL, f"pose model missing: {path}")


def check_phrases(env: dict) -> Result:
    """Every fixed check-in phrase is ready as a sound file (no waiting for the network)."""
    from voice.tts import Speaker

    voice_cfg = json.loads((ROOT / "config" / "voice.json").read_text(encoding="utf-8"))
    phrases = json.loads((ROOT / "config" / "escalation.json").read_text(encoding="utf-8"))["phrases"]
    speaker = Speaker(env.get("OPENAI_TTS_MODEL") or "gpt-4o-mini-tts", env.get("OPENAI_TTS_VOICE") or "coral",
                      voice_cfg, ROOT / voice_cfg["phrases_dir"])
    missing = [name for name, text in phrases.items() if not speaker.cache_path(text).exists()]
    if missing:
        return WARN, f"phrases not prepared yet: {', '.join(missing)} (the room agent makes them at start)"
    return OK, f"all {len(phrases)} check-in phrases ready as sound files"


def check_zones() -> Result:
    data = json.loads((ROOT / "config" / "zones.json").read_text(encoding="utf-8"))
    names = [z["name"] for z in data.get("zones", [])]
    if not names:
        return WARN, "no safe zone: lying on the sofa would count as lying on the floor"
    return OK, f"safe zone(s): {', '.join(names)} - {data.get('note', '')[:60]}"


def check_dashboard_installed() -> Result:
    if (ROOT / "dashboard" / "node_modules").exists():
        return OK, "dashboard packages installed"
    return FAIL, "dashboard packages missing: run  npm install  in the dashboard folder"


def check_database(db_path: Path) -> list[Result]:
    """No incident left open; the simulated week is there for the Insights page."""
    import db

    if not db_path.exists():
        return [(WARN, f"no database yet ({db_path.name}): run scripts\\reset_demo.py --yes")]
    engine = db.make_engine(db_path)
    try:
        open_ones = db.unfinished_incidents(engine)
        now = datetime.now(timezone.utc)
        rows = db.activity_between(engine, now - timedelta(days=8), now)
    finally:
        engine.dispose()
    offset = json.loads((ROOT / "config" / "analytics.json").read_text(encoding="utf-8"))["utc_offset_hours"]
    days = {(db.to_utc(r.ts) + timedelta(hours=offset)).date() for r in rows if r.simulated}   # local days
    results = [(FAIL, f"{len(open_ones)} incident(s) still open: run scripts\\reset_demo.py --yes")
               if open_ones else (OK, "no incident left open")]
    results.append((OK, f"simulated history on {len(days)} days (Insights page)") if len(days) >= 6
                   else (WARN, "simulated history missing or old: run scripts\\reset_demo.py --yes"))
    return results


# -- online services (nothing is sent) ---------------------------------------------------------------

def check_openai(env: dict) -> Result:
    from openai import OpenAI

    model = env.get("OPENAI_MODEL") or "gpt-5.4-mini"
    try:
        OpenAI(api_key=env.get("OPENAI_API_KEY"), timeout=8, max_retries=0).models.retrieve(model)
        return OK, f"OpenAI answers and knows {model}"
    except Exception as exc:
        return FAIL, f"OpenAI not reachable or key refused ({type(exc).__name__})"


def check_telegram(env: dict) -> Result:
    import httpx

    base = f"https://api.telegram.org/bot{env.get('TELEGRAM_BOT_TOKEN', '')}"
    try:
        me = httpx.get(f"{base}/getMe", timeout=8).json()
        chat = httpx.get(f"{base}/getChat", params={"chat_id": env.get("TELEGRAM_CHAT_ID")}, timeout=8).json()
    except Exception as exc:     # never echo the URL: it contains the token
        return FAIL, f"Telegram not reachable ({type(exc).__name__})"
    if not me.get("ok"):
        return FAIL, "Telegram refused the bot token"
    if not chat.get("ok"):
        return FAIL, "the bot cannot see the family group (chat ID wrong, or the bot was removed)"
    return OK, f"Telegram: bot @{me['result'].get('username')} can post to \"{chat['result'].get('title')}\""


# -- the running Guardian ------------------------------------------------------------------------------

def check_running() -> list[Result]:
    status = get_json(f"{SERVER}/status")
    if status is None:
        return [(WARN, "Guardian is not running: start it with start.bat, then run this check again")]
    settings = get_json(f"{SERVER}/settings") or {}
    alerts = settings.get("alerts", {})
    fps = status.get("fps") or 0
    results = [
        (OK, "server answers"),
        (OK, "room agent connected") if status.get("room_connected") else (FAIL, "room agent not connected"),
        (OK, f"camera on, {fps:.0f} FPS") if status.get("camera") == "ok" and fps >= 10
        else (FAIL, f"camera {status.get('camera') or 'offline'} ({fps:.0f} FPS)"),
        (OK, "family alerts go to Telegram") if alerts.get("telegram")
        else (WARN, "Telegram is OFF: alerts only go to the log (started with --no-telegram?)"),
        (OK, "check-in decisions by the AI") if alerts.get("ai") == "OpenAIAgent"
        else (WARN, "check-in decisions by the TEST AI, not OpenAI"),
        (OK, "no incident open right now") if status.get("state") == "monitoring"
        else (WARN, f"an incident is open right now ({status.get('state')})"),
    ]
    try:
        with urllib.request.urlopen(DASHBOARD, timeout=3) as r:
            results.append((OK, "dashboard answers on port 5173") if r.status == 200 else (FAIL, "dashboard error"))
    except Exception:
        results.append((FAIL, "dashboard not reachable on port 5173"))
    return results


# -- hardware (only with --hardware) ---------------------------------------------------------------

def check_microphone() -> Result:
    """1 s from the default microphone, kept in memory only: digital silence means it is muted."""
    from voice.audio import SoundDevice, dbfs

    try:
        device = SoundDevice()
        level = dbfs(device.record(1.0, device.input_rate()))
    except Exception as exc:
        return FAIL, f"microphone not available ({type(exc).__name__})"
    if level < -100:
        return FAIL, "the microphone hears nothing at all: it is muted (Windows sound settings)"
    return OK, f"microphone works (room level {level:.0f} dBFS)"


# -- report ----------------------------------------------------------------------------------------

def run_checks(args: argparse.Namespace) -> list[Result]:
    env = dotenv_values(ROOT / ".env") if (ROOT / ".env").exists() else {}
    checks: list[Callable[[], Result | list[Result]]] = [
        lambda: check_env(env), check_model, lambda: check_phrases(env), check_zones, check_dashboard_installed,
        lambda: check_database(Path(os.environ.get("GUARDIAN_DB") or ROOT / "server" / "guardian.db")),
    ]
    if not args.offline and env:
        checks += [lambda: check_openai(env), lambda: check_telegram(env)]
    checks.append(check_running)
    if args.hardware:
        checks.append(check_microphone)
    results: list[Result] = []
    for check in checks:
        try:
            out = check()
        except Exception as exc:
            out = (FAIL, f"check failed: {type(exc).__name__}: {exc}")
        results += out if isinstance(out, list) else [out]
    return results


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--hardware", action="store_true", help="also check the microphone (1 s, kept in memory)")
    p.add_argument("--offline", action="store_true", help="skip the OpenAI and Telegram checks")
    args = p.parse_args(argv)
    if os.name == "nt":
        os.system("")                                  # lets the Windows console show colours
    colour = {OK: "\033[32m", WARN: "\033[33m", FAIL: "\033[31m"}
    results = run_checks(args)
    print("Guardian pre-demo check\n")
    for level, text in results:
        print(f"  {colour[level]}{level:4s}\033[0m  {text}")
    print("\nAlso check by hand:")
    for line in REMINDERS:
        print(f"  [ ] {line}")
    fails, warns = sum(r[0] == FAIL for r in results), sum(r[0] == WARN for r in results)
    print(f"\n{'ALL GREEN' if not fails and not warns else f'{fails} red, {warns} yellow'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
