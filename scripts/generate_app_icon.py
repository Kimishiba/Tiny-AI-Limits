#!/usr/bin/env python3
"""
Generate macOS AppIcon.icns and iconset for Tiny Screen.app.
Follows Apple macOS Human Interface Guidelines (1024x1024 squircle canvas, drop shadows, multi-res iconset).
"""

import os
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG_DIR = os.path.join(REPO_ROOT, "img")
OUTPUT_DIR = os.path.join(REPO_ROOT, "resources")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_squircle_mask(size, radius):
    """Create a high-resolution antialiased rounded rectangle mask."""
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    r = radius * scale
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, w, h], radius=r, fill=255)
    return mask.resize(size, Image.Resampling.LANCZOS)

def generate_master_1024():
    """Build the master 1024x1024 macOS app icon."""
    canvas_size = (1024, 1024)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    # macOS Big Sur+ standard squircle icon body size & radius
    body_size = (840, 840)
    body_pos = (92, 92)
    radius = 185

    # 1. Drop shadow & squircle geometry
    shadow_offset = (0, 16)
    shadow_blur = 28
    squircle_mask = create_squircle_mask(body_size, radius)
    shadow_img = Image.new("RGBA", (body_size[0] + shadow_blur * 4, body_size[1] + shadow_blur * 4), (0, 0, 0, 0))
    shadow_fill = Image.new("RGBA", shadow_img.size, (0, 0, 0, 140))
    
    # Paste shadow mask into shadow_img
    shadow_mask_padded = Image.new("L", shadow_img.size, 0)
    shadow_mask_padded.paste(squircle_mask, (shadow_blur * 2, shadow_blur * 2))
    shadow_img.paste(shadow_fill, (0, 0), shadow_mask_padded)
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(shadow_blur))

    # Composite shadow onto canvas
    canvas.paste(
        shadow_img,
        (body_pos[0] - shadow_blur * 2 + shadow_offset[0], body_pos[1] - shadow_blur * 2 + shadow_offset[1]),
        shadow_img
    )

    # 2. Icon body background (dark cyber gradient)
    body_bg = Image.new("RGBA", body_size, (0, 0, 0, 0))
    draw_bg = ImageDraw.Draw(body_bg)
    
    # Vertical gradient from deep cyber slate (#181926) to dark obsidian (#0c0d14)
    for y in range(body_size[1]):
        ratio = y / float(body_size[1])
        r = int(24 * (1 - ratio) + 12 * ratio)
        g = int(25 * (1 - ratio) + 13 * ratio)
        b = int(38 * (1 - ratio) + 20 * ratio)
        draw_bg.line([(0, y), (body_size[0], y)], fill=(r, g, b, 255))

    # Add subtle high-tech radial accent glow in the center
    glow = Image.new("RGBA", body_size, (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    draw_glow.ellipse([120, 120, body_size[0] - 120, body_size[1] - 120], fill=(0, 212, 255, 30))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    body_bg.alpha_composite(glow)

    # Add border ring inside squircle
    border_draw = ImageDraw.Draw(body_bg)
    border_draw.rounded_rectangle(
        [2, 2, body_size[0] - 2, body_size[1] - 2],
        radius=radius,
        outline=(255, 255, 255, 45),
        width=3
    )

    # 3. Add foreground branding emblem
    brand_file = os.path.join(IMG_DIR, "boot_logo_cyber.png")
    if not os.path.exists(brand_file):
        brand_file = os.path.join(IMG_DIR, "kimishiba_logo.png")

    if os.path.exists(brand_file):
        brand_img = Image.open(brand_file).convert("RGBA")
        target_brand_size = 640
        brand_resized = brand_img.resize((target_brand_size, target_brand_size), Image.Resampling.LANCZOS)
        
        brand_x = (body_size[0] - target_brand_size) // 2
        brand_y = (body_size[1] - target_brand_size) // 2 - 10
        body_bg.paste(brand_resized, (brand_x, brand_y), brand_resized)

    # 4. Mask body to squircle (reuse cached mask)
    masked_body = Image.new("RGBA", body_size, (0, 0, 0, 0))
    masked_body.paste(body_bg, (0, 0), squircle_mask)

    # 5. Composite body onto canvas
    canvas.paste(masked_body, body_pos, masked_body)

    return canvas

def build_iconset_and_icns():
    """Generate multi-resolution icons and run iconutil to create AppIcon.icns."""
    master = generate_master_1024()
    
    master_png = os.path.join(OUTPUT_DIR, "AppIcon_1024.png")
    master.save(master_png, "PNG")
    print(f"[OK] Master icon generated: {master_png}")

    iconset_dir = os.path.join(OUTPUT_DIR, "AppIcon.iconset")
    if os.path.exists(iconset_dir):
        shutil.rmtree(iconset_dir)
    os.makedirs(iconset_dir, exist_ok=True)

    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    for size, filename in sizes:
        resized = master.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_dir, filename), "PNG")

    print(f"[OK] Generated {len(sizes)} icon resolutions in {iconset_dir}")

    icns_path = os.path.join(OUTPUT_DIR, "AppIcon.icns")
    try:
        subprocess.run(
            ["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
            check=True
        )
        print(f"[OK] Successfully built {icns_path}")
    except Exception as e:
        print(f"[WARN] iconutil failed: {e}")
        return None
    finally:
        shutil.rmtree(iconset_dir, ignore_errors=True)

    return icns_path

if __name__ == "__main__":
    build_iconset_and_icns()
