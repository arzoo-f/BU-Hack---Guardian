"""Audio in and out through the laptop's default speaker and microphone (sounddevice).

Recording happens only when Guardian has just asked a question. The recording stays in memory:
it is never saved; when speech is heard it is sent to OpenAI for transcription (privacy slide).
"""
import io
import math
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf


def decode_wav(data: bytes) -> tuple[np.ndarray, int]:
    """WAV bytes -> (float32 samples, sample rate)."""
    samples, rate = sf.read(io.BytesIO(data), dtype="float32")
    return samples, rate


def encode_wav(samples: np.ndarray, rate: int) -> bytes:
    """float32 samples -> 16-bit WAV bytes."""
    buffer = io.BytesIO()
    sf.write(buffer, samples, rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def dbfs(samples: np.ndarray) -> float:
    """Loudness as RMS in dB relative to full scale (0 dBFS = loudest possible)."""
    if samples.size == 0:
        return -120.0
    rms = float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))
    return 20 * math.log10(max(rms, 1e-6))


def loudest_window_dbfs(samples: np.ndarray, rate: int, window_s: float) -> float:
    """Loudness of the loudest window (where the voice is), checked every quarter window."""
    window = max(int(rate * window_s), 1)
    if samples.size <= window:
        return dbfs(samples)
    step = max(window // 4, 1)
    return max(dbfs(samples[i:i + window]) for i in range(0, samples.size - window + 1, step))


def trim_silence(samples: np.ndarray, rate: int, threshold_db: float, keep_start_s: float,
                 keep_end_s: float) -> np.ndarray:
    """Cut near-silence (10 ms frames quieter than threshold_db) from both ends, keeping a short
    margin. The generated phrases end with 0.5-1.3 s of silence that only delays the listening."""
    mono = samples if samples.ndim == 1 else samples.mean(axis=1)
    frame = max(int(rate * 0.01), 1)
    loud = [i for i in range(0, len(mono), frame) if dbfs(mono[i:i + frame]) > threshold_db]
    if not loud:
        return samples
    start = max(loud[0] - int(keep_start_s * rate), 0)
    end = min(loud[-1] + frame + int(keep_end_s * rate), len(samples))
    return samples[start:end]


def _read(stream, seconds: float, rate: int, stop: threading.Event | None) -> np.ndarray:
    """Read `seconds` of mono audio in 0.1 s blocks, or until `stop` is set (space bar fallback)."""
    blocks: list[np.ndarray] = []
    wanted = int(seconds * rate)
    got = 0
    while got < wanted and not (stop is not None and stop.is_set()):
        block, _ = stream.read(min(int(rate * 0.1), wanted - got))
        blocks.append(block[:, 0].copy())
        got += len(block)
    return np.concatenate(blocks) if blocks else np.zeros(0, dtype=np.float32)


class Microphone:
    """The microphone, switched on for one whole question: room noise, the question, the answer.
    Switching it on takes about 0.75 s on the demo laptop, so it happens once per question, and
    listening starts the moment Guardian stops talking. Blocking: use a worker thread."""

    def __init__(self, rate: int) -> None:
        self.rate = rate
        self._stream = sd.InputStream(samplerate=rate, channels=1, dtype="float32")
        self._stream.start()

    def read(self, seconds: float, stop: threading.Event | None = None) -> np.ndarray:
        return _read(self._stream, seconds, self.rate, stop)

    def skip_buffered(self) -> None:
        """Drop what was captured meanwhile (Guardian's own voice), so the answer starts now."""
        available = self._stream.read_available
        if available:
            self._stream.read(available)

    def close(self) -> None:
        self._stream.stop()
        self._stream.close()


class SoundDevice:
    """Plays and records on the default devices. All calls block: run them in a worker thread."""

    def play(self, samples: np.ndarray, rate: int) -> None:
        sd.play(samples, rate)
        sd.wait()

    def input_rate(self) -> int:
        return int(sd.query_devices(kind="input")["default_samplerate"])

    def open_mic(self, rate: int) -> Microphone:
        return Microphone(rate)

    def record(self, seconds: float, rate: int, stop: threading.Event | None = None) -> np.ndarray:
        """Record mono audio for `seconds`, or until `stop` is set (space bar fallback)."""
        with sd.InputStream(samplerate=rate, channels=1, dtype="float32") as stream:
            return _read(stream, seconds, rate, stop)
