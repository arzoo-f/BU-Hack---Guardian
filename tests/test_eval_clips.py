"""Clip evaluation tests (BUILD_PLAN step 2.6): result table, summary and the accuracy file."""
import eval_clips
from eval_clips import ClipResult
from settings import load_vision_config
from vision.zones import Zones

CONFIG = load_vision_config()


def result(name: str, expected: str, detected: str | None = None, **extra) -> ClipResult:
    base = dict(detect_t=4.4 if detected else None, after_landing=3.0 if detected else None,
                stumbles=0, rested_in=None, final_label="lying")
    return ClipResult(name=name, expected=expected, detected=detected, **{**base, **extra})


RESULTS = [
    result("tune_fall_forward_01", "fall", "fast_fall"),
    result("tune_fall_forward_02", "fall"),                           # a missed fall
    result("tune_bend_01", "no_fall", stumbles=1),
    result("tune_lie_sofa_01", "no_fall", rested_in="sofa"),
    result("tune_kneel_01", "no_fall", "fast_fall"),                  # a false alarm
]


def test_summary_counts_caught_falls_and_false_alarms():
    assert eval_clips.summary(RESULTS) == "1 of 2 falls caught; 1 false alarms in 3 normal clips"


def test_table_marks_each_clip():
    rows = {line.split(" | ")[0].strip("| "): line for line in eval_clips.table(RESULTS)[2:]}
    assert rows["tune_fall_forward_01"].endswith("| 4.4 | 3.0 | OK |")
    assert "MISSED" in rows["tune_fall_forward_02"]
    assert "OK (1 stumble logged)" in rows["tune_bend_01"]
    assert "OK (resting in the sofa zone)" in rows["tune_lie_sofa_01"]
    assert "FALSE ALARM" in rows["tune_kneel_01"]


def test_expected_comes_from_the_sidecar_or_the_name(tmp_path):
    named = tmp_path / "tune_fall_sideways_01.mp4"
    assert eval_clips.expected_of(named) == "fall"
    assert eval_clips.expected_of(tmp_path / "tune_bend_01.mp4") == "no_fall"
    named.with_suffix(".json").write_text('{"expected": "no_fall"}')
    assert eval_clips.expected_of(named) == "no_fall"


def test_write_accuracy_replaces_only_its_own_section(tmp_path, monkeypatch):
    path = tmp_path / "accuracy.md"
    path.write_text("# Guardian - fall detection accuracy\n\nIntro text.\n\n## Tuning set\n\nold table\n\n"
                    "## Fresh test set\n\nkeep me\n", encoding="utf-8")
    monkeypatch.setattr(eval_clips, "ACCURACY_MD", path)
    eval_clips.write_accuracy("tune", RESULTS, CONFIG, Zones())
    text = path.read_text(encoding="utf-8")
    assert "Intro text." in text and "old table" not in text
    assert "**1 of 2 falls caught; 1 false alarms in 3 normal clips.**" in text
    assert text.count("## Tuning set") == 1
    assert "## Fresh test set\n\nkeep me" in text
    eval_clips.write_accuracy("test", RESULTS[:1], CONFIG, Zones())
    text = path.read_text(encoding="utf-8")
    assert "keep me" not in text and text.count("## Fresh test set") == 1 and "## Tuning set" in text
