"""Skeleton picture for the family alert (BUILD_PLAN step 3.7).

Drawn from the 33 keypoints on a plain background: it never contains camera pixels (the server
never receives any). The figure keeps its position in the room, so family can see at a glance
whether the person is on the floor.
"""
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

SIZE = (480, 360)          # same 4:3 shape as the camera image
BACKGROUND = (24, 32, 48)
BONE = (235, 235, 235)
JOINT = (255, 120, 80)
CAPTION = (170, 180, 200)
MIN_VISIBILITY = 0.3
CONNECTIONS = [(0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
               (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
               (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20), (11, 23),
               (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28), (27, 29),
               (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)]


def skeleton_png(keypoints: list[list[float]] | None, caption: str = "", size: tuple[int, int] = SIZE) -> bytes:
    """PNG bytes of the skeleton (or a 'no skeleton' note) with an optional caption line."""
    w, h = size
    image = Image.new("RGB", size, BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=15)
    if keypoints:
        pts = [(x * w, y * h, v) for x, y, v in keypoints]
        for a, b in CONNECTIONS:
            if pts[a][2] >= MIN_VISIBILITY and pts[b][2] >= MIN_VISIBILITY:
                draw.line([pts[a][:2], pts[b][:2]], fill=BONE, width=4)
        for x, y, v in pts:
            if v >= MIN_VISIBILITY:
                draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=JOINT)
    else:
        draw.text((w / 2, h / 2), "No skeleton available", fill=CAPTION, font=font, anchor="mm")
    if caption:
        draw.text((10, h - 10), caption, fill=CAPTION, font=font, anchor="ld")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
