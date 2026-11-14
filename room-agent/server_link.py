"""WebSocket link from the room agent to the server, with automatic reconnection.

Every outgoing message is checked against contracts/room, every incoming command against
contracts/command. While disconnected, live data (pose, activity, status) is dropped, but
incident messages are kept and sent after reconnecting.
"""
import asyncio
import json
import logging
from collections import deque
from collections.abc import Awaitable, Callable

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, WebSocketException

from contracts import ContractError, validate

log = logging.getLogger("guardian.room.link")

KEEP_WHILE_OFFLINE = {"fall_detected", "posture_update", "voice_reply"}
MAX_BACKOFF_S = 3.0  # plan: reconnect within 10 s of a server restart


def ws_url(server_url: str) -> str:
    """http://host:8000 -> ws://host:8000/ws/room"""
    base = server_url.rstrip("/").replace("https://", "wss://").replace("http://", "ws://")
    return base + "/ws/room"


class ServerLink:
    """Keeps one WebSocket open to the server and passes commands to `on_command`."""

    def __init__(self, url: str, on_command: Callable[[dict], Awaitable[None]] | None = None) -> None:
        self.url = url
        self.on_command = on_command
        self._ws = None
        self._pending: deque[dict] = deque(maxlen=50)
        self._tasks: set[asyncio.Task] = set()
        self._warned = False  # say "no connection" once per outage, not every retry

    @property
    def connected(self) -> bool:
        return self._ws is not None

    async def send(self, message: dict) -> None:
        """Validate and send one message (or keep it for later if it matters and we are offline)."""
        validate("room", message)
        ws = self._ws
        if ws is not None:
            try:
                await ws.send(json.dumps(message))
                return
            except ConnectionClosed:
                self._ws = None
        if message["type"] in KEEP_WHILE_OFFLINE:
            self._pending.append(message)

    async def run_forever(self) -> None:
        """Connect, flush kept messages, receive commands; reconnect after any drop."""
        delay = 1.0
        while True:
            try:
                async with connect(self.url, open_timeout=3) as ws:
                    self._ws = ws
                    delay = 1.0
                    self._warned = False
                    log.info("connected to %s", self.url)
                    while self._pending:
                        await ws.send(json.dumps(self._pending.popleft()))
                    async for text in ws:
                        self._dispatch(text)
            except (OSError, TimeoutError, WebSocketException) as exc:
                if not self._warned:
                    log.warning("no connection to the server (%s); retrying every few seconds",
                                type(exc).__name__)
                    self._warned = True
            finally:
                if self._ws is not None:
                    log.info("disconnected")
                self._ws = None
            await asyncio.sleep(delay)
            delay = min(delay * 2, MAX_BACKOFF_S)

    def _dispatch(self, text: str | bytes) -> None:
        """Validate a command and handle it in its own task, so listening never blocks receiving."""
        try:
            command = validate("command", json.loads(text))
        except (json.JSONDecodeError, ContractError) as exc:
            log.warning("ignored bad command: %s", exc)
            return
        if self.on_command is None:
            return
        task = asyncio.create_task(self.on_command(command))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
