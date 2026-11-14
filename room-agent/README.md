# room-agent

Runs next to the camera: camera -> pose -> activity and falls -> server, plus voice check-ins.
Raw video frames never leave this program.

Run (from this folder):

```
..\.venv\Scripts\python.exe main.py --camera 0              # live camera + local debug window (Q quits)
..\.venv\Scripts\python.exe main.py --camera 0 --no-window  # live camera, no window
..\.venv\Scripts\python.exe main.py --mock                  # scripted person, no camera
..\.venv\Scripts\python.exe main.py --mock --fall-every 20  # faster fake falls for testing
..\.venv\Scripts\python.exe main.py --clip ..\clips\tune_fall_forward_01.mp4   # replay a clip
```

Real voice arrives in Stage 4. In the debug window the safe zones are blue, a possible fall is
amber and a confirmed fall is red.

| File | Purpose |
| --- | --- |
| `main.py` | entry point and command-line options |
| `camera_mode.py` | vision loop: frames -> pose -> activity and falls -> server, debug window, about 15 FPS |
| `vision/pose.py` | camera capture and MediaPipe pose detection |
| `vision/sources.py` | live camera or recorded clip as a frame source; frame pacing |
| `vision/features.py` | per-frame body measurements from the keypoints |
| `vision/activity.py` | activity labels (standing, walking, sitting, lying) with a 1 s vote |
| `vision/fall.py` | fall state machine: fast path, slow path, stumbles, `fallen` (see DECISIONS D-007) |
| `vision/zones.py` | safe zones (sofa, bed) from `config/zones.json` |
| `vision/analyzer.py` | activity + falls in one object, shared by the live loop and clip scoring |
| `vision/clipdata.py` | keypoints of a recorded clip, cached in `clips/.cache/` |
| `guide.py` | timed on-screen instructions for the checkpoints (`--guide view` / `activity`) |
| `vision/debug_view.py` | local debug window drawing (never leaves the laptop) |
| `settings.py` | reads `config/vision.json`, model paths |
| `server_link.py` | WebSocket to the server, contract checks, automatic reconnection |
| `mockroom.py` | mock mode: fake skeleton, activity, heartbeat, a fake fall every 60 s |
| `commands.py` | carries out `speak` / `speak_and_listen` and sends `voice_reply` |
| `voice/stub.py` | stand-in voice: prints, and "hears" "I'm okay" (mock mode, clip replays) |
| `voice/tts.py` | speaking: cached fixed phrases, OpenAI speech, the laptop's own voice as backup |
| `voice/stt.py` | listening: loudness check against the room noise, OpenAI transcription |
| `voice/live.py` | `LiveVoice` (one question at a time, space bar = "I'm okay"), `SilentVoice` (--no-voice) |
| `voice/audio.py` | speaker and microphone access, loudness maths |
| `voice/phrases/` | generated speech for the fixed phrases (git-ignored, made again when missing) |
| `models/` | MediaPipe model files (git-ignored) |
