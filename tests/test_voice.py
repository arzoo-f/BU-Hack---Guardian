"""Voice tests (BUILD_PLAN steps 4.1-4.3) with a fake sound device and a fake OpenAI: no sound, no network."""
import asyncio
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from commands import CommandHandler
from contracts import validate
from voice.audio import dbfs, decode_wav, encode_wav, loudest_window_dbfs, trim_silence
from voice.live import LiveVoice, SilentVoice
from voice.stt import SPACE_BAR_REPLY, Listener
from voice.tts import Speaker

CONFIG = json.loads((Path(__file__).resolve().parents[1] / "config" / "voice.json").read_text("utf-8"))
RATE = 16000


def tone(seconds: float, amplitude: float, rate: int = RATE) -> np.ndarray:
    t = np.arange(int(seconds * rate)) / rate
    return (amplitude * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def room_noise(seconds: float, level: float = 0.001) -> np.ndarray:
    return (level * np.random.default_rng(1).standard_normal(int(seconds * RATE))).astype(np.float32)


class FakeDevice:
    """Records what is played; 'records' scripted audio."""

    def __init__(self, recordings: list[np.ndarray] | None = None) -> None:
        self.played: list[tuple[int, int]] = []
        self.recordings = list(recordings or [])
        self.events: list[str] = []

    def play(self, samples, rate):
        self.played.append((len(samples), rate))
        self.events.append("play")

    def input_rate(self):
        return RATE

    def record(self, seconds, rate, stop=None):
        self.events.append(f"record {seconds}")
        if stop is not None and stop.is_set():
            return np.zeros(0, dtype=np.float32)
        return self.recordings.pop(0) if self.recordings else room_noise(seconds)

    def open_mic(self, rate):
        self.events.append("mic on")
        return FakeMic(self)


class FakeMic:
    """voice.audio.Microphone on a FakeDevice: same scripted recordings, events in the same list."""

    def __init__(self, device: FakeDevice) -> None:
        self.device = device

    def read(self, seconds, stop=None):
        return self.device.record(seconds, RATE, stop)

    def skip_buffered(self):
        self.device.events.append("skip")

    def close(self):
        self.device.events.append("mic off")


class FakeOpenAI:
    """audio.speech.create and audio.transcriptions.create, scripted."""

    def __init__(self, fail_speech=False, transcript="Yes, I'm okay", fail_stt=False) -> None:
        self.speech_calls, self.stt_calls = [], []
        fail_s, fail_t = fail_speech, fail_stt

        async def speech_create(**kwargs):
            self.speech_calls.append(kwargs)
            if fail_s:
                raise ConnectionError("offline")
            return SimpleNamespace(content=encode_wav(tone(0.5, 0.1, 24000), 24000))

        async def stt_create(**kwargs):
            self.stt_calls.append(kwargs)
            if fail_t:
                raise ConnectionError("offline")
            return SimpleNamespace(text=f" {transcript} ")

        self.audio = SimpleNamespace(speech=SimpleNamespace(create=speech_create),
                                     transcriptions=SimpleNamespace(create=stt_create))


def offline_voice(text, rate):
    return encode_wav(tone(0.3, 0.1, 22050), 22050)


def make_speaker(tmp_path, client=None, device=None):
    return Speaker("gpt-4o-mini-tts", "coral", CONFIG, tmp_path / "phrases", client=client,
                   device=device or FakeDevice(), offline=offline_voice)


# -- sound helpers ----------------------------------------------------------------------------------

def test_loudness_maths():
    assert dbfs(np.zeros(100, dtype=np.float32)) == pytest.approx(-120)
    assert dbfs(tone(1, 1.0)) == pytest.approx(-3.0, abs=0.1)        # full-scale sine
    samples = np.concatenate([room_noise(2), tone(0.5, 0.05), room_noise(2)])
    assert loudest_window_dbfs(samples, RATE, 0.5) > dbfs(samples) + 5
    back, rate = decode_wav(encode_wav(tone(0.2, 0.5), RATE))
    assert rate == RATE and len(back) == int(0.2 * RATE)


def test_silence_around_a_phrase_is_trimmed():
    quiet = np.zeros(RATE, dtype=np.float32)
    phrase = np.concatenate([quiet[: RATE // 2], tone(1, 0.1), quiet])          # 0.5 s, 1 s speech, 1 s
    trimmed = trim_silence(phrase, RATE, CONFIG["trim_silence_db"], CONFIG["keep_before_speech_s"],
                           CONFIG["keep_after_speech_s"])
    expected = 1 + CONFIG["keep_before_speech_s"] + CONFIG["keep_after_speech_s"]
    assert len(trimmed) / RATE == pytest.approx(expected, abs=0.02)
    assert len(trim_silence(tone(1, 0.1), RATE, -45, 0.05, 0.15)) == RATE      # nothing to cut
    assert len(trim_silence(quiet, RATE, -45, 0.05, 0.15)) == RATE              # all quiet: unchanged


async def test_spoken_phrases_lose_their_trailing_silence(tmp_path):
    device = FakeDevice()
    speaker = make_speaker(tmp_path, device=device)
    path = speaker.cache_path("Are you okay?")
    path.parent.mkdir(parents=True)
    path.write_bytes(encode_wav(np.concatenate([tone(1, 0.1, 24000), np.zeros(24000, np.float32)]), 24000))
    assert await speaker.speak("Are you okay?") == "cache"
    assert device.played == [(round((1 + CONFIG["keep_after_speech_s"]) * 24000), 24000)]


# -- 4.1 speaking -------------------------------------------------------------------------------------

async def test_fixed_phrases_are_made_once_and_reused(tmp_path):
    client, device = FakeOpenAI(), FakeDevice()
    speaker = make_speaker(tmp_path, client, device)
    phrases = ["Are you okay? Please say yes or no.", "I have messaged your family. Help is coming."]
    assert set((await speaker.prepare(phrases)).values()) == {"generated"}
    assert len(client.speech_calls) == 2
    sent = client.speech_calls[0]
    assert sent["model"] == "gpt-4o-mini-tts" and sent["voice"] == "coral" and sent["response_format"] == "wav"
    assert sent["instructions"] == CONFIG["tts_instructions"]
    assert set((await speaker.prepare(phrases)).values()) == {"cached already"}
    assert await speaker.speak(phrases[0]) == "cache"
    assert len(client.speech_calls) == 2 and device.played == [(12000, 24000)]


def test_cache_name_changes_with_text_model_or_voice(tmp_path):
    a = make_speaker(tmp_path)
    b = Speaker("gpt-4o-mini-tts", "sage", CONFIG, tmp_path / "phrases")
    assert a.cache_path("hello") != a.cache_path("hello!")
    assert a.cache_path("hello") != b.cache_path("hello")
    assert a.cache_path("hello") == make_speaker(tmp_path).cache_path("hello")


async def test_other_sentences_are_made_on_demand(tmp_path):
    client = FakeOpenAI()
    speaker = make_speaker(tmp_path, client)
    assert await speaker.speak("Glad you're okay. Do you want me to tell your daughter?") == "openai"
    assert not list((tmp_path / "phrases").glob("*.wav"))      # one-off sentences are not kept


async def test_laptop_voice_takes_over_when_openai_fails(tmp_path):
    device = FakeDevice()
    speaker = make_speaker(tmp_path, FakeOpenAI(fail_speech=True), device)
    assert "not cached" in (await speaker.prepare(["Are you okay?"]))["Are you okay?"]
    assert await speaker.speak("Are you okay?") == "offline"
    assert device.played == [(int(0.3 * 22050), 22050)]
    assert await make_speaker(tmp_path, client=None).speak("No key at all") == "offline"


# -- 4.2 listening ------------------------------------------------------------------------------------

def make_listener(recordings, client=None):
    return Listener("gpt-4o-mini-transcribe", CONFIG, client=client, device=FakeDevice(recordings))


async def test_silence_is_no_answer_and_never_sent_to_openai():
    client = FakeOpenAI()
    listener = make_listener([room_noise(6)], client)
    reply = await listener.listen(6, noise_db=-60.0)
    assert reply["transcript"] == "" and reply["heard_speech"] is False
    assert client.stt_calls == []


async def test_a_voice_is_transcribed():
    client = FakeOpenAI(transcript="Yes, I'm okay")
    speech = np.concatenate([room_noise(1), tone(1.2, 0.05), room_noise(3.8)])   # about -29 dBFS, as measured
    reply = await make_listener([speech], client).listen(6, noise_db=-60.0)
    assert reply["heard_speech"] is True and reply["transcript"] == "Yes, I'm okay"
    (call,) = client.stt_calls
    assert call["model"] == "gpt-4o-mini-transcribe"
    assert call["language"] == "en" and "prompt" not in call   # D-012 English only; D-013 no prompt
    name, wav = call["file"]
    assert name == "reply.wav" and wav[:4] == b"RIFF"
    assert reply["loudest_dbfs"] > reply["noise_dbfs"] + CONFIG["speech_margin_db"]


async def test_speech_must_stand_out_from_a_noisy_room():
    tv = room_noise(6, level=0.02)                      # about -34 dBFS of background
    reply = await make_listener([tv], FakeOpenAI()).listen(6, noise_db=-34.0)
    assert reply["heard_speech"] is False


async def test_failed_transcription_returns_an_empty_reply():
    speech = np.concatenate([room_noise(1), tone(1, 0.05), room_noise(4)])
    reply = await make_listener([speech], FakeOpenAI(fail_stt=True)).listen(6, noise_db=-60.0)
    assert reply["heard_speech"] is True and reply["transcript"] == ""


async def test_space_bar_means_i_am_okay():
    stop = threading.Event()
    stop.set()
    reply = await make_listener([]).listen(6, noise_db=-60.0, stop=stop)
    assert reply == {"transcript": SPACE_BAR_REPLY, "heard_speech": True, "via": "space bar"}


# -- 4.3 the voice the room agent uses ------------------------------------------------------------------

async def test_live_voice_listens_only_after_the_question():
    device = FakeDevice()
    speech = np.concatenate([tone(1, 0.05), room_noise(5)])
    listener = Listener("m", CONFIG, client=FakeOpenAI(transcript="yes"), device=device)
    device.recordings = [room_noise(CONFIG["noise_sample_s"]), speech]
    speaker = make_speaker(Path("unused"), FakeOpenAI(), device)
    voice = LiveVoice(speaker, listener, CONFIG)
    voice.space_pressed()                               # an old press must not answer this question
    reply = await voice.ask("Are you okay? Please say yes or no.", 6)
    # one microphone for the whole question; Guardian's own voice is dropped before the answer
    assert device.events == ["mic on", f"record {CONFIG['noise_sample_s']}", "play", "skip", "record 6", "mic off"]
    assert reply["transcript"] == "yes" and reply["heard_speech"] is True


async def test_room_noise_is_measured_again_only_after_a_while():
    now = [100.0]
    device = FakeDevice()
    voice = LiveVoice(make_speaker(Path("unused"), FakeOpenAI(), device),
                      Listener("m", CONFIG, client=FakeOpenAI(), device=device), CONFIG, clock=lambda: now[0])
    noise_sample = f"record {CONFIG['noise_sample_s']}"
    await voice.ask("Are you okay?", 6)
    now[0] += 12                                        # the second question of the same incident
    await voice.ask("Can you hear me?", 8)
    assert device.events.count(noise_sample) == 1
    now[0] += CONFIG["reuse_noise_for_s"] + 1           # a later incident: the room may have changed
    await voice.ask("Are you okay?", 6)
    assert device.events.count(noise_sample) == 2


async def test_the_microphone_is_switched_off_even_when_recording_fails():
    class BrokenMic(FakeMic):
        def read(self, seconds, stop=None):
            if seconds == 6:
                raise OSError("device lost")
            return super().read(seconds, stop)

    device = FakeDevice()
    device.open_mic = lambda rate: (device.events.append("mic on"), BrokenMic(device))[1]
    voice = LiveVoice(make_speaker(Path("unused"), FakeOpenAI(), device),
                      Listener("m", CONFIG, client=FakeOpenAI(), device=device), CONFIG)
    assert await voice.ask("Are you okay?", 6) == {"transcript": "", "heard_speech": False}
    assert device.events[-1] == "mic off"


async def test_room_agent_replies_with_the_live_voice():
    sent = []

    class Link:
        async def send(self, message):
            sent.append(validate("room", message))

    device = FakeDevice([room_noise(0.5), np.concatenate([tone(1, 0.05), room_noise(7)])])
    voice = LiveVoice(make_speaker(Path("unused"), FakeOpenAI(), device),
                      Listener("m", CONFIG, client=FakeOpenAI(transcript="Some water, please"), device=device),
                      CONFIG)
    handler = CommandHandler(Link(), voice)
    await handler.handle({"type": "speak_and_listen", "incident_id": "inc_001", "attempt": 2, "listen_seconds": 8,
                          "text": "Glad you're okay. Do you need anything?"})
    assert sent == [{"type": "voice_reply", "incident_id": "inc_001", "attempt": 2,
                     "transcript": "Some water, please", "heard_speech": True}]


async def test_silent_voice_never_hears_anything():
    async def no_wait(_):
        return None

    assert await SilentVoice(sleep=no_wait).ask("Are you okay?", 6) == {"transcript": "", "heard_speech": False}
