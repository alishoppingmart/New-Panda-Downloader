#!/usr/bin/env python3
"""Draw a clean flat 'green panda' badge logo and export PNG + ICO."""
from PIL import Image, ImageDraw

S = 1024  # supersample canvas
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# ---- colors ----
BADGE       = (31, 170, 89, 255)    # bright green badge
BADGE_DARK  = (15, 122, 61, 255)    # darker green (ears / eye patches)
FACE        = (255, 255, 255, 255)  # white face
INK         = (28, 40, 33, 255)     # near-black for eyes/nose

def rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)

# ---- badge background (rounded square) ----
m = 40
rounded_rect(d, (m, m, S - m, S - m), radius=220, fill=BADGE)

cx, cy = S // 2, S // 2 + 30

# ---- ears (dark green circles, behind face) ----
ear_r = 150
d.ellipse((cx - 300 - ear_r, cy - 270 - ear_r, cx - 300 + ear_r, cy - 270 + ear_r), fill=BADGE_DARK)
d.ellipse((cx + 300 - ear_r, cy - 270 - ear_r, cx + 300 + ear_r, cy - 270 + ear_r), fill=BADGE_DARK)

# ---- face (white circle) ----
face_r = 330
d.ellipse((cx - face_r, cy - face_r, cx + face_r, cy + face_r), fill=FACE)

# ---- eye patches (dark green angled ovals) ----
def eye_patch(ox, tilt):
    patch = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pd = ImageDraw.Draw(patch)
    px, py = cx + ox, cy - 40
    pd.ellipse((px - 95, py - 130, px + 95, py + 130), fill=BADGE_DARK)
    patch = patch.rotate(tilt, center=(px, py))
    img.alpha_composite(patch)

eye_patch(-150, 22)
eye_patch(150, -22)

# ---- eyes (white + ink pupils) ----
def eye(ox):
    ex, ey = cx + ox, cy - 55
    d.ellipse((ex - 42, ey - 50, ex + 42, ey + 50), fill=FACE)
    d.ellipse((ex - 24, ey - 28, ex + 24, ey + 28), fill=INK)
    d.ellipse((ex - 6, ey - 24, ex + 14, ey - 4), fill=(255, 255, 255, 255))

eye(-150)
eye(150)

# ---- nose + mouth ----
d.ellipse((cx - 45, cy + 95, cx + 45, cy + 165), fill=INK)
d.line((cx, cy + 165, cx, cy + 210), fill=INK, width=12)
d.arc((cx - 70, cy + 150, cx, cy + 240), start=20, end=160, fill=INK, width=12)
d.arc((cx, cy + 150, cx + 70, cy + 240), start=20, end=160, fill=INK, width=12)

# ---- export ----
logo = img.resize((256, 256), Image.LANCZOS)
logo.save("panda_logo.png")

# transparent square icon for window/exe
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.resize((256, 256), Image.LANCZOS).save("panda_icon.ico", sizes=icon_sizes)

print("Wrote panda_logo.png and panda_icon.ico")
