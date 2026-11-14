# BUHack 2.0 – Fall-Detection Guardian: Development Instructions for Claude Code

*Stage-by-stage build plan, revised for a two-person team with Claude Code as the primary developer*

*Version 2.0 · 12 November 2026 · Replaces the four-person plan (version 1) · All times are Hong Kong time (HKT)*

> **Who reads what**
>
> - **Claude Code:** read the whole document, in order, before doing anything. Parts I to IV and the appendices are your instructions.
> - **Person A (project owner):** read “Start here” on the next page and the glossary in Appendix D. After that, follow Claude’s checkpoints; you do not need to read the technical parts.
> - **Person B (presentation lead):** read Sections 2, 3 and 17 (your timeline is in Section 17), then Part IV: the demo script, risks and judge questions, and the submission checklist.
>

> **How to read the labels**
>
> - **HUMAN CHECKPOINT** boxes: things only Person A (or Person B) can do. Claude stops and waits until they reply.
> - **Completion criteria** boxes: what Claude must verify before a stage counts as finished.
> - **Changed from the original plan** boxes and Section 5: where this version differs from version 1, and why.
> - **Safety** boxes: rules that protect people, privacy or credentials. They are never skipped.
>

# Start here (Person A)

This document makes Claude Code the lead developer of Guardian. You supervise it, give it what it needs from the real world, and check the results. You never have to write code.

1. Make a project folder, for example `C:\guardian` on Windows or `~/guardian` on a Mac. Inside it, make a folder called `docs` and put this file in it. If you also have the Markdown copy (`BUILD_PLAN.md`), put it in `docs` too: Claude Code reads Markdown more easily than Word.
2. Open a terminal in the project folder and start Claude Code by typing `claude`. Type `/model` and choose Opus 5.5.
3. Copy prompt A1 from Appendix A, paste it into Claude Code and press Enter.
4. Claude summarises the plan and then guides you one step at a time. When it shows a **HUMAN CHECKPOINT**, do the steps and reply “done”, or paste what it asks for. It waits for you.
5. Never paste passwords, API keys or tokens into the chat. Claude tells you which file to open and where to paste them.
6. Before the official kickoff, only do Stage 0 (setup). Claude must not write project code until the hackathon starts, unless the rules allow it.

> **If you use Windows**
>
> Run Claude Code and Guardian in normal Windows (PowerShell or Windows Terminal), not inside WSL. Programs inside WSL cannot easily use the webcam and the microphone.
>

**What a normal step looks like.** Claude builds something, tests it, tells you what it did, and then either continues or shows a HUMAN CHECKPOINT. A checkpoint has at most three numbered steps, says what you should see, and says what to reply.

**If anything is unclear,** say to Claude: “Explain that more simply.” That is always a fine thing to ask. If you feel lost, paste prompt A6.

**If you close Claude Code** (or it crashes, or you come back after sleeping), start it again in the project folder and paste prompt A3. Claude reads its progress log and continues where it stopped.

# Contents

- **Part I – Orientation for Claude Code**
   - 1\. Your mission
   - 2\. Team and responsibilities
   - 3\. Hackathon facts you must respect
   - 4\. Product summary
   - 5\. Changes from the original four-person plan
   - 6\. Development rules
   - 7\. Models and tools
   - 8\. Message templates and progress log
- **Part II – Technical specification**
   - 9\. Architecture and tech stack
   - 10\. Repository layout
   - 11\. Configuration
   - 12\. Interface contracts and data model
   - 13\. Vision and detection specification
   - 14\. Escalation flow and the five hard rules
   - 15\. Privacy and safety requirements
   - 16\. Scope: MUST, SHOULD, OPTIONAL, WON’T
- **Part III – Stage-by-stage instructions**
   - 17\. Schedule overview
   - 18\. Stage 0 – Preliminary setup (Thu 12 – Fri 13 Nov, before kickoff)
   - 19\. Stage 1 – Scaffold, contracts and mocks (H0–H2 · Fri 8–10 pm)
   - 20\. Stage 2 – Vision: pose, activity and fall detection (H2–H7 · Fri 10 pm – Sat 3 am)
   - 21\. Stage 3 – Server, escalation engine and AI decisions (H7–H16 · Sat 3 am – 12 pm)
   - 22\. Stage 4 – Voice check-ins and Telegram alerts (H16–H20 · Sat 12–4 pm)
   - 23\. Stage 5 – Dashboard core (H20–H24 · Sat 4–8 pm)
   - 24\. Stage 6 – Integration gate (H24–H28 · Sat 8 pm – Sun 12 am)
   - 25\. Stage 7 – Data layer and polish (H28–H34 · Sun 12–6 am, mock-only)
   - 26\. Stage 8 – Accuracy, safe zones and reliability (H34–H40 · Sun 6 am – 12 pm)
   - 27\. Stage 9 – Review and documentation support (H40–H43 · Sun 12–3 pm)
   - 28\. Stage 10 – Rehearsal, backup video and submission (H43–H46 · Sun 3–6 pm; deadline H48)
- **Part IV – Demo, risks and submission**
   - 29\. Live demo script (3 minutes)
   - 30\. Risks and fallbacks
   - 31\. Submission and deliverables
- **Appendices**
   - Appendix A – Prompts for Person A to paste into Claude Code
   - Appendix B – CLAUDE.md template
   - Appendix C – Pre-demo checklist
   - Appendix D – Plain-English glossary for Person A
   - Appendix E – References

# Part I – Orientation for Claude Code

Part I tells you who you are working with, what the hackathon requires, what changed from the original plan, and the rules you follow for the whole project.

## 1. Your mission

You are the primary software developer for **Guardian**, a privacy-first fall-detection system for elderly people living alone, built for the BUHack 2.0 hackathon. You write, test, debug and integrate all of the software: computer vision, voice, backend, database, AI integration, Telegram alerts and the React dashboard.

You cannot act in the physical world. Person A installs software, creates accounts, adds credentials, connects and positions hardware, and performs every physical test. Your job is to lead: plan the work, build it in small tested steps, and ask Person A for exactly what you need, at the right moment, in plain language.

**Success means:** by Sunday 15 November, 6:00 pm HKT, the project is submitted on Devpost; both demo scenarios run reliably on the live camera; the code is tested, clean and documented; and Person B has every technical input for the README, the Devpost page and the slides.

**How you work, in one line:** understand everything first, plan, build one small piece, test it, report, ask when you need a human, and never skip a checkpoint.

## 2. Team and responsibilities

| Who | Role | Responsible for | Not responsible for |
| --- | --- | --- | --- |
| **Claude Code** | Primary developer | All software: room agent (vision and voice), server, database, AI agent, Telegram alerts, dashboard, scripts and tests. Debugging, integration and optimisation. Technical inputs for Person B: README draft sections, diagrams, screenshots, GIFs, accuracy tables. Telling Person A exactly what to do and when. | Physical actions; creating accounts; spending money; cutting scope without Person A’s approval; clicking Submit |
| **Person A** | Project owner and human operator | Installing software; creating accounts; pasting credentials into `.env`; connecting and placing the camera, microphone and speaker; physical tests (walking, sitting, safe falls, speaking); approving decisions; verifying results; switching Claude Code models; forwarding files to Person B | Writing or editing code |
| **Person B** | Presentation lead | Pitch; slides; final README text; Devpost page and submission; demo and backup-video recording; narrating the live demo; tapping Acknowledge on the family phone during the demo; final deliverables | Code; operating Claude Code |

**About Person A.** Some programming experience, mostly React. Not an experienced software engineer; works by vibe coding. Explain things in plain words, give one small step at a time, and never expect Person A to edit code.

**About Person B.** Does not use this Claude Code session. Put everything for Person B in `docs/handoff/` and ask Person A to forward it.

## 3. Hackathon facts you must respect

| Item | Detail |
| --- | --- |
| Event | BUHack 2.0, organised by HKBU Coding Club. Online, 48-hour build sprint, 13–15 November 2026. |
| Theme | Data-driven Apps: “Create apps that collect, analyze, or visualize data to help people make better decisions.” Theme partner: Habitect.ai. |
| Deadline | Sunday 15 November 2026, about 8:00 pm HKT. **Our target: submitted by 6:00 pm**, because Devpost uploads and video processing often run late. |
| Kickoff (H0) | Assumed Friday 13 November, 8:00 pm HKT (48 hours before the deadline). Person A confirms the real time in Stage 0. If it differs, shift every hour in this plan by the same amount. |
| Demo | Live, with a recorded backup video. The format (video call? time limit? when?) is confirmed in Stage 0. |
| Judging | Technical Implementation 30% · Presentation 30% · Innovation 20% · Impact 20%. |
| Deliverable | A minimum viable product (proof of concept) submitted through Devpost. Cloud deployment is welcome; a local demo is acceptable. |
| Final requirements | Published at kickoff. Person A pastes them to you at H0. Where they conflict with this plan, they win: tell Person A what has to change. |
| Code before kickoff | Assume it is not allowed. Before H0 you only set up and check the environment, unless Person A confirms the rules allow more. |
| Finals | Finalists present in person at the HKBU closing ceremony. |
| Team | Two people. Teams of 2–5 are allowed. |

> **Final requirements, published at kickoff (D-011, `docs/DECISIONS.md`)**
>
> Fri 13 Nov 10:00 – Sun 15 Nov 10:00. Required: a team-owned GitHub repository created for this hackathon, public for judging, with meaningful commits during the hackathon period; and a presentation video **under 3 minutes** linked on YouTube, Vimeo or Youku. One submission per team; a missing file can disqualify. No live demo is mentioned.
>

## 4. Product summary

Guardian is a privacy-first room monitor for elderly people living alone. A laptop camera turns video into skeleton keypoints, tracks activity, detects falls, checks in by voice, and escalates to family when the person does not answer. The video never leaves the room; only keypoints, activity labels and incidents reach the dashboard.

**Pitch line (Data-driven apps):** camera → activity data → AI decisions that help a family act. The dashboard shows the data (activity timeline, daily mobility, incident log with the AI’s reasoning); this is what makes Guardian a data-driven app and not only a computer-vision demo.

### Decisions already made

- Target user: elderly people living alone. Children mode is future work (one slide), not built.
- Dropped: detecting objects held in hand.
- Demo: live, with a recorded backup.
- Runtime AI: the GPT API (Person A’s OpenAI tokens) for check-in decisions, text-to-speech and speech-to-text. No Claude API at runtime.
- Hardware: Intel Core Ultra 7/9 laptops, no discrete GPU. MediaPipe Pose runs on the CPU.
- Development: Claude Code with Opus 5.5 as the main model, Fable 5.2 for hard problems and reviews, and Claude in Chrome for browser work.

### What makes it data-driven

Guardian collects activity data all day (standing, walking, sitting, lying), turns it into daily mobility measures and trends, and logs every incident step by step with the AI’s reasoning. Keep this angle visible in the dashboard (Today and Insights pages, incident detail) and give Person B the numbers for the pitch.

## 5. Changes from the original four-person plan

Everything not listed here is unchanged: the architecture, the interface contracts, the MUST features, the five hard rules, the privacy rules, the feature freeze at H40 and submission by 6:00 pm on Sunday.

| # | Original plan (version 1) | Revised plan (this version) | Why |
| --- | --- | --- | --- |
| 1 | Four people in four parallel workstreams: vision, backend and AI, voice, dashboard | Claude Code builds everything in one sequence (Stages 0–10). Person A operates and tests; Person B owns presentation | Two members left the team |
| 2 | First integration at H18–H24 | The full fall → voice → alert loop runs in the terminal by about H20 (end of Stage 4). The demo-ready integration gate, with the dashboard, is H24–H28 (Stage 6) | One developer works in sequence; building a thin loop first exposes risk early |
| 3 | People sleep in pairs while others keep working | Person A sleeps in two 6-hour windows (Saturday 3–9 am and Sunday 12–6 am). If Person A allows it, Claude does mock-only work during them | Nobody else is awake to operate Claude Code |
| 4 | Branches, pull requests, a merge freeze at H18 and GitHub issues per owner | Commit to `main` after each tested step, tag each finished stage, and track bugs in `docs/PROGRESS.md` | A pull-request workflow adds nothing with one developer and confuses a beginner |
| 5 | Record at least 20 tuning clips with teammates | Minimum 14 tuning clips (6 falls, 8 normal); target 20 | Person A is the only actor and falls are tiring |
| 6 | Fresh test set with the exit check “10 test falls, ≤1 miss, no sofa alarms” | Minimum 6 fresh falls and 6 normal clips, with the same pass rule (≤1 missed fall, no sofa alarms). Target 10 falls if time and energy allow, or if Person B can act some clips | Same reason; the pass rule does not change |
| 7 | Safe zones set on the dashboard Settings page by clicking over a still skeleton frame | Safe zones are drawn in the room agent’s local debug window, which shows the real camera image and never leaves the laptop. The dashboard displays the zones; a dashboard zone editor becomes OPTIONAL | Simpler and more accurate, with less code |
| 8 | Demo roles for four people: narrator, actor, dashboard driver, phone holder | Person B narrates and taps Acknowledge; Person A acts; a dashboard “demo mode” follows the active incident by itself; a second device shows the room in the video call | Two people. The room agent occupies the laptop camera, so the call app cannot use it |
| 9 | Fable for hard parts, Sonnet for boilerplate, teammates’ own AI tools | Opus 5.5 by default; Fable 5.2 for hard problems and reviews (Person A switches the model); Claude in Chrome for browser tasks | Person A’s instruction and the tools now available |
| 10 | No heartbeat message in the contracts | Contract addition: a `status` heartbeat from the room agent every 5 s (camera ok or offline, FPS) | The existing “camera offline” requirement needs it |
| 11 | Progress tracked by people and 6-hourly team calls | `docs/PROGRESS.md` (live log) and `docs/DECISIONS.md` (approved changes). Person A and Person B still check in every 6 hours | Any new Claude Code session can resume exactly where the last one stopped |
| 12 | Space bar or raised hand counts as “I’m OK” (fallback) | Space bar fallback is SHOULD. Raised-hand fallback is OPTIONAL and counts only as a reply, never as proof of safety: Rule 3 still escalates if the person stays down | A raised hand may also mean “help” |
| 13 | Settings page edits contacts, safe zones and sensitivity | Settings page shows contacts and sensitivity; editing them in the dashboard is OPTIONAL (they live in config files) | Less code; no effect on the demo |
| 14 | Not stated | Clarification: an incident cannot be Resolved while the person is still lying on the floor outside a safe zone, unless family has acknowledged | Required for hard rule 3 to work as written |
| 15 | `CLAUDE.md` per folder and “only edit your own folder” | One root `CLAUDE.md` (Appendix B) for one developer; the folder rule is dropped | Only one developer edits the code |
| 16 | No regression tools named | `scripts/sim_scenarios.py` replays both demo scenarios automatically; `scripts/preflight.py` checks the system before rehearsals and the demo; `scripts/reset_demo.py` resets the data | Protects the demo once it works, with fewer physical falls |

If anything else in this plan turns out to be impractical while you work, do not drop it silently. Tell Person A, propose an alternative, and record the decision in `docs/DECISIONS.md`.

## 6. Development rules

Follow these rules for the whole project. They also appear in short form in `CLAUDE.md` (Appendix B).

### At the start of every session

1. Read `CLAUDE.md`, this plan (`docs/BUILD_PLAN.md`) and `docs/PROGRESS.md` before changing anything. Then tell Person A, in two or three lines, where the project stands and what comes next.
2. Plan before implementing. At the start of each stage, show Person A a short plan: the files you will create or change, the order, how you will test, and what you will need from Person A. Inside a stage, one line per step is enough.

### How you build

3. Work in small steps: one component, or one group of related functions, at a time. Never generate the whole application, a whole stage or a very large file in one go. As a guide, stop and test after every 150–300 new lines.
4. Test after every component: run it, run its tests, or run it against mocks. Report what you actually ran and what happened. Never claim something works without running it.
5. Use mocks so each part can run and be tested on its own: `--mock` and `--clip` modes for the room agent, a fake GPT client, a fake Telegram client, a fake clock for escalation tests, and a mock data mode for the dashboard.
6. Get a working end-to-end system first. Follow the scope in Section 16: never start a SHOULD item while a MUST item is broken, or an OPTIONAL item while a SHOULD item is broken.
7. Keep the repository layout in Section 10. Put thresholds and timings in the `config/` files, not scattered through the code.
8. Commit after every tested step with a clear message, and tag every finished stage (for example `stage-3-done`). If a change makes things worse, go back to the last good commit instead of piling on patches.
9. Keep documentation current: docstrings on public functions, a short README in each top-level folder, and `docs/PROGRESS.md` updated after every step.

### Interfaces, safety and privacy

10. Do not change the interface contracts (Section 12), the architecture (Section 9) or the five hard rules (Section 14) without first explaining why to Person A and getting approval. Record every approved change in `docs/DECISIONS.md`, then update `contracts/` and `docs/BUILD_PLAN.md`.
11. The five hard rules live in code (`server/escalation.py`), each has its own test, and you never weaken them to make a demo easier.
12. Privacy: raw video frames never leave the room agent process. Nothing sends, stores or logs camera images, except test clips Person A records on purpose; those stay in `clips/` and are never committed or uploaded. Everything else is keypoints, labels, events or skeleton drawings.
13. Telegram messages go only to the team’s test group. Never contact emergency services or anyone outside the team.

### Secrets

14. Never print, log, echo or commit secrets. Real keys live only in `.env`, which is git-ignored; commit `.env.example` with empty values.
15. Ask Person A to paste keys into `.env` themselves. Never ask for keys in the chat. If a key appears in the chat or in a file about to be committed, warn Person A and explain how to replace (rotate) it.
16. Before every commit, check that no `.env`, key, token, database file or video clip is staged.

### Working with Person A

17. Stop at every HUMAN CHECKPOINT and wait for Person A’s reply. Never assume a physical test passed, and never skip a checkpoint because you feel confident.
18. Ask for at most three actions at a time, as numbered steps: exactly what to type or click, what Person A should see when it works, and one sentence on why. Use the checkpoint template in Section 8.
19. Use plain words. If a technical term is unavoidable, explain it in a few words (Appendix D helps). Never ask Person A to edit code: you edit files yourself.
20. When something fails, say what failed, the likely cause and what you will try next. After two failed attempts at the same problem, stop and offer options, including switching to Fable 5.2.
21. End every stage with a Stage Report (Section 8) and wait for Person A to reply “continue”.
22. Watch the clock. At every Stage Report, compare the time with the schedule (Section 17). If you are more than two hours behind, propose cuts from the bottom of the scope table before continuing; Person A decides.

### Tools and permissions

23. Use the models and tools as Section 7 describes.
24. Install Python packages only inside the project’s virtual environment (`.venv`) and npm packages only inside `dashboard/`. Anything system-wide (Python, Node.js, Git, drivers, apps) is installed by Person A, following your instructions.
25. Never click Submit on Devpost, make the repository public, or delete anything outside the project folder without Person A’s explicit approval.

## 7. Models and tools

| Tool | Use it for | How |
| --- | --- | --- |
| **Claude Code + Opus 5.5** | Default for all development, testing and debugging | Person A selects it with `/model` at the start of each session. |
| **Claude Code + Fable 5.2** | (1) Designing `vision/fall.py` and reviewing `server/escalation.py`; (2) bugs that survive two attempts or cross two components; (3) reviews at the end of Stages 3, 6 and 9 | Ask: “Please switch to Fable 5.2: type /model, choose Fable 5.2, then reply continue.” Afterwards ask Person A to switch back to Opus 5.5 to save Fable tokens. If Fable is not available, continue with Opus 5.5 and note it in `docs/PROGRESS.md`. |
| **Claude in Chrome** | Browser testing of the dashboard (console errors, failed requests, layout, phone width); screenshots and GIFs for Person B; checking Devpost pages and links; filling the Devpost form draft for a human to review | If this Claude Code session can control Chrome directly, use it. Otherwise write a ready-to-paste prompt for Person A to run in the Claude in Chrome extension, and ask Person A to paste back the result. |
| **GPT API (OpenAI)** | Runtime only: check-in decisions, text-to-speech, speech-to-text | Model names come from `.env`, so they can change without code changes. In Stage 0, list the models the account can use and pick small, fast ones. |
| **Subagents (optional)** | An independent review of your own work with a fresh context | Reviews only. Never let two agents edit the same files. |

### Long sessions and new sessions

When the conversation gets long or slow, update `docs/PROGRESS.md`, then ask Person A to type `/clear` and paste resume prompt A3 (Appendix A). Nothing is lost: this plan, `CLAUDE.md` and `docs/PROGRESS.md` hold the state. The same prompt resumes work after a break, after sleep or after a crash.

### Usage limits

Claude subscriptions have usage limits that reset over time. Keep steps small, so little work is lost if a limit is reached. If a limit blocks you, Person A waits for the reset; meanwhile Person A and Person B do non-code work such as room setup or presentation tasks.

## 8. Message templates and progress log

Use these formats so Person A always knows what is happening and what to do. The examples show the shape; fill in the real content.

### Human checkpoint

```
HUMAN CHECKPOINT CP2.2 · Activity check · Person A · about 5 minutes
Why: I need you on camera to check that the activity labels are right.
Do this:
  1. Stand 2-3 m from the camera, facing it.
  2. Follow the five instructions in the preview window (about 10 s each).
  3. Come back to the keyboard.
You should see: the label in the top-left corner change as you move.
Then reply: "done", or tell me anything that looked wrong.
```

### Stage report

```
STAGE REPORT · Stage 4 - Voice and Telegram · Sat 4:10 pm (H20:10; plan said H20)
Done: text-to-speech with cached phrases, speech-to-text, Telegram alert + Acknowledge.
Tested: pytest (41 passed); CP4.1 voice test 3/3; CP4.3 full loop, both scenarios.
Measured: fall -> first word 4.6 s; fall -> phone alert 24 s.
Known issues: none blocking. Speaker volume must stay at 80% or more.
Decisions: none (or what was decided and why; see docs/DECISIONS.md).
For Person B: nothing yet.
Next: Stage 5 - Dashboard core (about 4 hours). Reply "continue" to start.
```

### Problem report

```
PROBLEM · speech-to-text
What happened: the transcript is empty although you spoke.
Likely cause: recording starts before the speaker stops, so the loudness check cuts it.
What I tried: (1) a longer pause after playback, (2) a lower loudness threshold.
Options: (1) test a 0.5 s pause after playback (recommended),
         (2) switch to Fable 5.2 to debug the audio timing.
```

### docs/PROGRESS.md

Create this file at H0 and update it after every step. It is the memory of the project: any new session starts by reading it.

```markdown
# Guardian - progress log
Current stage: 4 - Voice and Telegram (started H16, Sat 12:05 pm)
Last checkpoint passed: CP4.1
Schedule: on time (+0:10)

## Overnight summary (only after a mock-only window)

## Done
- Stage 3: server, escalation engine, AI agent (tag stage-3-done)

## In progress
- Telegram Acknowledge button (server/notify.py)

## Open issues
- (none)

## Measured
- Processing speed: 14.8 FPS (lite model)
- Fall -> first spoken word: 4.6 s (median of 3)

## Next step
- CP4.2 Telegram test with Person A and Person B
```

# Part II – Technical specification

Part II is the source of truth for what you build. It keeps the technical content of the original plan; additions and clarifications are marked.

## 9. Architecture and tech stack

Three programs talk over WebSockets on one laptop: a Python **room agent** (camera, pose, voice), a FastAPI **server** (database, AI decisions, alerts) and a React **dashboard**. Raw video stays inside the room agent; everything downstream sees keypoints and events only.

*Figure 1 – System architecture. Only keypoints, labels and events reach the server. Short voice clips do go to OpenAI for speech, so the privacy slide says so. (The figure is in the Word version; the surrounding text and tables carry the same information.)*

### What travels where

| From → to | What travels | How |
| --- | --- | --- |
| Camera, mic, speaker ↔ room agent | Video frames and audio | Local only; never leaves the laptop |
| Room agent → OpenAI | Recorded reply audio (speech-to-text); text to be spoken (text-to-speech) | HTTPS |
| Room agent → server | Keypoints (about 5 per second, never stored), activity, falls, posture updates, voice replies, heartbeat | WebSocket `/ws/room` |
| Server → room agent | `speak` and `speak_and_listen` commands | WebSocket `/ws/room` |
| Server → OpenAI | Incident state, attempt, transcript, posture and time since the fall; a decision comes back | HTTPS, 5 s timeout |
| Server ↔ dashboard | Live status, pose, activity, incidents and decisions; Acknowledge | WebSocket `/ws/dashboard` and REST |
| Server ↔ Telegram | Alerts with a skeleton image and gentle messages; Acknowledge button presses | HTTPS (Bot API, long polling) |

### Tech stack

| Part | Tech | Why | Notes for no-GPU laptops |
| --- | --- | --- | --- |
| Pose | MediaPipe Pose Landmarker (lite or full) + OpenCV, Python 3.11 | 33 keypoints per person, runs well on CPU | Process 640×480 at about 15 FPS; that is enough for falls. FPS is measured in Stage 0 |
| Activity + fall logic | Rules on keypoint features, smoothed over about 1 s | Explainable, tunable in hours, no training data needed | OPTIONAL upgrade: scikit-learn classifier on the same features |
| Voice out | OpenAI text-to-speech; the fixed phrases are pre-generated as audio files at startup | Natural voice with no delay during an incident | Fallback: pyttsx3 (offline system voice) |
| Voice in | Record with sounddevice, transcribe with OpenAI speech-to-text | Handles accents better than the browser speech API | Fallback: the space bar counts as a reply (raised hand is OPTIONAL) |
| Server | FastAPI + uvicorn, SQLite via SQLModel | Python, async WebSockets, zero setup | One-file database, easy to seed |
| AI decision | GPT via the OpenAI API, JSON-schema structured output | Returns a decision the code can trust to parse | Use the cheapest fast model on the account |
| Alerts | Telegram Bot API to a family group chat | Free, instant, visible on a phone during the demo | OPTIONAL: Twilio voice call (trial accounts can only call verified numbers) |
| Dashboard | React + Vite + Tailwind + Recharts | Person A’s strongest stack | Skeleton drawn on a canvas from keypoints; no video |
| Runtime | Python 3.11 in a project virtual environment (`.venv`); Node.js LTS | Stable versions for MediaPipe and Vite | On Windows, run natively, not in WSL (camera and microphone access) |

**Python packages (installed into `.venv`):** mediapipe, opencv-python, numpy, fastapi, uvicorn[standard], sqlmodel, httpx, websockets, openai, python-dotenv, sounddevice, soundfile, pyttsx3, pillow, jsonschema, pytest, pytest-asyncio. OPTIONAL later: scikit-learn. **npm packages (installed into `dashboard/`):** react, vite, tailwindcss, recharts.

> **Camera placement matters more than the model**
>
> Put the camera high in a corner, angled down, with the whole floor in view. A built-in laptop webcam at desk height will miss falls behind furniture. If possible, use a USB webcam or a phone as a webcam (DroidCam or similar) mounted on a shelf.
>

### Programs, commands and addresses

| Program | Start command (from its folder, with `.venv` active) | Address |
| --- | --- | --- |
| Server | `uvicorn app:app --host 0.0.0.0 --port 8000` (add `--reload` while developing) | `http://localhost:8000` |
| Room agent | `python main.py` with `--mock`, `--clip FILE`, `--camera 0` or `--no-voice` | Connects to `ws://localhost:8000/ws/room` |
| Dashboard | `npm run dev -- --host` | `http://localhost:5173`, and `http://LAPTOP-IP:5173` from a phone on the same Wi-Fi |

The dashboard finds the server from the address it was opened with (`window.location.hostname`), so it also works from a phone. The server allows the dashboard’s origin (CORS).

## 10. Repository layout

```
guardian/
├── CLAUDE.md               # rules for coding agents (Appendix B); copy as AGENTS.md
├── .env                    # real keys and settings (never committed)
├── .env.example            # same keys, empty values (committed)
├── .gitignore
├── start.bat / start.sh    # start all three programs (Stage 9)
├── config/
│   ├── vision.json         # activity and fall thresholds
│   ├── escalation.json     # timings and help keywords
│   └── zones.json          # safe-zone polygons
├── contracts/              # JSON Schemas for every message type
├── room-agent/
│   ├── main.py             # entry point: --mock, --clip FILE, --camera 0, --no-voice
│   ├── models/             # MediaPipe .task model files (git-ignored)
│   ├── vision/             # pose.py, features.py, activity.py, fall.py, zones.py
│   └── voice/              # tts.py, stt.py, phrases/
├── server/                 # app.py, db.py, agent.py, escalation.py, notify.py,
│                           # analytics.py, snapshot.py
├── dashboard/              # Vite + React + Tailwind + Recharts
├── scripts/                # record_clips, replay_clip, eval_clips, telegram_setup,
│                           # seed_history, sim_scenarios, reset_demo, preflight
├── tests/                  # pytest: contracts, features, fall, escalation, api
├── clips/                  # recorded test videos (git-ignored, never uploaded)
└── docs/
    ├── BUILD_PLAN.md       # this plan (Markdown copy)
    ├── PROGRESS.md         # live progress log
    ├── DECISIONS.md        # approved changes to the plan
    ├── accuracy.md         # clip results and the accuracy claim
    ├── handoff/            # packs 1-4 for Person B
    └── media/              # diagrams, screenshots, GIFs
```

`.env`, `.venv/`, `node_modules/`, `clips/`, the SQLite database and the MediaPipe model files are git-ignored. `scripts/` grows stage by stage; every script explains itself with `--help`. `replay_clip` is a thin wrapper around `main.py --clip`.

## 11. Configuration

Secrets and machine settings live in `.env`. Thresholds and timings live in `config/*.json`, so tuning never needs code changes.

### .env (never committed)

```
# Secrets: Person A pastes these values
OPENAI_API_KEY=
TELEGRAM_BOT_TOKEN=

# Filled in by Claude Code (not secret)
TELEGRAM_CHAT_ID=          # family test group; a negative number for groups
OPENAI_MODEL=              # small, fast chat model for check-in decisions
OPENAI_TTS_MODEL=
OPENAI_TTS_VOICE=
OPENAI_STT_MODEL=
SERVER_URL=http://localhost:8000
ROOM_NAME=living_room
CAMERA_INDEX=0
DEMO_MODE=false
```

### config/escalation.json

```json
{
  "checkin1_listen_s": 6,
  "checkin2_listen_s": 8,
  "floor_rule_s": 90,
  "realert_every_s": 120,
  "ai_timeout_s": 5,
  "activity_log_every_s": 2,
  "camera_offline_alert_s": 120,
  "help_keywords": ["help", "hurt", "pain", "can't get up", "cannot get up", "救命"]
}
```

The values come from the original plan. The keyword list is matched case-insensitively; it may be extended, never shortened.

### config/vision.json (starting values)

```json
{
  "frame_width": 640,
  "frame_height": 480,
  "target_fps": 15,
  "model": "pose_landmarker_lite.task",
  "pose_send_hz": 5,
  "vote_frames": 15,
  "lying_torso_deg": 60,
  "sitting_knee_deg": 120,
  "walking_hip_shift_bodywidths_per_s": 0.3,
  "fall_drop_speed_bodyheights_per_s": 1.0,
  "fall_torso_deg": 60,
  "fall_window_s": 1.0,
  "fall_confirm_s": 3.0,
  "slow_path_lying_s": 60,
  "zones_file": "config/zones.json"
}
```

These are the starting points from the original plan; the clips decide the real values (Stages 2 and 8). Switch `model` to the full model if the lite model is not accurate enough and the laptop stays at 12 FPS or more.

### config/zones.json

```json
{
  "zones": [
    {
      "name": "sofa",
      "polygon": [[0.10, 0.55], [0.42, 0.55], [0.42, 0.80], [0.10, 0.80]]
    }
  ]
}
```

Polygon corners are fractions of the image width and height (0 to 1), so they survive a change of resolution.

## 12. Interface contracts and data model

These contracts are fixed. In Stage 1, turn them into JSON Schema files in `contracts/` and test every example message against them. Change them only with Person A’s approval (rule 10).

### Room agent → server (WebSocket /ws/room)

```json
{"type": "activity", "ts": "2026-11-14T10:02:03Z", "room": "living_room", "activity": "sitting", "confidence": 0.88, "zone": null}
{"type": "pose", "ts": "...", "keypoints": [[0.51, 0.22, 0.98], "... 33 x [x, y, visibility]"]}
{"type": "fall_detected", "ts": "...", "incident_id": "inc_001", "reason": "fast_fall", "features": {"drop_speed": 1.9, "torso_angle": 78, "seconds_low": 3.2}}
{"type": "posture_update", "incident_id": "inc_001", "activity": "standing"}
{"type": "voice_reply", "incident_id": "inc_001", "attempt": 1, "transcript": "I'm okay, I just slipped", "heard_speech": true}
{"type": "status", "ts": "...", "camera": "ok", "fps": 14.8}
```

`activity` is one of `standing`, `walking`, `sitting`, `lying`, `fallen`, `absent`. `pose` is sent about 5 times a second for the live skeleton and is never stored. `reason` is `fast_fall` or `found_on_floor`.

> **Changed from the original plan: two contract additions**
>
> The `status` heartbeat (every 5 s: camera `ok` or `offline`, and the current FPS) is new; the existing “camera offline” requirement needs it. The `reason` field on `fall_detected` makes the original “found on floor” wording explicit. Everything else is exactly as in version 1.
>

### Server → room agent

```json
{"type": "speak_and_listen", "incident_id": "inc_001", "text": "Are you okay? Please say yes or no.", "listen_seconds": 6}
{"type": "speak", "text": "I have messaged your family. Help is coming."}
```

> **Approved contract addition (D-009, `docs/DECISIONS.md`)**
>
> `speak_and_listen` may also carry `"attempt": 1` (the number of the question within the incident). The room agent copies it into its `voice_reply`, so a lost command cannot put the two sides out of step.
>

### Server → dashboard (WebSocket /ws/dashboard)

Message types `status`, `pose`, `activity`, `incident_update` and `decision`, each with the same fields as above plus `incident_id` and `state`.

> **Approved clarification (D-006, `docs/DECISIONS.md`)**
>
> The exact fields are in `contracts/dashboard/`. States are `monitoring`, `checkin_1`, `checkin_2`, `follow_up`, `escalate`, `resolved`; `incident_update` mirrors one `incident_events` row (`kind` + `payload`); `decision` may name its `source` (`ai` or `hard_rule`) and the `rule` (1-5).
>

### REST endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/status` | Current status: activity, camera, open incident |
| GET | `/incidents` | List of incidents |
| GET | `/incidents/{id}` | One incident with every step (said, heard, decided, alerted, acknowledged) |
| GET | `/activity?from=&to=` | Activity log for the Today page |
| GET | `/analytics/daily` | Minutes per activity per day, sit-to-stand count, longest still period, today versus the 7-day average, insight sentences |
| POST | `/incidents/{id}/ack` | Acknowledge from the dashboard |
| POST | `/zones` | Save safe zones (sent by the room agent; an OPTIONAL dashboard editor may also use it) |
| POST | `/contacts` | Save contacts |
| POST | `/simulate/fall` | Start a simulated incident for testing and rehearsals |

### AI decision (GPT structured output; the server validates it)

```json
{"assessment": "ok | unclear | needs_help | no_response",
 "action": "follow_up | ask_again | escalate | resolve",
 "say": "Glad you're okay. Do you need anything?",
 "request": "a glass of water",
 "reason": "Person answered clearly and is standing up."}
```

| Incident state | Actions the AI may choose | Anything else |
| --- | --- | --- |
| Check-in 1 | `follow_up`, `ask_again`, `escalate` | Treated as `escalate` (Rule 5) |
| Check-in 2 | `follow_up`, `escalate` | Treated as `escalate` (Rule 5) |
| Follow-up | `resolve`, `escalate` | Treated as `escalate` (Rule 5) |

Invalid JSON, a missing field or an unknown value counts as a disallowed action. The AI is never asked about Monitoring, Escalate or Resolved: code drives those states.

### Data model (SQLite)

| Table | Main columns | Notes |
| --- | --- | --- |
| `activity_log` | ts, room, activity, confidence, zone, simulated | One row every 2 s; seeded history rows have simulated = true |
| `incidents` | id, started_at, reason, state, features (JSON), resolved_at, acknowledged_by | One row per fall or found-on-floor event |
| `incident_events` | id, incident_id, ts, kind (state, speak, reply, decision, alert, ack, request), payload (JSON) | The step-by-step story the dashboard shows |
| `contacts` | id, name, relation, telegram_chat_id | For the demo: the family test group |
| `zones` | id, name, polygon (JSON, 0–1 coordinates) | Mirror of `config/zones.json` |

Pose messages are never stored.

## 13. Vision and detection specification

### Per-frame features

- hip-centre height
- body height in pixels
- torso angle from vertical (shoulder midpoint → hip midpoint)
- bounding-box width/height ratio
- knee angles
- hip vertical speed, in body-heights per second

### Activity labels

Apply these rules to every frame, then take a majority vote over the last ~15 frames (about 1 s):

- **lying:** torso angle above 60°
- **sitting:** torso upright and knee angle under ~120°
- **walking:** standing and the hip moves sideways more than ~0.3 body-widths in 1 s
- **standing:** everything else with a person visible
- **absent:** no person found
- **fallen:** set by the fall state machine after a confirmed fall, until the person is up again

### Fall state machine

- **Fast path:** the hip drops faster than ~1 body-height per second **and** the torso angle passes 60° within 1 s → candidate. Still low and horizontal after 3 s → `fall_detected` with reason `fast_fall`. Up again within 3 s → log a stumble; no incident.
- **Slow path:** lying outside a safe zone for 60 s → `fall_detected` with reason `found_on_floor`.
- **Safe zones:** lying with the hip centre inside a zone polygon (sofa, bed) means resting, not falling: neither path raises an alarm.
- **After a fall:** send `posture_update` whenever the smoothed activity changes, so the server knows whether the person got up.

Thresholds are starting points; the clips decide the real values.

> **Changed after the tuning clips (D-007, approved; details in `docs/DECISIONS.md`)**
>
> Safe falls were no faster than a fast sit, and falls towards or away from the camera never tilted past 60° in the picture. A fall is now: upright → "down" within 3 s (the torso's upward length below half of its standing length, and not a bend), still down 3 s later → `fast_fall`. The slow path and safe zones work as above (a provisional sofa zone is set until Stage 8, D-008). Tuning set: 6 of 6 falls, 0 of 8 false alarms (`docs/accuracy.md`).

### Debug window (local only)

The room agent can show a local window with the camera image, the skeleton, the activity label, key feature values, FPS and the safe zones. It exists only for setup and testing; its pixels never leave the laptop.

| Key | Action |
| --- | --- |
| `Z` | Start drawing a safe zone: click its corners on the image |
| `S` | Save the zones to `config/zones.json` and send them to the server |
| `Space` | Counts as an “I’m OK” reply during a check-in (fallback) |
| `C` | Simulate “camera offline” (for testing with a built-in camera) |
| `Q` | Quit |

> **Changed from the original plan: where safe zones are drawn**
>
> Version 1 set zones on the dashboard Settings page by clicking over a still skeleton frame. Zones are now drawn in this debug window, which shows the real camera image (it never leaves the laptop), so the corners land exactly on the sofa or bed. The dashboard shows the zones; a dashboard zone editor is OPTIONAL.
>

### Known limits (state them in the README)

- Falls hidden behind furniture can be missed; camera placement reduces this.
- One person in the room at a time.
- Accuracy figures come from a small, self-recorded test set.

## 14. Escalation flow and the five hard rules

*Figure 2 – Escalation flow. The AI chooses only among the actions allowed in each state; the hard rules in code can always force an escalation. (The figure is in the Word version; the surrounding text and tables carry the same information.)*

### States

| State | What happens | Next |
| --- | --- | --- |
| Monitoring | Activity logged every 2 s | Fall detected → Check-in 1 |
| Check-in 1 | “Are you okay?” then listen 6 s; the AI reads the reply | OK + getting up → Follow-up · unclear or silent → Check-in 2 · needs help → Escalate |
| Check-in 2 | Louder, simpler: “Can you hear me? Say yes if you are okay.” Listen 8 s | OK → Follow-up · anything else → Escalate |
| Follow-up | “Do you need anything?” Any request goes to family as a non-urgent message | Resolved, once the person is up |
| Escalate | Telegram alert (time, room, skeleton snapshot, transcript, AI reason); the speaker says help is coming; repeat every 2 min | Family taps Acknowledge (Telegram or dashboard) → Resolved |
| Resolved | Incident closed and logged | Back to Monitoring |

### Fixed phrases (pre-generated audio)

| Moment | Phrase |
| --- | --- |
| Check-in 1 | “Are you okay? Please say yes or no.” |
| Check-in 2 | “Can you hear me? Say yes if you are okay.” |
| Follow-up | “Glad you’re okay. Do you need anything?” (the AI may supply its own `say` text) |
| Escalate | “I have messaged your family. Help is coming.” |

### The five hard rules (in code, not in the AI)

> **Hard rules – never weaken these**
>
> The AI may only escalate sooner, never later. These five rules are also the best answer when a judge asks “what if the AI is wrong?”
>
> 1. No answer after two check-ins → escalate, whatever the AI says.
> 2. Keywords such as help, hurt, pain, can’t get up, 救命 → escalate at once, before calling the AI.
> 3. Still on the floor 90 s after the fall, even after saying “I’m OK” → escalate.
> 4. GPT call fails or takes over 5 s → treat it as no answer.
> 5. The AI must pick from the actions allowed in the current state; anything else is treated as escalate.
>

### Implementation notes

- Rule 2 runs on every transcript before any AI call. Keywords come from `config/escalation.json` and are matched case-insensitively.
- Rule 1: after Check-in 2, only a clear OK (a valid `follow_up`) avoids escalation; silence, unclear replies and failures all escalate.
- Rule 3: a timer starts at `fall_detected`. At 90 s, if the latest posture is `lying` or `fallen` outside a safe zone and nobody has acknowledged, escalate, whatever was said.
- Rule 4: a timeout or error counts as “no answer”: from Check-in 1 go to Check-in 2; from Check-in 2 escalate; in Follow-up, simply record “no request”.
- Rule 5: validate the AI output against the JSON schema and the allowed-actions table in Section 12; anything else becomes `escalate`.
- Clarification (new): an incident cannot be Resolved while the person is still lying on the floor outside a safe zone, unless family has acknowledged. An OK reply while still down moves to Follow-up, but the incident stays open and Rule 3 still applies.
- A second `fall_detected` during an open incident is logged on that incident; it does not start a new one.
- Escalate repeats the Telegram alert every 2 minutes until someone acknowledges, from Telegram or the dashboard. Acknowledging in one place updates the other.
- Every decision is stored in `incident_events` with its reason, so the dashboard can show why.

> **Changed by the Stage 3 safety review (D-010, approved; details in `docs/DECISIONS.md`)**
>
> Rule 2 applies to every reply heard during an incident, whichever question it answers. A failed alert is retried after 15 s, and "Help is coming" is only said once an alert went out (until then: "I am trying to reach your family."). "Needs help" with any action other than escalate is treated as escalate (Rule 5). After a server restart, an unfinished incident is re-opened as an alert until someone acknowledges. A real fall closes an open simulated incident.
>

### Required escalation tests (tests/test_escalation.py)

| Test | Checks |
| --- | --- |
| `test_ok_and_up_goes_to_followup_and_resolves` | The normal Scenario 1 path |
| `test_request_sends_gentle_message` | A follow-up request reaches family as a non-urgent message |
| `test_silence_twice_escalates` | Rule 1 |
| `test_help_keyword_escalates_without_ai_call` | Rule 2 (the fake AI must not be called) |
| `test_ok_but_still_on_floor_escalates_at_90s` | Rule 3 |
| `test_ai_timeout_counts_as_no_answer` | Rule 4 |
| `test_invalid_or_disallowed_action_escalates` | Rule 5 |
| `test_realert_every_2_min_until_ack` | Repeated alerts stop after Acknowledge |
| `test_ack_from_dashboard_or_telegram_resolves` | Both acknowledgement paths |
| `test_cannot_resolve_while_on_floor` | The clarification above |

## 15. Privacy and safety requirements

- **Video stays local.** Raw frames never leave the room agent. No frame is stored or logged, except test clips Person A records on purpose; those stay in `clips/`, are never committed or uploaded, and can be deleted after the hackathon.
- **Only derived data travels.** Keypoints, activity labels, events and skeleton drawings. Pose messages are not stored.
- **The family alert image is a skeleton** drawn on a plain background from keypoints, never a camera photo.
- **Voice and OpenAI.** Reply audio goes to OpenAI for transcription, and OpenAI generates the spoken audio. Say so on the privacy slide and in the README.
- **Consent and control.** The person consents and chooses which rooms are monitored. State this in the README and the pitch.
- **Not a medical device.** Guardian is a prototype safety aid. Say so in the README.
- **Test group only.** Alerts go only to the team’s Telegram test group; never to real emergency services.
- **Physical safety while testing.** Use a mat or cushions; kneel first, then roll onto the mat; never drop straight from standing; rest between falls; nobody falls when tired; stop if anything hurts. Use replay and simulation for repeat runs that do not need a live fall.
- **Secrets.** Rules 14–16 (Section 6) apply at all times.

## 16. Scope: MUST, SHOULD, OPTIONAL, WON’T

When time runs short, cut from the bottom of the table upward. Never cut a MUST. Never weaken a safety or privacy requirement to save time.

| Priority | Feature | Stage | Notes |
| --- | --- | --- | --- |
| **MUST** | Pose → activity labels → fast-fall detection | 2 |  |
| **MUST** | Two voice check-ins with transcription | 4 |  |
| **MUST** | GPT decision plus the five hard rules, each with a test | 3 | Includes the wrong-key test (Rule 4 behaviour) |
| **MUST** | Telegram alert with skeleton image and Acknowledge | 4 |  |
| **MUST** | Follow-up question and gentle family message for requests | 3–4 | Part of the escalation flow and Scenario 1 |
| **MUST** | Dashboard: live status, skeleton, alert mode, incident log with AI reasons | 5 |  |
| **MUST** | Privacy rules (Section 15); SQLite log of activity and incidents | all |  |
| **MUST** | Both demo scenarios pass three times in a row on the live camera | 6 |  |
| SHOULD | Today timeline and Insights page with seeded history | 7 |  |
| SHOULD | Safe zones (sofa, bed), drawn in the debug window | 8 | Changed: drawn in the debug window, not the dashboard |
| SHOULD | Slow-path “found on floor” detection | 8 |  |
| SHOULD | Accuracy numbers from fresh clips | 8 | Minimum clip counts reduced (Section 5, rows 5–6) |
| SHOULD | Reliability: camera-offline alert, automatic reconnection, 30-minute run | 7–8 |  |
| SHOULD | Dashboard demo mode (follows the active incident) | 5 | New: needed for a two-person demo |
| SHOULD | Space bar “I’m OK” fallback | 4 |  |
| SHOULD | Settings page showing contacts and sensitivity | 5 |  |
| SHOULD | Start scripts, `preflight.py`, `reset_demo.py`, `sim_scenarios.py` | 7–9 | Tools that protect the demo |
| OPTIONAL | Cantonese check-in phrases | 8 | Strong for Impact: the original plan notes that most older people living alone in Hong Kong speak Cantonese |
| OPTIONAL | Twilio phone call as a second alert channel | 8 | Trial accounts can only call verified numbers |
| OPTIONAL | scikit-learn classifier | 8 | Only if the rules miss the accuracy target |
| OPTIONAL | Dashboard zone editor; editing contacts and sensitivity in the dashboard | – |  |
| OPTIONAL | Raised-hand fallback (counts as a reply only) | 4 | Never as proof of safety |
| WON’T | Objects held in hand, children mode, several people in the room, mobile app, cloud hosting | – | Children mode stays a “what’s next” slide |

# Part III – Stage-by-stage instructions

Work through the stages in order. Each stage is laid out the same way:

- **Goal:** what the stage achieves.
- **At a glance:** what Claude Code, Person A and Person B each do, and roughly how much of Person A’s time it takes.
- **Steps for Claude Code:** numbered steps (2.1, 2.2 …). Each says what to build and how to test it.
- **HUMAN CHECKPOINT boxes:** placed exactly where you must stop and wait for Person A.
- **Completion criteria:** what you verify before the Stage Report. All must be met, or Person A must explicitly accept an exception, which you record in `docs/DECISIONS.md`.
- **If you are behind:** what to cut or postpone first.

A stage is finished only when every completion criterion is met and Person A has replied “continue” to your Stage Report.

## 17. Schedule overview

All times assume H0 = Friday 13 November, 8:00 pm HKT. If kickoff is at a different time, shift everything by the same amount.

*Figure 3 – The 48-hour schedule, Person A’s sleep windows and the key gates. (The figure is in the Word version; the surrounding text and tables carry the same information.)*

| Stage | When (HKT) | Hours | Goal | Exit check |
| --- | --- | --- | --- | --- |
| 0 Preliminary setup | Thu 12 – Fri 13 Nov, before 8 pm | before H0 | Tools installed, accounts made, hardware proven | Environment report all green |
| 1 Scaffold and mocks | Fri 8–10 pm | H0–H2 | Repository, contracts, three programs talking | Mock fall appears on the dashboard |
| 2 Vision | Fri 10 pm – Sat 3 am | H2–H7 | Pose, activity labels, fast-fall detection, tuning clips | Labels right; ≥5 of 6 tuning falls caught |
| 3 Server, escalation, AI | Sat 3 am – 12 pm (3A while Person A sleeps) | H7–H16 | Database, API, escalation engine, hard rules, GPT decisions | All escalation tests pass; a real fall creates an incident |
| 4 Voice and Telegram | Sat 12–4 pm | H16–H20 | Voice check-ins, alerts, Acknowledge | Full loop works in the terminal |
| 5 Dashboard core | Sat 4–8 pm | H20–H24 | Live page, alert mode, incidents, demo mode | Dashboard follows a real incident |
| 6 Integration gate | Sat 8 pm – Sun 12 am | H24–H28 | Both scenarios on the live camera, three times each | 3 passes in a row each; timings met |
| 7 Data layer and polish | Sun 12–6 am (while Person A sleeps) | H28–H34 | Seeded history, Today and Insights, polish, automated reliability | Overnight summary; simulator passes |
| 8 Accuracy and reliability | Sun 6 am – 12 pm | H34–H40 | Safe zones, slow path, fresh test set, failure tests | ≤1 missed fresh fall; no sofa alarms; freeze at H40 |
| 9 Review and docs support | Sun 12–3 pm | H40–H43 | Fable review, cleanup, start scripts, inputs for Person B | Handoff pack 4 complete |
| 10 Rehearse and submit | Sun 3–6 pm | H43–H46 | Backup video, rehearsals, submission | Submitted by 6 pm |
| Buffer | Sun 6–8 pm | H46–H48 | Verify links; rest before the demo | Deadline 8 pm |

**Key gates:** full loop in the terminal by H20 · demo-ready integration gate by H28 · feature freeze at H40 (Sunday 12 pm) · submitted by H46 (Sunday 6 pm) · deadline H48 (Sunday 8 pm).

### Sleep windows

Person A sleeps about 6 hours in each window: Saturday 3–9 am (H7–H13) and Sunday 12–6 am (H28–H34). Before sleeping, Person A may let you continue with mock-only work (Stage 3A and Stage 7): building and testing that needs no camera, microphone, speaker, OpenAI or Telegram. If Person A prefers to stop you instead, those steps run after Person A wakes, the schedule slips by up to 6 hours, and you propose cuts at the next Stage Report.

### Person B’s timeline

| When | Person B |
| --- | --- |
| Before H0 (Stage 0) | Read the rules and schedule; join the Telegram test group; research Habitect.ai and official Hong Kong figures on older people living alone and on falls (Census and Statistics Department, Department of Health); save the links |
| H0–H2 | Read the final submission requirements with Person A and list every required deliverable |
| H2–H16 | Slide template and outline; README and Devpost skeletons; pitch script v0; rest during the night |
| H16–H20 | Telegram test from your own phone (CP4.2) |
| H20–H28 | Receive handoff packs 1 and 2 (diagram, screenshots, timings); join the scenario runs if possible and tap Acknowledge |
| H28–H34 | Rest |
| H34–H40 | Receive pack 3 (accuracy numbers); pitch script v1 timed at 3 minutes; answers to judge questions |
| H40–H43 | Receive pack 4; final README text, Devpost text and slides |
| H43–H46 | Record the backup video with Person A; lead three rehearsals; submit by 6 pm |
| H46–H48 | Check every link in a private window; prepare for the live demo |

### Physical effort

Person A will do about 30 safe falls over the weekend: tuning and test clips, live tests, scenario runs, rehearsals, the backup video and the demo. Spread them out, use replay and simulation for repeat runs that do not need a live fall, and let Person B act some clips when the two are together.

### Team check-ins

Person A and Person B check in every ~6 hours for 10 minutes: done, next, blocked.

## 18. Stage 0 – Preliminary setup (Thu 12 – Fri 13 Nov, before kickoff)

**Goal:** when the clock starts at H0, nothing needs installing or creating, and the camera, microphone and speaker are proven to work from Python.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Read and summarise the plan; check the computer; create `.venv` and install packages; create `.gitignore` and an empty `.env`; run throwaway checks for the camera, MediaPipe, audio, OpenAI and Telegram; write an environment report. **No project code.** |
| **Person A** | About 2.5 hours, spread over Thursday and Friday: CP0.1 rules and timing · CP0.2 install tools · CP0.3 OpenAI key · CP0.4 Telegram bot and group · CP0.5 camera · CP0.6 speaker and mic · CP0.7 demo room · CP0.8 Chrome extension and GitHub · CP0.9 kickoff readiness |
| **Person B** | Rules and schedule (can take over CP0.1); join the Telegram group; research Habitect.ai and Hong Kong figures; slide template and outlines |

> **No project code before kickoff**
>
> Until H0, write only throwaway check scripts, in a separate folder next to the project (`../setup-checks/`) that is never committed. Installing tools and packages, and creating `.gitignore` and `.env`, count as setup. Keep notes in `setup-checks/ENVIRONMENT.md`; copy them into `docs/PROGRESS.md` at H0. If Person A confirms that the rules allow more, note it and follow the rules.
>

### Steps for Claude Code

**0.1 Understand the plan.** Read this document completely. If only the Word file exists, extract its text into `docs/BUILD_PLAN.md` first (for example by unzipping the .docx and reading `word/document.xml`, or with python-docx once Python is installed) and check that the tables and code blocks survived. Summarise to Person A in ten lines or fewer: the product, the three roles, the stage sequence and what happens before kickoff. Ask whether anything is unclear.

**0.2 Check the computer.** Detect the operating system. Check Git, Python 3.11, Node.js and npm, and report a short table: installed, missing or wrong version. On Windows, confirm you are not running inside WSL. Then run CP0.1 and, if anything is missing, CP0.2.

> **HUMAN CHECKPOINT CP0.1 · Rules and timing**
>
> **Who:** Person A (or Person B) · **Time:** about 15 minutes
>
> **Why:** the kickoff time, the demo format and the code rules shape the whole plan.
>
> 1. Open the BUHack 2.0 page on Devpost (https://buhack-2.devpost.com/) and its Rules and Schedule pages.
> 2. Find: the exact kickoff time; whether code written before kickoff is allowed; how the live demo works (video call? time limit? when?); whether a demo video is required.
> 3. Tell Claude the answers. If you are unsure, copy the exact sentences. If the rules are unclear, email the organiser.
>

> **HUMAN CHECKPOINT CP0.2 · Install missing tools**
>
> **Who:** Person A · **Time:** about 20 minutes
>
> **Why:** Claude needs these tools to build and run Guardian.
>
> 1. Install only what Claude reports as missing, using the links and clicks Claude gives you. Typical Windows set: Python 3.11 from python.org (tick “Add python.exe to PATH” on the first screen), Node.js LTS from nodejs.org, Git for Windows from git-scm.com.
> 2. Close the terminal, open a new one in the project folder, and type `claude --continue` to reopen this conversation.
> 3. Reply “done”. Claude checks the versions.
>
> Optional: install VS Code to open files such as `.env` comfortably. Notepad also works.
>

**0.3 Python environment.** Create `.venv` in the project folder with Python 3.11 and install the packages listed in Section 9. Download the MediaPipe Pose Landmarker model files (lite and full). **Test:** import every package and print the versions.

**0.4 Secrets file.** Create `.gitignore` (containing `.env`) and a `.env` with the keys from Section 11 and empty values. Explain to Person A in one sentence what `.env` is. Then run CP0.3 and CP0.4.

> **HUMAN CHECKPOINT CP0.3 · OpenAI API key**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** Guardian uses OpenAI for check-in decisions, speech and transcription.
>
> 1. On platform.openai.com, sign in, open “API keys” and create a new secret key. Copy it.
> 2. Open the `.env` file in the project folder (VS Code or Notepad). Paste the key right after `OPENAI_API_KEY=`, with no spaces or quotes, and save.
> 3. In the OpenAI billing settings, set a monthly budget limit you are comfortable with. Then reply “key added”. **Do not paste the key into this chat.**
>

> **HUMAN CHECKPOINT CP0.4 · Telegram bot and family test group**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** family alerts go to a Telegram group through a bot.
>
> 1. In Telegram, open @BotFather, send `/newbot`, and choose a name (for example “Guardian Alerts”) and a username ending in `bot`. Paste the token BotFather sends into `.env` after `TELEGRAM_BOT_TOKEN=` and save.
> 2. Create a group called “Guardian Family (test)”, add Person B and the new bot, and send “hello” in the group.
> 3. Reply “done”. Claude sends a test message: tell Claude whether you and Person B both received it.
>

**0.5 Service checks.** With throwaway scripts in `setup-checks/`: list the OpenAI models the account can use, make one tiny test call, and choose a small fast chat model, a text-to-speech model and voice, and a speech-to-text model. Write the names into `.env` and tell Person A which you chose. Find the Telegram group’s chat ID, write it into `.env` and send the test message.

**0.6 Hardware checks.** Run the official MediaPipe Pose sample on the camera and measure FPS at 640×480. If it is below 12 FPS, try the lite model, process every second frame or close other apps, and tell Person A. Then test audio: play a test sentence, record 5 s, play it back and measure the loudness. Run CP0.5, CP0.6 and CP0.7.

> **HUMAN CHECKPOINT CP0.5 · Camera check**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** Claude must know that the camera works and how fast pose detection runs.
>
> 1. Use the laptop you will demo on (the one with the best camera view, speaker and mic) and plug in the camera you will use (a USB webcam if you have one). If Windows asks for camera permission, allow it (Settings → Privacy & security → Camera → let desktop apps access your camera).
> 2. Claude opens a preview window. Stand 2–3 m away and walk around.
> 3. Tell Claude whether a skeleton is drawn on you and follows you. Claude reports the speed (FPS).
>
> Optional: with your permission, Claude can save one still frame from this setup check and look at it to judge the camera angle. That one picture is sent to Claude for analysis (Guardian itself never sends camera images); say no if you prefer, and describe the view instead.
>

> **HUMAN CHECKPOINT CP0.6 · Speaker and microphone check**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** the voice check-in must work across the room.
>
> 1. Put the laptop (or speaker) where it will stand during the demo, and stand about 3 m away.
> 2. Claude plays a test sentence: say whether it was easy to hear.
> 3. When Claude says “speak now”, say “Yes, I’m okay” in a normal voice. Claude plays it back and reports the loudness.
>
> If either is weak, use a Bluetooth or USB speaker, or a USB microphone, and repeat.
>

> **HUMAN CHECKPOINT CP0.7 · Prepare the demo room**
>
> **Who:** Person A · **Time:** about 30 minutes
>
> **Why:** camera placement matters more than the model.
>
> 1. Mount the camera high in a corner (shelf, tripod or tape), angled down, so that the whole floor is visible.
> 2. Put a yoga mat or cushions where falls will happen. Make sure a chair and a sofa or bed are in view (for the safe-zone test). Check the light, including at night if you might demo then: pose detection gets much worse in dim rooms.
> 3. Tell Claude when you are ready; Claude repeats the camera check to confirm the final view.
>

**0.7 Browser and repository.** Run CP0.8. After Person A creates the repository, check that git can reach it (for example `git ls-remote`). Do not commit or push anything before H0.

> **HUMAN CHECKPOINT CP0.8 · Claude in Chrome and GitHub**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** Claude in Chrome tests the dashboard; GitHub keeps a safe copy of the code.
>
> 1. Install the Claude in Chrome extension in Google Chrome and sign in.
> 2. On GitHub, create an empty private repository called `guardian` (no README) and add Person B as a collaborator.
> 3. Paste the repository address (URL) here. If a sign-in window opens when Claude checks it, sign in.
>

**0.8 Environment report.** Write `setup-checks/ENVIRONMENT.md`: versions, FPS, chosen models, audio results, the kickoff time and the answers from CP0.1. Run CP0.9, send the Stage Report, then wait for kickoff. At H0, Person A pastes prompt A2.

> **HUMAN CHECKPOINT CP0.9 · Kickoff readiness**
>
> **Who:** Person A and Person B · **Time:** about 5 minutes
>
> **Why:** the next 48 hours need two people available at known times.
>
> 1. On Devpost, check that the team lists both of you (both must be eligible Hong Kong students). If the two members who left are still listed, ask the organiser whether to remove them.
> 2. Agree check-in times (every ~6 hours, 10 minutes: done, next, blocked) and when Person B is free for the Telegram test (Saturday midday), the scenario runs (Saturday evening) and the rehearsals (Sunday afternoon). Charge your phones and keep the laptop chargers ready.
> 3. Reply “ready”.
>
> Optional for Person A: sketch the dashboard on paper (status card, live skeleton, timeline, incident log). Claude can follow it in Stage 5.
>

> **Person B in this stage**
>
> - Read the rules and schedule (or do CP0.1 for Person A).
> - Join the Telegram test group and confirm the test message.
> - Look up Habitect.ai, the Data-driven theme partner, and note anything the pitch can connect to.
> - Find official Hong Kong figures on older people living alone and on falls (Census and Statistics Department, Department of Health). Save the links: they open the pitch.
> - Prepare a slide template and outlines (headings only) for the README and the Devpost page.
> - Agree the final product name with Person A (“Guardian” is the working name).
>

> **Completion criteria – Stage 0**
>
> - [ ] Kickoff time, pre-kickoff code rule, demo format and video requirement recorded; Devpost team membership checked.
> - [ ] Git, Python 3.11 and Node.js LTS installed; versions printed.
> - [ ] `.venv` created; every package imports; MediaPipe model files downloaded.
> - [ ] MediaPipe sample runs on the demo laptop at 12 FPS or more at 640×480 (actual figure recorded).
> - [ ] OpenAI test call works; model names written in `.env`.
> - [ ] Telegram test message received by Person A and Person B.
> - [ ] Test sentence easy to hear at 3 m; “Yes, I’m okay” recorded clearly at 3 m.
> - [ ] Camera mounted with the whole floor, the mat, a chair and the sofa or bed in view.
> - [ ] Claude in Chrome installed; GitHub repository reachable.
> - [ ] No project code written or committed (unless the rules allow it).
>

## 19. Stage 1 – Scaffold, contracts and mocks (H0–H2 · Fri 8–10 pm)

**Goal:** by H2, a fake fall travels from a mock room agent through the server to the dashboard, and every later stage has a place to plug in.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Repository, `CLAUDE.md`, contracts and their tests, config files, skeletons of the server, room agent and dashboard with mock data, first push to GitHub. |
| **Person A** | About 15 minutes: CP1.1 paste the final requirements · CP1.2 confirm the mock fall on the dashboard |
| **Person B** | Read the final requirements and list every required deliverable |

### Steps for Claude Code

**1.1 Kickoff information.** Run CP1.1. Compare the final requirements with this plan and report anything that changes it (for example a required video or a deployed URL); wait for Person A’s decision. Move the notes from `setup-checks/ENVIRONMENT.md` into `docs/PROGRESS.md` once it exists (step 1.2).

> **HUMAN CHECKPOINT CP1.1 · Kickoff information**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** the official requirements override this plan.
>
> 1. Copy the final submission requirements from Devpost (or the kickoff announcement) and paste them here.
> 2. Confirm the official start time.
> 3. Forward the requirements to Person B.
>

**1.2 Repository.** Initialise git; create the layout in Section 10; `.gitignore`; `.env.example`; `CLAUDE.md` from Appendix B (plus a copy as `AGENTS.md`); `docs/BUILD_PLAN.md` (if it is not there yet), `docs/PROGRESS.md`, `docs/DECISIONS.md` and `docs/handoff/`; the three `config/` files with the values from Section 11. Make the first commit and push to GitHub. **Test:** `git status` shows that `.env` is ignored.

**1.3 Contracts.** Write JSON Schemas in `contracts/` for room events, server commands, dashboard messages and the AI decision (Section 12). Add example messages and `tests/test_contracts.py`, which validates every example. **Test:** the contract tests pass.

**1.4 Server skeleton.** A FastAPI app with `/ws/room`, `/ws/dashboard`, `GET /status` and `POST /simulate/fall`. It stores incoming events in SQLite (minimal tables for now), forwards them to every connected dashboard, and allows the dashboard’s origin (CORS). **Test:** start it and call `/status`.

**1.5 Room agent skeleton.** `main.py --mock` sends activity every 2 s, pose at 5 Hz (a fake skeleton), a heartbeat every 5 s and a fake fall every 60 s, and reconnects by itself if the server restarts. Voice stub: `speak()` prints the text; `listen()` returns “I’m okay” after 6 s. **Test:** run it against the server and check the server log.

**1.6 Dashboard skeleton.** Vite + React + Tailwind, with Recharts installed for later. It connects to `/ws/dashboard` (server address from `window.location.hostname`) and shows the connection state, the current status and the last event. **Test:** the dev server starts and the page loads with no console errors.

**1.7 Whole loop.** Start all three programs and check that the mock fall reaches the dashboard. Run CP1.2. Then commit, tag `stage-1-done`, push and send the Stage Report.

> **HUMAN CHECKPOINT CP1.2 · See the loop working**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** this proves the three programs can talk to each other.
>
> 1. If Windows Firewall asks whether Python or Node.js may use the network, click Allow (private networks).
> 2. Open Chrome at http://localhost:5173 and wait up to one minute.
> 3. Tell Claude whether you see “Connected” and a fall event appear.
>

> **Person B in this stage**
>
> - Read the final requirements and send Person A a list of every required deliverable (video? repository link? slides? anything else).
> - Continue the research and the slide outline.
>

> **Completion criteria – Stage 1**
>
> - [ ] Each program starts with one command and shows no errors.
> - [ ] The mock fall appears on the dashboard within 1 s of being sent.
> - [ ] The contract tests pass.
> - [ ] `.env` is ignored by git; the first commit is on GitHub.
> - [ ] `docs/PROGRESS.md` exists and names the next step.
>

## 20. Stage 2 – Vision: pose, activity and fall detection (H2–H7 · Fri 10 pm – Sat 3 am)

**Goal:** on the real camera, the activity labels are right and fast falls are caught; the tuning clips are recorded.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Pose capture and debug window, features, activity labels, clip recorder and replay, fall state machine (designed with Fable 5.2), clip evaluation, room agent connected to the server. |
| **Person A** | About 75 minutes: CP2.1 camera view · CP2.2 activity check · CP2.3 tuning clips (about 40 minutes) · CP2.4 live fall test · model switches when Claude asks |
| **Person B** | Slides and outlines; help with the clips if you are together |

### Steps for Claude Code

**2.1 Pose capture.** `vision/pose.py`: camera at 640×480, MediaPipe Pose Landmarker in video mode, about 15 FPS, 33 keypoints out. The local debug window shows the camera image, the skeleton and the FPS. **Test:** run it on the camera, then CP2.1.

> **HUMAN CHECKPOINT CP2.1 · Camera view**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** the whole body must be visible, standing and lying, or falls will be missed.
>
> 1. Claude opens the debug window. Stand by the far wall, then lie down slowly on the mat.
> 2. Tell Claude whether the skeleton covers your whole body, including your feet, in both positions.
> 3. If it does not, move or tilt the camera and repeat.
>

**2.2 Features.** `vision/features.py` computes the per-frame features in Section 13. **Test:** unit tests with synthetic keypoints for standing, sitting and lying.

**2.3 Activity labels.** `vision/activity.py` applies the rules and the 15-frame majority vote from Section 13. Draw the label and the key feature values in the debug window, and log the labels with timestamps. Run CP2.2, compare the log with the sequence, and adjust the rules if needed (one repeat at most).

> **HUMAN CHECKPOINT CP2.2 · Activity check**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** Claude needs to see each activity once to check the labels.
>
> 1. Stand 2–3 m from the camera.
> 2. Follow the five instructions shown in the window, about 10 seconds each: stand still; walk across the room and back; sit on the chair; lie down slowly on the mat; leave the camera view and come back.
> 3. Reply “done”, and mention anything that looked wrong.
>

**2.4 Clip recorder and replay.** `scripts/record_clips.py` shows a 5 s countdown, records 10 s and saves `clips/tune_<label>_<nn>.mp4`, working through a list of labels. `main.py --clip FILE` (wrapped by `scripts/replay_clip.py`) feeds a clip through the same pipeline instead of the camera. **Test:** record one clip and replay it. Then CP2.3.

> **Safe falls**
>
> Use a mat or cushions. Kneel first, then roll onto the mat; never drop straight from standing. Rest between falls. Stop if anything hurts. If you are too tired, postpone the falls and tell Claude: nobody falls when tired.
>

> **HUMAN CHECKPOINT CP2.3 · Tuning clips**
>
> **Who:** Person A (Person B can act some clips) · **Time:** about 40 minutes
>
> **Why:** recorded clips let Claude tune fall detection without you falling again and again.
>
> 1. Claude starts the recorder and shows the list. Falls: forward ×2, backward ×2, sideways ×2. Normal: fast sit on the chair ×2, lie down on the sofa or bed ×2, bend to pick something up ×2, kneel ×2.
> 2. For each clip, wait for the countdown, do the action, then stay still until recording stops. After a fall, stay on the mat for at least 5 seconds.
> 3. Reply “done” after the last clip. That is 14 clips minimum; up to 20 if you have the energy.
>

> **Changed from the original plan**
>
> Version 1 asked for at least 20 tuning clips recorded with teammates. With one actor, the minimum is 14 (6 falls, 8 normal) and 20 stays the target.
>

**2.5 Fall state machine.** Ask Person A to switch to Fable 5.2 for this step (“type /model, choose Fable 5.2, then reply continue”), and to switch back to Opus 5.5 afterwards. Build `vision/fall.py` exactly as Section 13 describes: the fast path with stumble logging, the `fallen` label, and the slow-path timer (fully tested in Stage 8). Every threshold comes from `config/vision.json`. **Test:** unit tests with synthetic feature sequences (fall, stumble, slow lie-down).

**2.6 Clip evaluation.** `scripts/eval_clips.py` runs every clip through the detector and prints a table: clip, expected, detected, seconds to detection. Tune `config/vision.json` until at least 5 of 6 tuning falls are caught and at most 1 normal clip raises an alarm; Stage 8 finishes the job. Save the table in `docs/accuracy.md`.

**2.7 Live fall test.** Run CP2.4 and report when each event was detected.

> **HUMAN CHECKPOINT CP2.4 · Live fall test**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** clips are not enough; the live pipeline must catch a real fall.
>
> 1. Claude starts the room agent on the camera. Do one safe fall onto the mat and stay down for 5 seconds.
> 2. Get up, do a second safe fall, then sit down fast on the chair.
> 3. Reply “done”.
>

**2.8 Connect to the server.** The room agent sends real activity (every 2 s), pose (5 Hz), the heartbeat and `fall_detected` events to the server. **Test:** the events appear in the server log and the dashboard shows the live status. Commit, tag `stage-2-done`, push, send the Stage Report.

> **Person B in this stage**
>
> - Slide template and outline, README and Devpost skeletons, pitch script v0.
> - If you are with Person A, help with the clip session: run the countdowns or act some clips.
>

> **Completion criteria – Stage 2**
>
> - [ ] Processing speed is 12 FPS or more on the demo laptop (target about 15).
> - [ ] Activity check: standing, walking, sitting, lying and absent each labelled correctly.
> - [ ] At least 14 tuning clips recorded and listed in `docs/accuracy.md`.
> - [ ] At least 5 of 6 tuning falls caught; at most 1 false alarm in the normal tuning clips.
> - [ ] Both live falls raise `fall_detected` within 5 s of landing; the fast sit raises nothing.
> - [ ] The server receives activity, pose, heartbeat and fall events from the real camera.
> - [ ] Feature and fall tests pass; every threshold lives in `config/vision.json`.
>

**If you are behind:** keep the fast path. Leave the slow path and safe zones for Stage 8, and record any missing tuning clips right after Sleep window 1.

## 21. Stage 3 – Server, escalation engine and AI decisions (H7–H16 · Sat 3 am – 12 pm)

**Goal:** the server stores everything, runs the escalation flow with the five hard rules, and gets valid decisions from GPT. A real fall on camera creates an incident and runs the flow with the voice stub.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | 3A, mock-only during Sleep window 1: database, API, escalation engine with the five hard rules and their tests, AI agent (fake and real), analytics functions, skeleton snapshot. 3B, with Person A: Fable review, live GPT test, wrong-key test, real fall → incident. |
| **Person A** | About 25 minutes, plus sleep: CP3.0 before you sleep · CP3.1 morning check · CP3.2 model switch · CP3.3 check the AI’s decisions · CP3.4 one live fall |
| **Person B** | Nothing needed from Claude: presentation work or rest |

### Stage 3A – mock-only, during Sleep window 1 (H7–H13)

> **HUMAN CHECKPOINT CP3.0 · Before you sleep**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** Claude can keep building safe, mock-only parts while you rest.
>
> 1. Ask Claude how to let it edit project files and run tests without asking, for this window only (Claude Code’s permission settings). Allow only that.
> 2. Paste prompt A5 (Appendix A), naming Stage 3A.
> 3. Go to sleep. If you would rather not leave Claude working, skip steps 1 and 2: Stage 3A then runs after you wake, and Claude proposes cuts to catch up.
>

> **Rules for mock-only windows (Stages 3A and 7)**
>
> - No camera, microphone or speaker (recorded clips are fine).
> - No calls to OpenAI or Telegram: use the fakes.
> - No changes to contracts, to the hard rules or to the timings in `config/escalation.json`.
> - Commit only tested work; never commit secrets.
> - If blocked, stop and write what you need in `docs/PROGRESS.md`.
>

**3.1 Database.** `server/db.py` with every table in Section 12. **Test:** insert and query tests.

**3.2 API.** `server/app.py`: both WebSockets and every REST route in Section 12, including `/simulate/fall`. **Test:** FastAPI test-client tests for each route.

**3.3 Escalation engine.** `server/escalation.py`: the states in Section 14 with asyncio timers and the timings from `config/escalation.json`; the five hard rules; the allowed-actions table; the “no Resolved while still on the floor” clarification; re-alerts every 2 minutes until acknowledged. Voice, AI and notifier are passed in as interfaces, so fakes can replace them.

**3.4 Escalation tests.** `tests/test_escalation.py` with a fake clock, a fake AI, a fake notifier and a fake room agent, covering the ten required tests in Section 14. **Test:** all pass.

**3.5 AI agent.** `server/agent.py`: `FakeAgent` for tests and `OpenAIAgent` (JSON-schema structured output, validation, 5 s timeout). Input: state, attempt number, transcript, current posture, seconds since the fall. Log every decision with its reason. Do not call OpenAI during 3A.

**3.6 Analytics functions.** `server/analytics.py`: minutes per activity per day, sit-to-stand count, longest still period, today versus the 7-day average, and one or two plain-English insight sentences. **Test:** unit tests on synthetic data.

**3.7 Skeleton snapshot.** `server/snapshot.py` draws the latest keypoints as a skeleton on a plain background (PNG) for Telegram. **Test:** the image is created from keypoints only.

**3.8 Overnight summary.** Write a short summary at the top of `docs/PROGRESS.md` (what was built, test results, questions for Person A), commit, push, and stop.

### Stage 3B – with Person A (H13–H16)

> **HUMAN CHECKPOINT CP3.1 · Morning check**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** you decide whether the overnight work is accepted.
>
> 1. Paste prompt A3 (Appendix A).
> 2. Read Claude’s overnight summary and ask about anything unclear.
> 3. Reply “continue”.
>

**3.9 Fable review.** Run CP3.2. With Fable 5.2, review `escalation.py` and its tests against Section 14, following prompt A4: list the issues first, fix the confirmed ones, rerun the tests, then ask Person A to switch back to Opus 5.5.

> **HUMAN CHECKPOINT CP3.2 · Switch model**
>
> **Who:** Person A · **Time:** about 1 minute
>
> **Why:** Fable 5.2 reviews the most safety-critical code.
>
> 1. Type `/model` and choose Fable 5.2.
> 2. Reply “continue”.
> 3. When Claude asks later, switch back the same way to Opus 5.5.
>

**3.10 Live GPT test.** Run `OpenAIAgent` on six sample replies: “I’m okay, I just slipped”; silence; “help me, I can’t get up”; “my hip hurts”; “yes”; “what?”. Show Person A a table: reply → hard-rule result → AI decision → reason → time taken. Then CP3.3.

> **HUMAN CHECKPOINT CP3.3 · Check the AI’s decisions**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** you are the human check on the AI’s judgement.
>
> 1. Read the table Claude shows.
> 2. Tell Claude if any decision looks wrong to you. For example, “my hip hurts” must escalate.
> 3. Reply “ok” when you are satisfied.
>

**3.11 Wrong-key test.** Run the incident flow with an invalid OpenAI key set only for that test process (never edit `.env` for this). The silent scenario must still escalate (Rules 1 and 4).

**3.12 Real fall → incident.** Wire the room agent’s `fall_detected`, `posture_update` and `voice_reply` messages into the engine. The voice is still the stub and the notifier still prints. Run CP3.4. Then commit, tag `stage-3-done`, push, send the Stage Report.

> **HUMAN CHECKPOINT CP3.4 · One live fall**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** this proves that a real fall starts the real escalation engine.
>
> 1. Wait until Claude says everything is running.
> 2. Do one safe fall onto the mat and stay down.
> 3. Reply “done”. Claude shows you the steps of the incident.
>

> **Completion criteria – Stage 3**
>
> - [ ] All ten escalation tests pass, plus the database, API and analytics tests.
> - [ ] Live GPT returns schema-valid decisions for all six samples, each in under 5 s.
> - [ ] “help me, I can’t get up” and “my hip hurts” escalate through Rule 2, without an AI call.
> - [ ] With an invalid key, the silent scenario still escalates.
> - [ ] A real fall on camera creates an incident and runs the flow with the voice stub.
> - [ ] Fable review findings fixed, or logged in `docs/PROGRESS.md` with a reason.
>

## 22. Stage 4 – Voice check-ins and Telegram alerts (H16–H20 · Sat 12–4 pm)

**Goal:** Guardian talks to the person, understands the answer, and alerts family on Telegram with an Acknowledge button. By the end, the whole loop works without the dashboard.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Text-to-speech with cached phrases, speech-to-text with a loudness check, voice commands in the room agent, the space bar fallback, Telegram alerts with Acknowledge and gentle messages, the full loop. |
| **Person A** | About 35 minutes: CP4.1 voice test · CP4.2 Telegram test (with Person B) · CP4.3 first full loop |
| **Person B** | CP4.2 on your own phone; then back to slides |

### Steps for Claude Code

**4.1 Text-to-speech.** `voice/tts.py`: OpenAI text-to-speech returning WAV; pre-generate the four fixed phrases (Section 14) into `voice/phrases/` at startup; play them with sounddevice; generate the AI’s custom `say` text on demand; fall back to pyttsx3 if OpenAI fails. **Test:** a small command-line test speaks a sentence.

**4.2 Speech-to-text.** `voice/stt.py`: start recording only after playback ends, so it does not hear itself; record `listen_seconds`; a loudness check sets `heard_speech`; with no speech, skip transcription (faster); otherwise send the audio to OpenAI speech-to-text. Expose `speak(text)` and `speak_and_listen(text, seconds) -> {transcript, heard_speech}`. **Test:** a command-line test, then CP4.1.

> **HUMAN CHECKPOINT CP4.1 · Voice test**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** the check-in must work from where a person would fall.
>
> 1. Stand where you will be during the demo, about 3 m from the speaker.
> 2. Claude plays “Are you okay?” three times. Answer “Yes, I’m okay” the first time, stay silent the second time, and say “Help” the third time.
> 3. Reply “done”. Claude shows what it heard and may ask you to change the volume and repeat once.
>

**4.3 Room agent commands.** Handle `speak_and_listen` and `speak` from the server and reply with `voice_reply`; ignore Guardian’s own voice. Add the space bar fallback in the debug window (a reply that counts as “I’m OK”). **Test:** a simulated incident drives the real voice.

**4.4 Telegram alerts.** `server/notify.py`: `sendPhoto` with the skeleton snapshot, a caption (time, room, transcript, AI reason) and an inline Acknowledge button. A background long-polling loop (`getUpdates`) receives button presses, answers them and edits the message to “Acknowledged by” plus the name. Follow-up requests go out as a gentle, non-urgent message (“Mum asked for a glass of water”). Re-alert every 2 minutes until acknowledged; acknowledging on the dashboard also updates the Telegram message. Keep the fake notifier for tests. Then CP4.2.

> **HUMAN CHECKPOINT CP4.2 · Telegram test**
>
> **Who:** Person A and Person B · **Time:** about 5 minutes
>
> **Why:** family alerts must arrive and the button must work.
>
> 1. Claude sends a test alert to the family test group.
> 2. Both of you check that you see the skeleton picture, the text and an Acknowledge button.
> 3. Person A taps Acknowledge and replies “done”. Claude checks that the message changed to “Acknowledged”.
>

**4.5 Full loop without the dashboard.** Run CP4.3. Measure fall → first spoken word and, in Scenario 2, fall → phone alert. Commit, tag `stage-4-done`, push, send the Stage Report.

> **Safe falls**
>
> Use a mat or cushions. Kneel first, then roll onto the mat; never drop straight from standing. Rest between falls. Stop if anything hurts. If you are too tired, postpone the falls and tell Claude: nobody falls when tired.
>

> **HUMAN CHECKPOINT CP4.3 · First full loop**
>
> **Who:** Person A (Person B on the phone if available) · **Time:** about 15 minutes
>
> **Why:** this is the first time the whole product works end to end.
>
> 1. Scenario 1: do a safe fall. When asked, say “Yes, I slipped” and get up. When asked whether you need anything, say “Some water, please”.
> 2. Scenario 2: do a safe fall and stay silent through both questions until the alert arrives; then tap Acknowledge (or Person B does).
> 3. Reply “done”. Claude reports the timings.
>

> **Person B in this stage**
>
> - Take part in CP4.2 from your own phone.
> - If available, watch for the gentle message and the alert during CP4.3.
>

> **Completion criteria – Stage 4**
>
> - [ ] The check-in is easy to hear at 3 m; “Yes, I’m okay” is transcribed correctly 3 times out of 3; silence is detected as no speech; “Help” escalates at once.
> - [ ] Fall → first spoken word under 6 s.
> - [ ] The Telegram alert with the skeleton image arrives on both phones; Acknowledge works; the gentle request message works.
> - [ ] Re-alert every 2 minutes until acknowledged (fake-clock test, plus one real 2-minute wait).
> - [ ] Scenario 2: the phone alert arrives under 30 s after the fall.
> - [ ] The alert image contains no camera pixels (skeleton only).
>

## 23. Stage 5 – Dashboard core (H20–H24 · Sat 4–8 pm)

**Goal:** a family member can see the status, follow an incident step by step and acknowledge it, on a laptop or a phone.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Live page, alert mode, incidents list and detail, demo mode, settings view, Chrome QA pass, handoff pack 1 for Person B. |
| **Person A** | About 20 minutes: CP5.1 look and feel · CP5.2 live check |
| **Person B** | Receive handoff pack 1 and start the slides with real screenshots |

> **Design rules (from the original plan)**
>
> One visual style: calm colours for OK, amber for checking in, red only for alerts. Large type: a family member should read the status from across a room. It must work on a phone screen, because family will open it there.
>

### Steps for Claude Code

**5.1 Live page.** A large status card (OK / Checking in / ALERT), the live skeleton drawn on a canvas from pose events, the current activity, the camera status, and the safe zones drawn over the skeleton when they exist.

**5.2 Alert mode.** The page turns red, plays a sound, and shows the transcript, the AI’s reason and an Acknowledge button (`POST /incidents/{id}/ack`).

**5.3 Incidents.** A list plus a detail view showing each step: what was said, what was heard, what the AI decided and why, the alerts sent, and who acknowledged.

**5.4 Demo mode.** A toggle (or `?demo=1` in the address) that makes the dashboard jump to the active incident and back to Live by itself, so nobody needs to click during the demo.

**5.5 Settings.** Show the contacts and the sensitivity setting (read-only); editing them here is OPTIONAL. Add a “Simulate fall” button (calls `/simulate/fall`) for testing and rehearsals.

**5.6 Browser QA.** Use Claude in Chrome (Section 7) during a simulated incident (`/simulate/fall`): console errors, failed requests, broken states, and the layout at laptop and phone width. Fix what it finds. Then CP5.1 and CP5.2.

> **HUMAN CHECKPOINT CP5.1 · Look and feel**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** you are the first real user; your eye catches what tests miss.
>
> 1. Open the dashboard on the laptop, and on your phone at the address Claude gives you (same Wi-Fi). If Windows asks whether Node.js may use the network, click Allow.
> 2. Claude starts a simulated incident: watch the status change and the alert appear.
> 3. Tell Claude up to three things that are hard to read or understand.
>

> **HUMAN CHECKPOINT CP5.2 · Live check**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** the dashboard must follow the real camera, not only simulations.
>
> 1. Turn on demo mode (Claude shows you how).
> 2. Walk, sit, then do one safe fall and answer “I’m okay”.
> 3. Reply “done”, and say whether the dashboard followed you without any clicks.
>

**5.7 Handoff pack 1.** Put the architecture diagram, three or four dashboard screenshots and a one-paragraph technical summary in `docs/handoff/pack1/`, and ask Person A to forward them. Commit, tag `stage-5-done`, push, send the Stage Report.

> **Person B in this stage**
>
> - Receive pack 1 and put the real screenshots into the slides.
>

> **Completion criteria – Stage 5**
>
> - [ ] The status updates within 1 s of events; the skeleton moves smoothly (about 5 updates per second).
> - [ ] Alert mode appears by itself during an escalation; Acknowledge on the dashboard resolves the incident and updates the Telegram message.
> - [ ] The incident detail shows every step with the AI’s reasons.
> - [ ] No console errors in the Chrome QA pass; usable at phone width; works from the phone over Wi-Fi.
> - [ ] Demo mode follows a live incident without clicks.
> - [ ] Handoff pack 1 delivered.
>

## 24. Stage 6 – Integration gate (H24–H28 · Sat 8 pm – Sun 12 am)

**Goal:** both demo scenarios work three times in a row on the real camera. This is the most important stage: no new features.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Run and time the scenarios, fix bugs only, Chrome QA, Fable review of the integration, handoff pack 2, tag the demo-safe version. |
| **Person A** | About 60–90 minutes with rests: CP6.1 scenario runs · CP6.2 cut decision (only if behind) |
| **Person B** | Tap Acknowledge during the runs if available; receive pack 2 |

### Steps for Claude Code

**6.1 Prepare.** Start the full system on the demo laptop, reset the database to a clean state, and turn on automatic timing (fall → first spoken word; fall → phone alert). Then CP6.1; record pass or fail after every run.

> **Safe falls**
>
> Use a mat or cushions. Kneel first, then roll onto the mat; never drop straight from standing. Rest between falls. Stop if anything hurts. If you are too tired, postpone the falls and tell Claude: nobody falls when tired.
>

> **HUMAN CHECKPOINT CP6.1 · Scenario runs**
>
> **Who:** Person A (Person B on the phone if possible) · **Time:** 60–90 minutes with rests
>
> **Why:** the demo must work every time, not just once.
>
> 1. Scenario 1 (“I’m okay”): safe fall → answer “Yes, I slipped” → stand up → when asked whether you need anything, say “Some water, please” → Person B gets a gentle message.
> 2. Scenario 2 (“No answer”): safe fall → stay silent through both check-ins → red alert → Person B (or you) taps Acknowledge → the dashboard shows Resolved. Once, also sit down fast on the chair: nothing should alert.
> 3. Repeat until each scenario passes three times in a row, resting between falls. After each run, reply “pass” or say what went wrong.
>

**6.2 Fix bugs only.** Fix what the runs reveal; add no features. After two failed attempts at one bug, ask for Fable 5.2. After any fix, rerun the affected scenario.

**6.3 Chrome QA.** One Claude in Chrome pass during a scenario: console errors and broken states.

**6.4 Integration review.** With Fable 5.2 (Person A switches the model), review the path from `fall_detected` to Resolved for race conditions (for example a posture update arriving while listening), missed timers and reconnection gaps. Fix confirmed issues and rerun both scenarios once.

**6.5 Lock the demo-safe version.** Record the timings in `docs/PROGRESS.md`; put them, with fresh screenshots of the incident flow, in `docs/handoff/pack2/`; commit, tag `stage-6-done` (the demo-safe version), push, send the Stage Report. From now on, every change must keep both scenarios passing.

> **HUMAN CHECKPOINT CP6.2 · Cut decision (only if behind)**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** if the gate is not passed by H28, something must give.
>
> 1. Read Claude’s proposed cuts. The original plan’s advice: drop the Insights page and the safe-zone editor, and spend the time on reliability.
> 2. Choose what to cut. A MUST item is never cut.
> 3. Reply with your decision; Claude records it in `docs/DECISIONS.md`.
>

> **Person B in this stage**
>
> - If you can, join the runs: watch for the gentle message and tap Acknowledge in Scenario 2.
> - Receive pack 2 (timings and incident screenshots) for the slides.
>

> **Completion criteria – Stage 6**
>
> - [ ] Scenario 1 passes 3 times in a row; Scenario 2 passes 3 times in a row.
> - [ ] Fall → first spoken word under 6 s (median); Scenario 2: fall → phone alert under 30 s.
> - [ ] No crash or manual restart during the runs; the fast sit raises nothing.
> - [ ] Tag `stage-6-done` exists; timings recorded in `docs/PROGRESS.md`; pack 2 delivered.
>

## 25. Stage 7 – Data layer and polish (H28–H34 · Sun 12–6 am, mock-only)

**Goal:** the dashboard shows real data analysis (Today and Insights) and looks finished, and the reliability checks that need no person are done.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Scenario simulator, seeded history, analytics endpoints, Today and Insights pages, visual polish, demo reset script, reconnection and 30-minute tests. Mock-only: no hardware, OpenAI or Telegram. |
| **Person A** | About 5 minutes, plus sleep: CP7.0 before you sleep |
| **Person B** | Rest |

> **HUMAN CHECKPOINT CP7.0 · Before you sleep**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** Claude can finish the data layer and the polish while you rest.
>
> 1. As in CP3.0, allow file edits and test runs only, for this window.
> 2. Paste prompt A5, naming Stage 7.
> 3. Go to sleep.
>

The rules for mock-only windows (Stage 3A) apply. In addition, the demo-safe behaviour of `stage-6-done` must not break.

### Steps for Claude Code

**7.1 Scenario simulator.** `scripts/sim_scenarios.py` runs Scenario 1 and Scenario 2 end to end with a replayed fall clip, scripted voice replies and the fake notifier, and checks the outcome. Run it before and after every change in this stage.

**7.2 Seeded history.** `scripts/seed_history.py`: seven days of realistic activity, with mobility dropping over the last three days so the insight has something to find. The rows are marked as simulated.

**7.3 Analytics endpoints.** Wire `/analytics/daily` and `/activity` to `analytics.py`, with insight sentences such as “Active 35% less than her 7-day average today” and “Longest still period: 2 h 10 min”.

**7.4 Today page.** A coloured band of activity across the day, from today’s real data.

**7.5 Insights page.** Minutes active per day for 7 days, the sit-to-stand count and the insight sentences, with a small “simulated history” label.

**7.6 Polish.** Apply the design rules from Stage 5 to every page; add empty, loading and offline states everywhere; check the phone layout.

**7.7 Demo reset.** `scripts/reset_demo.py` returns the database to the seeded history with no open incidents.

**7.8 Automated reliability.** Kill and restart the server: the room agent (in replay mode) and the dashboard must reconnect within 10 s without help. Then run the full stack for 30 minutes on a replay loop: no crash, memory flat. Record the numbers.

**7.9 Overnight summary.** Write the summary at the top of `docs/PROGRESS.md`, commit, tag `stage-7-done`, push, and stop.

> **Completion criteria – Stage 7**
>
> - [ ] `sim_scenarios.py` passes before and after the stage.
> - [ ] Insights shows 7 days with the “simulated history” label and at least two insight sentences computed from the data.
> - [ ] Today shows the activity band.
> - [ ] Every page has empty, loading and offline states and is readable at phone width.
> - [ ] `reset_demo.py` works.
> - [ ] After a server restart, everything reconnects within 10 s without help.
> - [ ] 30-minute run: no crash; memory use recorded and flat.
>

## 26. Stage 8 – Accuracy, safe zones and reliability (H34–H40 · Sun 6 am – 12 pm)

**Goal:** few false alarms, accuracy figures you can quote, and proven recovery from real failures. The stage ends with the feature freeze at H40 (Sunday 12 pm).

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Safe-zone tool, slow-path test, re-tuning, one evaluation of the fresh test set, real-hardware failure tests, handoff pack 3, feature freeze. |
| **Person A** | About 70 minutes: CP8.1 morning check · CP8.2 safe zones · CP8.3 found-on-floor test · CP8.4 fresh test clips · CP8.5 failure tests |
| **Person B** | Receive the accuracy numbers (pack 3); pitch script v1 timed at 3 minutes; answers to judge questions |

> **HUMAN CHECKPOINT CP8.1 · Morning check**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** you accept the overnight work before the freeze.
>
> 1. Paste prompt A3.
> 2. Read Claude’s overnight summary and open the Today and Insights pages.
> 3. Tell Claude up to three changes you want, then reply “continue”.
>

### Steps for Claude Code

**8.1 Safe-zone tool.** In the debug window: `Z` starts a zone, clicks set its corners, `S` saves `config/zones.json`. The room agent posts the zones to `/zones`, the dashboard shows them, and lying with the hip centre inside a zone counts as resting. Then CP8.2.

> **HUMAN CHECKPOINT CP8.2 · Safe zones**
>
> **Who:** Person A · **Time:** about 10 minutes
>
> **Why:** lying on the sofa must never alarm the family.
>
> 1. In the debug window, press Z, click the corners of the sofa (or bed) on the image, then press S.
> 2. Lie on the sofa for 20 seconds, three times, getting up in between.
> 3. Reply “done”. Nothing should have alerted.
>

**8.2 Slow path.** Run CP8.3 and check that a “found on floor” incident started between 60 and 65 s.

> **HUMAN CHECKPOINT CP8.3 · “Found on floor” test**
>
> **Who:** Person A · **Time:** about 3 minutes
>
> **Why:** someone who slides down slowly must still get help.
>
> 1. Lie down slowly on the mat, outside any safe zone (no fall).
> 2. Stay still for about 70 seconds.
> 3. When Guardian asks whether you are okay, answer and get up, then reply “done”.
>

**8.3 Re-tune.** Run `eval_clips.py` on the tuning clips with the zones in place. Target: every tuning fall caught, and nothing raised by the sofa, fast-sit and bending clips. Update `docs/accuracy.md`, then freeze the thresholds for the fresh test.

**8.4 Fresh test set.** Run CP8.4, then evaluate the fresh clips once with the frozen thresholds. Write the results table and an honest one-line claim in `docs/accuracy.md`, for example: “5 of 6 falls caught, 0 false alarms in 6 normal clips (small, self-recorded test set)”.

> **Safe falls**
>
> Use a mat or cushions. Kneel first, then roll onto the mat; never drop straight from standing. Rest between falls. Stop if anything hurts. If you are too tired, postpone the falls and tell Claude: nobody falls when tired.
>

> **HUMAN CHECKPOINT CP8.4 · Fresh test clips**
>
> **Who:** Person A (Person B can act some clips) · **Time:** about 30 minutes
>
> **Why:** honest accuracy figures come from clips the system was never tuned on.
>
> 1. Claude starts the recorder with a new list. Falls: forward ×2, backward ×2, sideways ×2. Normal: fast sit ×2, lie on the sofa ×2, bend to pick something up ×1, kneel ×1.
> 2. Do each action after the countdown. Do not ask for results until all clips are recorded.
> 3. Reply “done”. Up to 10 falls if you have the energy, or let Person B act some.
>

> **Changed from the original plan**
>
> Version 1’s exit check was “10 test falls, ≤1 miss, no sofa alarms”. The pass rule stays the same; the minimum is now 6 fresh falls and 6 normal clips, with 10 falls as the target.
>

> **Test-set honesty**
>
> The fresh clips are a test set: never tune on them. If thresholds change after you have seen the results, label the figures “after tuning” or record a new fresh set.
>

**8.5 OPTIONAL classifier.** Only if the rules miss the pass rule and time allows: train a scikit-learn classifier on the tuning-clip features, compare it with the rules (respecting the note above), and keep whichever is better.

**8.6 Failure tests.** Run CP8.5 and check each recovery in the logs.

> **HUMAN CHECKPOINT CP8.5 · Failure tests**
>
> **Who:** Person A · **Time:** about 15 minutes
>
> **Why:** a live demo must survive a loose cable or a crash.
>
> 1. Unplug the USB camera (or press C in the debug window if the camera is built in). Check that the dashboard says “camera offline”, wait 2 minutes for the family alert, then plug the camera back in.
> 2. Claude restarts the server: watch the dashboard and the room agent reconnect by themselves.
> 3. Reply “done”, and mention anything that looked wrong.
>

**8.7 Pack 3 and feature freeze.** Put the accuracy table, the one-line claim and the final timings in `docs/handoff/pack3/` and ask Person A to forward them. Run `sim_scenarios.py` and one live run of each scenario. At H40, commit, tag `feature-freeze`, push and send the Stage Report: from now on only bug fixes, cleanup and documentation.

> **OPTIONAL extras**
>
> Only if every MUST and SHOULD item is done before about H38: one OPTIONAL item, chosen by Person A. Cantonese check-in phrases are the strongest for Impact (the original plan notes that most older people living alone in Hong Kong speak Cantonese); a Twilio call or a dashboard zone editor are the alternatives.
>

> **Person B in this stage**
>
> - Receive pack 3 and put the accuracy claim and timings into the slides.
> - Pitch script v1, timed at 3 minutes; answers to the judge questions in Section 30.
>

> **Completion criteria – Stage 8**
>
> - [ ] Lying on the sofa in a safe zone: no alert in 3 tries.
> - [ ] “Found on floor” triggers between 60 and 65 s.
> - [ ] Tuning set: every fall caught; at most 1 false alarm (target 0).
> - [ ] Fresh set, evaluated once: at most 1 missed fall and no sofa alarms; results in `docs/accuracy.md`.
> - [ ] “Camera offline” shows within 10 s; the family alert follows after 2 minutes; recovery on reconnect.
> - [ ] After a server restart, reconnection within 10 s.
> - [ ] `sim_scenarios.py` passes and one live run of each scenario passes.
> - [ ] Tag `feature-freeze` at H40; pack 3 delivered.
>

**If you are behind:** keep the fresh test set (it gives the pitch its numbers) and the camera-offline test; drop the OPTIONAL classifier and extras first.

## 27. Stage 9 – Review and documentation support (H40–H43 · Sun 12–3 pm)

**Goal:** the code is reviewed and clean, starts with one command, and Person B has everything needed for the README, the Devpost page and the slides.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Fable review, cleanup without behaviour change, start scripts and preflight check, fresh-clone test, secret scan, GIFs and screenshots, handoff pack 4. |
| **Person A** | About 15 minutes: CP9.1 model switch · CP9.2 start-script check · CP9.3 forward pack 4 |
| **Person B** | Final README text, Devpost page text, slides and judge-question answers |

### Steps for Claude Code

**9.1 Fable review.** Run CP9.1. With Fable 5.2 and prompt A4, review `server/escalation.py`, `room-agent/vision/fall.py`, `server/agent.py` and `server/notify.py`: bugs, gaps in the hard rules and unclear code, most severe first. Fix only bugs and safety issues; log the rest. Then ask Person A to switch back.

> **HUMAN CHECKPOINT CP9.1 · Switch model**
>
> **Who:** Person A · **Time:** about 1 minute
>
> **Why:** the final review uses the strongest model.
>
> 1. Type `/model`, choose Fable 5.2, and reply “continue”.
> 2. When Claude asks, switch back to Opus 5.5 the same way.
>

**9.2 Cleanup.** Remove dead code, add missing docstrings and clarify names, without changing behaviour. **Test:** all tests and `sim_scenarios.py` pass afterwards.

**9.3 Start and preflight.** `start.bat` (Windows) and `start.sh` (Mac/Linux) start the server, the room agent and the dashboard, and open the dashboard. `scripts/preflight.py` checks the server, the room agent, camera FPS, OpenAI, Telegram, the database reset and open incidents, and prints a green or red list. Then CP9.2.

> **HUMAN CHECKPOINT CP9.2 · Start-script check**
>
> **Who:** Person A · **Time:** about 5 minutes
>
> **Why:** on demo day, starting Guardian must take one action.
>
> 1. Close every Guardian window.
> 2. Double-click `start.bat` (or run the command Claude gives you).
> 3. Tell Claude whether all three programs started and the dashboard opened.
>

**9.4 Fresh-clone test.** Clone the repository into a temporary folder, follow the README setup steps exactly, and start Guardian. Fix every missing step. This also proves another laptop could run the demo.

**9.5 Secret scan.** Search the whole git history for keys and tokens, and confirm that `.env`, the clips and the database were never committed. If anything leaked, stop and tell Person A how to replace the key.

**9.6 Media.** With Claude in Chrome: a GIF of the dashboard following a simulated incident, and a screenshot of every page. Save them in `docs/media/`.

**9.7 Handoff pack 4.** In `docs/handoff/pack4/`: a README draft with the technical sections filled in (how it works, architecture diagram, privacy design, accuracy results, setup steps, the hard rules, known limits and a “not a medical device” note); technical notes for the Devpost page (How we built it, Challenges, Accomplishments, What we learned: facts only); the GIFs and screenshots; the accuracy claim; and suggested technical answers to the judge questions in Section 30. Run CP9.3. Commit, tag `stage-9-done`, push, send the Stage Report.

> **HUMAN CHECKPOINT CP9.3 · Forward pack 4**
>
> **Who:** Person A · **Time:** about 2 minutes
>
> **Why:** Person B writes the final texts from these files.
>
> 1. Send the files in `docs/handoff/pack4/` to Person B (Claude tells you where they are and can zip them).
> 2. Reply “sent”.
>

> **Person B in this stage**
>
> - Final README text, based on Claude’s draft.
> - Devpost page text: Inspiration, What it does, How we built it, Challenges, Accomplishments, What we learned, What’s next (children mode, multi-room, wearable fallback).
> - About six slides: problem with Hong Kong figures → solution → live demo → how it works and privacy → data and accuracy → what’s next.
> - Answers to the likely judge questions (Section 30).
>

> **Completion criteria – Stage 9**
>
> - [ ] Fable findings fixed, or logged with a reason.
> - [ ] All tests and `sim_scenarios.py` pass after cleanup; one live run of each scenario passes.
> - [ ] `start.bat` / `start.sh` work from a fresh clone; Person A confirmed CP9.2.
> - [ ] `preflight.py` is all green on the demo laptop.
> - [ ] No secrets anywhere in the git history.
> - [ ] Pack 4 delivered.
>

## 28. Stage 10 – Rehearsal, backup video and submission (H43–H46 · Sun 3–6 pm; deadline H48)

**Goal:** submitted by 6:00 pm on Sunday, with a demo that has run at least five times. Person B leads; Claude supports.

| Who | Responsibilities in this stage |
| --- | --- |
| **Claude Code** | Reset and preflight before every run; watch the logs; fix only demo-breaking bugs; fill the Devpost form draft with Claude in Chrome when asked; tag `submitted`. |
| **Person A** | About 2.5 hours with Person B: CP10.1 backup video · CP10.2 three rehearsals · CP10.3 pre-demo checklist · CP10.4 submit · CP10.5 check links |
| **Person B** | Leads the rehearsals and the submission; narrates |

### Steps for Claude Code

**10.1 Before every run.** Run `reset_demo.py`, then `preflight.py`, and walk Person A through the pre-demo checklist (Appendix C) when asked (prompt A7).

**10.2 During rehearsals.** Watch the logs. Fix only bugs that would break the demo; after any fix, run `sim_scenarios.py` and one live scenario before the next rehearsal.

> **HUMAN CHECKPOINT CP10.1 · Backup video**
>
> **Who:** Person A and Person B · **Time:** about 30 minutes
>
> **Why:** if the live demo fails, the recording saves the presentation.
>
> 1. Film both scenarios from two angles: the room, and the dashboard together with the phone.
> 2. Check that the recording plays, then store it in two places (laptop and cloud).
> 3. Reply “done”.
>

> **HUMAN CHECKPOINT CP10.2 · Rehearse three times**
>
> **Who:** Person A and Person B · **Time:** about 45 minutes
>
> **Why:** a demo you have practised is a demo that works.
>
> 1. Use the same video-call software the judges will use, with a timer, following the demo script (Section 29).
> 2. After each run, tell Claude what broke, if anything. Do not fix anything yourselves, and add no features.
> 3. Reply “rehearsed” after the third clean run.
>

> **HUMAN CHECKPOINT CP10.3 · Pre-demo checklist**
>
> **Who:** Person A · **Time:** about 10 minutes, before every rehearsal and the real demo
>
> **Why:** most demo failures are setup mistakes.
>
> 1. Paste prompt A7.
> 2. Go through Appendix C item by item with Claude.
> 3. Reply “ready”.
>

**10.3 Devpost form.** If asked, use Claude in Chrome to fill the Devpost form draft from Person B’s text. Never click Submit. Then CP10.4 and CP10.5.

> **HUMAN CHECKPOINT CP10.4 · Submit by 6:00 pm**
>
> **Who:** Person B with Person A · **Time:** about 30 minutes
>
> **Why:** Devpost uploads and video processing often run late.
>
> 1. Person A makes the GitHub repository public (Settings → General → Change visibility), or shares it as the rules say.
> 2. Person B checks the README, the Devpost text, the gallery images and the video link, then clicks Submit.
> 3. Reply “submitted”.
>

> **HUMAN CHECKPOINT CP10.5 · Check links**
>
> **Who:** Person A or Person B · **Time:** about 10 minutes
>
> **Why:** a broken link can cost points.
>
> 1. Open the Devpost project page in a private (incognito) browser window.
> 2. Click every link: repository, video, any demo links. Claude in Chrome can do this check and report back.
> 3. Reply “all links work”, or say which one failed.
>

**10.4 Final tag.** Tag `submitted`, push, and update `docs/PROGRESS.md`. After this, change nothing unless a demo-breaking bug appears; then fix it only with Person A’s approval and rerun every check.

> **If you reach the finals**
>
> The closing ceremony is in person at HKBU. Bring the demo setup: camera mount, mat, speaker, chargers and a phone hotspot. On site, run the start script and `preflight.py`, redraw the safe zone if the room is different, and go through the pre-demo checklist. Venue Wi-Fi may block services: use the hotspot for OpenAI and Telegram.
>

> **Completion criteria – Stage 10**
>
> - [ ] Backup video recorded and stored in two places.
> - [ ] The demo has run at least five times in total, the last two without failures.
> - [ ] Devpost submission confirmed before 6:00 pm; every link checked in a private window.
> - [ ] Repository public (or shared as the rules say); tag `submitted` pushed.
>

# Part IV – Demo, risks and submission

## 29. Live demo script (3 minutes)

Person B narrates and shares the slides. Person A is the actor in the room. The demo laptop shares the dashboard in demo mode, so it follows the incident without clicks. A second device joins the call to show the room, and Person B’s phone shows the Telegram family group. Practise falling safely: kneel first, then roll onto the mat.

> **Video-call setup**
>
> - The room agent uses the laptop camera, so the video-call app cannot. Show the room from a second device: Person A’s phone on a stand, or Person B’s laptop if you are together.
> - Mute the demo laptop’s microphone in the call to avoid echo. Let the room device carry the room sound, so the judges hear Guardian speak.
> - Person B keeps the phone with the Telegram family group visible to their own camera.
>

| Time | On screen | What happens | Point it makes | Who |
| --- | --- | --- | --- | --- |
| 0:00–0:20 | Title slide | Hong Kong figure on older people living alone and falls | Real problem | B speaks |
| 0:20–0:35 | Live page | Skeleton moving, activity label changing; “no video leaves this laptop” | Privacy by design | A moves, B narrates |
| 0:35–0:50 | Live page | Actor sits down fast, then lies on the sofa zone; the status stays green | Not a naive detector | A acts |
| 0:50–1:40 | Live page → incident (demo mode) | Fall → “Are you okay?” → “Yes, I slipped” → stands → “Do you need anything?” → “Some water” → family gets a gentle message | AI conversation, not just an alarm | A acts; B shows the phone |
| 1:40–2:30 | Live page + phone | Second fall, actor stays silent → second check-in → red alert → phone buzzes → Person B taps Acknowledge | Escalation works, with hard-rule safety | A and B |
| 2:30–3:00 | Insights + incident detail | Mobility trend, AI reasons per step, accuracy numbers; closing line | Data-driven decisions for families | A gets up and opens the pages; B speaks |

If any step fails, Person B says “here’s the recorded run” and plays that part of the backup video without stopping the narration. If safe zones were cut, skip the sofa: show only the fast sit.

> **Changed from the original plan**
>
> Version 1 used four people (narrator, actor, dashboard driver, phone holder). With two people, Person B narrates and holds the phone, Person A acts, and the dashboard’s demo mode replaces the driver.
>

## 30. Risks and fallbacks

| Risk | Fallback |
| --- | --- |
| Integration slips past H28 | Thin end-to-end loop first; contracts and mocks from H2; cut decision CP6.2; cut from the bottom of the scope table |
| False alarms (fast sit, sofa, bending) | 3 s confirmation, safe zones, and the voice check-in itself as the safety net |
| Missed fall behind furniture | Camera high in a corner; state it as a known limit in the README |
| Speech recognition fails or the room is noisy | Short yes/no questions; loudness check; the space bar counts as a reply (raised hand OPTIONAL) |
| Mic hears the speaker | Start recording only after playback ends |
| GPT slow or down | 5 s timeout; the hard rules escalate anyway; fixed phrases are pre-generated; pyttsx3 voice fallback |
| Internet drops during the online demo | Everything except OpenAI and Telegram runs locally; phone hotspot ready; backup video |
| Claude Code usage limits or Fable tokens run out | Opus 5.5 by default; Fable only for the listed tasks; small steps; `docs/PROGRESS.md` lets a new session resume quickly; while blocked, do non-code work |
| Long sessions lose context | `docs/PROGRESS.md`, resume prompt A3 and `/clear` |
| Person A exhausted or hurt (the only actor) | Two sleep windows; replay and simulation for repeat runs; rests between falls; Person B acts some clips if present; stop if anything hurts |
| Demo laptop fails | Push after every stage; README setup tested from a fresh clone (Stage 9), so another laptop can run Guardian |
| Video-call app cannot use the camera | The room agent owns the camera; show the room from a second device |
| Claude in Chrome unavailable | Claude writes a manual browser checklist for Person A |
| API key leaked | `.env` git-ignored; secret scan in Stage 9; spending limit set; replace (rotate) the key if it was ever pushed |
| Someone gets hurt rehearsing | Mat, kneel-then-roll falls, nobody falls when tired |

### Answers to likely judge questions

- **What if the AI decides wrong?** It can only escalate sooner. Silence, help keywords and staying on the floor escalate through code rules the AI cannot override.
- **Isn’t a camera at home invasive?** No video is stored or sent. Family sees a skeleton and labels. The person consents and chooses which rooms.
- **How accurate is it?** Give the fresh-clip numbers and say that the test set is small and self-recorded.
- **Why not a wearable?** People forget to wear or charge them, and a wearable cannot talk to the person. The two can work together.
- **How is this different from existing fall detectors?** They send an alarm. Guardian talks to the person first, keeps the family informed with data, and runs on an ordinary laptop with no cloud video.
- **Is it a medical device?** No. It is a prototype safety aid.

## 31. Submission and deliverables

| Deliverable | Owner | Claude’s input | Due |
| --- | --- | --- | --- |
| Devpost project page (text, gallery, links) | Person B | Technical notes, screenshots and GIFs (pack 4); form draft via Claude in Chrome if asked | Draft H42, final H45 |
| Public GitHub repository with README | Person A (visibility); Person B (README text) | Code, README technical draft, setup steps tested from a fresh clone | H45 |
| Backup video (and demo video if required) | Person B with Person A | `reset_demo.py`, `preflight.py`, demo mode | H44 |
| Slides (about six) | Person B | Architecture diagram, timings, accuracy numbers, screenshots (packs 1–4) | H43 |
| Live demo | Person A and Person B | Demo mode, start scripts, preflight, fixes for demo-breaking bugs | At the scheduled slot |
| Anything else in the final requirements | As agreed at H0 (CP1.1) | As needed | Before 6 pm Sunday |

Any extra deliverable from the final requirements (CP1.1) is added to this table at H0.

> **After CP1.1 (D-011):** the presentation video (under 3 minutes, YouTube/Vimeo/Youku link) is a required deliverable and also the demo (no live demo is mentioned); the repository must be public with meaningful commits during the hackathon period. Person B lists every field of the Devpost submission form, because a missing file can disqualify.

# Appendices

## Appendix A – Prompts for Person A to paste into Claude Code

Copy a prompt exactly, fill in anything in [square brackets], paste it into Claude Code and press Enter.

### A1. First session (Stage 0, before kickoff)

```
You are the primary developer for our BUHack 2.0 project, Guardian.
Read docs/BUILD_PLAN.md completely before doing anything else. If only the Word
version exists, extract its text first and save it as docs/BUILD_PLAN.md.
Then:
1. Summarise the project, my role, Person B's role and your role in 10 lines or fewer.
2. We are before the official kickoff, so only Stage 0 is allowed: environment
   checks and setup. Do not write project code.
3. Guide me through Stage 0 one checkpoint at a time, in plain language.
   Wait for my reply at every HUMAN CHECKPOINT.
```

### A2. Kickoff (H0)

```
The hackathon has officially started. H0 is [day and time].
Read docs/BUILD_PLAN.md, ../setup-checks/ENVIRONMENT.md and CLAUDE.md if it exists.
Here are the final submission requirements: [paste them here]
Tell me if they change anything in the plan. Then start Stage 1, following the
development rules. Wait for me at every HUMAN CHECKPOINT.
```

### A3. Resume (new session, after /clear, after sleep or after a crash)

```
We are continuing the Guardian project. Read CLAUDE.md, docs/BUILD_PLAN.md and
docs/PROGRESS.md (before kickoff: ../setup-checks/ENVIRONMENT.md instead).
Tell me in a few lines: the current stage, what is finished, what is next, how we
are doing against the schedule, and whether you need anything from me.
Then continue from the next unfinished step.
```

### A4. Review with Fable 5.2 (after switching with /model)

```
You are reviewing, not rewriting. Read CLAUDE.md, Section 14 of docs/BUILD_PLAN.md
and these files: [the files Claude named].
List bugs, gaps in the five hard rules, race conditions and unclear code, most
severe first, with file and line. Do not change any file until I approve.
```

### A5. Before you sleep (mock-only window)

```
I am going to sleep for about 6 hours. Finish your current step and update
docs/PROGRESS.md. Then work only on the mock-only steps of Stage [3A or 7] in
docs/BUILD_PLAN.md.
Do not use the camera, microphone or speaker. Do not call OpenAI or Telegram.
Do not change contracts, the hard rules or the timings in config/escalation.json.
Never commit secrets.
If you get stuck, stop and write what happened and what you need in
docs/PROGRESS.md. When you finish, write an overnight summary at the top of
docs/PROGRESS.md.
```

### A6. When you are stuck or confused

```
I am stuck or confused. Stop what you are doing. Explain in simple words what is
happening and what you need from me, and give me one step at a time.
```

### A7. Before a rehearsal or the demo

```
We are about to [rehearse / do the live demo]. Run scripts/reset_demo.py and
scripts/preflight.py, tell me anything that is not green and how to fix it, then
walk me through the pre-demo checklist (Appendix C) one item at a time.
```

## Appendix B – CLAUDE.md template

Create this file at the repository root in Stage 1 and copy it as `AGENTS.md`.

```markdown
# Guardian - BUHack 2.0
Privacy-first fall detection for elderly people living alone.
Room agent (Python) -> server (FastAPI + SQLite) -> dashboard (React).
Full plan: docs/BUILD_PLAN.md. Live status: docs/PROGRESS.md.

## Who is who
- Claude Code writes and tests all code.
- Person A runs Claude Code, does every physical and account step, and approves
  decisions. Not an experienced engineer: plain words, at most 3 steps at a time.
- Person B does the presentation; send files via docs/handoff/.

## Hard rules
- Raw video frames never leave room-agent. Send keypoints and events only.
- All messages follow contracts/*.json. Do not change a contract without asking.
- Escalation hard rules live in server/escalation.py, not in the AI prompt.
  Never weaken them.
- Secrets come from .env. Never hard-code, print or commit keys.
  Never ask for keys in the chat.
- Stop at every HUMAN CHECKPOINT and wait for Person A.
- Telegram goes only to the team test group.

## Run (with .venv active)
- server:     cd server && uvicorn app:app --host 0.0.0.0 --port 8000 --reload
- room-agent: cd room-agent && python main.py --mock   (or --camera 0, --clip FILE)
- dashboard:  cd dashboard && npm run dev -- --host    (port 5173)
- tests:      pytest
- regression: python scripts/sim_scenarios.py          (from Stage 7)

## Way of working
- Read this file, docs/BUILD_PLAN.md and docs/PROGRESS.md at the start of every session.
- Plan first, then implement one small step, run it, then continue.
- Commit after every tested step; tag finished stages.
- Update docs/PROGRESS.md after every step.

## Style
- Small functions, type hints, docstrings on public functions.
- Thresholds and timings live in config/*.json.
```

## Appendix C – Pre-demo checklist

Print it and tape it next to the demo laptop. Go through it before every rehearsal and before the real demo (prompt A7).

- [ ] Laptop on power; sleep and screen saver off; notifications off.
- [ ] Server, room agent and dashboard running (start script); `preflight.py` all green.
- [ ] Telegram open on Person B’s phone, visible to the judges.
- [ ] Database reset to the seeded history with no open incidents (`reset_demo.py`).
- [ ] Room lit, mat in place, camera angle checked on the Live page; the safe zone still matches the sofa.
- [ ] Speaker volume high enough for the mic to hear the answer.
- [ ] Demo mode on in the dashboard.
- [ ] Second device in the call showing the room; the demo laptop’s call microphone muted.
- [ ] Backup video open in a second window on Person B’s computer.
- [ ] Phone hotspot ready in case the Wi-Fi drops.

## Appendix D – Plain-English glossary for Person A

| Word | Meaning |
| --- | --- |
| Terminal | The text window where you type commands (PowerShell or Windows Terminal on Windows, Terminal on a Mac). |
| Claude Code | The AI developer that runs in your terminal and edits the files in your project folder. |
| Repository (repo) | The project folder tracked by Git, with a copy on GitHub. |
| Commit | A saved snapshot of the project that you can go back to. |
| Tag | A name stuck on an important commit, such as “stage-6-done”. |
| Virtual environment (.venv) | A private box of Python packages used only by this project. |
| API key / token | A password that lets a program use a paid or private service. Never share it. |
| .env file | A private text file that holds API keys and settings. It is never uploaded. |
| Mock | A pretend version of a part (fake camera data, fake AI) used for testing. |
| WebSocket | A live connection that lets programs send each other messages instantly. |
| localhost and port | “localhost” means “this computer”; the port number (8000, 5173) is the door a program listens on. |
| JSON and schema | JSON is a text format for data; a schema is the rulebook that says what a message must contain. |
| FPS | Frames per second: how many camera images are processed each second. |
| Keypoints and skeleton | The 33 body points (shoulders, hips, knees …) found in each image, drawn as a stick figure. |
| Threshold | A cut-off number; for example, a torso tilted more than 60° counts as lying. |
| Debug window | A window on the laptop that shows the camera image with the skeleton. It is for testing only and never leaves the laptop. |
| Clip and replay | A recorded video fed into Guardian instead of the live camera, so tests can be repeated without falling again. |
| Model (/model) | Which Claude model Claude Code uses: Opus 5.5 by default, Fable 5.2 for hard problems and reviews. |
| Feature freeze | After this time (H40), no new features: only bug fixes, cleanup and documentation. |
| H0, H24, H48 | Hours since the official kickoff. H48 is the deadline. |

## Appendix E – References

- BUHack 2.0 on Devpost (event facts, themes, judging): https://buhack-2.devpost.com/
- Version 1 of this plan: “BUHack 2.0 – Fall-Detection Guardian: Stage-by-Stage Build Plan” (12 November 2026).
- Documentation Claude Code may consult while building: MediaPipe (ai.google.dev/edge/mediapipe), the OpenAI API (platform.openai.com/docs), the Telegram Bot API (core.telegram.org/bots/api) and FastAPI (fastapi.tiangolo.com).

