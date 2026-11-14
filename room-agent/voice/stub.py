"""Stand-in voice for mock mode, clip replays and tests: prints instead of speaking, 'hears' a fixed reply."""
import asyncio
from collections.abc import Awaitable, Callable


class StubVoice:
    """speak() prints the text; listen() waits `seconds` and returns `reply`."""

    def __init__(self, reply: str = "I'm okay",
                 sleep: Callable[[float], Awaitable[None]] = asyncio.sleep) -> None:
        self.reply = reply
        self._sleep = sleep
        self.spoken: list[str] = []

    def space_pressed(self) -> None:
        pass

    async def speak(self, text: str) -> None:
        self.spoken.append(text)
        print(f"[voice stub] says: {text}")

    async def listen(self, seconds: float) -> dict:
        await self._sleep(seconds)
        print(f"[voice stub] heard: {self.reply!r}")
        return {"transcript": self.reply, "heard_speech": bool(self.reply)}

    async def ask(self, text: str, listen_seconds: float) -> dict:
        await self.speak(text)
        return await self.listen(listen_seconds)
