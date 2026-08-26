#!/usr/bin/env python3
"""
generate_boot_animation_frames.py
Generates 8 high-resolution RGB565 PROGMEM frames for the GC9A01 240x240 display
featuring the Cyber Kimishiba mascot with spinning 360-degree background cyber circuits.
Also generates 1-bit monochrome frames for SSD1306 128x64 OLED.
"""

import os
import math
from PIL import Image, ImageDraw, ImageFilter

def generate_frames():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_img_path = os.path.join(root_dir, "img", "boot_logo_cyber.png")
    out_header_path = os.path.join(root_dir, "src", "boot_logo_animation.h")
    
    if not os.path.exists(src_img_path):
        print(f"Error: {src_img_path} not found")
        return
        
    logo = Image.open(src_img_path).convert("RGBA")
    w, h = logo.size
    cx, cy = w // 2, h // 2
    
    # 1. Extract Pure 360-degree Circuit Track Ring
    ring_mask = Image.new("L", (w, h), 0)
    draw_rm = ImageDraw.Draw(ring_mask)
    draw_rm.ellipse((cx - 495, cy - 495, cx + 495, cy + 495), fill=255)
    draw_rm.ellipse((cx - 330, cy - 330, cx + 330, cy + 330), fill=0)

    circuit_ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    circuit_ring.paste(logo, (0, 0), ring_mask)

    # Top ear sector patch (replace ear remnants with clean circuit arcs)
    top_mask = Image.new("L", (w, h), 0)
    draw_tm = ImageDraw.Draw(top_mask)
    draw_tm.polygon([(cx, cy), (160, 60), (864, 60)], fill=255)

    circ_rot_left = circuit_ring.rotate(-85, resample=Image.BICUBIC)
    circ_rot_right = circuit_ring.rotate(85, resample=Image.BICUBIC)
    half_top_left = Image.new("L", (w, h), 0)
    ImageDraw.Draw(half_top_left).polygon([(cx, cy), (160, 60), (cx, 60)], fill=255)
    half_top_right = Image.new("L", (w, h), 0)
    ImageDraw.Draw(half_top_right).polygon([(cx, cy), (cx, 60), (864, 60)], fill=255)

    circuit_ring.paste(circ_rot_left, (0, 0), half_top_left)
    circuit_ring.paste(circ_rot_right, (0, 0), half_top_right)

    # 2. Extract Complete Dog Mascot (Head + Visor + Cyber Ears + Neck Collar)
    dog_mask = Image.new("L", (w, h), 0)
    draw_dm = ImageDraw.Draw(dog_mask)
    head_pts = [
        # Left Ear Outer & Tip
        (240, 420), (216, 320), (230, 180), (275, 125), (330, 130), (380, 210), (410, 290),
        # Crown between ears
        (450, 305), (512, 305), (574, 305),
        # Right Ear Tip & Outer
        (614, 290), (644, 210), (694, 130), (749, 125), (794, 180), (808, 320), (784, 420),
        # Right Cheek & Neck
        (804, 520), (784, 620), (730, 715), (640, 755),
        # Bottom Collar
        (512, 770), (384, 755),
        # Left Neck & Cheek
        (294, 715), (240, 620), (220, 520)
    ]
    draw_dm.polygon(head_pts, fill=255)
    dog_mask = dog_mask.filter(ImageFilter.GaussianBlur(3))

    dog_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dog_layer.paste(logo, (0, 0), dog_mask)

    # 3. Extract Static Base HUD ("TINY AI" Bottom Plate)
    badge_mask = Image.new("L", (w, h), 0)
    draw_bm = ImageDraw.Draw(badge_mask)
    draw_bm.polygon([(cx, cy), (160, 960), (864, 960)], fill=255)
    badge_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    badge_layer.paste(logo, (0, 0), badge_mask)

    # Outer Screen Mask
    outer_circle = Image.new("L", (240, 240), 0)
    ImageDraw.Draw(outer_circle).ellipse((0, 0, 239, 239), fill=255)

    NUM_FRAMES = 8
    frame_rgb565_arrays = []

    print(f"Generating {NUM_FRAMES} high-resolution rotation keyframes...")
    for f_idx in range(NUM_FRAMES):
        angle = f_idx * (360.0 / NUM_FRAMES)
        
        comp = Image.new("RGBA", (w, h), (4, 6, 8, 255))
        
        # Rotated Circuit Ring
        rot_ring = circuit_ring.rotate(angle, resample=Image.BICUBIC)
        comp.paste(rot_ring, (0, 0), rot_ring)
        
        # Soft ambient cyan back-glow behind dog
        glow_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_g = ImageDraw.Draw(glow_img)
        draw_g.ellipse((cx - 360, cy - 360, cx + 360, cy + 360), fill=(0, 229, 255, 38))
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(16))
        comp.paste(glow_img, (0, 0), glow_img)
        
        # Overlay Central Mascot
        comp.paste(dog_layer, (0, 0), dog_layer)
        
        # Overlay Bottom Badge
        comp.paste(badge_layer, (0, 0), badge_layer)
        
        # Downsample to 240x240
        frame240 = comp.resize((240, 240), Image.Resampling.LANCZOS).convert("RGB")
        final_frame = Image.new("RGB", (240, 240), (4, 6, 8))
        final_frame.paste(frame240, (0, 0), outer_circle)
        
        # Convert to RGB565
        pixels = list(final_frame.getdata())
        data_565 = []
        for r, g, b in pixels:
            r5 = (r >> 3) & 0x1F
            g6 = (g >> 2) & 0x3F
            b5 = (b >> 3) & 0x1F
            val16 = (r5 << 11) | (g6 << 5) | b5
            data_565.append(val16)
        frame_rgb565_arrays.append(data_565)
        print(f"  Generated Frame {f_idx+1}/{NUM_FRAMES} (angle = {int(angle)}°)")

    # 4. Generate 1-bit Monochrome OLED Frames (48x48 dog with rotating orbit ticks)
    dog_cropped = dog_layer.crop((200, 100, 824, 780))
    dog_oled = dog_cropped.resize((48, 48), Image.Resampling.LANCZOS).convert("L")
    oled_mascot_bytes = []
    for y in range(48):
        for xb in range(0, 48, 8):
            byte_val = 0
            for bit in range(8):
                px = xb + bit
                if px < 48:
                    val = dog_oled.getpixel((px, y))
                    if val > 80:
                        byte_val |= (1 << (7 - bit))
            oled_mascot_bytes.append(byte_val)

    # 5. Write C Header
    header_content = f"""// AUTO-GENERATED BY tools/generate_boot_animation_frames.py
// DO NOT EDIT DIRECTLY

#pragma once
#include <Arduino.h>

#define BOOT_ANIM_FRAME_COUNT {NUM_FRAMES}
#define BOOT_ANIM_FRAME_WIDTH  240
#define BOOT_ANIM_FRAME_HEIGHT 240

// 8x 240x240 RGB565 PROGMEM Frames
"""
    for f_idx, frame_data in enumerate(frame_rgb565_arrays):
        header_content += f"const uint16_t boot_kimishiba_frame_{f_idx}[57600] PROGMEM = {{\n"
        for i in range(0, len(frame_data), 16):
            chunk = frame_data[i:i+16]
            hex_strs = [f"0x{val:04X}" for val in chunk]
            header_content += "    " + ", ".join(hex_strs) + ("," if i + 16 < len(frame_data) else "") + "\n"
        header_content += "};\n\n"

    header_content += "const uint16_t* const boot_kimishiba_frames[BOOT_ANIM_FRAME_COUNT] PROGMEM = {\n"
    for f_idx in range(NUM_FRAMES):
        header_content += f"    boot_kimishiba_frame_{f_idx},\n"
    header_content += "};\n\n"

    # Add OLED 1-bit mascot
    header_content += f"""// OLED SSD1306 1-bit Mascot Bitmap (48x48)
#define OLED_MASCOT_W 48
#define OLED_MASCOT_H 48

const uint8_t oled_kimishiba_mascot[288] PROGMEM = {{
"""
    for i in range(0, len(oled_mascot_bytes), 12):
        chunk = oled_mascot_bytes[i:i+12]
        header_content += "    " + ", ".join([f"0x{val:02X}" for val in chunk]) + ",\n"
    header_content += "};\n"

    with open(out_header_path, "w") as f:
        f.write(header_content)

    print(f"[SUCCESS] Wrote {out_header_path} ({len(frame_rgb565_arrays)*57600*2 // 1024} KB total Flash)")

if __name__ == "__main__":
    generate_frames()
