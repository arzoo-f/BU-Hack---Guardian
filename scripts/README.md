# scripts

Helper programs. Each one explains itself with `--help`. Run them from the repository root
with the project Python: `.venv\Scripts\python.exe scripts\<name>.py`.

| Script | Purpose | Stage |
| --- | --- | --- |
| `record_clips.py` | record tuning / test clips with on-screen instructions | 2, 8 |
| `replay_clip.py` | feed a recorded clip through the room agent pipeline | 2 |
| `eval_clips.py` | score every clip with the fall detector; `--write` updates `docs/accuracy.md` | 2, 8 |
| `ai_check.py` | sample replies through the real AI and the hard rules; `--more`, `--wrong-key` | 3 |
| `voice_check.py` | asks "Are you okay?" through the real speaker and microphone, shows what was heard | 4 |
| `sim_scenarios.py` | both demo scenarios end to end on recorded clips, scripted replies, fake AI and Telegram | 7 |
| `seed_history.py` | seven days of simulated activity (less active at the end) for the Insights page | 7 |
| `reset_demo.py` | `--yes`: clean demo database - no incidents, only the simulated week | 7 |
| `soak.py` | `restart`: kill and restart the server, time the reconnections; `soak`: 30-minute run, memory sampled | 7 |

Recorded clips go to `clips/` (git-ignored, never uploaded). Each `.mp4` has a `.json` next to
it with the label, the expected result and the time of every frame.
