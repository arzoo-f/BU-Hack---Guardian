"""Guardian room agent: camera -> pose -> activity and falls -> server; voice check-ins.

    ..\\.venv\\Scripts\\python.exe main.py --camera 0        # live camera, debug window, real voice
    ..\\.venv\\Scripts\\python.exe main.py --camera 0 --no-voice
    ..\\.venv\\Scripts\\python.exe main.py --clip ..\\clips\\tune_fall_forward_01.mp4   # replay a clip
    ..\\.venv\\Scripts\\python.exe main.py --clip ..\\clips\\tune_fall_forward_01.mp4 --live-voice
    ..\\.venv\\Scripts\\python.exe main.py --mock            # scripted person, no camera
    ..\\.venv\\Scripts\\python.exe main.py --mock --fall-every 20 --seconds 60

Voices: the live camera uses the real speaker and microphone; mock mode and clip replays use a
printed stand-in that always "hears" "I'm okay" (unless --live-voice); --no-voice hears nothing.
"""
import argparse
import asyncio
import contextlib
import json
import logging
import os
import sys
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

from commands import CommandHandler  # noqa: E402
from mockroom import MockRoom  # noqa: E402
from server_link import ServerLink, ws_url  # noqa: E402
from settings import load_vision_config  # noqa: E402
from voice.live import SilentVoice  # noqa: E402
from voice.stub import StubVoice  # noqa: E402

log = logging.getLogger("guardian.room")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Guardian room agent")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--mock", action="store_true", help="scripted person, no camera")
    src.add_argument("--camera", type=int, metavar="N", help="live camera index")
    src.add_argument("--clip", metavar="FILE", help="replay a recorded clip")
    p.add_argument("--no-voice", action="store_true", help="never speak or listen (questions go unanswered)")
    p.add_argument("--live-voice", action="store_true", help="clip: use the real speaker and microphone")
    p.add_argument("--server", help="server address (default: SERVER_URL from .env)")
    p.add_argument("--no-window", action="store_true", help="camera/clip: no debug window")
    p.add_argument("--fast", action="store_true", help="clip: process as fast as possible, not in real time")
    p.add_argument("--loop", action="store_true", help="clip: play it again and again (long reliability runs)")
    p.add_argument("--guide", choices=["activity", "view", "falls"],
                   help="camera: timed on-screen instructions (view = CP2.1, activity = CP2.2, falls = CP2.4)")
    p.add_argument("--log-frames", action="store_true", help="camera: per-frame CSV in room-agent/logs/")
    p.add_argument("--fall-every", type=float, default=60.0, help="mock: seconds between fake falls")
    p.add_argument("--seconds", type=float, help="stop after this many seconds")
    return p.parse_args(argv)


def fixed_phrases() -> list[str]:
    """The check-in phrases the server uses (config/escalation.json), to prepare in advance."""
    config = json.loads((ROOT / "config" / "escalation.json").read_text(encoding="utf-8"))
    return list(config["phrases"].values())


def make_live_voice():
    """The real speaker and microphone, with OpenAI speech when a key is configured."""
    from voice.live import LiveVoice
    from voice.stt import Listener
    from voice.tts import Speaker

    config = json.loads((ROOT / "config" / "voice.json").read_text(encoding="utf-8"))
    client = None
    if os.environ.get("OPENAI_API_KEY"):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(timeout=config["stt_timeout_s"], max_retries=0)
    else:
        log.warning("no OPENAI_API_KEY: the laptop's own voice speaks and nothing is transcribed")
    speaker = Speaker(os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"), os.environ.get("OPENAI_TTS_VOICE", "coral"),
                      config, ROOT / config["phrases_dir"], client=client)
    listener = Listener(os.environ.get("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe"), config, client=client)
    return LiveVoice(speaker, listener, config)


def choose_voice(args: argparse.Namespace):
    if args.no_voice:
        return SilentVoice()
    if args.camera is not None or args.live_voice:
        return make_live_voice()
    return StubVoice()


def server_url(args: argparse.Namespace) -> str:
    return args.server or os.getenv("SERVER_URL", "http://localhost:8000")


def make_link(args: argparse.Namespace, voice) -> ServerLink:
    """Server link whose commands (speak, speak_and_listen) are carried out by `voice`."""
    link = ServerLink(ws_url(server_url(args)))
    link.on_command = CommandHandler(link, voice).handle
    return link


def zone_sender(url: str):
    """Send safe zones saved in the debug window to the server (the dashboard shows them),
    in the background so the camera never waits."""
    def send(zones: list[dict]) -> None:
        def post() -> None:
            request = urllib.request.Request(f"{url.rstrip('/')}/zones", method="POST",
                                             data=json.dumps({"zones": zones}).encode(),
                                             headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(request, timeout=5):
                    log.info("safe zones sent to the server")
            except Exception as exc:
                log.error("could not send the safe zones to the server (%s); they are saved in "
                          "config/zones.json", type(exc).__name__)
        threading.Thread(target=post, daemon=True).start()
    return send


async def prepare_phrases(voice) -> None:
    """Generate the fixed phrases in the background, so the camera starts at once."""
    speaker = getattr(voice, "speaker", None)
    if speaker is None:
        return
    for text, outcome in (await speaker.prepare(fixed_phrases())).items():
        log.info("phrase %s: %r", outcome, text)


async def run_camera(args: argparse.Namespace) -> None:
    from camera_mode import VisionLoop  # imports MediaPipe; mock mode does not need it
    from guide import GUIDES, Guide
    from vision.sources import CameraSource, ClipSource, LoopingClipSource

    config = load_vision_config()
    w, h = config["frame_width"], config["frame_height"]
    if args.clip:
        source = (LoopingClipSource if args.loop else ClipSource)(args.clip, w, h, realtime=not args.fast)
    else:
        source = CameraSource(args.camera, w, h)
    voice = choose_voice(args)
    link = make_link(args, voice)
    guide = Guide(GUIDES[args.guide]) if args.guide else None
    loop = asyncio.get_running_loop()

    def emit(message: dict) -> None:
        """Called from the vision thread: hand the message to the asyncio side."""
        future = asyncio.run_coroutine_threadsafe(link.send(message), loop)
        future.add_done_callback(
            lambda f: not f.cancelled() and f.exception() and log.error("send failed: %s", f.exception()))

    vision = VisionLoop(source, config, emit, os.getenv("ROOM_NAME", "living_room"),
                        show_window=not args.no_window, seconds=args.seconds, guide=guide,
                        frame_log=args.log_frames, on_space=voice.space_pressed,
                        on_zones_saved=zone_sender(server_url(args)))
    tasks = [asyncio.create_task(link.run_forever()), asyncio.create_task(prepare_phrases(voice))]
    try:
        await asyncio.to_thread(vision.run)
        await asyncio.sleep(0.3)  # let the last queued messages go out
    finally:
        vision.stop.set()
        for task in tasks:
            task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks)
    if guide:
        print_guide_summary(guide)


def print_guide_summary(guide) -> None:
    print("\nWhat you did            Expected   Camera saw (share)")
    for text, expected, seen, share, ok in guide.summary():
        name = text.split("  ", 1)[-1][:22]
        print(f"{'OK ' if ok else 'XX '} {name:22s} {expected:10s} {seen} ({share:.0%})")


async def run_mock(args: argparse.Namespace) -> None:
    link = make_link(args, SilentVoice() if args.no_voice else StubVoice())
    room = MockRoom(os.getenv("ROOM_NAME", "living_room"), fall_every=args.fall_every)
    log.info("mock mode: room %s, fake fall every %.0f s, server %s", room.room, args.fall_every, link.url)
    link_task = asyncio.create_task(link.run_forever())
    try:
        await room.run(link, until=args.seconds)
    finally:
        link_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await link_task


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for name in ("httpx", "httpcore"):          # request URLs can carry secrets: never log them
        logging.getLogger(name).setLevel(logging.WARNING)
    load_dotenv(ROOT / ".env")
    args = parse_args(argv)
    try:
        asyncio.run(run_mock(args) if args.mock else run_camera(args))
    except KeyboardInterrupt:
        log.info("stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
