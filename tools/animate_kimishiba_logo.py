#!/usr/bin/env python3
"""
animate_kimishiba_logo.py
Creates an animated looping GIF of the Kimishiba Option C logo with:
- Natural OLED eye blinking and saccades (^ ^ -> - - -> O O -> ^ ^)
- Neon cyan visor glow & breathing light pulses on typography and collar LEDs
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

SRC_IMAGE_PATH = "/Users/alessandro.longoni/.gemini/antigravity/brain/4f8d6a26-b494-4545-bcec-bce16fdbd51e/kimishiba_profile_logo_1787310238306.jpg"
OUT_GIF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img", "kimishiba_logo_animated.gif")
OUT_PNG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img", "kimishiba_logo.png")

TARGET_SIZE = (600, 600)

def draw_caret_eye(draw, cx, cy, scale=1.0, width_mult=1.0, color=(0, 240, 255), glow_color=(0, 180, 255)):
    # Pixel caret ^
    w = 26 * scale * width_mult
    h = 24 * scale
    thickness = int(7 * scale)
    
    # Outer glow
    for off in range(3, 0, -1):
        c_glow = (int(glow_color[0] * 0.4), int(glow_color[1] * 0.4), int(glow_color[2] * 0.4))
        draw.line([(cx - w, cy + h/2), (cx, cy - h/2), (cx + w, cy + h/2)], fill=c_glow, width=thickness + off*3)
    
    # Main bright caret line
    draw.line([(cx - w, cy + h/2), (cx, cy - h/2), (cx + w, cy + h/2)], fill=color, width=thickness)

def draw_closed_eye(draw, cx, cy, scale=1.0, color=(0, 240, 255), glow_color=(0, 180, 255)):
    # Horizontal blinking slit -
    w = 26 * scale
    thickness = int(6 * scale)
    # Glow
    for off in range(3, 0, -1):
        c_glow = (int(glow_color[0] * 0.4), int(glow_color[1] * 0.4), int(glow_color[2] * 0.4))
        draw.line([(cx - w, cy), (cx + w, cy)], fill=c_glow, width=thickness + off*3)
    draw.line([(cx - w, cy), (cx + w, cy)], fill=color, width=thickness)

def draw_round_eye(draw, cx, cy, scale=1.0, pupil_x=0, pupil_y=0, color=(0, 240, 255), glow_color=(0, 180, 255)):
    # Round wide curious eyes O O
    r = 20 * scale
    thickness = int(6 * scale)
    # Outer glow
    draw.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], outline=glow_color, width=thickness + 4)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=thickness)
    # Center pupil dot
    pr = 6 * scale
    draw.ellipse([cx + pupil_x - pr, cy + pupil_y - pr, cx + pupil_x + pr, cy + pupil_y + pr], fill=color)

def main():
    if not os.path.exists(SRC_IMAGE_PATH):
        print(f"Error: Source image not found at {SRC_IMAGE_PATH}")
        return

    base_img = Image.open(SRC_IMAGE_PATH).convert("RGBA")
    os.makedirs(os.path.dirname(OUT_GIF_PATH), exist_ok=True)
    
    # Save clean static PNG
    base_img.resize(TARGET_SIZE, Image.LANCZOS).save(OUT_PNG_PATH, "PNG", optimize=True)
    print(f"Saved static PNG to {OUT_PNG_PATH}")

    # Build clean background without the eye carets so we can draw custom animated eye frames
    # Eye screen background patch
    visor_bg = base_img.copy()
    draw_patch = ImageDraw.Draw(visor_bg)
    
    # Fill inside visor glass with deep dark glass color (matching original background)
    # Left eye box: x ~ [370, 480], y ~ [395, 470]
    # Right eye box: x ~ [545, 655], y ~ [395, 470]
    dark_glass = (18, 24, 30, 255)
    draw_patch.rounded_rectangle([365, 395, 485, 470], radius=14, fill=dark_glass)
    draw_patch.rounded_rectangle([540, 395, 660, 470], radius=14, fill=dark_glass)
    # Blur slightly to blend smoothly
    blurred_mask = Image.new("L", base_img.size, 0)
    b_draw = ImageDraw.Draw(blurred_mask)
    b_draw.rounded_rectangle([365, 395, 485, 470], radius=14, fill=255)
    b_draw.rounded_rectangle([540, 395, 660, 470], radius=14, fill=255)
    blurred_mask = blurred_mask.filter(ImageFilter.GaussianBlur(5))
    
    clean_base = Image.composite(visor_bg, base_img, blurred_mask)

    # Eye centers on 1024x1024 canvas
    left_cx, left_cy = 428, 432
    right_cx, right_cy = 582, 432

    frames = []
    durations = []

    # Animation script:
    # 1. Normal smiling carets (^ ^)
    # 2. Blink to closed (- -)
    # 3. Glance right
    # 4. Glance left
    # 5. Quick double blink
    # 6. Wide happy eyes (O O)
    # 7. Back to (^ ^) with glowing pulse

    timeline = [
        # (EyeType, open_scale, shift_x, shift_y, glow_pulse, duration_ms)
        ("CARET", 1.0, 0, 0, 0.0, 150),
        ("CARET", 1.0, 0, 0, 0.1, 150),
        ("CARET", 1.0, 0, 0, 0.2, 150),
        # Blink 1
        ("CLOSED", 1.0, 0, 0, 0.3, 40),
        ("CARET", 0.6, 0, 0, 0.4, 40),
        ("CARET", 1.0, 0, 0, 0.5, 120),
        # Glance Right
        ("CARET", 1.0, 14, 0, 0.6, 180),
        ("CARET", 1.0, 18, 0, 0.7, 220),
        ("CARET", 1.0, 18, 0, 0.8, 200),
        # Glance Left
        ("CARET", 1.0, -14, 0, 0.7, 180),
        ("CARET", 1.0, -18, 0, 0.6, 220),
        ("CARET", 1.0, -18, 0, 0.5, 200),
        # Return Center & Double Blink
        ("CARET", 1.0, 0, 0, 0.4, 120),
        ("CLOSED", 1.0, 0, 0, 0.3, 35),
        ("CARET", 0.7, 0, 0, 0.2, 35),
        ("CARET", 1.0, 0, 0, 0.3, 70),
        ("CLOSED", 1.0, 0, 0, 0.4, 35),
        ("CARET", 0.7, 0, 0, 0.5, 35),
        ("CARET", 1.0, 0, 0, 0.6, 150),
        # Curious Round Eyes
        ("ROUND", 1.0, 0, 0, 0.8, 200),
        ("ROUND", 1.0, 0, 0, 0.9, 220),
        ("ROUND", 1.0, 0, 0, 1.0, 220),
        # Back to Caret Smile
        ("CARET", 0.7, 0, 0, 0.8, 50),
        ("CARET", 1.0, 0, 0, 0.6, 150),
        ("CARET", 1.0, 0, 0, 0.3, 150),
    ]

    print("Rendering animation frames...")
    for eye_type, scale, sx, sy, pulse, dur in timeline:
        frame = clean_base.copy()
        draw = ImageDraw.Draw(frame)

        # Pulse brightness for cyan neon elements
        glow_int = int(220 + 35 * math.sin(pulse * math.pi))
        cyan_bright = (int(glow_int * 0.7), glow_int, 255, 255)
        cyan_glow = (0, int(glow_int * 0.8), 255, 180)

        # Draw eyes
        if eye_type == "CARET":
            draw_caret_eye(draw, left_cx + sx, left_cy + sy, scale=scale, color=cyan_bright, glow_color=cyan_glow)
            draw_caret_eye(draw, right_cx + sx, right_cy + sy, scale=scale, color=cyan_bright, glow_color=cyan_glow)
        elif eye_type == "CLOSED":
            draw_closed_eye(draw, left_cx + sx, left_cy + sy, scale=scale, color=cyan_bright, glow_color=cyan_glow)
            draw_closed_eye(draw, right_cx + sx, right_cy + sy, scale=scale, color=cyan_bright, glow_color=cyan_glow)
        elif eye_type == "ROUND":
            draw_round_eye(draw, left_cx + sx, left_cy + sy, scale=scale, pupil_x=sx, pupil_y=sy, color=cyan_bright, glow_color=cyan_glow)
            draw_round_eye(draw, right_cx + sx, right_cy + sy, scale=scale, pupil_x=sx, pupil_y=sy, color=cyan_bright, glow_color=cyan_glow)

        # Resize to target size for crisp GIF
        small_frame = frame.resize(TARGET_SIZE, Image.LANCZOS).convert("RGB")
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
    print(f"Done! Created animated logo GIF: {OUT_GIF_PATH} ({os.path.getsize(OUT_GIF_PATH)} bytes)")

if __name__ == "__main__":
    main()
