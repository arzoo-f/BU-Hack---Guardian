# Handoff pack 4 – README, Devpost page, judge questions

Made Sun 15 Nov, about 2 am. Person A forwards this to Person B.

> **Update (Sun ~6 am, organisers' email):** the official submission is on **MentorMates**, not
> Devpost. Devpost is optional (portfolio only, not judged). Use the same texts below on MentorMates.
> Judges watch the demo video (up to 5 minutes, YouTube, Public or Unlisted) and read the GitHub
> repo. The README no longer needs the video link: it now says the video is linked from our
> MentorMates submission.
Facts only: put them in your own words. Every number here was measured; where it came from is in
`docs/PROGRESS.md`, `docs/accuracy.md` and pack 3.

## 1. The README is already written

`README.md` at the top of the repository is the README judges will see. It covers what Guardian
does, the five safety rules, the results, privacy, how to run it and the known limits.
You can change anything you like in the wording. Do not change the numbers or the limits.

## 2. Screenshots for the Devpost gallery (real, from the filmed takes)

| File | What it shows |
| --- | --- |
| `screen_incident_no_answer.png` | The 8:58 pm "no answer" take step by step: two questions, no answer, "Safety rule 1: alert the family", family alerted on Telegram, acknowledged 17 s later |
| `screen_incident_water.png` | The 10:09 pm "I'm okay" take: "Yes, I just did." → AI asks whether they need anything → "Can I get some water, please?" → family told (not urgent) |
| `screen_incidents.png` | All 9 filmed incidents, all resolved |

The names of the people who tapped Acknowledge are replaced by "family member" (the rest is
exactly as stored). Pack 1 has the architecture diagram, the Live page, the phone layout, Today and
Insights.

## 3. Devpost page – facts per section

**What it does** – use the 6 numbered points under "What it does" in `README.md`.

**How we built it**
- Three programs on one ordinary laptop (Intel Core Ultra 7, no graphics card), talking over
  WebSockets. Every message is checked against a JSON Schema in both directions.
- Room agent (Python): Google MediaPipe Pose (full model) on the built-in camera, about 15 frames a
  second; activity and fall rules written by us and tuned on 14 clips we recorded; the laptop
  speaker and microphone for the voice check-in.
- Server (Python, FastAPI, SQLite): the check-in steps, the five safety rules in code, the AI
  decision (OpenAI gpt-5.4-mini with a strict JSON schema, about 1 s), Telegram alerts with a
  stick-figure picture and an Acknowledge button.
- Voice: the fixed questions are generated once with OpenAI's voice (gpt-4o-mini-tts) and stored;
  answers are transcribed with gpt-4o-mini-transcribe; the laptop's own voice is the backup.
- Dashboard: React, Vite, Tailwind CSS, Recharts.
- Testing: 282 automated tests (every safety rule has one), 16 dashboard tests, a simulator that
  plays both demo scenarios on recorded falls, a 30-minute non-stop run.
- The code was written with Claude Code (Opus 5.5); a stronger model (Fable 5.2) reviewed the
  safety logic. We tested every step on the real laptop.

**Challenges we ran into**
- **A camera mounted high can't see some falls tilt.** A fall towards or away from the camera
  barely tilts the body in the picture; the torso just looks shorter. We measured our clips and
  built a new signal: how much of the torso still points up compared with the last time the person
  stood ("torso ratio": lying 0.22–0.41, kneeling or sitting 0.60–0.70).
- **Safe falls are slow.** Falls onto a mat dropped the hips at 0.29–0.80 body-heights per second,
  no faster than a fast sit (0.26–0.32) or a bend. So Guardian does not rely on speed: it looks at
  the shape and position of the body, before and 3 seconds after.
- **Speech-to-text invents words in near-silence.** We gave the model a hint listing the expected
  answers; in a silent test it "heard" that list, including "Yes, I'm okay". That could have
  wrongly calmed things down, so we removed the hint, and Guardian now checks loudness first and
  never sends silence.
- **The safety review found real bugs.** For example, if one question got lost during a
  reconnection, every later answer was ignored, so a person saying "Yes, I'm okay" would have
  been treated as silent. All 9 findings were fixed, each with a test that failed before the fix.
- **A security slip.** A library logged web addresses that contained the Telegram bot key. We found
  it, stopped the logging, replaced the key and scanned the whole history: no key was ever
  published.
- **Honest numbers.** Our first fresh test caught only 2 of 6 falls: in 4 clips the person was
  already kneeling when recording started. We kept that result, explained it, and recorded 6 more
  falls the right way.

**Accomplishments we're proud of**
- The whole system runs on one ordinary laptop, and no video ever leaves it.
- Caught all 8 fresh test falls that started from standing, about 3 s after landing, with 0 false
  alarms in 6 normal movements (small, self-recorded test).
- Every one of the 9 filmed demo takes behaved safely: 4 of 4 "no answer" falls alerted the family,
  and 5 of 5 "I'm okay" falls were resolved without bothering anyone.
- It survives failures: a crashed server is restarted and everything reconnects within 4 s; if the
  camera stops, the family is told.
- Every decision is explained: the dashboard shows "AI: ..." or "Safety rule N: ..." for each step.

**What we learned**
- Measure before you build: our guesses about falls (fast, tilted) were wrong for half the cases.
- An AI in a safety system needs fixed rules around it, and those rules need tests.
- The honest small number is worth more than a big untested one.

**What's next**
- Cantonese check-ins (most older people living alone in Hong Kong speak Cantonese).
- Hear "help" even while Guardian is still talking.
- Several rooms; a small dedicated device instead of a laptop; testing with more people.
- Catch falls that start from sitting or kneeling faster than the 60-second rule.

**Built with** (tags): python, mediapipe, opencv, fastapi, sqlite, websockets, openai, telegram,
react, vite, tailwindcss, recharts, pytest, vitest

## 4. Answers to likely judge questions

- **What if the AI decides wrong?** It can only make an alert come sooner. Silence twice, help
  words, staying on the floor for 90 s, an AI error or an odd AI answer all alert the family
  through rules written in code, which the AI cannot override.
- **Isn't a camera at home invasive?** No video is stored or sent. The family sees a stick figure
  and labels. The person agrees to it and chooses the rooms.
- **What does go to the cloud?** The short spoken answer, to be turned into text, and the text, to
  the AI. Never silence, never video.
- **How accurate is it?** 8 of 8 fresh falls from standing, 0 false alarms in 6 normal movements.
  Small, self-recorded test with one person; falls from kneeling are found by the 60-second rule.
- **How fast?** It asks "Are you okay?" about 4 s after landing; with no answer the family's phone
  gets the alert in 30–39 s.
- **What if the internet is down?** Seeing falls and asking the questions work offline (the
  questions are stored, and the laptop's own voice is the backup). Answers can't be turned into
  text or read by the AI then, so they count as "no answer" and Guardian still escalates. Telegram needs the internet: Guardian retries every 15 s
  and says "I am trying to reach your family" until the alert really goes out.
- **Why not a wearable?** People forget to wear or charge them, and a wearable cannot talk to the
  person. The two can work together.
- **How is it different from existing fall alarms?** They send an alarm. Guardian talks to the
  person first, so a slip doesn't panic the family, and it keeps them informed with daily data.
- **Is it a medical device?** No. It is a prototype safety aid.

## 5. Do not claim
- Chinese or Cantonese voice support (the voice check-in understands English only).
- That "help" is heard while Guardian is still asking (it listens after the question).
- That falls from sitting or kneeling are caught within seconds (the 60-second rule finds them).
- Real users or clinical testing (the tests were by one team member, onto a mat).
- The Insights week as real data (it is simulated and labelled "simulated history").
