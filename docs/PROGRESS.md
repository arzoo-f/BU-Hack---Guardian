# Guardian - progress log

## STATUS (Sun 15 Nov, 6:05 am = H44) - read this first
Demo video FILMED; Person B is adding subtitles. Stages 1-9 done (tags up to stage-9-done;
feature-freeze tagged). The SUBMISSION IS ON MENTORMATES, not Devpost (D-015). Code is final and
pushed without the video link (Person A, ~6 am). Stage 10 left, no code:
1. Person A makes the GitHub repo public (CP10.4); Claude checks it from outside.
2. Both team members registered on MentorMates and in the same team/submission there.
3. Person B uploads the video to YouTube (Public or Unlisted, up to 5 min) and checks it plays in a
   private window.
4. MentorMates form: repo link, YouTube link, theme Data-driven Apps, judging-criteria answers,
   slides optional (pack 4 texts). Submit by ~9 am (deadline 10:00 am).
5. CP10.5: open the submission, video and repo in a private window; Claude tags `submitted`.
   After 10 am: no more pushes to main (any finals prep stays local or on a branch).
Devpost (optional, not judged): Person B already filled every field; submit it too if time allows.
Both registered on Devpost (no team option there; it does not matter for judging).
Person A's answers (Sun ~1:55 am): (1) the video's alert timing "is okay, leave it" - closed;
(2) `docs/Screenshot 2026-11-14 205638.png` (camera picture of Person A's face, never committed)
deleted; (3) Fable review skipped.

### Stage 9 (Sun 1:25 am -)
- 9.5 secret scan PASSED: the real OpenAI key and Telegram token are in no commit (checked against
  the values in .env, never printed); key/token patterns found only the deliberately fake
  "sk-this-key-..." (known false positive); .env, clips, databases, logs, model files and voice
  files were never committed; committed images are the diagram and stick-figure screenshots only.
  Note for Person A: all 71 commits carry a personal Gmail address, visible once the repo is public.
- README.md written (what it does, five rules, results, privacy, setup, tests, known limits).
- 9.4 fresh-clone test (clone into the scratchpad, README followed word for word, no keys): pip
  and npm installs OK. Found and fixed: `room-agent/models/` does not exist in a clone (empty folder)
  -> README downloads use `curl.exe --create-dirs` and the folder has a .gitkeep; `curl` in
  PowerShell 5.1 is not curl -> `curl.exe`; `start.bat` must be `.\start.bat` in PowerShell. The
  downloaded models are byte-identical to ours. Mock start: server, room agent and dashboard ready
  in 5 s.
- 9.7 pack 4 (docs/handoff/pack4/): Devpost facts per section, judge answers, "do not claim" list,
  3 real screenshots of the filmed incidents (team names replaced by "family member").
- CP9.3 PASSED (Sun ~1:45 am): Person A forwarded pack 4 to Person B ("sent"). Person A will send
  the video link for the README.
- 9.1 Fable review SKIPPED (Person A, Sun ~1:55 am). Reason: Fable already reviewed the escalation
  engine on Friday (9 findings, all fixed with tests, D-010); since then 282 tests, the 30-minute
  run and all 9 filmed takes behaved correctly; the video is filmed, so code changes now add risk
  without changing the submission. 9.2 cleanup: skipped for the same reason. 9.6 GIF: not made
  (the video and the pack 1/4 screenshots cover it).
- CP9.2: start.bat used for CP8.5 and every filming take (Person A); fresh clone started too.
- Stage 9 done; tagged stage-9-done.

### Stage 6 = the filming takes (checked from the database and logs, Sun 1:20 am)
Read with `scripts/incident_times.py`'s analysis (server started briefly with fake AI/Telegram).
| Time (Sat) | Incident | What happened | First word | Phone alert |
| --- | --- | --- | --- | --- |
| 20:58 | 125517_1 | silent twice -> Rule 1 -> Telegram -> Ack (Telegram) | 4.2 s | 36.9 s |
| 21:15 | 130356_1 | "Yes, I am okay." -> follow-up "No, nothing. I'm fine." -> resolved | 4.2 s | - |
| 21:22 | 130356_2 | "Yes, I am fine." -> "Let me have some water, please." -> gentle message | 3.6 s | - |
| 21:57 | 130356_3 | found_on_floor (60.1 s) -> "Yeah, I'm okay." -> "No, thank you" -> resolved | 61.2 s | - |
| 22:05 | 130356_4 | "Yes, I'm okay." -> "Now it's okay, I just slipped." -> resolved | 3.6 s | - |
| 22:09 | 130356_5 | "Yes, I just did." -> "Can I get some water, please?" -> gentle message | 3.6 s | - |
| 22:11 | 130356_6 | two unclear (loud, non-English transcripts) -> AI escalate -> 3 alerts -> Ack (dashboard) | 3.6 s | 38.9 s |
| 22:18 | 130356_8 | silent, then "Sorry, sorry." -> AI escalate -> Telegram -> Ack | 3.6 s | 36.8 s |
| 22:19 | 130356_9 | unclear (Chinese transcript of a loud sound), then silence -> Rule 1 -> Ack | 3.6 s | 36.9 s |
- Every take behaved safely: 4/4 no-answer takes alerted and were acknowledged; 5/5 okay takes
  resolved (2 with a water request -> gentle message; 3 said they needed nothing). No crash, no
  manual restart, no other incident (fast sits and the sofa raised nothing). A second fall during
  take 130356_6 was logged on the open incident (by design, D-010).
- Fall -> first spoken word 3.6-4.2 s (target < 6 s). Landing -> phone alert 36.8-38.9 s (target
  ~30 s; 30 and 33 s in the two earlier test runs). Why slower: the room was louder (-56 to -60
  dBFS), so the silences passed the loudness check (+13.8 dB over a 12 dB margin) and went to
  speech-to-text (~3 s each) before counting as no answer. Not a safety problem; pack 3 now says
  "under 40 seconds".
- Speech-to-text returned Turkish, Urdu and Chinese text for loud non-speech sounds although
  `stt_language` "en" IS passed (room-agent/voice/stt.py:56): the language hint is not a hard
  limit. Each time the AI read it as unclear -> asked again / escalated: safe. Known limit for the
  README.

## OVERNIGHT SUMMARY (Sat 14 Nov, 12:00 - 1:10 am)
Everything below was done without camera, microphone, speaker, OpenAI or Telegram (fakes only).
No contracts, hard rules or escalation timings were changed. Tests: 260 Python + 16 dashboard, all pass.

1. **Dashboard finished (Stages 5 and 7):** new Today page (the day as a coloured activity band,
   with buttons to look at earlier days) and Insights page (7 days of active minutes and stand-ups,
   the insight sentences, a "simulated history" label). Every page now has loading, offline and
   empty states. A browser check of every page at laptop and phone width found 0 problems after
   fixing two real bugs: a page opened during an incident showed "No steps yet", and a page that
   lost the server still said "All is well" (now a grey "Status unknown"; an alert stays red).
2. **Simulated week of history** for the Insights page (`scripts/seed_history.py`; the last 3 days
   are less active) and a demo reset (`scripts/reset_demo.py --yes`). The dev database is reset now.
3. **Both demo scenarios run end to end by themselves** (`scripts/sim_scenarios.py`, recorded falls,
   scripted answers): fast sit = no alarm; "Yes, I slipped" -> water request -> gentle message;
   silence -> alert -> Acknowledge. 17/17 checks pass. Fall -> first question 3.0 s; fall -> family
   alert 17.0 s.
4. **Reliability:** server killed and restarted -> room agent and dashboard back 1.1 s later.
   30-minute run: no crash, 90 incidents all acknowledged, 10,324 messages, 0 invalid, 0 errors;
   memory flat (server about 80 MB, +0.6%; room agent about 221 MB, +1.0%).
5. **Handoff pack 1 for Person B** in `docs/handoff/pack1/`: architecture diagram, 7 screenshots
   (placeholders from a test run), one-paragraph technical summary, facts they can use now.

**What I need from you this morning** (each step is short; I will guide you through them):
- Tell me what "the verification" in your 00:08 message was, so I can record it.
- CP5.1 + CP5.2: open the dashboard in Chrome and say whether it looks and reads right (5 min).
- CP4.2: Telegram live test with Person B (alert, Acknowledge button) (10 min).
- CP4.3: full loop with safe falls: Scenario 1 and Scenario 2 (15 min, the mat).
- Forward `docs/handoff/pack1/` to Person B. Person B: confirm the Telegram test message and list
  every Devpost submission field.
- Approve or change the draft schedule below.
Tags stage-4-done, stage-5-done and stage-7-done wait for those checkpoints.

Current stage: 4 (Telegram live test pending), 5 (look-and-feel checks pending), 7 (done, waiting
for your checks). Stages 2 and 3 done (tags stage-2-done, stage-3-done, Fri 10:40 pm).
OVERNIGHT (Fri ~10:45 pm - Sat 6 am): Person A asleep; mock-only work approved ("build overnight";
Person A available again at about 6 am). Rules: no camera/mic/speaker, no OpenAI or Telegram calls
(fakes only), no changes to contracts, hard rules or escalation timings, commit only tested work.
Last checkpoint passed: CP2.3 - 14 tuning clips (CP0.9 and CP1.1 still open; CP2.4 next)
Schedule: H0 = Fri 13 Nov 10:00 am HKT, deadline H48 = Sun 15 Nov 10:00 am (D-001).
Fri 2:10 pm = H4:10. Stage 3 is done except one live fall; the plan has Stage 3 ending at H16
(Sat 2 am), so about 11 h ahead even after a pause of about 5 h (9:05 am - 2:05 pm, usage limit).
CP1.1 done (Fri ~2:20 pm): final requirements in D-011 - presentation video under 3 min on
YouTube/Vimeo/Youku; public repo with meaningful commits Fri 10:00 - Sun 10:00.

## Saturday morning checkpoints (Person A awake from ~2:30 am)
- CP5.1 PASSED (Sat 2:43 am): practice incident on the laptop dashboard - amber, red, Acknowledge
  -> resolved. "Everything was easy to understand and read." Phone: not connected (only one
  dashboard was open; ProtonVPN / university Wi-Fi may block it - try again later).
  Fix from it: the alert step said "Family alerted on Telegram" while Telegram was off (84fce21).
- CP5.2 PASSED (Sat 7:13 am, real camera, live voice, real AI, Telegram off, demo mode on): fall
  -> "Are you okay?" -> heard "Yes, I am okay." -> AI follow-up -> heard "Thank you so much." -> AI
  resolve. "The dashboard jumped to the incident by itself and then went back to Live."
  (A first try at 7:09 also worked end to end; Person A restarted the step anyway.)
  Tagged stage-5-done.
- Timing seen in CP5.2 (per question): command -> end of playback about 6 s (phrases are 2.8-4.7 s
  long, so about 1.5-2 s of start-up), listen 6 / 8 s, speech-to-text 2.6-3.3 s, AI 1.5-2 s.
  Estimate for Scenario 2 (silence, no speech-to-text): 3 + 12 + 14 + ~1.5 = about 30 s from
  landing to the family alert - right at the 30 s target. Measure in CP4.3; if needed, cut the
  playback start-up (keep the audio device open / trim leading silence) before touching any timing.
- Morning plan approved by Person A (Sat ~7:20 am; Telegram and Person B unavailable for ~4 h):
  1 voice speed-up, 2 full falls test with Telegram off, 3 real sofa zone, 4 found-on-floor test,
  5 fresh test clips; then with Person B: CP4.2 Telegram and Stage 6.
- #1 DONE (e65a521): microphone switched on once per question (it cost ~0.75 s, twice) and phrases
  played without their trailing silence. Question start -> listening: 6.9 s -> 5.0 s on the real
  devices; listening now starts right when the phrase ends. No escalation timing changed.
- #2 DONE (Sat 7:25-7:28 am, real camera + voice + AI, Telegram off, demo mode on):
  Scenario 2 PASSED: silence twice -> Safety rule 1 -> alert (log) 25.8 s after the fall was
  confirmed = about 29 s after landing (target < 30 s); Acknowledge on the dashboard -> resolved.
  Scenario 1 PASSED with one extra question: the first answer was transcribed as "Ja sanokhe" ->
  AI "unclear" -> second question -> "Yes, I just slipped." -> follow-up -> "Some water, please."
  -> gentle message (log) "some water" -> resolved, no alert. Fall -> first question about 4 s.
  Fixes after #2: speech-to-text gets a prompt describing the expected short answers (okay words
  AND help words, no language set, so 救命 still works; checked on the real API); the room noise
  level is reused for 30 s, so the second question starts ~0.5 s sooner (config/voice.json).
- #3 = CP8.2 PASSED (Sat 7:37-7:39 am): safe-zone tool built (Stage 8.1, aa17d74); Person A drew
  the sofa in the debug window (config/zones.json, also saved on the server, shown on the
  dashboard). Lay on the sofa three times: 14 of 15 "lying" readings were inside the sofa zone
  (the 15th while getting up); no incident. (The polygon repeats its first corner as a 5th point -
  harmless.) Check in 8.3: the tuning clips' sofa hip position (~0.45, 0.39) is near the new top
  edge.
- #4 = CP8.3 PASSED (Sat 7:41 am): lay down slowly on the mat (sat first), stayed still;
  "found_on_floor" incident 60 s after lying down (target 60-65 s); check-in; "No, thank you" ->
  resolved; no alert. Answers from the floor get transcribed oddly ("Ya esta ok.", earlier
  "Ja sanokhe"): safe (worst case a second question), but consider stt language "en" (would lose
  救命) and check the Windows microphone volume - Person A to decide.
- 8.3: tuning clips re-scored with the drawn sofa zone: 6/6 falls, 0/8 false alarms (unchanged).
  THRESHOLDS FROZEN for the fresh test set (docs/accuracy.md).
- #5 = CP8.4 (Sat 7:45-8:00 am), settings frozen, each set scored once:
  first fresh set 2/6 falls, 0/6 false alarms - all 4 misses began already kneeling (no upright
  reference for the fast-fall rule; the screen said "kneel, then roll"). Person A chose to record a
  second fresh set of 6 falls starting from standing ("STAND until GO!"): 6/6, each ~3 s after
  landing. CLAIM (docs/accuracy.md): all 8 fresh falls from standing caught ~3 s after landing,
  0 false alarms in 6 normal movements; the 4 falls from kneeling are left to the 60-s floor rule.
  Known limit for the README/judges: a fall that starts from sitting or kneeling is found after 60 s.
- Found while reading CP8.5: the camera-offline family alert (SHOULD; config
  camera_offline_alert_s = 120) and the debug-window C key were never built. Built (Sat ~8:05-8:15,
  Person A approved): server/camera_watch.py (camera offline / room agent gone / never connected for
  120 s -> one family message; another when the camera is back; not an incident) and C in the debug
  window (pretend the camera is unplugged). Also fixed a zone test left failing by the drawn zone.
  Live check (Telegram off, log): server restarted 08:09:43 with no room agent -> family message
  at 08:11:43 (120 s); camera program started 08:12:11 -> "can see the living room again" at
  08:12:16. The Telegram version and the C key are checked in CP8.5 with Person A.
- Pack 3 for Person B written (docs/handoff/pack3/README.md): claim, table, timings, known limits.
  Person A to forward. Phone timing goes in pack 2 after the Telegram test.
- Sat ~8:20 am: Person A away from the room setup until ~11 am - camera program, server and
  dashboard stopped (no camera / microphone / speaker until then). Pack 1 and 3 forwarded to
  Person B by Person A. D-012: speech-to-text English only; microphone volume set to 100.
- 9.3 early: start.bat / stop.bat / start.sh (scripts/run_guardian.py: ordered start with readiness
  checks, auto-restart, --mock / --no-telegram / --demo) and scripts/preflight.py (green/red list,
  nothing sent, keys never shown). Both checked in mock mode.
- docs/handoff/video_shot_list.md for Person A and B: sources, before-every-take steps, 2:45 shot
  list from Section 29, honest shortening of waits.
- At ~11 am with Person B: CP4.2 Telegram, CP8.5 failure tests (C key, server restart), Stage 6
  (3 passes of each scenario, timings, pack 2 screenshots), then feature freeze and the video.
- CP4.2 PASSED (Sat 6:23 pm, practice mode, Telegram on): alert with picture 16 s after the
  practice fall; Acknowledge tapped on Telegram 30 s later -> resolved, caption updated.
  SECURITY: httpx logged request URLs (with the bot token) to logs/server.log; fixed (4c3704a),
  log scrubbed, disk and git history scanned clean. Person A revoked the old token with @BotFather
  and put a new one in .env (Sat ~6:30 pm); preflight: the bot can post to the group.
- CP8.5 PASSED (Sat 6:49-6:53 pm, start.bat, real camera, Telegram on): C at 18:49:32 -> family
  message in the group at 18:51:34; C again at 18:52:14 -> "can see the living room again"; server
  killed at 18:52:25 -> start script restarted it: server 3 s, room agent 3 s, dashboard 4 s
  (target < 10 s). Person A saw a green card during C: an old browser tab (opened before the
  2618acb fix); a fresh tab went grey ("Guardian cannot see the room") and back - confirmed.
- Stage 6 / filming (D-014). Before the D-013 fix: S1 pass (19:05, first word 4.2 s), S2 fail
  (19:06, prompt hallucination). After the fix: S2 pass at 19:16 (silence -> no answer twice ->
  Rule 1 -> Telegram alert -> Ack; landing -> phone ~30 s) and S2 pass at 19:43 (a sound in the room
  passed the loudness check but the transcript was empty - no hallucination; landing -> phone
  ~33 s). Telegram sendPhoto takes ~2.5 s. Pack 3 timing corrected. (These two incidents were
  deleted by a demo reset before I looked; checked from the logs.)
  Note: room noise measured -77 dBFS this morning (yesterday -59 to -61): quieter room or lower
  microphone gain - check Windows "Input volume" = 100 before the demo.

## Waiting for Person A
- CP0.9: check the Devpost team list (both must be eligible HK students); agree check-in times
  with Person B.
- Person B: confirm the Telegram test message in "Guardian Family (Test)"; read the final rules;
  list every field of the Devpost submission form (D-011).
- Person B (Sat morning): confirm the Telegram test message; list every Devpost submission field.
- Approve or change the draft schedule below.

## Draft revised schedule (NOT yet approved by Person A)
Idea: Person A sleeps both nights; Claude does mock-only work meanwhile (rules of Stage 3A apply);
the demo video is recorded on Saturday evening while everyone is fresh.

| When (HKT) | Hours | Work | Person A |
| --- | --- | --- | --- |
| Fri 12:45-3 am | before H0 | Stage 1 scaffold (mock only) | asleep |
| Fri 8-10 am | before H0 | CP1.2, CP0.9 | about 30 min |
| Fri 10 am-3 pm | H0-H5 | CP1.1; Stage 2 vision, tuning clips | about 75 min, falls |
| Fri 3-9 pm | H5-H11 | Stage 3 server, escalation, AI (Fable review) | about 25 min |
| Fri 9-11 pm | H11-H13 | Stage 4 part 1: voice (CP4.1) | about 15 min |
| Fri 11 pm-Sat 7 am | H13-H21 | Mock only: Stage 5 dashboard core, Stage 7 data layer | asleep |
| Sat 7-11 am | H21-H25 | Stage 4 Telegram (CP4.2 with Person B), full loop; CP5.1/5.2 | about 50 min |
| Sat 11 am-3 pm | H25-H29 | Stage 6 integration gate (3 passes each scenario) | 60-90 min, falls |
| Sat 3-7 pm | H29-H33 | Stage 8 safe zones, slow path, fresh clips, failure tests | about 70 min |
| Sat 7-10 pm | H33-H36 | Record the demo video (D-003); Stage 9 review; feature freeze 10 pm | about 60 min |
| Sat 10 pm-12 am | H36-H38 | Handoff pack 4, README draft | about 15 min |
| Sun 12-6 am | H38-H44 | Mock only: cleanup, docs, fresh-clone test (no features) | asleep |
| Sun 6-8 am | H44-H46 | Final checks; Person B submits by 8 am | with Person B |
| Sun 8-10 am | H46-H48 | Buffer; deadline 10 am | |

## Done
- Stage 0 (Thu 12 Nov, 10:35 pm - Fri 12:40 am): see the environment notes below.

## In progress
- CP2.4 live fall test (2 safe falls + 1 fast sit; ask for one fall with the head TOWARDS the
  camera) - POSTPONED by Person A (Fri ~8:05 am): "I will let you know when I am free".
  Then finish 2.8 with the dashboard open, tag stage-2-done, Stage 2 report.
- CP3.4 (one live fall starts a real incident) is combined with CP2.4: one session of falls,
  postponed by Person A ("later").
- Model back on Opus 5.5 (Fri ~2:20 pm). Stage 4 (voice and Telegram) started meanwhile.

## CP2.4 + CP3.4 live fall test PASSED (Fri 10:35 pm, final room, `--guide falls`, --no-voice)
- Fall 1 (across the picture): fall_detected (fast_fall) 3.1 s after going down; torso ratio 0.24.
- Fall 2 (head pointing to the laptop - the direction no clip covered): fall_detected 3.1 s after
  going down; torso ratio -0.86 (head below the hips in the picture), tilt only 23 deg.
- Fast sit on the chair: sitting, no alarm. Person up again -> "recovered" both times.
- Both falls opened real incidents on the server (state checkin_1, speak sent), acknowledged
  by the test watcher -> resolved. 43 activity rows stored (incl. 9 "fallen"); no server errors.
- The guide marked fall 1 "standing" only because Person A fell at the very end of that step.
- => Stage 2 and Stage 3 completion criteria met (waiting for Person A's "continue").

## Overnight work log (mock-only)
- 4.4 Telegram (code + fakes only; the live test is CP4.2 with Person B): `server/notify.py`
  TelegramNotifier - sendPhoto with the skeleton picture, caption (room, local time, heard, why,
  [TEST] for simulated incidents, "Reminder n" on repeats) and an inline Acknowledge button;
  long polling for button presses (only from TELEGRAM_CHAT_ID; others ignored and answered);
  acknowledging anywhere edits every alert of the incident to "Acknowledged by ..." and removes
  the button; gentle messages for requests; errors never contain the token. make_notifier():
  Telegram when token + chat ID are set, log otherwise, GUARDIAN_FAKE_TELEGRAM=1 forces the log.
  tests/conftest.py forces fake AI and fake Telegram for every test run. Bugs found by the tests:
  Telegram's own `timeout` parameter clashed with the HTTP timeout argument; an instant empty
  answer made polling spin (now waits 1 s). tests/test_notify.py (13).
- Stage 5 dashboard core (5.1-5.5): Live page (big status card: green "All is well" / amber
  "Checking in..." / red "ALERT - family notified"; live skeleton canvas with the safe zones;
  current activity; camera status; the open incident's steps as they happen), alert panel (what
  was heard, why, big Acknowledge button -> POST /incidents/{id}/ack; 409 = already handled;
  beeping alarm once "Sound on" is clicked), Incidents list and Incident detail (every step in
  plain English: Guardian asked / Heard / AI or Safety rule N: decision + reason / family alerted /
  acknowledged by), demo mode (?demo=1 or header button: follows the open incident, back to Live
  8 s after it ends), Settings (who is told, sensitivity, safe zones - read-only; "Simulate a
  fall"). Server: GET /zones falls back to config/zones.json; GET /settings (read-only summary).
  vitest added (dashboard only): 8 tests, wording + every component rendered with sample data.
  Live end-to-end (mock agent, no voice, fake AI and Telegram): monitoring > checkin_1 >
  checkin_2 > escalate > acknowledged like the button > resolved; 265 messages, 0 invalid; all
  pages compile in the dev server; REST + CORS OK. Not yet seen in a real browser: CP5.1/CP5.2
  (Person A) and the Chrome QA pass (5.6).
- 7.2 + 7.7 `scripts/seed_history.py` (7 days before today, rows 10 s apart, all simulated=True,
  the last 3 days less active: about 150 -> 40-60 active min, 5 -> 3-4 stand-ups, longest still
  period 1.5-2 h -> 3-4 h) and `scripts/reset_demo.py --yes` (acknowledges an open incident through
  a running server, deletes all incidents and activity, re-seeds).
- 7.3-7.5 GET /analytics/timeline?date= (one local day as activity segments; gaps stay gaps).
  Today page: activity band 00-24 with a "now" line, hover/tap details, three numbers, table view,
  previous/next day. Insights page: insight sentences, active minutes per day (7-day average line)
  and stand-ups per day (one measure per chart), table, "Earlier days: simulated history" label.
  Band colours checked for colour-blind safety in every pairing (blue / orange / aqua; "on the
  floor" uses the alert red with a warning sign and label).
- 7.1 `scripts/sim_scenarios.py`: real server (throwaway DB, fake AI, recording fake Telegram), real
  vision code on recorded clips (fast processing), scripted replies. 17/17 checks pass on
  tune_fall_forward_01 and on tune_fall_sideways_01 (fast sit + Scenario 1 + Scenario 2), again after
  the later changes. Timings include the 3 s fall confirmation (clip time is skipped in fast mode).
- 7.6 + 5.6: shared loading / offline / empty states on every page. QA in headless Edge (DevTools
  protocol; every page loaded from scratch at 1280 px and 390 px; console, exceptions, failed
  requests, sideways scroll): 0 problems after the fixes. Found and fixed: Live showed "No steps
  yet" when opened mid-incident (now reads the incident's stored steps); offline Live still said
  "All is well" (now "Status unknown"; alerts stay red, "(last known)"); missing favicon; a
  development-only socket warning.
- 7.8 `scripts/soak.py restart`: room agent and dashboard client back 1.1 s after the server came
  back (limit 10 s); 0 invalid messages. `scripts/soak.py soak` (30 min, Sat
  ~1:10-1:40 am, looped tune_fall_forward_01, no voice, every alert acknowledged): PASS - no crash,
  90 incidents / 90 acknowledged, 10,324 dashboard messages, 0 invalid, 0 handler errors, 0
  rejected, 1 dashboard connection. Memory (first third -> last third after a 2-min warm-up):
  server 80.4 -> 80.9 MB (+0.6%), room agent 220.2 -> 222.3 MB (+1.0%). An earlier 30-min run
  also passed but measured only the .venv launcher (about 4 MB); fixed in bc2205a.
  New: room agent `--loop` (replays a clip again and again), server `GUARDIAN_DB` (another DB file).
- Handoff pack 1 (`docs/handoff/pack1/`): architecture diagram (PNG + SVG), 7 screenshots from a
  mock run (placeholders: the real-camera ones go in pack 2), technical summary, usable facts.

## Done in Stage 4 (Fri 2:25 pm -)
- 4.1 Speaking `voice/tts.py`: fixed phrases (config/escalation.json) generated with OpenAI
  (gpt-4o-mini-tts, coral, calm instructions in config/voice.json) and kept as WAV in
  room-agent/voice/phrases/ (git-ignored): 5 phrases, 2.8-4.7 s each. Other sentences on demand;
  the laptop's own voice (pyttsx3, checked: works from a thread) when OpenAI fails.
- 4.2 Listening `voice/stt.py`: room noise measured 0.5 s before each question, recording starts
  0.2 s after the question ends, speech = loudest 0.5 s at least 12 dB over the noise and over
  -50 dBFS; silence is never sent to OpenAI; transcription with gpt-4o-mini-transcribe.
- 4.3 (part) `voice/live.py` LiveVoice / SilentVoice; commands use voice.ask(); main.py: real voice
  for --camera, stub for mock and clips (--live-voice to use the real one), --no-voice silent;
  phrases prepared in the background at start-up; Space in the debug window = "I'm okay".
  `scripts/voice_check.py` for CP4.1. tests/test_voice.py (13); 241 tests pass.
- CP4.1 voice test (final room), Fri ~3:00-3:20 pm:
  run 1: nothing heard - the microphone was muted (-97 dBFS, 77% exact zeros; privacy allowed;
  same default device). Person A unmuted it.
  run 2: "I am okay." OK; a +17 dB sound in the silent round (no words, probably movement);
  "Help" not counted although +20 dB over the room.
  run 3 (with per-half-second levels): "Yes, I am okay." at -37 dBFS; silence max -66; "Help" -54;
  room -75..-79 before the question, about -67 after it. No echo of Guardian's own voice (the
  first half second after a question is quiet). Levels are ~15 dB lower than last night's test
  (old room: room -60, speech -30): microphone gain lower after unmuting?
  Fix from the data: min_speech_dbfs -50 -> -60 (only meant to reject a dead/muted mic at -97).
  On run 3's numbers: answer +23 dB over the threshold, "Help" +5.7 dB, silence -6.2 dB.
  run 4 (confirmation, -60 floor): "I am okay." (-37.5 dBFS) OK; silence OK; "Help" NOT recorded at
  all (max -65 = background) - Person A thinks they said "Help" before the question had finished.
  Guardian only listens after its own question (so it never hears itself).
  CONCLUDED FOR NOW by Person A (Fri ~3:30 pm): answers understood 3/3 ("I am okay." x2,
  "Yes, I am okay."), silence detected, the question easy to hear from the mat. A "Help" said
  over the question is missed; the safety net holds (no answer -> second question -> Rule 1).
  Open: barge-in listening (listen while asking, stop talking when a voice is heard) - option for
  later; the plan's "'Help' escalates at once" is met only when said after the question.

## Done in Stage 3 (Fri 8:15 am -)
- 3.1 Database: all five tables (activity_log, incidents, incident_events, contacts, zones) with
  helpers; tests/test_db.py.
- 3.3-3.4 Escalation engine `server/escalation.py`: states, the five hard rules in code, no Resolved
  while on the floor unless acknowledged, re-alerts every 2 min, stale AI answers dropped (epoch),
  missing replies (room offline) count as no answer after listen + reply_grace_s, storage failures
  never block an alert (_SafeRecorder), notifier/room failures logged. config/escalation.json:
  phrases, followup_listen_s 8, reply_grace_s 15 (existing values unchanged).
  tests/test_escalation.py: the 10 required tests + edge cases (27).
- 3.5 AI agent `server/agent.py`: OpenAIAgent (strict JSON schema whose action list is limited to the
  state, reasoning_effort none, no retries) and FakeAgent (word rules); `make_agent()` uses the fake
  without a key or with GUARDIAN_FAKE_AI=1. No OpenAI call made yet (live test = 3.10 / CP3.3).
- 3.2 API `server/app.py`: engine wired to the room WebSocket (commands), SQLite and dashboards;
  voice replies handled beside the receive loop (the AI may take 5 s); tick every 0.5 s; routes
  /incidents, /incidents/{id}, /incidents/{id}/ack (404/409), /activity, /zones, /contacts (GET and
  POST), /simulate/fall. `server/notify.py`: LogNotifier until Stage 4.
- 181 tests pass. Real uvicorn + mock room agent (fake AI): fall -> check-in -> "I'm okay" ->
  follow-up -> resolved in 14 s, every step stored.
- 3.6 Analytics `server/analytics.py` + GET /analytics/daily (minutes per activity per local day,
  sit-to-stand, longest still period, today vs the same hours of the last 7 days, insight
  sentences); config/analytics.json (UTC+8). 3.7 `server/snapshot.py`: skeleton PNG from
  keypoints only. 195 tests pass.
- 3.10 Live AI test (`scripts/ai_check.py`, gpt-5.4-mini). First run: 2 poor calls - "I'm okay, I
  just slipped" -> escalate ("slipped may mean injury") and "yes" -> ask again ("too brief").
  Fix: the question that was asked now goes to the AI (`question` in the context) and the prompt
  says a mentioned slip/fall is expected, a plain "yes" means okay, "no" means escalate. Second
  run: all six samples sensible (follow_up, code ask_again, rule 2, rule 2, follow_up, ask_again),
  slowest 1.8 s; `--more`: 9/9 extra replies as expected (no, dizzy, swelling wrist -> escalate).
- 3.11 Wrong-key test (`ai_check.py --wrong-key`, key only in that process): every AI failure ->
  Rule 4; silent scenario escalates (rules 4 then 1) and the alert is sent. PASSED.
- CP3.3 PASSED (Fri ~8:50 am): Person A checked the six samples and nine extra replies: "ok".
- 3.9 Fable 5.2 review of `server/escalation.py` and its tests (Fri ~8:55-9:10 am; documented and
  committed Fri ~2:10 pm after a usage-limit pause). 3 serious + 6 medium findings, reproduced
  with throwaway experiments, listed for Person A, approved ("fix all") and fixed: see D-009
  (numbered questions, contract addition) and D-010. Engine restructured so notifier and room
  calls run outside the lock ("effects"). 228 tests pass (33 new). Live AI check after the prompt
  change: six samples and 9/9 extra replies still right, slowest 1.8 s. Real restart test: server
  killed during a check-in -> same incident restored as an alert -> acknowledged -> resolved.
- The development database was deleted twice during this work (20 unfinished incidents from
  earlier mock and clip runs would have been re-opened as alerts). It only held test data.
- Left in Stage 3: 3.12 / CP3.4 one live fall -> incident (combine with the postponed CP2.4).

## Done in Stage 2 (continued, Fri 7:35-8:00 am, on Fable 5.2)
- 2.5 Fall state machine: `vision/fall.py` (UprightReference, posture classes up/down/low/resting/
  other, fast path, slow path, fallen-until-upright), `vision/zones.py` (safe zones), `vision/
  analyzer.py` (activity + falls in one object, shared by the live loop and the clip scoring),
  extra features (torso length and rise, feet below hips, in_view). Rule form changed from the
  plan after measuring the clips: see D-007. `tests/test_fall.py` 21 tests.
- 2.6 Clip evaluation: `vision/clipdata.py` (keypoints per clip, cached in clips/.cache/),
  `scripts/eval_clips.py` (--set, --write, --no-zones, --trace). Tuning set: 6/6 falls caught,
  0/8 false alarms, detection 3.0-3.1 s after landing; 1 false alarm (lie_sofa_02) without the
  provisional sofa zone (D-008). Thresholds moved 10-20% either way: same result. Table in
  `docs/accuracy.md`.
- 2.8 (part): `camera_mode.py` now sends `fall_detected` (incident ids `inc_<start>_<n>`) and
  `posture_update` on every label change after a fall, and the activity message carries the zone.
  Debug window: zones in blue, "POSSIBLE FALL..." in amber, FALLEN in red. Replayed
  fall_forward_02, fast_sit_01 and fall_sideways_01 through `main.py --clip` into the real server:
  incidents opened for the two falls only, posture_update fallen received, 0 rejected messages.
  131 tests pass.
- Replaying the recorded activity checks: the lie-downs on the mat raise `fast_fall`, because
  Person A went from standing to lying in 1-2.5 s. That is the intended behaviour (D-007).

## Tuning clips recorded (clips/, git-ignored; final room)
- 8/8 normal clips (Fri ~07:10-07:25): fast_sit x2, lie_sofa x2, bend x2, kneel x2. Replayed with
  current rules, person in view 99-100%: fast_sit -> sitting at 1.5-1.8 s; lie_sofa -> lying;
  kneel -> brief sitting/standing; bend_02 -> sitting 2 s; bend_01 -> LYING for 2.2 s (side-on bend:
  wide box, head low). Not a fall by the plan's rules (needs a fast drop, then 3 s low), but the
  fall logic in 2.5 must stay quiet on bend_01.
- 6/6 fall clips (Fri ~07:30), CP2.3 PASSED (14 clips, the plan's minimum). Each pair: _01 across
  the picture, _02 towards/away from the camera. Final label with current ACTIVITY rules
  (person in view 99-100%): forward_01 lying, backward_01 lying, sideways_01 lying;
  forward_02 STANDING, backward_02 SITTING, sideways_02 SITTING.
  => Falls along the camera's line of sight are the hard case: from up high the body looks short
     and upright (torso tilt < 60, box narrow). 2.5 must catch them (plan target: >= 5 of 6
     tuning falls, <= 1 alarm on the 8 normal clips), e.g. with how far the hips drop and how
     much the body's height shrinks compared with just before the fall, not only the tilt.
  Per-frame keypoints of every clip replay are in room-agent/logs/ (git-ignored).

## FINAL ROOM (Fri ~6:45 am): the team moved to the room where the demo video will be filmed
- Set up by Person A: laptop up high, sofa, chair and mat in view. Audio from the mat (CP0.6)
  still to re-check in this room (Stage 4 at the latest).
- First real clip (tune_fast_sit_01, 06:40) moved to clips/rejected/ (chair was later moved). It was
  first misread as a "phantom person"; after the second clip it is clear it was Person A sitting in
  the chair at its earlier, closer spot (legs cut off at the image bottom), labelled "standing"
  because the knee angle was not usable. Lesson: whole-frame pixel change is tiny when the person
  is small in the picture - do not use it to judge whether someone moved.
- Recorder wording made clearer: "GET READY ... wait for GO", then a big red "GO!" while recording.
- CP2.3a recorder test PASSED (07:10): tune_fast_sit_01 recorded (300 frames, 29.9 FPS) and replayed:
  standing -> sitting at 1.5 s. Needed a new sitting cue: from this chair position the bent knee
  looked > 120 deg, but the thighs pointed 46 deg from straight down (standing/walking 2-4 deg,
  sitting 46-49 deg even with the ankles washed out). Rule: sitting = knee < sitting_knee_deg
  OR thigh > sitting_thigh_deg 30. Replays: old room sitting 55% -> 81%, final room 06:58 sitting
  49% -> 98%, 07:05 still 5/5. 103 tests pass.
- CP2.1 (new room, `--guide view`) PASSED 06:55: empty room 100% absent (no phantom person);
  Person A confirms whole body incl. feet, standing and lying.
- CP2.2 (new room): run 06:58 2/5 - on the chair the ankles vanished (Person A: auto-exposure
  washed out the feet when far from the camera) and lying with the head AWAY from the camera
  looked like sitting (torso foreshortened to 0.56x, tilted only 51 deg). Run 07:05 4/5 - lying
  (head away, legs straight) measured 59-61 deg, just under lying_torso_deg 60 -> "standing".
  Fix (data from 3 runs): lying = torso > 60 deg OR (bbox w/h > lying_box_ratio 1.0 AND head less
  than lying_head_rise 1.2 torso lengths above the hips). Lying 1.18-1.72 / 0.46-1.01; standing,
  walking, sitting 0.28-0.60 / 1.40-1.49. Replaying the recorded keypoints with the new rule:
  run 07:05 5/5 (lying 100%), old-room run still 5/5. CP2.2 PASSED in the final room.
- `--guide activity` get-ready step is now 15 s (Person A was running 5-8 s late).

## Done in Stage 2
- 2.1 Pose capture: `vision/pose.py` (Camera, PoseDetector in video mode, C++ start-up chatter
  hidden), `vision/debug_view.py`, `camera_mode.py` (worker thread, pose 5 Hz, heartbeat 5 s),
  `main.py --camera N [--no-window] [--seconds S]`. config/vision.json now uses the FULL model
  (16-18 ms/frame here; easy to switch back). Frame pacing averages target_fps: a naive
  "skip if < 1/15 s since last" dropped every other frame of the ~22 FPS camera (9.9 FPS);
  fixed to 15.2 FPS. CP2.1 PASSED: whole body incl. feet, standing at the far wall and lying
  on the mat (45 s run: 14.8 FPS, person in 81% of frames - the rest is Person A out of view at
  the start).
- 2.2 Features: `vision/features.py` FeatureTracker -> torso angle, knee angle (more bent knee),
  hip position, hip speed down (body-heights/s over speed_window_s), sideways hip shift over 1 s
  (body-widths), bbox ratio, skeleton length + rolling max over scale_window_s as the speed scale.
  New config keys: min_keypoint_visibility 0.5, speed_window_s 0.3, scale_window_s 3.0.
  Mock "sitting" now bends the knees. `tests/test_features.py` 11 passed (86 total).
- 2.3 Activity labels: `vision/activity.py` (rules of Section 13 + majority vote over vote_frames;
  unclear frames do not vote; ties keep the current label), wired into `camera_mode.py`
  (activity message every 2 s, label changes logged with timestamps, label and features in the
  debug window). `guide.py` + `main.py --guide activity` show CP2.2's timed instructions and print
  a summary; `--log-frames` writes a per-frame CSV with features and keypoints (points only,
  never pixels) to `room-agent/logs/` (git-ignored). `tests/test_activity.py` 7 passed (94 total).
- CP2.2 run 1 (02:00): person found only in the first 8 s - the view or light had changed
  (laptop moved or lights dimmed); not a code problem.
- CP2.2 run 2 (02:02): 4/5 - sitting seen as standing. Cause: from up high, knees/ankles had
  visibility < 0.5, so no knee angle was ever measured while standing or sitting. Fix (the one
  rule adjustment the plan allows): new config key min_leg_visibility 0.3 for knees/ankles
  (torso still needs 0.5); the debug window already drew legs at 0.3 and Person A confirmed the
  legs were covered in CP2.1.
- CP2.2 run 3 (02:12) PASSED 5/5: standing 100%, walking 83%, sitting 55% (knee median 93 deg
  when seen), lying 100%, absent 32% (most common label while leaving; see open issues).
- 2.4 Clip recorder and replay (Fri 6-6:40 am): `vision/sources.py` (CameraSource, ClipSource;
  clip times from a .json sidecar with every frame's real time, else the header FPS);
  `camera_mode.VisionLoop` now takes a source and runs on the source's clock, so a replayed clip
  behaves as it did live; `main.py --clip FILE [--fast]`; `scripts/record_clips.py` (auto-advancing
  instructions for a laptop mounted high: 12 s to get ready, 25 s after a fall, 5 s countdown,
  10 s recording; text never burned into the video; existing clips skipped; --only, --max, keys
  SPACE/P/R/S/Q); `scripts/replay_clip.py` wrapper. `tests/test_clips.py` 6 passed (100 total);
  synthetic clip replayed through main.py at 14.9 FPS.

## Done in Stage 1
- 1.2 Repository: layout, CLAUDE.md/AGENTS.md, config, docs; first commit pushed to GitHub (34697e2).
- 1.3 Contracts: 13 message schemas + AI decision + common definitions; 34 example messages;
  `tests/test_contracts.py` 53 passed. Dashboard interpretation recorded as D-006.
- 1.4 Server skeleton: `server/app.py` (WS /ws/room + /ws/dashboard, GET /status,
  POST /simulate/fall, CORS for port 5173, contracts checked both ways), `server/db.py`
  (activity_log, incidents; `incidents.simulated` added so simulated falls can be left out of
  statistics). `tests/test_api.py` 10 passed; real uvicorn answered /status and /simulate/fall.
  Lessons: this SQLModel version needs timezone-aware datetimes (store UTC with tzinfo); an error
  while handling one message is logged and counted (`handler_errors`) instead of dropping the
  room agent.
- 1.5 Room agent `main.py --mock`: `mockroom.py` (scripted person, fake skeleton, fake fall every
  60 s), `server_link.py` (contract checks, reconnect with 1-3 s backoff, incident messages kept
  while offline), `commands.py` + `voice/stub.py`. `tests/test_room_mock.py` 12 passed (75 total).
  Live run against uvicorn: agent started before the server and connected when it came up;
  after a server kill it reconnected in about 5 s (including server start-up) and delivered the
  posture_update it had kept while offline.
- 1.6 Dashboard skeleton: Vite 8 + React 19 + Tailwind 4 (+ Recharts 3 installed), hand-written
  (no interactive generator). `useGuardianSocket` connects to ws://<page host>:8000/ws/dashboard
  and reconnects by itself; the page shows connection, current activity and state, camera/FPS
  and recent events. `npm run build` OK.
- 1.7 Automated loop check (server + dashboard dev server + mock agent): fall event reached a
  dashboard listener 15 ms after it was sent (limit 1 s); pose 4.7/s; 82 messages, all valid;
  no server errors.
- CP1.2 PASSED (Fri 1:47 am): Person A saw "Connected" and a "Fall detected" event in Chrome.
- Still open from Stage 1: step 1.1 / CP1.1 (final requirements) happens at kickoff, 10 am.

## Open issues
- Voice: "Help" said WHILE Guardian is still asking is not heard (Guardian listens only after its
  question). Still escalates via the second check-in and Rule 1, about 15 s later. Fix option:
  barge-in listening. Also: microphone levels were ~15 dB lower after unmuting; keep Windows
  "Input volume" at 100 (pre-demo checklist).
- Known false positive for the Stage 9 secret scan: commit d01a72e (scripts/ai_check.py line 45)
  contains a DELIBERATELY FAKE key-shaped string ("sk-this-key-is-..."), used for the wrong-key
  test. Checked Fri ~8:45 am: the real OpenAI key and Telegram token appear nowhere in the git
  history. The placeholder was changed in the next commit; commits now abort if the scan matches.
- Camera auto-exposure (final room): the image brightness changes when Person A is far from the
  camera and the feet can wash out. If it hurts the clips, try fixing the exposure in
  vision/pose.py (CAP_PROP_AUTO_EXPOSURE / CAP_PROP_EXPOSURE with DirectShow).
- Fall detection, not yet proven: (1) a fall with the head towards the camera (no clip; rule
  exists); (2) live falls (CP2.4); (3) the fresh test set (Stage 8) - the only honest figure.
- The ACTIVITY label can still say "sitting" or "standing" for someone lying along the camera's
  line of sight before the fall is confirmed (then it becomes "fallen"). The fall detector does not
  depend on that label. Consider using the detector's posture for the "lying" label in Stage 8.
- A bend can still log a harmless "stumble" while the person straightens up (tune_bend_01).
- Edge of the picture: bodies whose shoulders or hips are within 3% of the image edge are ignored
  by the fall detector (`edge_margin`); partly visible bodies gave 1-2 s "lying" blips earlier.
- Standing at 2-3 m: knee angle still not measured (ankles below min_leg_visibility) - harmless
  for labels (falls through to standing), but do not rely on legs while standing.
- Dashboard (minor): the "sofa (safe zone)" label is wider than the small provisional sofa zone on
  the skeleton view; it will fit once the real zone is drawn (Stage 8).
- The Insights comparison sentence ("Active N% less than the 7-day average so far today") only
  appears once today has data; just after midnight only the stand-up sentence shows. Take the final
  Insights screenshots in the daytime.
- Phone access (Stage 5): ProtonVPN is on and the laptop is on what looks like a university
  Wi-Fi (158.182.x.x). Either can block a phone from reaching the dashboard; plan: VPN off and/or
  a phone hotspot for demo devices.

## Measured
- Pose speed (built-in camera, 640x480): lite 20.7 FPS (11.7 ms/frame); full 20.7-25.3 FPS
  (16-18 ms/frame). The camera, not the CPU, is the limit. Proposal: full model in Stage 2.
- From up high: lying recognised (torso > 60 deg, max 90 deg); person found 87-100% of frames.
- AI decision (gpt-5.4-mini, reasoning_effort=none, strict JSON schema): 1.06 s median, 3/3 correct.
- TTS gpt-4o-mini-tts (coral): 1.5-3.5 s per phrase. STT gpt-4o-mini-transcribe: 1.0-3.0 s.
- Audio from the mat (~3 m): question easy to hear; "Yes, I'm okay" +28.8 dB over room noise,
  transcribed exactly.

## Stage 0 environment notes (moved from ../setup-checks/ENVIRONMENT.md)
- Windows 11 Home, native (not WSL). Intel Core Ultra 7 255H, 15.4 GB RAM, no discrete GPU.
- Git 2.53 (identity set; Git Credential Manager), Node.js 24.19 + npm 11.17,
  Python 3.11.9 next to 3.14 (3.11 is not on PATH: use `py -3.11` or `.venv\Scripts\python.exe`).
- `.venv`: packages pinned in `requirements.txt` (mediapipe 1.2.3, opencv-contrib-python 5.0.0.93, D-005).
- MediaPipe prints many harmless INFO/WARNING lines at start-up: silence them in Stage 2.
- Pose models in `room-agent/models/` (git-ignored): pose_landmarker_lite.task, pose_landmarker_full.task.
- OpenAI: models in `.env`. GPT-5.x calls MUST pass reasoning_effort="none" or they get slower.
- Telegram: bot @guardian_buhack_bot ("Guardian Alerts"), privacy mode on (fine: Guardian only
  sends and receives button presses). Group "Guardian Family (Test)" is a supergroup, chat ID in
  `.env`. In the group, commands must name the bot: `/start@guardian_buhack_bot`.
  Test message received by Person A; Person B to confirm.
- GitHub: https://github.com/SomeRadGuy/guardian.git (private).
- Camera: built-in only (index 0); laptop mounted high (D-004).
- Audio: built-in Realtek speakers and Intel Smart Sound microphone array.
  KEEP Windows mic "Input volume" at 100 (add to the pre-demo checklist and preflight).
- Voice lesson for Stage 4: people answer the moment the question ends. Start listening about
  0.2 s after playback ends - no pause, no beep. Room noise here is about -59 to -61 dBFS and
  speech from the mat about +29 dB above it, so a `heard_speech` threshold of about +10-12 dB
  over the measured noise leaves a wide margin.
- Throwaway check scripts stay in `D:\setup-checks\` (never committed): check_imports.py,
  bench_openai.py, check_telegram.py, camera_check.py, audio_check.py, set_env.py.

## Next step
- Stage 10 (submission on MentorMates, D-015): the 5-item list in STATUS at the top. Next: Person A makes the repo public (CP10.4).
