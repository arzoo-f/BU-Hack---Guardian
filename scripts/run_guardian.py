"""Start Guardian with one command (BUILD_PLAN step 9.3): the server, the room agent and the
dashboard, in that order, each checked before the next one starts; then the dashboard opens.
A program that stops by itself is started again. Ctrl+C, closing the window or stop.bat stops
all three. Their output goes to logs/ (git-ignored).

    start.bat / start.sh                            real camera, voice, AI and Telegram
    start.bat --no-telegram                         family alerts only in the server log
    start.bat --mock                                scripted person, no camera or voice (rehearse anywhere)
    start.bat --demo                                open the dashboard in demo mode
    stop.bat  (= run_guardian.py --stop)            stop a Guardian started from another window
"""
import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
PID_FILE = LOGS / "guardian.pids"
WINDOWS = os.name == "nt"
PYTHON = str(ROOT / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python"))
SERVER, DASHBOARD = "http://127.0.0.1:8000", "http://127.0.0.1:5173"
MAX_RESTARTS = 5


def say(text: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {text}", flush=True)


def get_json(url: str, timeout: float = 2) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read() or b"{}") if r.status == 200 else None
    except Exception:
        return None


def answers(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def wait_for(check, seconds: float) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if check():
            return True
        time.sleep(0.5)
    return False


def port_busy(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def lan_addresses() -> list[str]:
    """This laptop's addresses a phone on the same Wi-Fi could use (VPN tunnel addresses excluded)."""
    try:
        names = socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        return []
    return [a for a in names if not a.startswith(("127.", "169.254.", "10.2.0."))]


def kill_tree(pid: int) -> None:
    if WINDOWS:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.kill(pid, 15)
        except OSError:
            pass


class Program:
    """One of the three programs: how to start it, and how to tell that it is ready."""

    def __init__(self, name: str, args: list[str], cwd: Path, ready, ready_s: float, env: dict) -> None:
        self.name, self.args, self.cwd, self.ready, self.ready_s, self.env = name, args, cwd, ready, ready_s, env
        self.proc: subprocess.Popen | None = None
        self.restarts = 0
        self.log = LOGS / f"{name.replace(' ', '-')}.log"

    def start(self) -> bool:
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} start: {' '.join(self.args)}\n")
        handle = open(self.log, "ab")
        self.proc = subprocess.Popen(self.args, cwd=self.cwd, env=self.env, stdout=handle, stderr=subprocess.STDOUT)
        if wait_for(lambda: self.ready() or self.proc.poll() is not None, self.ready_s) and self.proc.poll() is None:
            say(f"{self.name}: ready")
            return True
        say(f"{self.name}: NOT ready after {self.ready_s:.0f} s - see {self.log.relative_to(ROOT)}")
        return False

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            kill_tree(self.proc.pid)


def build_programs(args: argparse.Namespace) -> list[Program]:
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    if args.no_telegram:
        env["GUARDIAN_FAKE_TELEGRAM"] = "1"
    camera = os.environ.get("CAMERA_INDEX", "0")
    # --mock: the scripted person never falls by itself (Telegram may be on); start a practice fall
    # with Settings > "Simulate a fall" instead.
    room_args = ["--mock", "--no-voice", "--fall-every", "0"] if args.mock else ["--camera", camera]
    npm = ["cmd", "/c", "npm"] if WINDOWS else ["npm"]
    return [
        Program("server", [PYTHON, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"],
                ROOT / "server", lambda: get_json(f"{SERVER}/status") is not None, 30, env),
        Program("room agent", [PYTHON, "main.py", *room_args, "--server", SERVER], ROOT / "room-agent",
                lambda: bool((get_json(f"{SERVER}/status") or {}).get("room_connected")), 60, env),
        Program("dashboard", [*npm, "run", "preview", "--", "--host", "--port", "5173", "--strictPort"],
                ROOT / "dashboard", lambda: answers(DASHBOARD), 30, env),
    ]


def build_dashboard() -> bool:
    """A production build: the same pages, without the development extras."""
    npm = ["cmd", "/c", "npm"] if WINDOWS else ["npm"]
    with open(LOGS / "dashboard.log", "a", encoding="utf-8") as log:
        log.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} build\n")
        log.flush()
        done = subprocess.run([*npm, "run", "build"], cwd=ROOT / "dashboard", stdout=log, stderr=subprocess.STDOUT)
    return done.returncode == 0


def stop_running() -> int:
    """stop.bat: stop the programs a run_guardian.py in another window started."""
    if not PID_FILE.exists():
        say("Guardian does not seem to be running (no logs/guardian.pids).")
        return 0
    for pid in PID_FILE.read_text().split():
        kill_tree(int(pid))
    PID_FILE.unlink(missing_ok=True)
    say("Guardian stopped.")
    return 0


def write_pids(programs: list[Program]) -> None:
    """This launcher first (stopping it stops the restarts), then the three programs."""
    pids = [os.getpid(), *(p.proc.pid for p in programs if p.proc)]
    PID_FILE.write_text(" ".join(map(str, pids)) + "\n")


def run(args: argparse.Namespace) -> int:
    LOGS.mkdir(exist_ok=True)
    if not WINDOWS:   # stop / kill: stop the three programs too (on Windows taskkill /T does it)
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    busy = [port for port in (8000, 5173) if port_busy(port)]
    if busy:
        say(f"Port {' and '.join(map(str, busy))} already in use: Guardian may be running already. "
            f"Run stop.bat first (or close the other Guardian window).")
        return 1
    programs = build_programs(args)
    say("Building the dashboard...")
    if not build_dashboard():
        say("The dashboard did not build - see logs/dashboard.log")
        return 1
    try:
        for program in programs:
            say(f"Starting the {program.name}...")
            if not program.start():
                return 1
            write_pids(programs)
        say("Guardian is running" + (" (MOCK: scripted person, no camera or voice)" if args.mock else "")
            + (" - family alerts go to the log only" if args.no_telegram else "") + ".")
        say("Dashboard: http://localhost:5173" + "".join(f"   phone: http://{a}:5173" for a in lan_addresses()))
        say("Press Ctrl+C or close this window to stop Guardian.")
        if not args.no_browser:
            webbrowser.open("http://localhost:5173/" + ("?demo=1" if args.demo else ""))
        while True:
            time.sleep(1)
            for program in programs:
                if program.proc.poll() is not None:
                    if program.restarts >= MAX_RESTARTS:
                        say(f"The {program.name} keeps stopping - see {program.log.relative_to(ROOT)}. Giving up.")
                        return 1
                    program.restarts += 1
                    say(f"The {program.name} stopped (exit code {program.proc.returncode}); starting it again "
                        f"({program.restarts}/{MAX_RESTARTS})...")
                    program.start()
                    write_pids(programs)
    except KeyboardInterrupt:
        say("Stopping Guardian...")
        return 0
    finally:
        for program in reversed(programs):
            program.stop()
        PID_FILE.unlink(missing_ok=True)
        say("Stopped.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mock", action="store_true", help="scripted person: no camera, microphone or speaker")
    p.add_argument("--no-telegram", action="store_true", help="family alerts go to the server log only")
    p.add_argument("--demo", action="store_true", help="open the dashboard in demo mode")
    p.add_argument("--no-browser", action="store_true", help="do not open the dashboard")
    p.add_argument("--stop", action="store_true", help="stop a Guardian started from another window")
    args = p.parse_args(argv)
    return stop_running() if args.stop else run(args)


if __name__ == "__main__":
    sys.exit(main())
