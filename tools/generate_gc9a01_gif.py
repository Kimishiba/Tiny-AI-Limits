#!/usr/bin/env python3
"""
Generate high-fidelity animated demonstration GIF for the GC9A01 240x240 Circular Display.
Demonstrates:
1. Continuous dual circular telemetry arcs (Claude & Antigravity)
2. 2x2 mechanical split-flap flip clock digit animations
3. Top crown rain indicator & stacked weather sub-HUD
4. Agent Attention Alert mode transition with pulsing warning badge
5. Robot Companion animated mascot glance
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont

def create_circular_mask(size):
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask

def get_font(size):
    for font_name in ["arial.ttf", "segoeui.ttf", "calibri.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(font_name, size)
        except:
            pass
    return ImageFont.load_default()

def draw_curved_text(draw, text, cx, cy, radius, center_angle_deg, font, color):
    # Total angular spread for text
    char_count = len(text)
    spread_deg = 36.0
    start_ang = center_angle_deg - spread_deg / 2.0
    step = spread_deg / max(1, char_count - 1)
    
    for i, ch in enumerate(text):
        ang_rad = math.radians(start_ang + i * step)
        x = cx + radius * math.cos(ang_rad)
        y = cy + radius * math.sin(ang_rad)
        draw.text((x, y), ch, fill=color, font=font, anchor="mm")

def render_gc9a01_frame(
    time_str="14:32",
    claude_pct=68.0,
    antigrav_pct=42.0,
    rain_text="RAIN IN 3H",
    bottom_line1="FRI AUG 21",
    bottom_line2="23.5 C",
    alert_mode=False,
    mascot_mode=False,
    mascot_eye_x=0.0
):
    size = 480 # Render at 2x resolution (480x480) for supersampled anti-aliasing
    scale = 2.0
    im = Image.new('RGB', (size, size), (6, 7, 10))
    draw = ImageDraw.Draw(im)
    
    cx, cy = size // 2, size // 2
    r_outer = int(112 * scale)
    r_gauge = int(104 * scale)
    r_inner = int(88 * scale)
    
    # 1. Subtle Outer Dial Ring
    draw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer), outline=(35, 40, 50), width=int(2 * scale))
    
    # 2. Gauge Track Arc Backgrounds
    arc_box = (cx - r_gauge, cy - r_gauge, cx + r_gauge, cy + r_gauge)
    gauge_w = int(8 * scale)
    
    # Left Track (Claude background: 126 deg to 234 deg)
    draw.arc(arc_box, start=126, end=234, fill=(12, 30, 42), width=gauge_w)
    # Right Track (Antigravity background: -54 deg to 54 deg)
    draw.arc(arc_box, start=-54, end=54, fill=(42, 22, 12), width=gauge_w)
    
    # 3. Active Gauge Fills
    c_sweep = (claude_pct / 100.0) * 108.0
    if c_sweep > 0:
        draw.arc(arc_box, start=126, end=126 + c_sweep, fill=(0, 229, 255), width=gauge_w)
        
    a_sweep = (antigrav_pct / 100.0) * 108.0
    if a_sweep > 0:
        draw.arc(arc_box, start=54 - a_sweep, end=54, fill=(255, 122, 0), width=gauge_w)
        
    # Fonts
    font_large = get_font(int(34 * scale))
    font_med = get_font(int(12 * scale))
    font_small = get_font(int(9 * scale))
    font_curved = get_font(int(8 * scale))
    
    # 4. Curved Telemetry Labels inside Gauges
    cld_str = f"CLD {int(claude_pct)}%"
    agy_str = f"AGY {int(antigrav_pct)}%"
    draw_curved_text(draw, cld_str, cx, cy, r_inner, 180.0, font_curved, (0, 200, 230))
    draw_curved_text(draw, agy_str, cx, cy, r_inner, 0.0, font_curved, (255, 140, 0))
    
    # 5. Top Crown Rain Indicator
    draw.text((cx, int(28 * scale)), rain_text, fill=(0, 229, 255) if "RAIN" in rain_text else (160, 175, 190), font=font_small, anchor="mm")
    
    if not mascot_mode:
        # 6. 2x2 Split-Flap Flip Cards
        h_str = time_str.split(":")[0]
        m_str = time_str.split(":")[1]
        digits = [h_str[0], h_str[1], m_str[0], m_str[1]]
        
        card_w, card_h = int(48 * scale), int(54 * scale)
        gap = int(4 * scale)
        
        card_coords = [
            (cx - card_w - gap//2, cy - card_h - gap//2 + int(4*scale)), # Top-Left
            (cx + gap//2,          cy - card_h - gap//2 + int(4*scale)), # Top-Right
            (cx - card_w - gap//2, cy + gap//2 + int(4*scale)),          # Bot-Left
            (cx + gap//2,          cy + gap//2 + int(4*scale))           # Bot-Right
        ]
        
        for idx, (x, y) in enumerate(card_coords):
            # Card Background
            r_c = int(4 * scale)
            draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=r_c, fill=(18, 20, 26), outline=(36, 42, 54), width=int(1*scale))
            
            # Digit
            draw.text((x + card_w//2, y + card_h//2), str(digits[idx]), fill=(240, 245, 255), font=font_large, anchor="mm")
            
            # Horizontal Split Crease
            split_y = y + card_h // 2
            draw.line((x, split_y, x + card_w, split_y), fill=(8, 9, 12), width=int(1.5*scale))
            draw.line((x, split_y + int(1*scale), x + card_w, split_y + int(1*scale)), fill=(45, 52, 68), width=int(1*scale))
            
            # Brass Hinge Brackets on Left and Right edges
            hw, hh = int(3 * scale), int(6 * scale)
            draw.rectangle((x - int(1*scale), split_y - hh//2, x + hw, split_y + hh//2), fill=(180, 140, 40))
            draw.rectangle((x + card_w - hw, split_y - hh//2, x + card_w + int(1*scale), split_y + hh//2), fill=(180, 140, 40))
            
        # 7. Bottom Sub-HUD Area
        if alert_mode:
            badge_w = int(128 * scale)
            badge_h = int(18 * scale)
            by = cy + int(70 * scale)
            draw.rounded_rectangle((cx - badge_w//2, by - badge_h//2, cx + badge_w//2, by + badge_h//2), radius=int(4*scale), fill=(255, 95, 31))
            draw.text((cx, by), "APPROVAL REQUIRED", fill=(0, 0, 0), font=font_small, anchor="mm")
        else:
            draw.text((cx, cy + int(64 * scale)), bottom_line1, fill=(140, 155, 175), font=font_small, anchor="mm")
            draw.text((cx, cy + int(78 * scale)), bottom_line2, fill=(240, 245, 255), font=font_med, anchor="mm")
    else:
        # Mascot Mode: Cybernetic Robot Eyes
        eye_w, eye_h = int(36 * scale), int(54 * scale)
        ex_offset = int(mascot_eye_x * scale)
        
        # Left Eye
        lx = cx - int(45 * scale) + ex_offset
        ly = cy - int(10 * scale)
        draw.rounded_rectangle((lx, ly, lx + eye_w, ly + eye_h), radius=int(8*scale), fill=(0, 229, 255))
        draw.rectangle((lx + int(8*scale), ly + int(10*scale), lx + eye_w - int(8*scale), ly + eye_h - int(10*scale)), fill=(6, 7, 10))
        
        # Right Eye
        rx = cx + int(10 * scale) + ex_offset
        ry = cy - int(10 * scale)
        draw.rounded_rectangle((rx, ry, rx + eye_w, ry + eye_h), radius=int(8*scale), fill=(0, 229, 255))
        draw.rectangle((rx + int(8*scale), ry + int(10*scale), rx + eye_w - int(8*scale), ry + eye_h - int(10*scale)), fill=(6, 7, 10))
        
        draw.text((cx, cy + int(68 * scale)), "DESKTOP COMPANION", fill=(0, 229, 255), font=font_small, anchor="mm")

    # Downsample from 480x480 to 240x240 with high quality anti-aliasing
    final_img = im.resize((240, 240), Image.Resampling.LANCZOS)
    
    # Circular mask
    mask = create_circular_mask(240)
    bg = Image.new('RGB', (240, 240), (14, 16, 20))
    bg.paste(final_img, (0, 0), mask)
    
    draw_bg = ImageDraw.Draw(bg)
    draw_bg.ellipse((0, 0, 239, 239), outline=(40, 45, 55), width=2)
    return bg

def main():
    print("Generating GC9A01 animated demonstration frames...")
    frames = []
    durations = []
    
    # Sequence 1: Flip Clock Telemetry Fill & Minute Transition (Frames 0-25)
    for i in range(25):
        t = i / 24.0
        c_pct = 20.0 + t * 48.0 # 20% -> 68%
        a_pct = 10.0 + t * 32.0 # 10% -> 42%
        m_digit = "32" if i < 15 else "33"
        time_s = f"14:{m_digit}"
        frame = render_gc9a01_frame(time_str=time_s, claude_pct=c_pct, antigrav_pct=a_pct, rain_text="RAIN IN 3H", bottom_line1="FRI AUG 21", bottom_line2="23.5 C")
        frames.append(frame)
        durations.append(80)
        
    # Sequence 2: Agent Attention Alert Mode Flash (Frames 25-35)
    for i in range(10):
        alert_on = (i % 4 < 2)
        frame = render_gc9a01_frame(time_str="14:33", claude_pct=68.0, antigrav_pct=42.0, rain_text="ALERT ACTIVE", bottom_line1="", bottom_line2="", alert_mode=alert_on)
        frames.append(frame)
        durations.append(140)
        
    # Sequence 3: Companion Mascot Glance (Frames 36-48)
    eye_positions = [0, 0, 4, 8, 8, 4, 0, -4, -8, -8, -4, 0, 0]
    for ex in eye_positions:
        frame = render_gc9a01_frame(claude_pct=68.0, antigrav_pct=42.0, rain_text="ONLINE", mascot_mode=True, mascot_eye_x=ex)
        frames.append(frame)
        durations.append(100)
        
    os.makedirs("round 240x240/assets", exist_ok=True)
    output_path = "round 240x240/assets/gc9a01_round_display_demo.gif"
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"[SUCCESS] Saved animated GC9A01 demonstration GIF to {output_path} ({len(frames)} frames)")

if __name__ == "__main__":
    main()
