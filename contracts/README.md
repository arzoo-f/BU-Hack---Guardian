# contracts

JSON Schemas for every message in Guardian (BUILD_PLAN Section 12). They are fixed: change
them only with Person A's approval, recorded in `docs/DECISIONS.md`.

| Folder / file | Direction |
| --- | --- |
| `room/` | room agent -> server (WebSocket `/ws/room`) |
| `command/` | server -> room agent (WebSocket `/ws/room`) |
| `dashboard/` | server -> dashboard (WebSocket `/ws/dashboard`) |
| `ai_decision.schema.json` | GPT structured output for check-in decisions |
| `common.schema.json` | shared field definitions (activity names, states, keypoints ...) |

`examples/valid/` and `examples/invalid/` hold example messages named
`<channel>.<type>[.<variant>].json`; `tests/test_contracts.py` checks every one.

Use from Python (repository root on `sys.path`):

```python
from contracts import validate, validate_decision, ContractError
validate("room", {"type": "status", "ts": "2026-11-14T10:02:05Z", "camera": "ok", "fps": 14.8})
```
