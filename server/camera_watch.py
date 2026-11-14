"""Camera-offline alert (BUILD_PLAN Section 18, SHOULD; config/escalation.json camera_offline_alert_s).

If Guardian cannot see the room for camera_offline_alert_s - the room agent reports the camera
offline, or the room agent is not connected at all - the family gets one message, and another when
the camera is back. This is not an incident: nobody is known to be hurt, so there is no check-in
and nothing to acknowledge. The five hard rules are untouched.
"""
import logging
from datetime import datetime

log = logging.getLogger("guardian.camera_watch")


class CameraWatch:
    """Tracks whether Guardian can see the room; tick() sends the messages when due."""

    def __init__(self, notifier, clock, alert_after_s: float, retry_s: float, room: str) -> None:
        self.notifier = notifier
        self.clock = clock
        self.alert_after_s = alert_after_s
        self.retry_s = retry_s
        self.room = room
        self.blind_since: float | None = None
        self.blind_since_utc: datetime | None = None
        self._heard = False          # until the room reports, the first tick counts as "cannot see"
        self.alerted = False
        self.back_pending = False
        self._next_try = 0.0

    def update(self, seeing: bool) -> None:
        """Camera ok (True), or camera offline / room agent gone (False)."""
        self._heard = True
        if seeing:
            if self.blind_since is not None:
                self.back_pending = self.alerted
                log.info("camera back after %.0f s", self.clock.monotonic() - self.blind_since)
            self.blind_since, self.blind_since_utc, self.alerted = None, None, False
        elif self.blind_since is None:
            self.blind_since, self.blind_since_utc = self.clock.monotonic(), self.clock.now()
            log.warning("Guardian cannot see the room (camera offline or room agent gone)")

    async def tick(self) -> None:
        """Send the offline message once it is due, or the 'back' message; retry failures."""
        if not self._heard:          # start-up with no room agent yet: start counting now
            self.update(False)
        now = self.clock.monotonic()
        if now < self._next_try:
            return
        if self.back_pending:
            if await self._send("camera_back", self.room):
                self.back_pending = False
        elif (self.blind_since is not None and not self.alerted
              and now - self.blind_since >= self.alert_after_s):
            if await self._send("camera_offline", self.room, self.blind_since_utc):
                self.alerted = True
                log.warning("family told: camera offline since %s", self.blind_since_utc.isoformat())

    async def _send(self, method: str, *args) -> bool:
        send = getattr(self.notifier, method, None)
        if send is None:            # a notifier without these messages (tests, simulators)
            return True
        try:
            await send(*args)
            return True
        except Exception as exc:
            log.error("%s message failed (%s); retrying in %.0f s", method, type(exc).__name__, self.retry_s)
            self._next_try = self.clock.monotonic() + self.retry_s
            return False
