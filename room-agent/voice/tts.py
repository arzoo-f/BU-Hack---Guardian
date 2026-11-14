"""Text-to-speech (BUILD_PLAN step 4.1).

OpenAI speech (model and voice from .env) with the fixed check-in phrases generated in advance and
kept as WAV files, so an incident never waits for the network. The laptop's own voice (pyttsx3)
takes over when OpenAI cannot be reached. Every sound, from either source, goes through the same
player.
"""
import asyncio
import hashlib
import logging
import tempfile
import threading
from pathlib import Path

from voice.audio import SoundDevice, decode_wav, trim_silence

log = logging.getLogger("guardian.room.tts")


def offline_wav(text: str, rate_wpm: int = 150) -> bytes:
    """The laptop's built-in voice (pyttsx3, SAPI5 on Windows) as WAV bytes. Blocking."""
    import pyttsx3

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "speech.wav"
        engine = pyttsx3.init()
        engine.setProperty("rate", rate_wpm)
        engine.save_to_file(text, str(path))
        engine.runAndWait()
        try:
            engine.stop()
        except Exception:
            pass
        return path.read_bytes()


class Speaker:
    """Says sentences out loud: cached phrase files first, OpenAI next, the laptop's voice last."""

    def __init__(self, model: str, voice: str, config: dict, cache_dir: Path, client=None,
                 device=None, offline=offline_wav) -> None:
        self.model = model
        self.voice = voice
        self.instructions = config["tts_instructions"]
        self.fallback_rate = config["fallback_rate_wpm"]
        self.trim = (config["trim_silence_db"], config["keep_before_speech_s"], config["keep_after_speech_s"])
        self.cache_dir = Path(cache_dir)
        self.client = client
        self.device = device or SoundDevice()
        self.offline = offline
        self._play_lock = threading.Lock()   # never two sounds at once

    # -- making the sound -------------------------------------------------------------------

    def cache_path(self, text: str) -> Path:
        """Where the WAV for this sentence is kept (the name changes if text, model or voice change)."""
        key = "|".join([text, self.model, self.voice, self.instructions])
        return self.cache_dir / f"{hashlib.sha1(key.encode('utf-8')).hexdigest()[:16]}.wav"

    async def _openai_wav(self, text: str) -> bytes:
        if self.client is None:
            raise RuntimeError("no OpenAI client")
        response = await self.client.audio.speech.create(model=self.model, voice=self.voice, input=text,
                                                         instructions=self.instructions, response_format="wav")
        return response.content

    async def make(self, text: str) -> tuple[bytes, str]:
        """(WAV bytes, source) for a sentence: 'cache', 'openai' or 'offline'."""
        path = self.cache_path(text)
        if path.exists():
            return path.read_bytes(), "cache"
        try:
            return await self._openai_wav(text), "openai"
        except Exception as exc:
            log.warning("OpenAI speech failed (%s); using the laptop's own voice", type(exc).__name__)
            return await asyncio.to_thread(self.offline, text, self.fallback_rate), "offline"

    async def prepare(self, phrases: list[str]) -> dict[str, str]:
        """Generate and keep the WAV of every fixed phrase that is not cached yet.
        Only OpenAI audio is kept: a fallback recording would hide OpenAI coming back."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        result = {}
        for text in phrases:
            if self.cache_path(text).exists():
                result[text] = "cached already"
                continue
            try:
                data = await self._openai_wav(text)
                self.cache_path(text).write_bytes(data)
                result[text] = "generated"
            except Exception as exc:
                result[text] = f"not cached ({type(exc).__name__}); the laptop's voice will be used"
        return result

    # -- saying it --------------------------------------------------------------------------

    def _play(self, data: bytes, text: str = "") -> None:
        samples, rate = decode_wav(data)
        samples = trim_silence(samples, rate, *self.trim)   # the listening starts sooner
        with self._play_lock:
            log.info("playing %.1f s: %s", len(samples) / rate, text)   # timing: fall -> first spoken word
            self.device.play(samples, rate)

    async def speak(self, text: str) -> str:
        """Say the sentence and return when it has finished; returns the source used."""
        data, source = await self.make(text)
        try:
            await asyncio.to_thread(self._play, data, text)
        except Exception as exc:
            log.error("could not play speech (%s): %r", type(exc).__name__, text)
            raise
        return source
