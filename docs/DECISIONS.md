# Guardian - decisions

Approved changes to `docs/BUILD_PLAN.md` (version 2), oldest first. Each entry: what, why, effect.

## D-001 · Thu 12 Nov · Kickoff and deadline are 10 hours earlier
- **What:** kickoff (H0) is Fri 13 Nov 10:00 am HKT; deadline (H48) is Sun 15 Nov 10:00 am HKT
  (confirmed by Person A). The plan assumed Fri 8 pm / Sun 8 pm.
- **Effect:** every H-time in the plan moves 10 hours earlier. Submission target (H46) is
  Sun 8:00 am. A revised day-by-day schedule with night-time sleep is drafted in
  `docs/PROGRESS.md` and waits for Person A's approval.

## D-002 · Thu 12 Nov · Code before kickoff is allowed
- **What:** the organisers confirmed by email to Person A that code may be written before kickoff
  (keep that email). At Person A's request, Stage 1 started Fri 13 Nov at about 12:45 am.
- **Effect:** CP1.1 (final requirements) still happens at kickoff; anything they change is
  handled then.

## D-003 · Thu 12 Nov · Recorded demo instead of a live demo
- **What (team decision):** Guardian runs locally; one team member films it in person; the
  recording is shown inside the PowerPoint presentation.
- **Why:** clearer for judges and far less risky than a live run.
- **Effect:** the Stage 10 "backup video" becomes the main demo video. The video-call setup in
  Section 29 (second device, muted call microphone) is no longer needed. Dashboard demo mode
  (SHOULD) stays: the recording can then follow an incident without clicks. If the team reaches
  the in-person finals at HKBU, a live demo may still be needed. The official judging format is
  checked at CP1.1.

## D-004 · Thu 12 Nov · Built-in camera, laptop mounted high
- **What (Person A):** there is no USB webcam, so the whole laptop goes up high (about 1.5-2 m),
  screen tilted so the camera looks down at the floor.
- **Effect:** the laptop's own speaker and microphone are used from there (tested: CP0.6 passed
  from the mat). The camera-offline test (CP8.5) uses the `C` key, since the camera cannot be
  unplugged.

## D-005 · Thu 12 Nov · opencv-contrib-python instead of opencv-python
- **What:** mediapipe 1.2.3 installs opencv-contrib-python (the same `cv2`, plus extra modules).
  Installing opencv-python as well makes the two overwrite each other.
- **Effect:** none on behaviour; `requirements.txt` says so.

## D-006 · Fri 13 Nov · How the dashboard messages are written down (approved by Person A, Fri ~8:10 am)
- **What:** Section 12 says dashboard messages carry "the same fields as above plus incident_id and
  state", but does not spell out `incident_update` or the state names. The contracts now say:
  - states are `monitoring`, `checkin_1`, `checkin_2`, `follow_up`, `escalate`, `resolved`
    (`monitoring` and `incident_id: null` when nothing is open);
  - `incident_update` mirrors one `incident_events` row: `kind` (state, speak, reply, decision,
    alert, ack, request) plus a `payload`, with optional `reason` and `simulated`;
  - `decision` may say who decided: `source` = `ai` or `hard_rule`, and which `rule` (1-5), so the
    dashboard can show why.
- **Effect:** the room agent and server messages are exactly as in Section 12; nothing there changed.

## D-007 · Fri 13 Nov · How a fall is recognised (approved by Person A, Fri ~8:10 am)
- **Plan (Section 13):** hips drop faster than about 1 body-height per second and the torso tilts
  past 60 degrees within 1 s -> candidate; still low and horizontal 3 s later -> fall.
- **What the 14 tuning clips showed:**
  1. Safe falls (kneel, then roll) are slow: hips drop at 0.29-0.80 body-heights/s, no faster than
     a fast sit (0.26-0.32), a kneel (0.38-0.47) or a bend (0.42-0.61). Speed cannot tell them apart.
  2. A fall towards or away from the camera never tilts past 60 degrees in the picture. The torso
     gets shorter instead (31-41% of its standing length), because the camera looks along the body.
- **Rule now (room-agent/vision/fall.py, thresholds in config/vision.json):**
  - "Torso ratio" = how much of the torso's standing length still points upwards in the picture,
    measured against the last time the person stood upright. Lying in any direction: 0.22-0.41.
    Kneeling and sitting: 0.60-0.70. Cut-off 0.5.
  - A bend also gives a low ratio, so "down" additionally needs the body to be wide, or the head
    beyond the hips, or the feet beyond the hips. A bend has the head hanging and the feet under
    the body.
  - Fast path: upright -> down within 3 s (`fall_window_s`), and still down 3 s later
    (`fall_confirm_s`) -> `fast_fall`. Upright again first -> a stumble, no incident.
  - Slow path: torso not upright (down, or bent over) outside a safe zone for 60 s -> `found_on_floor`.
  - After a fall the label is `fallen` until the person stands again; sitting up on the floor is
    still `fallen`.
- **Consequences to know:**
  - Lying down on the floor on purpose within about 3 s looks the same as a careful fall: Guardian
    asks "Are you okay?". For the found-on-floor test (CP8.3), go down in stages over more than 3 s.
  - Sliding from a chair to the floor is not "from upright": it is caught by the slow path (60 s).
  - Not yet tested on a clip: a fall with the head pointing TOWARDS the camera (covered by a rule,
    to be checked live at CP2.4).
- **Removed config keys:** `fall_drop_speed_bodyheights_per_s`, `fall_torso_deg`.
  **Contracts unchanged.** `fall_detected.features` still carries `drop_speed`, `torso_angle` and
  `seconds_low`, plus `torso_ratio`. Section 13 of the plan now carries a note pointing here.
- **Result on the tuning set:** 6 of 6 falls caught, 0 false alarms in 8 normal clips (1 without the
  sofa zone); the result is unchanged when each threshold is moved 10-20% either way.

## D-009 · Fri 13 Nov · Contract addition: questions are numbered (approved by Person A, "fix all", Fri ~9:00 am)
- **What:** `speak_and_listen` (server -> room agent) may carry `attempt`, the number of the question
  within the incident. The room agent copies it into its `voice_reply`.
- **Why (review finding H2):** the server and the room agent used to count questions separately. If
  one question did not reach the room (a reconnect), every later answer was thrown away as
  "unexpected": a person who said "Yes, I'm okay" was ignored and the family was alerted.
- **Effect:** `contracts/command/speak_and_listen.schema.json` (optional field, so older messages
  stay valid), `room-agent/commands.py`, `server/app.py`. Section 12 of the plan carries a note.

## D-010 · Fri 13 Nov · Changes from the Stage 3 safety review (approved by Person A, "fix all")
Fable 5.2 reviewed `server/escalation.py` and its tests against Section 14 and found 3 serious and
6 medium problems; all are fixed, each with a test that failed before the fix.
- **Rule 2 is checked on every reply** heard during an incident, whichever question it answers
  (H1: "help me" in an unexpected reply used to be ignored and the incident could close).
- **An AI answer only applies to the incident it was asked about** (H3).
- **A failed alert is retried after 15 s** (`alert_retry_s`), not after 2 minutes, and Guardian never
  says "I have messaged your family. Help is coming." unless an alert really went out. Until then
  it says the new phrase `escalate_pending`: "I am trying to reach your family." (M1). A sentence
  counts as said only if the room could be reached.
- **Nothing slow happens while the engine is locked:** notifier and room calls run after the lock is
  released, so a slow Telegram cannot delay acknowledgements, replies or posture updates (M2).
- **A stuck AI step counts as no answer** after `ai_timeout_s` + 3 s (M3).
- **Rule 5 is stricter:** "needs help" with any action other than escalate -> escalate. The AI's own
  sentence is replaced by the fixed phrase if it is longer than `max_say_chars` (120) or contains a
  help keyword, because "Do you need any help?" invites "No, I don't need help" (M4).
- **Server restart during an incident (Person A chose the safest option):** on start-up the newest
  unfinished real incident is re-opened as an alert ("Guardian restarted during this incident") and
  re-alerts until acknowledged; other unfinished incidents are closed with a note (M5).
  Consequence for testing: restarting the server while an incident is open raises an alert.
- **A real fall closes an open simulated incident** and starts a real one (M6).
- **Help keywords match words, not fragments:** "painful", "hurts", "HELP!" and "cant get up" match;
  "painting" and "Spain" do not. The keyword list is unchanged. Negations ("no pain") still alert.
- **Unchanged by design:** a second fall during an open real incident is only logged on it, so an
  old unacknowledged alert blocks new check-ins. `reset_demo.py` and `preflight.py` must check for
  open incidents (Stages 7 and 9).

## D-011 · Fri 13 Nov · Final submission requirements (CP1.1, pasted by Person A at ~2:20 pm)
- **Confirmed:** Fri 13 Nov 10:00 - Sun 15 Nov 10:00 (D-001); Hong Kong students; any tech stack or
  AI; judging Technical 30%, Presentation 30%, Innovation 20%, Impact 20% (as in the plan).
- **Submission rules:** one submission per team; nothing accepted after the deadline; "missing even
  1 file could cause a disqualification".
- **Required deliverables:**
  1. A GitHub repository that belongs to the team and was created for this hackathon, **public** for
     judging, showing **meaningful commits between Fri 13 Nov 10:00 and Sun 15 Nov 10:00**.
  2. A **presentation video under 3 minutes**, submitted as a YouTube, Vimeo or Youku link.
- **Not mentioned:** a live demo, finals, a slide file.
- **Effect on the plan:**
  - The presentation video is THE demo (confirms D-003). Target length 2:45 including the intro;
    Section 29's script (exactly 3:00) is shortened when Person B writes the video script.
    Upload by Sun ~7:00 am (processing time) and check the link in a private window (CP10.5).
  - Repository made public at submission (CP10.4), after the Stage 9 secret scan.
  - Commits: 24 commits were made before kickoff (Fri 01:15-08:47), allowed by the organisers'
    email (D-002). Every tested step after kickoff is committed, so the hackathon period will hold
    most of the work. Person A decided (Fri 10:40 pm): NO note in the README; keep the email.
  - Person B opens the Devpost submission form and lists every required field and file.

## D-008 · Fri 13 Nov · Provisional sofa zone (approved by Person A, Fri ~8:10 am)
- **What:** `config/zones.json` holds a sofa zone estimated from the two sofa tuning clips, so that
  lying on the sofa does not alarm before the zone tool exists.
- **Effect:** Person A redraws it in the debug window in Stage 8 (CP8.2). The debug window already
  shows the zone as a blue box.

## D-012 · Sat 14 Nov · Speech-to-text expects English only (Person A, Sat ~8:20 am)
- **Why:** answers spoken from the floor were sometimes transcribed in another language ("Ja
  sanokhe", "Ya está ok." for "Yes, I'm okay"), costing a second question once.
- **What:** `config/voice.json` `stt_language` = "en" is passed to the transcription model.
- **Effect:** more reliable English answers. A Chinese "救命" would no longer be recognised as such,
  so the help keyword does not fire for it (the keyword stays in the list: it may be extended,
  never shortened). The hard rules still alert on silence or an unclear answer. Known limit for the
  README: the voice check-in understands English.
- Also: Person A set the Windows microphone "Input volume" from 94 to 100.

## D-013 · Sat 14 Nov · No speech-to-text prompt (found in Stage 6, Sat 7:07 pm)
- **Why:** in a Scenario 2 run Person A stayed silent, yet the transcript was the prompt's own example
  list ("Yes, I'm okay. No. Help! I slipped. I can't get up. Some water, please."): with a prompt, the
  model "hears" its examples in near-silence. Here it contained "Help!" and alerted, but it could as
  easily have returned "Yes, I'm okay" - a false reassurance.
- **What:** the prompt added in the morning (fbe2434) is removed; English only (D-012) stays and
  covers the problem the prompt was meant to fix. The room agent now logs the loudness of every
  answer (loudest and room level), to see why a silent answer passed the loudness check.

## D-014 · Sat 14 Nov · Stage 6 gate merged into filming the demo video (Person A, Sat ~7:15 pm)
- **Why:** time (7:15 pm Saturday, submission by Sun 8 am); the video is the demo (D-003), so a
  failed take can be retaken, unlike a live demo.
- **What:** instead of a separate "3 passes in a row" session, every video take counts as a Stage 6
  run: after each take Claude checks the incident's stored steps (scripts/incident_times.py) for
  pass/fail and timings. The first silent take must show that silence is heard as no answer after
  D-013. Before the gate fix: Scenario 1 passed once, Scenario 2 failed once (D-013).
- **Demo content (Person A's plan):** the room and the local debug window next to the website (camera
  image stays local; website and family see only the stick figure), the sofa safe zone, walking and
  sitting, a silent fall -> Telegram alert -> Acknowledge. Suggested: one "I'm okay" fall too.

## D-015 · Sun 15 Nov · Submission moves to MentorMates (organisers' email, pasted by Person A ~6 am)
- **What changed:** the official submission is on MentorMates
  (https://www.mentormates.ai/events/b2b0d321-898e-49fe-99f0-2a3496004031/overview); Devpost is
  optional, portfolio only, not judged. Items: demo video (up to 5 minutes, YouTube, Public or
  Unlisted), GitHub repo with meaningful commits and a README, judging-criteria compliance,
  presentation (optional), theme (can be changed from the Devpost choice). Deadline unchanged:
  before Sun 15 Nov 10:00 am. Every participant must be registered on MentorMates.
- **Judging:** judges review the demo video and the GitHub repo (Technical 30%, Presentation 30%,
  Innovation 20%, Impact 20%). The earlier "video under 3 minutes" (D-011) is replaced by 5 minutes.
- **README:** Person A decided to push the final code without the video link (the video is still
  being subtitled and goes in the MentorMates form). README line 9 now says the video is linked from
  the MentorMates submission.
- **Theme:** keep Data-driven Apps (the plan's theme and pitch line; the dashboard, timeline and
  insights are the data part).
- **Finals (if selected):** Sun 5:30-9:30 pm, DLB 306, HKBU Shaw Campus; 3 min presentation + 5 min
  Q&A; bring the laptop for a local demo, student card and HKID; at least 30% of the team present
  (for two people: at least one).
- **Old-project rule:** the 24 commits before kickoff were allowed by the organisers' email (D-002);
  keep that email ready in case anyone asks.
