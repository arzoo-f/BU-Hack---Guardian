"""Speech-to-text (BUILD_PLAN step 4.2): record the reply, decide whether anyone spoke, transcribe.

A loudness check decides whether a voice was heard: the loudest half second must stand out from
the room noise measured just before the question. Silence is never sent to OpenAI (faster, and
nothing leaves the laptop). The recording is kept in memory only.
"""
import asyncio
import logging
import threading

import numpy as np

from voice.audio import SoundDevice, dbfs, encode_wav, loudest_window_dbfs

log = logging.getLogger("guardian.room.stt")

SPACE_BAR_REPLY = "I'm okay (space bar pressed)"


class Listener:
    """Records after a question and returns {"transcript", "heard_speech"} plus diagnostics."""

    def __init__(self, model: str, config: dict, client=None, device=None) -> None:
        self.model = model
        self.cfg = config
        self.client = client
        self.device = device or SoundDevice()
        self._rate: int | None = None

    @property
    def rate(self) -> int:
        if self._rate is None:
            self._rate = self.device.input_rate()
        return self._rate

    def open_mic(self):
        """Switch the microphone on for one question (see voice.audio.Microphone). Blocking."""
        return self.device.open_mic(self.rate)

    def measure_noise(self, mic=None) -> float:
        """Room loudness (dBFS) over noise_sample_s, from `mic` if it is already on. Blocking."""
        seconds = self.cfg["noise_sample_s"]
        return dbfs(mic.read(seconds) if mic is not None else self.device.record(seconds, self.rate))

    def speech_heard(self, samples: np.ndarray, noise_db: float) -> tuple[bool, float]:
        """(heard, loudest half-second in dBFS)."""
        loudest = loudest_window_dbfs(samples, self.rate, self.cfg["speech_window_s"])
        threshold = max(noise_db + self.cfg["speech_margin_db"], self.cfg["min_speech_dbfs"])
        return loudest >= threshold, loudest

    async def transcribe(self, wav: bytes) -> str:
        if self.client is None:
            raise RuntimeError("no OpenAI client")
        # English only (D-012): answers from the floor came back as "Ja sanokhe" / "Ya está ok.".
        # No prompt: with one, near-silence came back as the prompt's own example answers (D-013).
        language = {"language": self.cfg["stt_language"]} if self.cfg.get("stt_language") else {}
        result = await self.client.audio.transcriptions.create(model=self.model, file=("reply.wav", wav),
                                                               **language)
        return result.text

    async def listen(self, seconds: float, noise_db: float, stop: threading.Event | None = None, mic=None) -> dict:
        """Record for `seconds` (or until the space bar), then transcribe if a voice was heard.
        With `mic` already on, the recording starts at once, after dropping what it heard meanwhile."""
        if mic is not None:
            await asyncio.to_thread(mic.skip_buffered)
            samples = await asyncio.to_thread(mic.read, seconds, stop)
        else:
            samples = await asyncio.to_thread(self.device.record, seconds, self.rate, stop)
        if stop is not None and stop.is_set():
            return {"transcript": SPACE_BAR_REPLY, "heard_speech": True, "via": "space bar"}
        heard, loudest = self.speech_heard(samples, noise_db)
        half = max(int(self.rate * 0.5), 1)
        info = {"loudest_dbfs": round(loudest, 1), "noise_dbfs": round(noise_db, 1),
                "levels": [round(dbfs(samples[i:i + half]), 1) for i in range(0, samples.size, half)]}
        if not heard:
            return {"transcript": "", "heard_speech": False, **info}
        try:
            text = await asyncio.wait_for(self.transcribe(encode_wav(samples, self.rate)), self.cfg["stt_timeout_s"])
        except Exception as exc:  # a voice was heard but not understood: the server treats "" as no answer
            log.warning("transcription failed (%s)", type(exc).__name__)
            text = ""
        return {"transcript": text.strip(), "heard_speech": True, **info}
