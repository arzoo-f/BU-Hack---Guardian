"""Family notifications (BUILD_PLAN step 4.4).

TelegramNotifier - alerts in the family test group: a skeleton picture (drawn from keypoints, never
                   a camera image), a caption and an Acknowledge button; reminders until someone
                   acknowledges; gentle messages for requests; button presses come back by long
                   polling, and acknowledging anywhere edits the alert messages.
LogNotifier      - writes the same notifications to the server log (tests, mock work, no token).

Messages go only to TELEGRAM_CHAT_ID, the team's test group. The bot token is part of every API
address, so errors are re-raised without the address: the token never reaches a log.
"""
import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

import httpx

from snapshot import skeleton_png

log = logging.getLogger("guardian.notify")

SEND_TIMEOUT_S = 5.0     # the engine gives a notifier call 6 s in total
POLL_TIMEOUT_S = 25      # Telegram long polling
ACK_PREFIX = "ack:"


class TelegramError(Exception):
    """A Telegram call failed. The message never contains the bot token."""


def local_time(iso: str, utc_offset_hours: float) -> str:
    """'2026-11-14T02:07:10+00:00' -> 'Sat 10:07' in the room's time zone."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=utc_offset_hours)))
    return dt.strftime("%a %H:%M")


def alert_caption(incident: dict, attempt: int, utc_offset_hours: float) -> str:
    """The text under the skeleton picture."""
    lines = []
    if attempt > 1:
        lines.append(f"🔔 Reminder {attempt - 1}: nobody has acknowledged yet")
    test = "[TEST] " if incident.get("simulated") else ""
    what = "found on the floor" if incident["reason"] == "found_on_floor" else "possible fall"
    lines.append(f"🚨 {test}Guardian alert: {what}")
    lines.append(f"Room: {incident['room'].replace('_', ' ')} · {local_time(incident['started_at'], utc_offset_hours)}")
    heard = incident.get("transcript") or ""
    lines.append(f'Heard: "{heard}"' if heard else "Heard: no answer")
    if incident.get("ai_reason"):
        lines.append(f"Why: {incident['ai_reason']}")
    lines.append("Tap Acknowledge when someone is on the way.")
    return "\n".join(lines)


class LogNotifier:
    """Stands in for Telegram: every notification becomes a log line."""

    channel = "log"

    async def alert(self, incident: dict, attempt: int) -> None:
        log.warning("ALERT #%d to family: %s in %s, %s. Heard: %r. Why: %s", attempt, incident["reason"],
                    incident["room"], incident["started_at"], incident["transcript"], incident["ai_reason"])

    async def gentle(self, incident: dict, request: str) -> None:
        log.info("gentle message to family: they asked for %r", request)

    async def acknowledged(self, incident: dict, by: str) -> None:
        log.info("incident %s acknowledged by %s", incident["incident_id"], by)

    async def camera_offline(self, room: str, since: datetime) -> None:
        log.warning("message to family: Guardian cannot see the %s since %s", room, since.isoformat())

    async def camera_back(self, room: str) -> None:
        log.info("message to family: Guardian can see the %s again", room)


class TelegramNotifier:
    """Alerts, reminders and gentle messages in one Telegram group, with an Acknowledge button."""

    channel = "telegram"

    def __init__(self, token: str, chat_id: str, keypoints: Callable[[], list | None],
                 utc_offset_hours: float = 8, client: httpx.AsyncClient | None = None) -> None:
        self._base = f"https://api.telegram.org/bot{token}"
        self.chat_id = int(chat_id)
        self.keypoints = keypoints                      # latest pose, for the picture
        self.utc_offset = utc_offset_hours
        self.client = client or httpx.AsyncClient(timeout=SEND_TIMEOUT_S)
        self.on_ack: Callable[[str, str], Awaitable[bool]] | None = None   # set to engine.acknowledge
        self._alerts: dict[str, list[tuple[int, str]]] = {}               # incident -> [(message id, caption)]
        self._offset: int | None = None

    # -- Bot API --------------------------------------------------------------------------------

    async def _call(self, method: str, http_timeout: float = SEND_TIMEOUT_S, files: dict | None = None,
                    **params) -> dict:
        """One Bot API call; `params` are Telegram's own (getUpdates has its own `timeout`)."""
        try:
            if files:
                data = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in params.items()}
                response = await self.client.post(f"{self._base}/{method}", data=data, files=files,
                                                  timeout=http_timeout)
            else:
                response = await self.client.post(f"{self._base}/{method}", json=params, timeout=http_timeout)
            body = response.json()
        except Exception as exc:  # the exception text may contain the address, and so the token
            raise TelegramError(f"{method}: {type(exc).__name__}") from None
        if not body.get("ok"):
            raise TelegramError(f"{method}: {body.get('error_code')} {body.get('description')}")
        return body["result"]

    # -- the Notifier interface used by the escalation engine ------------------------------------

    async def alert(self, incident: dict, attempt: int) -> None:
        caption = alert_caption(incident, attempt, self.utc_offset)
        when = local_time(incident["started_at"], self.utc_offset)
        picture = skeleton_png(self.keypoints(), caption=f"{incident['room'].replace('_', ' ')} · {when}")
        button = {"inline_keyboard": [[{"text": "✅ Acknowledge",
                                        "callback_data": ACK_PREFIX + incident["incident_id"]}]]}
        message = await self._call("sendPhoto", chat_id=self.chat_id, caption=caption, reply_markup=button,
                                   files={"photo": ("guardian.png", picture, "image/png")})
        self._alerts.setdefault(incident["incident_id"], []).append((message["message_id"], caption))
        log.warning("Telegram alert #%d sent for %s", attempt, incident["incident_id"])

    async def gentle(self, incident: dict, request: str) -> None:
        test = "[TEST] " if incident.get("simulated") else ""
        text = (f"ℹ️ {test}Not urgent: after a small fall in the {incident['room'].replace('_', ' ')}, "
                f'they asked for: "{request}". They are okay.')
        await self._call("sendMessage", chat_id=self.chat_id, text=text)

    async def camera_offline(self, room: str, since: datetime) -> None:
        """Guardian has not been able to see the room for a while (camera_watch.py)."""
        local = since.astimezone(timezone(timedelta(hours=self.utc_offset))).strftime("%H:%M")
        text = (f"⚠️ Guardian cannot see the {room.replace('_', ' ')} since {local}: the camera is offline "
                f"or the laptop program stopped. Nobody is known to be hurt, but falls cannot be noticed "
                f"until it is back. Please check the laptop.")
        await self._call("sendMessage", chat_id=self.chat_id, text=text)

    async def camera_back(self, room: str) -> None:
        await self._call("sendMessage", chat_id=self.chat_id,
                         text=f"✅ Guardian can see the {room.replace('_', ' ')} again.")

    async def acknowledged(self, incident: dict, by: str) -> None:
        """Mark every alert of the incident as acknowledged and remove its button."""
        stamp = datetime.now(timezone(timedelta(hours=self.utc_offset))).strftime("%H:%M")
        for message_id, caption in self._alerts.pop(incident["incident_id"], []):
            try:
                await self._call("editMessageCaption", chat_id=self.chat_id, message_id=message_id,
                                 caption=f"{caption}\n\n✅ Acknowledged by {by} at {stamp}",
                                 reply_markup={"inline_keyboard": []})
            except TelegramError as exc:
                log.warning("could not edit alert message: %s", exc)

    # -- button presses ---------------------------------------------------------------------------

    async def poll_once(self) -> int:
        """One long-poll round; handles Acknowledge presses from the family group. Returns updates seen."""
        params = {"timeout": POLL_TIMEOUT_S, "allowed_updates": ["callback_query"]}
        if self._offset is not None:
            params["offset"] = self._offset
        updates = await self._call("getUpdates", http_timeout=POLL_TIMEOUT_S + 10, **params)
        for update in updates:
            self._offset = update["update_id"] + 1
            press = update.get("callback_query")
            if press:
                await self._handle_press(press)
        return len(updates)

    async def poll_forever(self) -> None:
        """Runs beside the server. A failure waits a few seconds and tries again; an empty answer that
        comes back at once (Telegram normally waits up to 25 s) waits 1 s, so polling never spins."""
        loop = asyncio.get_running_loop()
        while True:
            started = loop.time()
            try:
                if await self.poll_once() == 0 and loop.time() - started < 1.0:
                    await asyncio.sleep(1.0)
                else:
                    await asyncio.sleep(0)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.warning("Telegram polling problem (%s); retrying in 3 s", exc)
                await asyncio.sleep(3)

    async def _handle_press(self, press: dict) -> None:
        chat = (press.get("message") or {}).get("chat", {}).get("id")
        data = press.get("data") or ""
        if chat != self.chat_id or not data.startswith(ACK_PREFIX):
            log.warning("ignored a button press from another chat or with unknown data")
            await self._answer(press["id"], "This button is not for this chat.")
            return
        who = press.get("from", {})
        name = " ".join(p for p in (who.get("first_name"), who.get("last_name")) if p) or "family"
        incident_id = data[len(ACK_PREFIX):]
        handled = await self.on_ack(incident_id, f"Telegram: {name}") if self.on_ack else False
        await self._answer(press["id"], f"Thank you, {who.get('first_name') or name}. Marked as acknowledged."
                           if handled else "Already handled - thank you.")

    async def _answer(self, press_id: str, text: str) -> None:
        try:
            await self._call("answerCallbackQuery", callback_query_id=press_id, text=text)
        except TelegramError as exc:
            log.warning("could not answer the button press: %s", exc)


def make_notifier(keypoints: Callable[[], list | None], utc_offset_hours: float = 8):
    """Telegram when a token and chat ID are configured, otherwise the log.
    GUARDIAN_FAKE_TELEGRAM=1 forces the log (tests, mock-only work)."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", "")
    if os.environ.get("GUARDIAN_FAKE_TELEGRAM") == "1" or not token or not chat:
        log.warning("family alerts go to the LOG only (no Telegram)")
        return LogNotifier()
    log.info("family alerts go to the Telegram test group")
    return TelegramNotifier(token, chat, keypoints, utc_offset_hours)
