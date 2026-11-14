# Guardian - fall detection accuracy

All clips were recorded by the team in the final demo room, with the laptop's built-in camera
mounted high in a corner (640x480, processed at about 15 FPS). Clips are 10 seconds long, stay on
the laptop (`clips/`, never uploaded) and are scored with `scripts/eval_clips.py`.

Read the figures with care:

- The **tuning set** was used to choose the rules and thresholds, so its result shows that the
  rules fit those clips. It is **not** an accuracy claim.
- The honest figure comes from the **fresh test set** (Stage 8): clips recorded later and scored
  once, with the thresholds frozen beforehand.
- Falls are safe, deliberate falls by a healthy adult (kneel first, then roll onto a mat). They are
  slower than real falls. The test sets are small and self-recorded.
- One person, one room, one camera position.

What counts as a fall here: the person goes from upright to down on the floor within
`fall_window_s` and is still down `fall_confirm_s` later (`fast_fall`), or stays down outside a safe
zone for `slow_path_lying_s` (`found_on_floor`, not exercised by 10-second clips).
Known consequence: lying down on the floor on purpose within about 3 seconds looks the same to the
camera as a careful fall, so Guardian asks "Are you okay?" in both cases.

## The claim (fresh clips only, settings frozen, each set scored once)

> **In our fresh test clips, Guardian caught all 8 falls that started from standing, each about
> 3 seconds after landing, with 0 false alarms in 6 normal movements. It did not catch the 4 falls
> that started from kneeling within seconds; those are left to its 60-second "still on the floor"
> rule. Small, self-recorded test (one person, safe falls onto a mat, one room).**

| Fresh clips (Sat 14 Nov) | Falls caught | False alarms |
| --- | --- | --- |
| First set: 6 falls + 6 normal | 2 of 6 (the 2 that started standing) | 0 of 6 |
| Second set: 6 falls, all starting standing | 6 of 6 | - |
| All fresh falls | 8 of 12 within seconds: 8 of 8 from standing, 0 of 4 from kneeling | 0 of 6 |

Tuning clips (14, recorded Fri 13 Nov 2026, about 07:10-07:35): 6 falls - forward, backward and
sideways, each once across the picture (`_01`) and once towards or away from the camera (`_02`);
8 normal - fast sit on the chair x2, lie on the sofa x2, bend to pick something up x2, kneel x2.

## Tuning set

Evaluated Fri 13 Nov 2026, 07:52 with `scripts/eval_clips.py --set tune`.

**6 of 6 falls caught; 0 false alarms in 8 normal clips.**

Re-checked Sat 14 Nov 2026, 07:45 with the sofa zone Person A drew in the debug window (CP8.2):
the same result, clip for clip. (Detail: the two Friday sofa clips now end with the hip centre at
about (0.45, 0.39), just outside the drawn zone - Person A lay a little differently then - so they
pass as "no fall" without the zone's help; lying down slowly is not a fast fall, and 10-second clips
never reach the 60-second floor rule. Saturday's sofa clips end inside the zone at about (0.49, 0.43).) **Thresholds frozen from here for the fresh test set:**
`config/vision.json` as last changed in commit 88897be (Fri 13 Nov 07:56) and `config/zones.json`
as drawn in CP8.2 (commit 0f3371b).

| Clip | Expected | Detected | At (s into clip) | Seconds after landing | Result |
| --- | --- | --- | --- | --- | --- |
| tune_bend_01 | no_fall | - | - | - | OK (1 stumble logged) |
| tune_bend_02 | no_fall | - | - | - | OK |
| tune_fall_backward_01 | fall | fast_fall | 4.4 | 3.0 | OK |
| tune_fall_backward_02 | fall | fast_fall | 5.1 | 3.1 | OK |
| tune_fall_forward_01 | fall | fast_fall | 5.8 | 3.0 | OK |
| tune_fall_forward_02 | fall | fast_fall | 5.2 | 3.0 | OK |
| tune_fall_sideways_01 | fall | fast_fall | 4.6 | 3.0 | OK |
| tune_fall_sideways_02 | fall | fast_fall | 5.3 | 3.0 | OK |
| tune_fast_sit_01 | no_fall | - | - | - | OK |
| tune_fast_sit_02 | no_fall | - | - | - | OK |
| tune_kneel_01 | no_fall | - | - | - | OK |
| tune_kneel_02 | no_fall | - | - | - | OK |
| tune_lie_sofa_01 | no_fall | - | - | - | OK (resting in the sofa zone) |
| tune_lie_sofa_02 | no_fall | - | - | - | OK (resting in the sofa zone) |

Settings used: `model` = pose_landmarker_full.task, `target_fps` = 15, `torso_upright_ratio` = 0.5, `bend_head_rise` = 0.8, `lying_torso_deg` = 60, `lying_box_ratio` = 1.0, `lying_head_rise` = 1.2, `fall_window_s` = 3.0, `fall_confirm_s` = 3.0, `fall_confirm_share` = 0.7, `slow_path_lying_s` = 60.
Safe zones: sofa.

## Fresh test set

Evaluated Sat 14 Nov 2026, 07:53 with `scripts/eval_clips.py --set test`.

**2 of 6 falls caught; 0 false alarms in 6 normal clips.**

| Clip | Expected | Detected | At (s into clip) | Seconds after landing | Result |
| --- | --- | --- | --- | --- | --- |
| test_bend_01 | no_fall | - | - | - | OK |
| test_fall_backward_01 | fall | - | - | - | MISSED |
| test_fall_backward_02 | fall | - | - | - | MISSED |
| test_fall_forward_01 | fall | fast_fall | 6.0 | 3.1 | OK |
| test_fall_forward_02 | fall | fast_fall | 4.6 | 3.0 | OK |
| test_fall_sideways_01 | fall | - | - | - | MISSED |
| test_fall_sideways_02 | fall | - | - | - | MISSED |
| test_fast_sit_01 | no_fall | - | - | - | OK |
| test_fast_sit_02 | no_fall | - | - | - | OK |
| test_kneel_01 | no_fall | - | - | - | OK |
| test_lie_sofa_01 | no_fall | - | - | - | OK (resting in the sofa zone) |
| test_lie_sofa_02 | no_fall | - | - | - | OK (resting in the sofa zone) |

Settings used: `model` = pose_landmarker_full.task, `target_fps` = 15, `torso_upright_ratio` = 0.5, `bend_head_rise` = 0.8, `lying_torso_deg` = 60, `lying_box_ratio` = 1.0, `lying_head_rise` = 1.2, `fall_window_s` = 3.0, `fall_confirm_s` = 3.0, `fall_confirm_share` = 0.7, `slow_path_lying_s` = 60.
Safe zones: sofa.

## Why the first fresh test set caught only 2 of 6 falls

Looked at after scoring; nothing was re-tuned. In all four missed clips (backward x2, sideways x2)
Person A was already kneeling or sitting when the recording started: the screen said "kneel, then
roll" and Person A knelt during the countdown. The fast-fall rule needs to see the person upright
and then on the floor within 3 s, so it had no upright reference; both caught clips (forward)
start standing. A fall that starts from sitting or kneeling is caught by the 60-second "found on
the floor" rule instead (tested live in CP8.3), not within 3 s - a known limit. With the settings
still frozen, Person A then recorded a second fresh set of six falls that start standing ("STAND
until GO!"); both results are reported.

## Second fresh test set (falls only, starting from standing)

Evaluated Sat 14 Nov 2026, 08:01 with `scripts/eval_clips.py --set test2`.

**6 of 6 falls caught; 0 false alarms in 0 normal clips.**

| Clip | Expected | Detected | At (s into clip) | Seconds after landing | Result |
| --- | --- | --- | --- | --- | --- |
| test2_fall_backward_01 | fall | fast_fall | 5.6 | 3.0 | OK |
| test2_fall_backward_02 | fall | fast_fall | 4.6 | 3.0 | OK |
| test2_fall_forward_01 | fall | fast_fall | 5.4 | 3.0 | OK |
| test2_fall_forward_02 | fall | fast_fall | 5.2 | 3.0 | OK |
| test2_fall_sideways_01 | fall | fast_fall | 4.8 | 3.0 | OK |
| test2_fall_sideways_02 | fall | fast_fall | 5.0 | 3.1 | OK |

Settings used: `model` = pose_landmarker_full.task, `target_fps` = 15, `torso_upright_ratio` = 0.5, `bend_head_rise` = 0.8, `lying_torso_deg` = 60, `lying_box_ratio` = 1.0, `lying_head_rise` = 1.2, `fall_window_s` = 3.0, `fall_confirm_s` = 3.0, `fall_confirm_share` = 0.7, `slow_path_lying_s` = 60.
Safe zones: sofa.
