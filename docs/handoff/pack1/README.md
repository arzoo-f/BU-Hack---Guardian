# Handoff pack 1 – for the slides

Made Sat 14 Nov, about 1 am. Person A forwards this folder to Person B.

## What is in this folder

| File | What it shows | Suggested use |
| --- | --- | --- |
| `architecture.png` | The three programs, what travels between them, and where OpenAI and Telegram come in | "How it works" slide. `architecture.svg` is the same picture for PowerPoint (Insert > Pictures keeps it sharp) |
| `screen_live_all_well.png` | Live page: calm green status, the stick figure, "skeleton only – no video leaves the room" | Privacy slide or opening shot |
| `screen_live_alert.png` | Live page during an alert: red status, what was heard, why, the Acknowledge button and the steps so far | The core-flow slide |
| `screen_phone_alert.png` | The same alert at phone width | "Works on the family's phone too" |
| `screen_incident_story.png` | One incident step by step: fall, two questions, no answer, safety rule 1, family alerted, acknowledged | "Every decision is explained" |
| `screen_incidents.png` | The list of incidents | Optional |
| `screen_day_simulated.png` | One day as a coloured activity band, three numbers, time per activity | Data / insights slide |
| `screen_insights.png` | Minutes active per day and stand-ups per day for a week, with the 7-day average | Data / insights slide |

**These screenshots are placeholders.** They come from a test run with a scripted stand-in person
(no camera) and a simulated week of history, taken just after midnight. The Insights page therefore
shows only one sentence; in the daytime it also says things like "Active 60% less than the 7-day
average so far today". Pack 2 will have screenshots from the real camera in the demo room. The
simulated days are always labelled "Simulated history" on screen; keep that label visible if you
use these.

## Technical summary (one paragraph)

Guardian is three programs on one ordinary laptop with no GPU. The **room agent** (Python, Google
MediaPipe and OpenCV) turns each camera frame into a 33-point stick figure about 15 times a second,
works out whether the person is standing, walking, sitting or lying, and spots a fall when the body
goes from upright to the floor within 3 seconds and is still down 3 seconds later. Video never
leaves this program: only the stick-figure points and events go on. The **server** (Python, FastAPI,
SQLite) runs the check-in: it asks "Are you okay?" through the laptop speaker, sends the short
recorded answer to OpenAI for speech-to-text, and lets an OpenAI model choose the next step from a
short list of allowed actions. Five safety rules written in code sit above the AI and can only make
Guardian act sooner: for example, saying "help" alerts the family at once, and no answer to two
questions always alerts them. The family gets a Telegram message with a stick-figure picture (never
a photo) and an Acknowledge button. The **dashboard** (React, Vite, Tailwind, Recharts) shows the live
status, every step with its reason, and the daily mobility trends from the same activity data.

## Facts you can use now

- Fall to first question: about **3 s** (the 3 s is the deliberate "still down?" check).
  Fall to family alert when nobody answers: about **17 s** (target: under 30 s). Both measured with
  the end-to-end simulator on recorded falls; the live timings with the real microphone come in pack 2.
- If the server restarts, the camera program and the dashboard reconnect by themselves in about
  **1 s** once the server is back.
- The five safety rules (code, not AI): no answer twice → alert; "help", "hurt", "pain" and similar
  → alert at once; still on the floor 90 s after a fall → alert, whatever was said; AI error or slower
  than 5 s → treated as no answer; an AI answer outside the allowed actions → alert.
- Privacy, said honestly: no video is stored or sent anywhere. Short voice answers do go to OpenAI
  to be turned into text, so the privacy slide should say that.

**Not yet an accuracy claim:** the 14 tuning clips (6 falls caught, 0 false alarms in 8 normal
movements) were used to choose the thresholds, so they only show the rules fit those clips. The
honest accuracy figure comes from a fresh set of clips recorded and scored once on Sunday morning
(pack 3).
