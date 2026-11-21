#!/usr/bin/env python3
"""Build-time poster compositor for AURVIK (not the graded entrypoint).

Composites the place name + mood line onto the generated scene and writes
a deterministic 1024x1024 entry.png. Run once at build time; main.py only
copies the finished entry.png in the grader sandbox.
"""
import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.join(HERE, "media-generation-scene-0-3f08d671-7a4e-44d7-ad58-ce9c835b99bf.webp")
OUT = os.path.join(HERE, "entry.png")

PLACE = "AURVIK"
MOOD = "where the night glows"

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_ITALIC = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"

SIZE = 1024


def tracked_text(draw, cx, y, text, font, fill, tracking=0):
    """Draw centred text with letter tracking; return its bounding box."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    top = None
    bottom = None
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((x, y), ch, font=font)
        top = bbox[1] if top is None else min(top, bbox[1])
        bottom = bbox[3] if bottom is None else max(bottom, bbox[3])
        x += w + tracking
    return (cx - total / 2, top, cx + total / 2, bottom)


def main():
    scene = Image.open(SCENE).convert("RGB")
    # Square crop keeping the ice lighthouse (right of centre) and the
    # warm village glow at the left edge: 1280-wide window from x=320.
    crop = scene.crop((320, 0, 1600, 1280))
    poster = crop.resize((SIZE, SIZE), Image.LANCZOS)

    # Soft dark scrim behind the top type zone so the name stays legible
    # against the bright aurora ribbons.
    scrim = Image.new("L", (SIZE, SIZE), 0)
    sd = ImageDraw.Draw(scrim)
    for y in range(0, 300):
        alpha = int(150 * max(0.0, 1.0 - y / 300.0) ** 1.6)
        sd.line([(0, y), (SIZE, y)], fill=alpha)
    # Soft scrim along the bottom so the mood line reads over the water.
    for y in range(SIZE - 130, SIZE):
        alpha = int(110 * (1.0 - (SIZE - y) / 130.0) ** 1.4)
        sd.line([(0, y), (SIZE, y)], fill=alpha)
    scrim = scrim.filter(ImageFilter.GaussianBlur(6))
    dark = Image.new("RGB", (SIZE, SIZE), (6, 10, 30))
    poster = Image.composite(dark, poster, scrim)

    draw = ImageDraw.Draw(poster)
    ink = (245, 241, 230)          # warm off-white
    shadow = (8, 12, 34)           # deep night blue
    accent = (168, 224, 178)       # pale aurora green

    # Place name: big serif, wide tracking, top centre.
    name_font = ImageFont.truetype(SERIF_BOLD, 140)
    # Soft shadow for lift off the sky.
    for dx, dy in ((0, 5), (3, 4), (-3, 4)):
        tracked_text(draw, SIZE // 2 + dx, 52 + dy, PLACE, name_font, shadow, tracking=26)
    name_box = tracked_text(draw, SIZE // 2, 52, PLACE, name_font, ink, tracking=26)

    # Thin aurora-green rule under the name.
    rule_y = name_box[3] + 22
    draw.line([(SIZE // 2 - 130, rule_y), (SIZE // 2 + 130, rule_y)],
              fill=accent, width=3)

    # Mood line: small italic serif at the foot of the poster, over the
    # dark water — keeps it clear of the lighthouse and closes the eye
    # path name -> landmark -> horizon -> promise.
    mood_font = ImageFont.truetype(SERIF_ITALIC, 42)
    for dx, dy in ((0, 3), (2, 2), (-2, 2)):
        tracked_text(draw, SIZE // 2 + dx, SIZE - 88 + dy, MOOD, mood_font, shadow, tracking=7)
    tracked_text(draw, SIZE // 2, SIZE - 88, MOOD, mood_font, ink, tracking=7)

    # JPEG content in entry.png: the gate accepts a whole PNG or JPEG.
    # Quality 95 keeps the serif edges crisp; still far under the cap.
    poster.save(OUT, format="JPEG", quality=95, optimize=True, subsampling=1)
    data = open(OUT, "rb").read()
    print(f"entry.png: {len(data)} bytes, sha256={hashlib.sha256(data).hexdigest()}")
    print(f"size limit 1048576: {'OK' if len(data) <= 1048576 else 'TOO BIG'}")


if __name__ == "__main__":
    sys.exit(main())
