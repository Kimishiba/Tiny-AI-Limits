#!/usr/bin/env python3
import math
import os
import shutil
from PIL import Image, ImageDraw, ImageFont

ARTIFACT_DIR = "/Users/alessandrolongoni/.gemini/antigravity/brain/5a950c28-e828-469f-9a96-75d1aec7357e"
OUTPUT_DIR = os.path.join(ARTIFACT_DIR, "animations")
REPO_DOCS_DIR = "/Users/alessandrolongoni/Documents/Antigravity/Tiny AI Limits/docs/assets/concepts"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPO_DOCS_DIR, exist_ok=True)

def create_circular_mask(size):
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask

def get_font(size):
    for font_name in [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "DejaVuSans.ttf",
        "arial.ttf"
    ]:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            pass
    return ImageFont.load_default()

def draw_curved_text(draw, text, cx, cy, radius, center_angle_deg, font, color):
    char_count = len(text)
    spread_deg = 36.0
    start_ang = center_angle_deg - spread_deg / 2.0
    step = spread_deg / max(1, char_count - 1)
    for i, ch in enumerate(text):
        ang_rad = math.radians(start_ang + i * step)
        x = cx + radius * math.cos(ang_rad)
        y = cy + radius * math.sin(ang_rad)
        draw.text((x, y), ch, fill=color, font=font, anchor="mm")

def draw_top_arc_pixels(draw, cx, cy, r_min, r_max, color_func):
    """Draws pixel-accurate crown arc from 246 deg to 294 deg (center = 270 deg)."""
    deg = 246.0
    while deg <= 294.0:
        rad = math.radians(deg)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        for r in range(r_min, r_max + 1):
            x = cx + cos_r * r
            y = cy + sin_r * r
            col = color_func(deg, r)
            if col is not None:
                draw.rectangle((x - 0.5, y - 0.5, x + 0.5, y + 0.5), fill=col)
        deg += 0.5

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t)
    )

def render_base_ui(draw, size, scale, cx, cy):
    r_outer = int(116 * scale)
    r_gauge = int(104 * scale)
    r_inner = int(88 * scale)
    
    # Static outer gunmetal bezel
    draw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer), outline=(31, 35, 48), width=int(2 * scale))
    
    # Left Gauge (Claude Cyan 126..234)
    arc_box = (cx - r_gauge, cy - r_gauge, cx + r_gauge, cy + r_gauge)
    gauge_w = int(7 * scale)
    draw.arc(arc_box, start=126, end=234, fill=(12, 30, 42), width=gauge_w)
    c_sweep = 0.68 * 108.0
    draw.arc(arc_box, start=126, end=126 + c_sweep, fill=(0, 229, 255), width=gauge_w)
    
    # Right Gauge (Antigravity Orange -54..54)
    draw.arc(arc_box, start=-54, end=54, fill=(42, 22, 12), width=gauge_w)
    a_sweep = 0.42 * 108.0
    draw.arc(arc_box, start=54 - a_sweep, end=54, fill=(255, 122, 0), width=gauge_w)
    
    # Micro HUD badges
    font_badge = get_font(int(8 * scale))
    font_large = get_font(int(32 * scale))
    font_small = get_font(int(9 * scale))
    font_med = get_font(int(11 * scale))
    
    draw_curved_text(draw, "CLD 68%", cx, cy, r_inner, 180.0, font_badge, (0, 200, 230))
    draw_curved_text(draw, "AGY 42%", cx, cy, r_inner, 0.0, font_badge, (255, 140, 0))
    
    # Weather text under crown
    draw.text((cx, cy - int(92 * scale)), "NO RAIN", fill=(148, 163, 184), font=font_small, anchor="mm")
    
    # Center Split Flap Clock
    digits = ["1", "4", "3", "2"]
    card_w, card_h = int(44 * scale), int(50 * scale)
    gap = int(4 * scale)
    card_coords = [
        (cx - card_w - gap//2, cy - card_h - gap//2 + int(4*scale)),
        (cx + gap//2,          cy - card_h - gap//2 + int(4*scale)),
        (cx - card_w - gap//2, cy + gap//2 + int(4*scale)),
        (cx + gap//2,          cy + gap//2 + int(4*scale))
    ]
    for idx, (x, y) in enumerate(card_coords):
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=int(4*scale), fill=(18, 20, 26), outline=(36, 42, 54), width=int(1*scale))
        draw.text((x + card_w//2, y + card_h//2), digits[idx], fill=(240, 245, 255), font=font_large, anchor="mm")
        split_y = y + card_h // 2
        draw.line((x, split_y, x + card_w, split_y), fill=(8, 9, 12), width=int(1.5*scale))
    
    # Bottom HUD
    draw.text((cx, cy + int(64 * scale)), "FRI AUG 21", fill=(140, 155, 175), font=font_small, anchor="mm")
    draw.text((cx, cy + int(78 * scale)), "23.5 C", fill=(240, 245, 255), font=font_med, anchor="mm")

def finalize_frame(im, size=240):
    final_img = im.resize((size, size), Image.Resampling.LANCZOS)
    mask = create_circular_mask(size)
    bg = Image.new('RGB', (size, size), (10, 12, 16))
    bg.paste(final_img, (0, 0), mask)
    draw_bg = ImageDraw.Draw(bg)
    draw_bg.ellipse((0, 0, size - 1, size - 1), outline=(35, 40, 50), width=2)
    return bg

def save_and_copy(frames, durations, filename):
    out_artifact = os.path.join(OUTPUT_DIR, filename)
    out_docs = os.path.join(REPO_DOCS_DIR, filename)
    frames[0].save(out_artifact, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    frames[0].save(out_docs, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"Saved: {out_artifact}")

# ==========================================
# 1. CONCEPT A: TELEMETRY PACKET PING
# ==========================================
def generate_concept_a_ping():
    print("Generating Concept A: Telemetry Packet Ping...")
    frames = []
    durations = []
    num_frames = 34 # ~1.7s loop
    
    c_dim = (0, 68, 34)
    c_bright = (0, 255, 136)
    c_glow = (190, 255, 225)
    
    scale = 2.0
    size = int(240 * scale)
    cx, cy = size // 2, size // 2
    r_min, r_max = int(101 * scale), int(107 * scale)
    
    for f in range(num_frames):
        im = Image.new('RGB', (size, size), (6, 7, 10))
        draw = ImageDraw.Draw(im)
        render_base_ui(draw, size, scale, cx, cy)
        
        # Ping begins at frame 4, lasts 16 frames
        ping_frame = f - 4
        
        def color_func(deg, r):
            if ping_frame < 0 or ping_frame > 18:
                return c_dim
            progress = ping_frame / 18.0
            dist = abs(deg - 270.0) # 0 to 24
            wave_front = progress * 28.0
            dist_to_wave = abs(dist - wave_front)
            
            if dist_to_wave < 4.0:
                intensity = 1.0 - (dist_to_wave / 4.0)
                fade = max(0.0, 1.0 - progress * 0.7)
                col = lerp_color(c_bright, c_glow, intensity * fade)
                return lerp_color(c_dim, col, intensity * fade)
            else:
                tail = max(0.0, 1.0 - progress) * 0.3
                return lerp_color(c_dim, c_bright, tail)
        
        draw_top_arc_pixels(draw, cx, cy, r_min, r_max, color_func)
        frames.append(finalize_frame(im))
        durations.append(50)
        
    save_and_copy(frames, durations, "concept_a_telemetry_ping.gif")

# ==========================================
# 2. CONCEPT B: BIOLUMINESCENT BREATHING GLOW
# ==========================================
def generate_concept_b_breath():
    print("Generating Concept B: Bioluminescent Breathing Glow...")
    frames = []
    durations = []
    num_frames = 36 # 1.8s loop
    
    c_dim = (0, 75, 38)
    c_mid = (0, 190, 100)
    c_neon = (0, 255, 136)
    c_high = (150, 255, 205)
    
    scale = 2.0
    size = int(240 * scale)
    cx, cy = size // 2, size // 2
    r_min, r_max = int(101 * scale), int(107 * scale)
    
    for f in range(num_frames):
        im = Image.new('RGB', (size, size), (6, 7, 10))
        draw = ImageDraw.Draw(im)
        render_base_ui(draw, size, scale, cx, cy)
        
        t = f / num_frames
        sine_val = (math.sin(t * 2 * math.pi - math.pi/2) + 1.0) / 2.0
        breath = sine_val ** 1.3
        
        current_col = lerp_color(c_dim, c_neon, breath)
        current_core = lerp_color(c_mid, c_high, breath)
        
        def color_func(deg, r):
            r_ratio = abs(r - (r_min + r_max)/2.0) / ((r_max - r_min)/2.0)
            if r_ratio < 0.35 and breath > 0.5:
                return lerp_color(current_col, current_core, (1.0 - r_ratio) * (breath - 0.4) * 1.8)
            return current_col
            
        draw_top_arc_pixels(draw, cx, cy, r_min, r_max, color_func)
        frames.append(finalize_frame(im))
        durations.append(50)
        
    save_and_copy(frames, durations, "concept_b_breathing_glow.gif")

# ==========================================
# 3. CONCEPT C: PHOTON COMET SWEEP
# ==========================================
def generate_concept_c_sweep():
    print("Generating Concept C: Photon Comet / Radar Sweep...")
    frames = []
    durations = []
    num_frames = 36 # 1.8s loop
    
    c_bg = (0, 50, 25)
    c_bright = (0, 255, 136)
    c_bead = (220, 255, 240)
    
    scale = 2.0
    size = int(240 * scale)
    cx, cy = size // 2, size // 2
    r_min, r_max = int(101 * scale), int(107 * scale)
    
    for f in range(num_frames):
        im = Image.new('RGB', (size, size), (6, 7, 10))
        draw = ImageDraw.Draw(im)
        render_base_ui(draw, size, scale, cx, cy)
        
        t = f / num_frames
        head_pos = 270.0 + 22.0 * math.sin(t * 2 * math.pi)
        velocity = math.cos(t * 2 * math.pi)
        
        def color_func(deg, r):
            dist = abs(deg - head_pos)
            if dist < 2.2:
                return lerp_color(c_bright, c_bead, 1.0 - (dist / 2.2))
            
            is_tail = (deg < head_pos and velocity > 0) or (deg > head_pos and velocity < 0)
            if is_tail and dist < 18.0:
                tail_intensity = (1.0 - (dist / 18.0)) ** 1.5
                return lerp_color(c_bg, c_bright, tail_intensity * 0.9)
            
            if dist < 6.0:
                return lerp_color(c_bg, c_bright, (1.0 - dist/6.0)*0.5)
            return c_bg
            
        draw_top_arc_pixels(draw, cx, cy, r_min, r_max, color_func)
        frames.append(finalize_frame(im))
        durations.append(50)
        
    save_and_copy(frames, durations, "concept_c_photon_sweep.gif")

# ==========================================
# 4. CONCEPT D: SEGMENTED MARQUEE BEADS
# ==========================================
def generate_concept_d_marquee():
    print("Generating Concept D: Segmented Marquee Beads...")
    frames = []
    durations = []
    num_frames = 30 # 1.5s loop
    
    c_off = (10, 36, 22)
    c_dim = (0, 80, 42)
    c_bright = (0, 255, 136)
    c_white = (210, 255, 235)
    
    scale = 2.0
    size = int(240 * scale)
    cx, cy = size // 2, size // 2
    r_min, r_max = int(101 * scale), int(107 * scale)
    
    # 5 segments centered at 250, 260, 270, 280, 290
    segments = [250.0, 260.0, 270.0, 280.0, 290.0]
    
    for f in range(num_frames):
        im = Image.new('RGB', (size, size), (6, 7, 10))
        draw = ImageDraw.Draw(im)
        render_base_ui(draw, size, scale, cx, cy)
        
        t = f / num_frames
        wave_pos = (t * len(segments)) % len(segments)
        
        def color_func(deg, r):
            in_seg = False
            seg_idx = -1
            for idx, s_center in enumerate(segments):
                if abs(deg - s_center) <= 3.2:
                    in_seg = True
                    seg_idx = idx
                    break
            if not in_seg:
                return None
            
            seg_dist = abs(seg_idx - wave_pos)
            if seg_dist > len(segments) / 2:
                seg_dist = len(segments) - seg_dist
                
            intensity = max(0.0, 1.0 - (seg_dist / 1.5))
            if intensity > 0.65:
                return lerp_color(c_bright, c_white, (intensity - 0.65) / 0.35)
            elif intensity > 0.0:
                return lerp_color(c_dim, c_bright, intensity / 0.65)
            else:
                return c_off
                
        draw_top_arc_pixels(draw, cx, cy, r_min, r_max, color_func)
        frames.append(finalize_frame(im))
        durations.append(50)
        
    save_and_copy(frames, durations, "concept_d_segmented_marquee.gif")

# ==========================================
# 5. CONCEPT E: CONTEXT-AWARE DUAL STATE
# ==========================================
def generate_concept_e_context():
    print("Generating Concept E: Context-Aware Dual State...")
    frames = []
    durations = []
    
    scale = 2.0
    size = int(240 * scale)
    cx, cy = size // 2, size // 2
    r_min, r_max = int(101 * scale), int(107 * scale)
    
    # Phase 1: Calm connected idle breathing (Frames 0..18)
    for f in range(18):
        im = Image.new('RGB', (size, size), (6, 7, 10))
        draw = ImageDraw.Draw(im)
        render_base_ui(draw, size, scale, cx, cy)
        
        t = f / 18.0
        breath = (math.sin(t * 2 * math.pi) + 1.0) / 2.0
        col = lerp_color((0, 70, 36), (0, 200, 105), breath)
        
        def color_func(deg, r):
            return col
        draw_top_arc_pixels(draw, cx, cy, r_min, r_max, color_func)
        frames.append(finalize_frame(im))
        durations.append(60)
        
    # Phase 2: Active Agent Work Telemetry Stream (Frames 18..42)
    for f in range(24):
        im = Image.new('RGB', (size, size), (6, 7, 10))
        draw = ImageDraw.Draw(im)
        render_base_ui(draw, size, scale, cx, cy)
        
        draw.text((cx, cy - int(92 * scale)), "AGENT SYNC", fill=(0, 255, 136), font=get_font(int(9*scale)), anchor="mm")
        
        t = f / 12.0
        pulse_pos = 270.0 + 20.0 * math.sin(t * 2 * math.pi)
        
        def color_func(deg, r):
            dist = abs(deg - pulse_pos)
            if dist < 3.0:
                return (220, 255, 240)
            elif dist < 12.0:
                return lerp_color((0, 80, 42), (0, 255, 136), 1.0 - (dist / 12.0))
            return (0, 80, 42)
            
        draw_top_arc_pixels(draw, cx, cy, r_min, r_max, color_func)
        frames.append(finalize_frame(im))
        durations.append(40)
        
    save_and_copy(frames, durations, "concept_e_context_aware.gif")

if __name__ == "__main__":
    generate_concept_a_ping()
    generate_concept_b_breath()
    generate_concept_c_sweep()
    generate_concept_d_marquee()
    generate_concept_e_context()
    print("All GIFs generated successfully!")
