#!/usr/bin/env python3
"""
animate_round_avatar.py
Produces a circular GitHub profile avatar (both static PNG and animated GIF)
with 16-bit pixel art style, eye blinking, saccades, and a glowing neon cyan ring.
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter

SRC_IMAGE_PATH = "/Users/alessandro.longoni/.gemini/antigravity/brain/4f8d6a26-b494-4545-bcec-bce16fdbd51e/kimishiba_16bit_round_avatar_1787316458804.jpg"
OUT_GIF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img", "kimishiba_round_pfp_animated.gif")
OUT_PNG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img", "kimishiba_round_pfp.png")

TARGET_SIZE = (600, 600)
PIXEL_BLOCK = 6

def draw_pixel_rect(draw, x, y, w, h, color):
    draw.rectangle([x, y, x + w, y + h], fill=color)

def draw_16bit_caret_eye(draw, cx, cy, color=(0, 240, 255), glow_color=(0, 180, 255)):
    p = PIXEL_BLOCK
    offsets = [
        (-4, 2), (-3, 2), (-3, 1), (-2, 0), (-2, -1), (-1, -2), (0, -3), (1, -3),
        (2, -2), (2, -1), (3, 0), (3, 1), (4, 2), (5, 2)
    ]
    for ox, oy in offsets:
        draw_pixel_rect(draw, cx + ox*p - p, cy + oy*p - p, p*3, p*3, (0, 140, 220, 90))
    for ox, oy in offsets:
        draw_pixel_rect(draw, cx + ox*p, cy + oy*p, p, p, color)

def draw_16bit_closed_eye(draw, cx, cy, color=(0, 240, 255), glow_color=(0, 180, 255)):
    p = PIXEL_BLOCK
    for ox in range(-5, 6):
        draw_pixel_rect(draw, cx + ox*p - p//2, cy - p//2, p*2, p*2, (0, 140, 220, 90))
    for ox in range(-5, 6):
        draw_pixel_rect(draw, cx + ox*p, cy, p, p, color)

def draw_16bit_round_eye(draw, cx, cy, pupil_ox=0, pupil_oy=0, color=(0, 240, 255), glow_color=(0, 180, 255)):
    p = PIXEL_BLOCK
    ring = [
        (-3, -2), (-2, -3), (-1, -3), (0, -3), (1, -3), (2, -3), (3, -2),
        (-3, 2), (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3), (3, 2),
        (-3, -1), (-3, 0), (-3, 1),
        (3, -1), (3, 0), (3, 1)
    ]
    for ox, oy in ring:
        draw_pixel_rect(draw, cx + ox*p, cy + oy*p, p, p, color)
    for px in range(-1, 2):
        for py in range(-1, 2):
            draw_pixel_rect(draw, cx + (pupil_ox + px)*p, cy + (pupil_oy + py)*p, p, p, color)

def main():
    if not os.path.exists(SRC_IMAGE_PATH):
        print(f"Error: Source image not found at {SRC_IMAGE_PATH}")
        return

    base_img = Image.open(SRC_IMAGE_PATH).convert("RGBA")
    os.makedirs(os.path.dirname(OUT_GIF_PATH), exist_ok=True)
    
    # Save static round PNG
    static_png = base_img.resize(TARGET_SIZE, Image.NEAREST)
    static_png.save(OUT_PNG_PATH, "PNG", optimize=True)
    print(f"Saved static round PFP to {OUT_PNG_PATH}")

    # Build clean background inside 16-bit visor screen
    visor_bg = base_img.copy()
    draw_patch = ImageDraw.Draw(visor_bg)
    dark_glass = (12, 18, 26, 255)
    draw_patch.rectangle([340, 455, 470, 545], fill=dark_glass)
    draw_patch.rectangle([535, 455, 665, 545], fill=dark_glass)
    
    blurred_mask = Image.new("L", base_img.size, 0)
    b_draw = ImageDraw.Draw(blurred_mask)
    b_draw.rectangle([340, 455, 470, 545], fill=255)
    b_draw.rectangle([535, 455, 665, 545], fill=255)
    blurred_mask = blurred_mask.filter(ImageFilter.GaussianBlur(3))
    
    clean_base = Image.composite(visor_bg, base_img, blurred_mask)

    left_cx, left_cy = 402, 500
    right_cx, right_cy = 600, 500

    timeline = [
        ("CARET", 0, 0, 0.0, 150),
        ("CARET", 0, 0, 0.1, 150),
        ("CARET", 0, 0, 0.2, 150),
        # Blink 1
        ("CLOSED", 0, 0, 0.3, 40),
        ("CLOSED", 0, 0, 0.4, 40),
        ("CARET", 0, 0, 0.5, 120),
        # Look Right
        ("CARET", 2, 0, 0.6, 180),
        ("CARET", 3, 0, 0.7, 220),
        ("CARET", 3, 0, 0.8, 200),
        # Look Left
        ("CARET", -2, 0, 0.7, 180),
        ("CARET", -3, 0, 0.6, 220),
        ("CARET", -3, 0, 0.5, 200),
        # Center & Double Blink
        ("CARET", 0, 0, 0.4, 120),
        ("CLOSED", 0, 0, 0.3, 35),
        ("CARET", 0, 0, 0.2, 70),
        ("CLOSED", 0, 0, 0.4, 35),
        ("CARET", 0, 0, 0.6, 150),
        # Curious Round Eyes
        ("ROUND", 0, 0, 0.8, 200),
        ("ROUND", 0, 0, 0.9, 220),
        ("ROUND", 0, 0, 1.0, 220),
        # Back to Caret Smile
        ("CARET", 0, 0, 0.6, 150),
        ("CARET", 0, 0, 0.3, 150),
    ]

    frames = []
    durations = []

    print("Rendering circular 16-bit animation frames...")
    for eye_type, sx, sy, pulse, dur in timeline:
        frame = clean_base.copy()
        draw = ImageDraw.Draw(frame)

        glow_int = int(220 + 35 * math.sin(pulse * math.pi))
        cyan_bright = (int(glow_int * 0.7), glow_int, 255, 255)
        cyan_glow = (0, int(glow_int * 0.8), 255, 180)

        p = PIXEL_BLOCK
        if eye_type == "CARET":
            draw_16bit_caret_eye(draw, left_cx + sx*p, left_cy + sy*p, color=cyan_bright, glow_color=cyan_glow)
            draw_16bit_caret_eye(draw, right_cx + sx*p, right_cy + sy*p, color=cyan_bright, glow_color=cyan_glow)
        elif eye_type == "CLOSED":
            draw_16bit_closed_eye(draw, left_cx + sx*p, left_cy + sy*p, color=cyan_bright, glow_color=cyan_glow)
            draw_16bit_closed_eye(draw, right_cx + sx*p, right_cy + sy*p, color=cyan_bright, glow_color=cyan_glow)
        elif eye_type == "ROUND":
            draw_16bit_round_eye(draw, left_cx, left_cy, pupil_ox=sx, pupil_oy=sy, color=cyan_bright, glow_color=cyan_glow)
            draw_16bit_round_eye(draw, right_cx, right_cy, pupil_ox=sx, pupil_oy=sy, color=cyan_bright, glow_color=cyan_glow)

        small_frame = frame.resize(TARGET_SIZE, Image.NEAREST).convert("RGB")
        frames.append(small_frame)
        durations.append(dur)

    print(f"Saving {len(frames)} frames to {OUT_GIF_PATH}...")
    frames[0].save(
        OUT_GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Done! Created round animated avatar: {OUT_GIF_PATH} ({os.path.getsize(OUT_GIF_PATH)} bytes)")

if __name__ == "__main__":
    main()
