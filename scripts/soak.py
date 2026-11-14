"""Reliability runs without people (BUILD_PLAN step 7.8). Fake AI, fake Telegram, a throwaway database.

  restart  Server, a room agent replaying a fall clip on a loop, and a dashboard client. The server
           is killed and started again: the room agent and the dashboard client must both be back
           within 10 s of the server.
  soak     The same for --minutes (default 30). Every alert is acknowledged, as the dashboard button
           does. Memory of the server and the room agent is sampled every 30 s; nothing may crash,
           every message must match the contracts, and memory must stay flat.

    .venv\\Scripts\\python.exe scripts\\soak.py restart
    .venv\\Scripts\\python.exe scripts\\soak.py soak --minutes 30

Logs and a JSON summary go to a new folder in the system temp directory (printed at the start).
"""
import argparse
import asyncio
import contextlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT)]

import httpx  # noqa: E402
from websockets.asyncio.client import connect  # noqa: E402
from websockets.exceptions import WebSocketException  # noqa: E402

from contracts import ContractError, validate  # noqa: E402

PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe") if os.name == "nt" else sys.executable
RECONNECT_LIMIT_S = 10
SAMPLE_EVERY_S = 30
WARM_UP_S = 120          # memory before this is start-up, not growth
FLAT_LIMIT_PCT = 15      # last third of the run against the first third (after warm-up)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def memory_mb(pid: int) -> float | None:
    """Working set in MB of a process and its child processes (Windows; no extra package needed).
    The children matter: the .venv's python.exe is a small launcher that runs the real interpreter
    as a child process, so the launcher alone shows only about 4 MB."""
    script = (f"$ids = @({pid}) + @((Get-CimInstance Win32_Process -Filter 'ParentProcessId={pid}').ProcessId); "
              "(Get-Process -Id $ids -ErrorAction SilentlyContinue | Measure-Object WorkingSet64 -Sum).Sum")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True,
                             timeout=30).stdout.strip()
        return round(int(out) / 1048576, 1)
    except Exception:
        return None


class Stack:
    """The server and the room agent as separate processes, like on demo day."""

    def __init__(self, run_dir: Path, clip: Path) -> None:
        self.run_dir = run_dir
        self.clip = clip
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.env = {**os.environ, "GUARDIAN_FAKE_AI": "1", "GUARDIAN_FAKE_TELEGRAM": "1",
                    "GUARDIAN_DB": str(run_dir / "soak.db"), "PYTHONUNBUFFERED": "1"}
        self.server: subprocess.Popen | None = None
        self.room: subprocess.Popen | None = None
        self.server_starts = 0

    def _spawn(self, name: str, args: list[str], cwd: Path) -> subprocess.Popen:
        log = open(self.run_dir / f"{name}.log", "ab")
        return subprocess.Popen([PYTHON, *args], cwd=cwd, env=self.env, stdout=log, stderr=subprocess.STDOUT)

    def start_server(self) -> None:
        self.server_starts += 1
        self.server = self._spawn("server", ["-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port",
                                             str(self.port)], ROOT / "server")

    def start_room(self) -> None:
        self.room = self._spawn("room", [str(ROOT / "room-agent" / "main.py"), "--clip", str(self.clip), "--loop",
                                         "--no-window", "--no-voice", "--server", self.url], ROOT)

    def kill_server(self) -> None:
        self.server.kill()
        self.server.wait(timeout=10)

    def stop(self) -> None:
        for proc in (self.room, self.server):
            if proc and proc.poll() is None:
                proc.kill()
                with contextlib.suppress(Exception):
                    proc.wait(timeout=10)


class DashboardClient:
    """Listens like the dashboard (same 1 s -> 3 s reconnect delays), checks every message against the
    contracts, and presses Acknowledge on every alert."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.ws_url = url.replace("http://", "ws://") + "/ws/dashboard"
        self.connected = False
        self.connects = 0
        self.messages = 0
        self.invalid: list[str] = []
        self.incidents: dict[str, str] = {}
        self.acked: set[str] = set()
        self.ack_failures = 0

    async def run(self) -> None:
        delay = 1.0
        async with httpx.AsyncClient(base_url=self.url, timeout=5) as http:
            while True:
                try:
                    async with connect(self.ws_url, open_timeout=3) as ws:
                        self.connected, delay = True, 1.0
                        self.connects += 1
                        async for text in ws:
                            await self._on_message(json.loads(text), http)
                except (OSError, TimeoutError, WebSocketException):
                    pass
                self.connected = False
                await asyncio.sleep(delay)
                delay = min(delay * 2, 3.0)

    async def _on_message(self, msg: dict, http: httpx.AsyncClient) -> None:
        self.messages += 1
        try:
            validate("dashboard", msg)
        except ContractError as exc:
            self.invalid.append(str(exc)[:200])
        incident, state = msg.get("incident_id"), msg.get("state")
        if not incident or not state:
            return
        self.incidents[incident] = state
        if state == "escalate" and incident not in self.acked:
            self.acked.add(incident)
            with contextlib.suppress(httpx.HTTPError):
                r = await http.post(f"/incidents/{incident}/ack", json={"by": "soak test"})
                if r.status_code not in (200, 409):
                    self.ack_failures += 1


async def status(http: httpx.AsyncClient) -> dict | None:
    try:
        r = await http.get("/status", timeout=2)
        return r.json() if r.status_code == 200 else None
    except httpx.HTTPError:
        return None


async def wait_until(check, limit_s: float, step_s: float = 0.1) -> float | None:
    """Seconds until `check()` (async) is truthy, or None after limit_s."""
    start = time.monotonic()
    while time.monotonic() - start < limit_s:
        if await check():
            return time.monotonic() - start
        await asyncio.sleep(step_s)
    return None


async def bring_up(stack: Stack, client: DashboardClient, http: httpx.AsyncClient) -> bool:
    stack.start_server()
    if await wait_until(lambda: status(http), 30) is None:
        print("The server did not start; see server.log")
        return False
    stack.start_room()

    async def both() -> bool:
        s = await status(http)
        return bool(s and s["room_connected"] and client.connected)
    if await wait_until(both, 60) is None:
        print("The room agent or the dashboard client did not connect; see room.log")
        return False
    return True


async def restart_check(stack: Stack, summary: dict) -> bool:
    client = DashboardClient(stack.url)
    async with httpx.AsyncClient(base_url=stack.url) as http:
        listener = asyncio.create_task(client.run())
        try:
            if not await bring_up(stack, client, http):
                return False
            await asyncio.sleep(10)                   # steady running first
            print("Killing the server...")
            stack.kill_server()
            await asyncio.sleep(3)
            stack.start_server()
            server_up = await wait_until(lambda: status(http), 30)

            async def room_back() -> bool:
                s = await status(http)
                return bool(s and s["room_connected"])

            async def dash_back() -> bool:
                return client.connected

            room_s, dash_s = await asyncio.gather(wait_until(room_back, 30), wait_until(dash_back, 30))
            summary["restart"] = {"server_start_s": server_up, "room_back_after_server_s": room_s,
                                  "dashboard_back_after_server_s": dash_s}
            ok = (server_up is not None and room_s is not None and dash_s is not None
                  and room_s < RECONNECT_LIMIT_S and dash_s < RECONNECT_LIMIT_S)
            fmt = lambda v: "never" if v is None else f"{v:.1f} s"  # noqa: E731
            print(f"Server answering again after {fmt(server_up)}; then room agent back in {fmt(room_s)}, "
                  f"dashboard back in {fmt(dash_s)} (limit {RECONNECT_LIMIT_S} s)")
            await asyncio.sleep(10)                   # and it keeps working afterwards
            s = await status(http)
            alive = stack.room.poll() is None and s is not None and s["room_connected"]
            print(f"10 s later: room agent {'connected' if alive else 'NOT connected'}; "
                  f"{client.messages} dashboard messages, {len(client.invalid)} invalid")
            return ok and alive and not client.invalid
        finally:
            listener.cancel()


async def soak(stack: Stack, minutes: float, summary: dict) -> bool:
    client = DashboardClient(stack.url)
    samples: list[dict] = []
    async with httpx.AsyncClient(base_url=stack.url) as http:
        listener = asyncio.create_task(client.run())
        try:
            if not await bring_up(stack, client, http):
                return False
            start = time.monotonic()
            print(f"Running for {minutes:g} minutes. Every {SAMPLE_EVERY_S} s: memory, incidents, messages.")
            print("  min  server MB  room MB  incidents  acked  messages  invalid  errors")
            while time.monotonic() - start < minutes * 60:
                await asyncio.sleep(SAMPLE_EVERY_S)
                s = await status(http) or {}
                sample = {"t_s": round(time.monotonic() - start), "server_mb": memory_mb(stack.server.pid),
                          "room_mb": memory_mb(stack.room.pid), "incidents": len(client.incidents),
                          "acked": len(client.acked), "messages": client.messages, "invalid": len(client.invalid),
                          "handler_errors": s.get("handler_errors"), "rejected": s.get("rejected_messages"),
                          "room_connected": s.get("room_connected"),
                          "server_alive": stack.server.poll() is None, "room_alive": stack.room.poll() is None}
                samples.append(sample)
                if len(samples) % 10 == 1 or not (sample["server_alive"] and sample["room_alive"]):
                    print(f"  {sample['t_s'] / 60:4.0f}  {sample['server_mb']!s:>9}  {sample['room_mb']!s:>7}  "
                          f"{sample['incidents']:9d}  {sample['acked']:5d}  {sample['messages']:8d}  "
                          f"{sample['invalid']:7d}  {sample['handler_errors']!s:>6}")
                if not (sample["server_alive"] and sample["room_alive"]):
                    print("A process stopped; see the logs.")
                    break
        finally:
            listener.cancel()
    summary["samples"] = samples
    return judge(samples, client, summary)


def judge(samples: list[dict], client: DashboardClient, summary: dict) -> bool:
    if not samples:
        return False
    last = samples[-1]
    alive = all(s["server_alive"] and s["room_alive"] for s in samples)
    steady = [s for s in samples if s["t_s"] >= WARM_UP_S] or samples
    third = max(len(steady) // 3, 1)
    growth = {}
    for key in ("server_mb", "room_mb"):
        first = [s[key] for s in steady[:third] if s[key]]
        final = [s[key] for s in steady[-third:] if s[key]]
        if first and final:
            a, b = sum(first) / len(first), sum(final) / len(final)
            growth[key] = {"first_third_mb": round(a, 1), "last_third_mb": round(b, 1),
                           "growth_pct": round(100 * (b - a) / a, 1)}
    flat = all(g["growth_pct"] < FLAT_LIMIT_PCT for g in growth.values()) and len(growth) == 2
    summary["result"] = {"minutes": round(last["t_s"] / 60, 1), "no_crash": alive, "memory": growth,
                         "memory_flat": flat, "incidents": last["incidents"], "acked": last["acked"],
                         "messages": last["messages"], "invalid": last["invalid"],
                         "handler_errors": last["handler_errors"], "rejected": last["rejected"],
                         "ack_failures": client.ack_failures, "dashboard_connects": client.connects}
    print(json.dumps(summary["result"], indent=2))
    return (alive and flat and last["invalid"] == 0 and not last["handler_errors"] and not last["rejected"]
            and client.ack_failures == 0)


async def amain(args) -> int:
    if not args.clip.exists():
        print(f"Missing clip {args.clip}. The clips stay on the demo laptop (clips/ is not in git).")
        return 2
    run_dir = Path(tempfile.mkdtemp(prefix=f"guardian_{args.mode}_"))
    print(f"Logs: {run_dir}")
    stack = Stack(run_dir, args.clip)
    summary: dict = {"mode": args.mode, "clip": args.clip.name, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        ok = await (restart_check(stack, summary) if args.mode == "restart" else soak(stack, args.minutes, summary))
    finally:
        stack.stop()
    summary["passed"] = ok
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["restart", "soak"])
    p.add_argument("--minutes", type=float, default=30)
    p.add_argument("--clip", type=Path, default=ROOT / "clips" / "tune_fall_forward_01.mp4")
    return asyncio.run(amain(p.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
