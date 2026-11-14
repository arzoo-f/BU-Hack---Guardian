"""The voices the room agent can use. All offer speak(text) and ask(text, seconds) -> reply dict.

LiveVoice   - the real speaker and microphone (camera mode)
SilentVoice - --no-voice: says nothing, hears nothing (every question goes unanswered)
"""
import asyncio
import contextlib
import logging
import threading
import time

log = logging.getLogger("guardian.room.voice")


class LiveVoice:
    """Speaker + Listener, one question at a time, with the space bar as an "I'm okay" button."""

    def __init__(self, speaker, listener, config: dict, clock=time.monotonic) -> None:
        self.speaker = speaker
        self.listener = listener
        self.after_playback = config["listen_after_playback_s"]
        self.reuse_noise_for = config["reuse_noise_for_s"]
        self.space = threading.Event()
        self._lock = asyncio.Lock()
        self._clock = clock
        self._noise: tuple[float, float] | None = None    # (dBFS, when measured)

    def space_pressed(self) -> None:
        """Called from the vision thread when Space is pressed in the debug window."""
        self.space.set()

    async def speak(self, text: str) -> None:
        async with self._lock:
            await self._say(text)

    async def ask(self, text: str, listen_seconds: float) -> dict:
        """Measure the room, say the question, then listen right after it ends (people answer at once).
        The microphone stays on for the whole question, so listening starts without a gap."""
        async with self._lock:
            try:
                mic = await asyncio.to_thread(self.listener.open_mic)
            except Exception as exc:
                log.error("microphone not available (%s)", type(exc).__name__)
                await self._say(text)
                return {"transcript": "", "heard_speech": False}
            try:
                return await self._ask_with(mic, text, listen_seconds)
            finally:
                with contextlib.suppress(Exception):
                    await asyncio.to_thread(mic.close)

    async def _room_noise(self, mic) -> float:
        """The room's loudness: measured again only if the last measurement is older than
        reuse_noise_for_s, so the second question of an incident starts about 0.5 s sooner."""
        now = self._clock()
        if self._noise is None or now - self._noise[1] > self.reuse_noise_for:
            self._noise = (await asyncio.to_thread(self.listener.measure_noise, mic), now)
        return self._noise[0]

    async def _ask_with(self, mic, text: str, listen_seconds: float) -> dict:
        try:
            noise = await self._room_noise(mic)
        except Exception as exc:
            log.error("microphone not available (%s)", type(exc).__name__)
            await self._say(text)
            return {"transcript": "", "heard_speech": False}
        self.space.clear()          # only a press during this question counts
        await self._say(text)
        await asyncio.sleep(self.after_playback)
        try:
            reply = await self.listener.listen(listen_seconds, noise, self.space, mic)
        except Exception as exc:
            log.error("recording failed (%s)", type(exc).__name__)
            reply = {"transcript": "", "heard_speech": False}
        log.info("heard: %r (speech: %s, loudest %s dBFS, room %s dBFS)", reply["transcript"], reply["heard_speech"],
                 reply.get("loudest_dbfs", "-"), reply.get("noise_dbfs", "-"))
        return reply

    async def _say(self, text: str) -> None:
        try:
            source = await self.speaker.speak(text)
            log.info("said (%s): %s", source, text)
        except Exception as exc:  # no speaker: still listen, the person may answer anyway
            log.error("could not speak (%s): %s", type(exc).__name__, text)


class SilentVoice:
    """--no-voice: nothing is said or heard, so every question goes unanswered (and escalates)."""

    def __init__(self, sleep=asyncio.sleep) -> None:
        self._sleep = sleep

    def space_pressed(self) -> None:
        pass

    async def speak(self, text: str) -> None:
        log.info("(no voice) would say: %s", text)

    async def ask(self, text: str, listen_seconds: float) -> dict:
        log.info("(no voice) would ask: %s", text)
        await self._sleep(listen_seconds)
        return {"transcript": "", "heard_speech": False}
