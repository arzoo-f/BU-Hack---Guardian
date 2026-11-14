"""Safe-zone tool (BUILD_PLAN step 8.1): drawing in the debug window, saving, using the zones at once."""
import json

from camera_mode import VisionLoop
from settings import load_vision_config
from vision.sources import ClipSource
from vision.zone_editor import ZoneEditor
from vision.zones import Zones

CONFIG = load_vision_config()
SOFA = [(0.40, 0.33), (0.52, 0.33), (0.52, 0.45), (0.40, 0.45)]


def draw(editor: ZoneEditor, corners) -> None:
    for x, y in corners:
        editor.click(x, y)


def test_z_clicks_s_saves_the_sofa(tmp_path):
    editor = ZoneEditor(tmp_path / "zones.json")
    editor.click(0.1, 0.1)                                   # clicks before Z are ignored
    editor.start()
    assert editor.drawing and editor.name == "sofa"
    draw(editor, SOFA)
    zones = editor.save()
    assert zones.at(0.45, 0.39) == "sofa" and zones.at(0.2, 0.2) is None
    saved = json.loads((tmp_path / "zones.json").read_text("utf-8"))
    assert saved["zones"] == [{"name": "sofa", "polygon": [list(c) for c in SOFA]}]
    assert not editor.drawing and editor.message == "Saved: sofa"


def test_second_zone_undo_cancel_and_too_few_corners(tmp_path):
    editor = ZoneEditor(tmp_path / "zones.json")
    editor.start()
    draw(editor, SOFA)
    editor.start()                                           # Z again: the sofa is done, now the bed
    assert editor.name == "bed"
    draw(editor, [(0.6, 0.6), (0.9, 0.6), (0.9, 0.9), (0.5, 0.5)])
    editor.undo()                                            # the last click was a mistake
    editor.click(0.6, 0.9)
    names = [z["name"] for z in editor.save().as_list()]
    assert names == ["sofa", "bed"]
    editor.start()
    draw(editor, [(0.1, 0.1), (0.2, 0.1)])
    assert editor.save() is None and "3 corners" in editor.message and editor.drawing
    editor.cancel()
    assert not editor.drawing and "unchanged" in editor.message
    assert [z["name"] for z in json.loads((tmp_path / "zones.json").read_text("utf-8"))["zones"]] == ["sofa", "bed"]


def test_the_vision_loop_uses_new_zones_at_once_and_sends_them_on(tmp_path):
    sent = []
    loop = VisionLoop(ClipSource(tmp_path / "none.mp4", 640, 480), CONFIG, lambda m: None, "living_room",
                      show_window=False, zones=Zones(), on_zones_saved=sent.append)
    loop.zone_editor.path = tmp_path / "zones.json"
    loop.zone_key(ord("z"))
    for x, y in SOFA:
        loop.zone_click(x, y)
    loop.zone_click(0.9, 0.9)
    loop.zone_click(0, 0, right=True)                        # right click: undo the stray corner
    loop.zone_key(ord("s"))
    assert loop.zones.at(0.45, 0.39) == "sofa"
    assert loop.analyzer.fall.zones.at(0.45, 0.39) == "sofa"   # the fall detector uses it from the next frame
    assert sent == [[{"name": "sofa", "polygon": [list(c) for c in SOFA]}]]
