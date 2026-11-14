"""Voice test for CP4.1: Guardian asks "Are you okay?" three times through the real speaker and
microphone, and shows what it heard each time.

Answer "Yes, I'm okay" the first time, stay silent the second time, and say "Help" the third time.

    .venv\\Scripts\\python.exe scripts\\voice_check.py                # 15 s to get into position
    .venv\\Scripts\\python.exe scripts\\voice_check.py --wait 20 --rounds 1

The recordings stay in memory; speech (not silence) is sent to OpenAI for transcription.
"""
import argparse
import asyncio
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "room-agent"), str(ROOT)]

from dotenv import load_dotenv  # noqa: E402

EXPECTED = ["an answer", "silence", "help"]


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wait", type=float, default=15, help="seconds to get into position first")
    p.add_argument("--rounds", type=int, default=3)
    args = p.parse_args()
    load_dotenv(ROOT / ".env")
    import main as agent_main

    voice = agent_main.make_live_voice()
    await voice.speaker.prepare(agent_main.fixed_phrases())
    question = agent_main.fixed_phrases()[0]
    listen_s = 6
    print(f"Get into position: the first question comes in {args.wait:.0f} s.")
    await asyncio.sleep(args.wait)
    rows = []
    for n in range(args.rounds):
        start = time.perf_counter()
        reply = await voice.ask(question, listen_s)
        rows.append((n, reply, time.perf_counter() - start))
        await asyncio.sleep(3)
    print(f"\n{'Round':5s} {'Expected':10s} {'Heard speech':12s} {'Voice vs room':14s} Transcript")
    for n, reply, seconds in rows:
        margin = ("-" if "loudest_dbfs" not in reply else
                  f"{reply['loudest_dbfs'] - reply['noise_dbfs']:+.0f} dB")
        help_word = " <- help keyword" if re.search(r"\bhelp", reply["transcript"].lower()) else ""
        expected = EXPECTED[n] if n < len(EXPECTED) else "-"
        print(f"{n + 1:<5d} {expected:10s} {str(reply['heard_speech']):12s} {margin:14s} "
              f"{reply['transcript']!r}{help_word}   ({seconds:.1f} s for the whole question)")
    cfg = voice.listener.cfg
    print(f"\nSound levels in dBFS (speech counts if the loudest half second is >= room + "
          f"{cfg['speech_margin_db']} dB and >= {cfg['min_speech_dbfs']} dBFS):")
    for n, reply, _ in rows:
        if "levels" in reply:
            timeline = " ".join(f"{level:4.0f}" for level in reply["levels"])
            print(f"  round {n + 1}: room {reply['noise_dbfs']:6.1f}, loudest {reply['loudest_dbfs']:6.1f} | "
                  f"each half second after the question: {timeline}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
