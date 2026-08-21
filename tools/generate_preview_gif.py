#!/usr/bin/env python3
"""
generate_preview_gif.py
Generates an animated preview GIF showcasing:
1. Full-screen expressive eye blinking, glancing, and double-blinks
2. Split-screen HUD (Mini face + AI limits + Clock)
3. Detailed AI Quotas screen
4. Time & Weather screen
5. Agent Attention alert flashing screen
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont

W = 128
H = 64
SCALE = 4
OUT_W = W * SCALE
OUT_H = H * SCALE

FONT_5X7 = {
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E], '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46], '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10], '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3C, 0x4A, 0x49, 0x49, 0x30], '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36], '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00], '%': [0x23, 0x13, 0x08, 0x64, 0x62],
    'A': [0x7C, 0x12, 0x11, 0x12, 0x7C], 'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3E, 0x41, 0x41, 0x41, 0x22], 'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41], 'F': [0x7F, 0x09, 0x09, 0x09, 0x06],
    'G': [0x3E, 0x41, 0x49, 0x49, 0x7A], 'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00], 'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
    'K': [0x7F, 0x08, 0x14, 0x22, 0x41], 'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F], 'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E], 'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E], 'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31], 'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F], 'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
    'W': [0x7F, 0x20, 0x18, 0x20, 0x7F], 'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x07, 0x08, 0x70, 0x08, 0x07], 'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00], '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
    '.': [0x00, 0x60, 0x60, 0x00, 0x00], '-': [0x08, 0x08, 0x08, 0x08, 0x08],
    '/': [0x20, 0x10, 0x08, 0x04, 0x02], '>': [0x00, 0x41, 0x22, 0x14, 0x08],
    ',': [0x00, 0x50, 0x30, 0x00, 0x00], '[': [0x00, 0x7F, 0x41, 0x41, 0x00],
    ']': [0x00, 0x41, 0x41, 0x7F, 0x00]
}

def create_raw_frame():
    return [[0 for _ in range(W)] for _ in range(H)]

def set_pixel(fb, x, y, val=1):
    if 0 <= x < W and 0 <= y < H:
        fb[y][x] = 1 if val else 0

def fill_rect(fb, x, y, w, h, val=1):
    for j in range(max(0, y), min(H, y + h)):
        for i in range(max(0, x), min(W, x + w)):
            fb[j][i] = 1 if val else 0

def draw_rect(fb, x, y, w, h, val=1):
    for i in range(x, x + w):
        set_pixel(fb, i, y, val)
        set_pixel(fb, i, y + h - 1, val)
    for j in range(y, y + h):
        set_pixel(fb, x, j, val)
        set_pixel(fb, x + w - 1, j, val)

def fill_round_rect(fb, x, y, w, h, r, val=1):
    fill_rect(fb, x + r, y, w - 2 * r, h, val)
    fill_rect(fb, x, y + r, w, h - 2 * r, val)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                set_pixel(fb, x + r + dx, y + r + dy, val)
                set_pixel(fb, x + w - r + dx, y + r + dy, val)
                set_pixel(fb, x + r + dx, y + h - r + dy, val)
                set_pixel(fb, x + w - r + dx, y + h - r + dy, val)

def draw_char(fb, ch, x, y, size=1, val=1):
    glyph = FONT_5X7.get(ch.upper(), FONT_5X7[' '])
    for c in range(5):
        col = glyph[c]
        for r in range(7):
            if (col >> r) & 1:
                if size == 1:
                    set_pixel(fb, x + c, y + r, val)
                else:
                    fill_rect(fb, x + c * size, y + r * size, size, size, val)

def draw_string(fb, text, x, y, size=1, val=1):
    cur_x = x
    for ch in text:
        draw_char(fb, ch, cur_x, y, size, val)
        cur_x += 5 * size + 1 * size

def draw_eye(fb, cx, cy, width, height, radius, open_pct, pupil_x=0, pupil_y=0):
    eye_h = max(2, int(round(height * open_pct)))
    top_y = cy - eye_h // 2
    fill_round_rect(fb, cx - width // 2, top_y, width, eye_h, radius, 1)
    if open_pct > 0.45 and width > 14:
        pupil_w = max(3, int(round(width * 0.38)))
        pupil_h = max(3, int(round(eye_h * 0.46)))
        px = cx + pupil_x - pupil_w // 2
        py = cy + pupil_y - pupil_h // 2
        fill_rect(fb, px, py, pupil_w, pupil_h, 0)

def draw_progress_bar(fb, x, y, w, h, pct):
    pct = max(0.0, min(1.0, pct))
    draw_rect(fb, x, y, w, h, 1)
    fill_w = int((w - 4) * pct)
    if fill_w > 0:
        fill_rect(fb, x + 2, y + 2, fill_w, h - 4, 1)

def draw_header(fb, title, tag=""):
    draw_string(fb, title, 2, 2, 1, 1)
    if tag:
        tag_w = len(tag) * 6
        draw_string(fb, tag, 126 - tag_w, 2, 1, 1)
    for x in range(W):
        set_pixel(fb, x, 11, 1)

def fb_to_image(fb, color=(0, 240, 255), bg_color=(10, 14, 20)):
    # Render with glowing OLED bezel effect
    img = Image.new("RGB", (OUT_W, OUT_H), bg_color)
    pixels = img.load()
    
    for y in range(H):
        for x in range(W):
            on = fb[y][x] == 1
            pix_col = color if on else bg_color
            for sy in range(SCALE):
                for sx in range(SCALE):
                    # Slight subpixel border for retro OLED grid look
                    if sx == SCALE - 1 or sy == SCALE - 1:
                        dim_r = int(pix_col[0] * (0.85 if on else 0.5))
                        dim_g = int(pix_col[1] * (0.85 if on else 0.5))
                        dim_b = int(pix_col[2] * (0.85 if on else 0.5))
                        pixels[x * SCALE + sx, y * SCALE + sy] = (dim_r, dim_g, dim_b)
                    else:
                        pixels[x * SCALE + sx, y * SCALE + sy] = pix_col
    return img

def main():
    frames = []
    durations = []

    # =========================================================================
    # SCENE 1: Full-Screen Animated Robot Face (Blinking, Glancing, Double-Blink)
    # =========================================================================
    # 1A. Looking Center & First Blink
    blink_sequence = [
        (1.0, 0, 0, 80),   # Open center
        (1.0, 0, 0, 80),
        (0.6, 0, 0, 35),   # Closing
        (0.08, 0, 0, 35),  # Closed
        (0.6, 0, 0, 35),   # Opening
        (1.0, 0, 0, 100),  # Open center
        (1.0, 4, 0, 90),   # Look right
        (1.0, 5, 0, 120),
        (1.0, 5, 0, 120),
        (1.0, -4, 0, 90),  # Look left
        (1.0, -5, 0, 120),
        (1.0, -5, 0, 120),
        (1.0, 0, 0, 90),   # Look center
        # Double-blink burst
        (0.5, 0, 0, 30),
        (0.08, 0, 0, 35),
        (0.6, 0, 0, 30),
        (1.0, 0, 0, 60),
        (0.5, 0, 0, 30),
        (0.08, 0, 0, 35),
        (0.6, 0, 0, 30),
        (1.0, 0, 0, 140),
    ]

    for open_pct, px, py, dur in blink_sequence:
        fb = create_raw_frame()
        draw_eye(fb, 40, 32, 28, 40, 8, open_pct, px, py)
        draw_eye(fb, 88, 32, 28, 40, 8, open_pct, px, py)
        frames.append(fb_to_image(fb))
        durations.append(dur)

    # =========================================================================
    # SCENE 2: Split HUD Screen (Mini Animated Face + AI Meters + Clock)
    # =========================================================================
    split_sequence = [
        (1.0, 0, 0, 100, 0.75, 0.80, "10:58:30"),
        (1.0, 2, 0, 100, 0.75, 0.80, "10:58:31"),
        (0.4, 2, 0, 35, 0.74, 0.80, "10:58:31"),
        (0.08, 2, 0, 35, 0.74, 0.80, "10:58:31"),
        (0.6, 2, 0, 35, 0.74, 0.80, "10:58:31"),
        (1.0, 0, 0, 120, 0.74, 0.80, "10:58:32"),
        (1.0, -2, 0, 120, 0.73, 0.80, "10:58:32"),
        (1.0, 0, 0, 140, 0.73, 0.80, "10:58:33"),
    ]

    for open_pct, px, py, dur, c_pct, a_pct, time_s in split_sequence:
        fb = create_raw_frame()
        # Mini Face on Left
        draw_eye(fb, 16, 32, 18, 26, 5, open_pct, px, py)
        draw_eye(fb, 36, 32, 18, 26, 5, open_pct, px, py)
        # Vertical divider
        for y in range(4, 60, 2):
            set_pixel(fb, 48, y, 1)
        # Right Side HUD
        draw_string(fb, "AI LIMITS", 54, 4, 1, 1)
        draw_string(fb, "C:", 54, 16, 1, 1)
        draw_progress_bar(fb, 66, 16, 58, 7, c_pct)
        draw_string(fb, "A:", 54, 28, 1, 1)
        draw_progress_bar(fb, 66, 28, 58, 7, a_pct)
        draw_string(fb, time_s, 56, 42, 1, 1)
        draw_string(fb, "21.5C OK", 56, 52, 1, 1)
        frames.append(fb_to_image(fb))
        durations.append(dur)

    # =========================================================================
    # SCENE 3: Detailed AI Quotas Screen
    # =========================================================================
    for step in range(8):
        fb = create_raw_frame()
        draw_header(fb, "AI QUOTAS", "ONLINE")
        draw_string(fb, "Claude: 375k/500k", 2, 16, 1, 1)
        draw_progress_bar(fb, 2, 26, 124, 6, 0.75)
        draw_string(fb, "Antigrav: 80% left", 2, 36, 1, 1)
        draw_progress_bar(fb, 2, 46, 124, 6, 0.20)
        draw_string(fb, "Companion Active", 2, 56, 1, 1)
        frames.append(fb_to_image(fb))
        durations.append(150)

    # =========================================================================
    # SCENE 4: Time & Weather Screen
    # =========================================================================
    for step in range(8):
        fb = create_raw_frame()
        draw_header(fb, "TIME & WEATHER", "DESKTOP")
        sec = 30 + step
        time_str = f"10:58:{sec:02d}"
        draw_string(fb, time_str, 16, 18, 2, 1)
        for x in range(4, 124):
            set_pixel(fb, x, 38, 1)
        draw_string(fb, "21.5 C", 4, 46, 1, 1)
        draw_string(fb, "No Rain", 76, 46, 1, 1)
        draw_string(fb, "Desktop Companion", 4, 56, 1, 1)
        frames.append(fb_to_image(fb))
        durations.append(150)

    # =========================================================================
    # SCENE 5: Agent Attention Alert Screen (Flashing Inverted Warning)
    # =========================================================================
    for flash in range(6):
        inverted = (flash % 2 == 1)
        fb = create_raw_frame()
        if inverted:
            fill_rect(fb, 0, 0, W, H, 1)
            # Inverted shocked eyes
            draw_eye(fb, 44, 32, 20, 22, 6, 1.0, 0, 0)
            draw_eye(fb, 84, 32, 20, 22, 6, 1.0, 0, 0)
            # Cutouts
            fill_rect(fb, 42, 30, 4, 4, 1)
            fill_rect(fb, 82, 30, 4, 4, 1)
            draw_string(fb, "! AGENT ATTENTION !", 6, 8, 1, 0)
            draw_string(fb, "PLAN APPROVAL REQ", 12, 50, 1, 0)
            frames.append(fb_to_image(fb, color=(255, 60, 90)))
        else:
            draw_rect(fb, 0, 0, W, H, 1)
            draw_rect(fb, 2, 2, W - 4, H - 4, 1)
            draw_eye(fb, 44, 32, 20, 22, 6, 1.0, 0, 0)
            draw_eye(fb, 84, 32, 20, 22, 6, 1.0, 0, 0)
            draw_string(fb, "! AGENT ATTENTION !", 6, 8, 1, 1)
            draw_string(fb, "PLAN APPROVAL REQ", 12, 50, 1, 1)
            frames.append(fb_to_image(fb, color=(255, 60, 90)))
        durations.append(180)

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img", "oled_companion_demo.gif")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    print(f"Saving {len(frames)} frames to {out_path}...")
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Done! Created preview GIF: {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    main()
