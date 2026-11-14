"""Carry out server commands (speak, speak_and_listen) and send the voice_reply back."""
from collections import Counter


class CommandHandler:
    """Turns server commands into voice actions.

    Each reply names the question it answers: the server's own number when the command carries
    one (D-009), otherwise a local count of the questions received for that incident.
    """

    def __init__(self, link, voice) -> None:
        self.link = link
        self.voice = voice
        self.attempts: Counter[str] = Counter()

    async def handle(self, command: dict) -> None:
        if command["type"] == "speak":
            await self.voice.speak(command["text"])
            return
        incident_id = command["incident_id"]
        self.attempts[incident_id] += 1
        attempt = command.get("attempt", self.attempts[incident_id])
        heard = await self.voice.ask(command["text"], command["listen_seconds"])
        await self.link.send({
            "type": "voice_reply", "incident_id": incident_id, "attempt": attempt,
            "transcript": heard["transcript"], "heard_speech": heard["heard_speech"],
        })
