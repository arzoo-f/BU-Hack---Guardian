# Handoff pack 3 – accuracy and timings

Made Sat 14 Nov, about 8:15 am. Person A forwards this to Person B.
Everything here was measured on the demo laptop in the final room. The full detail is in
`docs/accuracy.md`.

## The accuracy claim (say it exactly like this)

> **In our fresh test clips, Guardian caught all 8 falls that started from standing, each about
> 3 seconds after landing, with 0 false alarms in 6 normal movements.**

Always add the honest part, on the slide or out loud:

> Small, self-recorded test: one person, safe falls onto a mat, one room. Falls that start from
> kneeling or sitting are not caught within seconds; Guardian finds those with its 60-second
> "still on the floor" rule instead.

Why we can call it honest: the settings were frozen before the fresh clips were recorded, each
set was scored once, and nothing was changed after seeing the results.

## The numbers behind it

| Clips (all recorded Sat 14 Nov) | Falls caught | False alarms |
| --- | --- | --- |
| First fresh set: 6 falls + 6 normal movements | 2 of 6 | 0 of 6 |
| Second fresh set: 6 falls, all starting from standing | 6 of 6 | – |
| **All fresh falls** | **8 of 8 from standing**, 0 of 4 from kneeling | **0 of 6** |

What happened in the first set: in four clips the person was already kneeling when the recording
started, so the camera never saw them standing. The fast-fall rule needs to see someone go from
standing to the floor. We kept that result, explained it, and recorded six more falls the right
way (starting from standing).

Normal movements that did **not** cause an alarm: sitting down fast on a chair (x2), lying down
on the sofa (x2), bending to pick something up, kneeling.

The 14 practice ("tuning") clips from Friday are 6 of 6 and 0 of 8, but the settings were chosen
on them, so **do not quote those as accuracy**.

## Timings (live, real camera, microphone and AI)

| Moment | Time | Target |
| --- | --- | --- |
| Landing → Guardian asks "Are you okay?" | **3.6–4.2 s** (3 s of that is the deliberate "still down?" check) | under 6 s |
| Landing → alert on the family's phone when nobody answers | **30–39 s** (two questions, then the alert with its picture) | about 30 s |
| Lying still on the floor without a fall → Guardian checks in | **60 s** | 60–65 s |
| Server crash → everything reconnected by itself | about **1 s** after it restarts | under 10 s |
| 30-minute non-stop run | no crash, 90 incidents handled, memory flat | – |

Measured with the real Telegram on Saturday evening: two test runs (30 s and 33 s) and the four
"no answer" takes filmed for the video (37, 37, 37 and 39 s). The filmed takes were slower because
the room was louder: each silence was loud enough to be sent to speech-to-text (about 3 s per
question) before it counted as no answer. Sending the alert with its stick-figure picture takes
about 2.5 s. Say **"under 40 seconds"**.

## Safety-relevant facts you can use

- The five safety rules are code, not AI. For example, no answer to two questions always alerts
  the family, and "help" alerts at once.
- If the camera stops working for 2 minutes, the family gets a message too ("Guardian cannot see
  the living room since 08:10"), and another one when it is back.
- Lying on the sofa never alerts: the sofa is marked as a safe zone on the camera image.
