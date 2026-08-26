#!/usr/bin/env python3
"""
generate_boot_logo_header.py
Converts 240x240 PNG boot logo into an RGB565 C array header (boot_logo.h)
compatible with Arduino_GFX / GC9A01 circular display.
"""

import sys
import os
from PIL import Image

def png_to_rgb565(image_path):
    im = Image.open(image_path).convert("RGB")
    im = im.resize((240, 240), Image.Resampling.LANCZOS)
    
    pixels = list(im.getdata())
    data = []
    
    for r, g, b in pixels:
        r5 = (r >> 3) & 0x1F
        g6 = (g >> 2) & 0x3F
        b5 = (b >> 3) & 0x1F
        val16 = (r5 << 11) | (g6 << 5) | b5
        data.append(val16)
        
    return data

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    img_cyber = os.path.join(root_dir, "img", "boot_logo_cyber_240x240.png")
    img_pixel = os.path.join(root_dir, "img", "boot_logo_pixel_240x240.png")
    out_header = os.path.join(root_dir, "src", "boot_logo.h")
    
    header_content = [
        "// Generated Boot Logo RGB565 Data for GC9A01 240x240 Display",
        "#pragma once",
        "#include <Arduino.h>",
        "",
        "#define BOOT_LOGO_WIDTH  240",
        "#define BOOT_LOGO_HEIGHT 240",
        ""
    ]
    
    if os.path.exists(img_cyber):
        data_cyber = png_to_rgb565(img_cyber)
        header_content.append("const uint16_t boot_logo_cyber[57600] PROGMEM = {")
        for i in range(0, len(data_cyber), 16):
            chunk = data_cyber[i:i+16]
            hex_strs = [f"0x{val:04X}" for val in chunk]
            header_content.append("    " + ", ".join(hex_strs) + ("," if i + 16 < len(data_cyber) else ""))
        header_content.append("};")
        header_content.append("")
        
    with open(out_header, "w") as f:
        f.write("\n".join(header_content) + "\n")
        
    print(f"Generated {out_header} successfully ({len(header_content)} lines).")

if __name__ == "__main__":
    main()
