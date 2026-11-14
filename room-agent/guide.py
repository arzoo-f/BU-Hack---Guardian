"""Timed on-screen instructions for checkpoints, and a summary of what the camera saw.

Used by `main.py --camera 0 --guide activity` for CP2.2.
"""
from collections import Counter

# (seconds, instruction shown in the window, expected smoothed label or None)
ACTIVITY_GUIDE = [
    (15, "Get ready: stand 2-3 m from the camera", None),
    (10, "1/5  STAND STILL", "standing"),
    (12, "2/5  WALK across the room and back", "walking"),
    (12, "3/5  SIT on the chair", "sitting"),
    (15, "4/5  LIE DOWN slowly on the mat", "lying"),
    (10, "5/5  LEAVE the camera view", "absent"),
    (8, "Come back - all done!", None),
]
VIEW_GUIDE = [  # CP2.1 in a new room: first prove nothing in the empty room looks like a person
    (5, "Get ready: walk OUT of the camera view", None),
    (12, "STAY OUT of view - no skeleton should appear", "absent"),
    (10, "Walk in and STAND by the far wall", "standing"),
    (15, "LIE DOWN slowly on the mat", "lying"),
    (5, "Done - come back", None),
]
FALLS_GUIDE = [  # CP2.4 + CP3.4: live falls (safe: kneel first, then roll onto the mat)
    (15, "Get ready: stand next to the mat", None),
    (15, "1/3 SAFE FALL onto the mat, ACROSS the picture - stay down", "fallen"),
    (15, "Get up slowly and rest", None),
    (15, "2/3 SAFE FALL, HEAD pointing TO THE LAPTOP - stay down", "fallen"),
    (15, "Get up slowly, then go to the chair", None),
    (10, "3/3 SIT DOWN FAST on the chair", "sitting"),
    (5, "Stand up - all done!", None),
]
GUIDES = {"activity": ACTIVITY_GUIDE, "view": VIEW_GUIDE, "falls": FALLS_GUIDE}
JUDGE_FROM = 0.4  # judge each step on its last 60%, after the person has moved into position


class Guide:
    """Knows which instruction is due at time t and remembers the labels seen during each step."""

    def __init__(self, steps: list[tuple[float, str, str | None]]) -> None:
        self.steps = steps
        self.total = sum(s for s, _, _ in steps)
        self._seen: list[list[str]] = [[] for _ in steps]

    def step_at(self, t: float) -> int | None:
        for i, (seconds, _, _) in enumerate(self.steps):
            if t < seconds:
                return i
            t -= seconds
        return None

    def instruction(self, t: float) -> str:
        i = self.step_at(t)
        if i is None:
            return "Done"
        start = sum(s for s, _, _ in self.steps[:i])
        return f"{self.steps[i][1]}   ({self.steps[i][0] - (t - start):.0f} s)"

    def record(self, t: float, label: str | None) -> None:
        i = self.step_at(t)
        if i is None or label is None:
            return
        start = sum(s for s, _, _ in self.steps[:i])
        if t - start >= JUDGE_FROM * self.steps[i][0]:
            self._seen[i].append(label)

    def summary(self) -> list[tuple[str, str, str, float, bool]]:
        """Rows of (instruction, expected, seen most, share, ok) for steps with an expectation."""
        rows = []
        for (_, text, expected), seen in zip(self.steps, self._seen):
            if expected is None:
                continue
            if seen:
                top, n = Counter(seen).most_common(1)[0]
                share = n / len(seen)
            else:
                top, share = "(nothing)", 0.0
            rows.append((text, expected, top, share, top == expected))
        return rows
