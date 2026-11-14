# Demo video – shot list (target 2:45, hard limit under 3:00)

For Person A (actor, runs the laptop) and Person B (narration, phone, editing).
The video is the demo (D-003, D-011): upload it to YouTube or Vimeo, then open the link in a
private browser window to check that anyone can watch it.

## What you need

| Source | What it shows | How |
| --- | --- | --- |
| **Room camera** | Person A in the room, and Guardian's voice | A phone on a stand, filming the room. The laptop camera is busy: Guardian uses it. |
| **Laptop screen** | The dashboard following the incident | Windows screen recording: **Win + Alt + R** (Xbox Game Bar), or OBS. Dashboard in demo mode. |
| **Family phone** | The Telegram alert arriving, and the Acknowledge tap | Person B's phone screen recording (built into iPhone and Android). |
| **Slides** | Problem, accuracy claim, closing | Person B's slides (packs 1 and 3 have the diagram and the numbers). |

Edit the three recordings side by side or picture-in-picture: room on one side, dashboard on the
other, phone in a corner when the alert arrives.

**Never in the video:** the black debug window with the camera image (the point is that no video
leaves the laptop), the `.env` file, any key or token, private chats or other notifications on
the phones (turn on Do Not Disturb, except for the Telegram group).

## Before every take (about 2 minutes)

1. `stop.bat`, then `.venv\Scripts\python.exe scripts\reset_demo.py --yes` (clean demo data).
2. `start.bat --demo` (Telegram on), then `.venv\Scripts\python.exe scripts\preflight.py` until it is
   all green.
3. Start the three recordings, then clap once in view of the room camera (makes syncing easy).

## Shot list

| Time | On screen | What happens | What it shows | Who |
| --- | --- | --- | --- | --- |
| 0:00–0:15 | Title slide | One real figure about older people living alone in Hong Kong and falls (Person B finds and cites the source). | A real problem | B narrates |
| 0:15–0:30 | Room + Live page | A walks and sits; the stick figure follows; label changes (Walking, Sitting). "Only this stick figure leaves the camera program – no video." | Privacy by design | A acts, B narrates |
| 0:30–0:42 | Room + Live page | A sits down fast on the chair, then lies on the sofa. The status stays green. | Not a naive detector (sofa safe zone) | A acts |
| 0:42–1:25 | Room + dashboard + phone | Safe fall on the mat → "Are you okay?" → A: "Yes, I slipped" → stands → "Do you need anything?" → "Some water, please" → the phone gets a gentle message. | A conversation, not just an alarm | A acts, B shows the phone |
| 1:25–2:10 | Room + dashboard + phone | Second safe fall, A stays silent → "Can you hear me?" → red alert → the phone buzzes with the stick-figure picture → B taps **Acknowledge** → dashboard says Resolved. | Escalation, with safety rules in code | A and B |
| 2:10–2:30 | Dashboard | Incident page: every step with who decided and why ("Safety rule 1: alert the family"). Then the Insights page (label "simulated history" visible). | Explainable decisions; data for families | screen only, B narrates |
| 2:30–2:45 | Slides | The accuracy claim from pack 3, with its honest limit; the tech in one line; the closing line. | Honest results | B narrates |

## Timing: shorten waits, never fake them

Each question takes about 15 s from start to answer, so the real Scenario 1 runs about 45 s and
the real Scenario 2 about 30 s until the phone buzzes. To fit 2:45, cut the silent waiting in the
edit, and say so on screen (for example a small "shortened" label, or a clock in the corner).
Keep one full, uncut take of each scenario: it is proof if a judge asks, and a backup.

## Takes

- Record each scenario at least twice, and keep the best one.
- Kneel first, then roll onto the mat, as in every test. Stop if anything hurts.
- If Guardian mishears an answer, it simply asks again. Keep that take only if it still fits; it
  is an honest moment, not a failure.
- After each take: `stop.bat`, `reset_demo.py --yes`, `start.bat --demo` again, so every take
  starts with the same clean data.

## Things to say carefully

- "Caught all 8 fresh test falls that started from standing, about 3 seconds after landing, with
  no false alarms in 6 normal movements – a small test we recorded ourselves." (pack 3)
- Guardian is a prototype, **not a medical device**.
- Voice answers are sent to OpenAI to be turned into text; no video is ever sent anywhere.
