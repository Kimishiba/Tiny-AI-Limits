#!/usr/bin/env python3
"""
Generate macOS AppIcon.icns and multi-resolution iconset for Tiny Screen.app.
Strictly follows the user's official Neo-Raw Design System (Neo-Brutalist Orange):
- Pure White canvas (#ffffff)
- Solid black 4px border & hard offset shadows (0px blur)
- Embedded Neo-Raw screen device with Vibrant Orange (#ff5f1f) viewport & AI neural spark
- Formatted to Apple macOS Human Interface Guidelines (1024x1024 canvas, 840x840 squircle, r=185).
"""

import os
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGOS_DIR = os.path.join(REPO_ROOT, "assets", "logos")
SVG_SOURCE = os.path.join(LOGOS_DIR, "logo_neobrutalist_gemini.svg")
OUTPUT_DIR = os.path.join(REPO_ROOT, "resources")
APP_BUNDLE_ICON = os.path.join(REPO_ROOT, "Tiny Screen.app", "Contents", "Resources", "AppIcon.icns")
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
    """Build the master 1024x1024 macOS app icon using the Neo-Raw Gemini logo."""
    canvas_size = (1024, 1024)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    body_size = (840, 840)
    body_pos = (92, 92)
    radius = 185

    # 1. macOS System Drop Shadow
    shadow_offset = (0, 16)
    shadow_blur = 28
    squircle_mask = create_squircle_mask(body_size, radius)
    shadow_img = Image.new("RGBA", (body_size[0] + shadow_blur * 4, body_size[1] + shadow_blur * 4), (0, 0, 0, 0))
    shadow_fill = Image.new("RGBA", shadow_img.size, (0, 0, 0, 90))

    shadow_mask_padded = Image.new("L", shadow_img.size, 0)
    shadow_mask_padded.paste(squircle_mask, (shadow_blur * 2, shadow_blur * 2))
    shadow_img.paste(shadow_fill, (0, 0), shadow_mask_padded)
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(shadow_blur))

    canvas.paste(
        shadow_img,
        (body_pos[0] - shadow_blur * 2 + shadow_offset[0], body_pos[1] - shadow_blur * 2 + shadow_offset[1]),
        shadow_img
    )

    # 2. Pure White Body for Neo-Raw aesthetic
    body_bg = Image.new("RGBA", body_size, (255, 255, 255, 255))

    # 3. Render vector SVG using qlmanage
    tmp_dir = "/tmp"
    rendered_png = os.path.join(tmp_dir, f"{os.path.basename(SVG_SOURCE)}.png")
    try:
        subprocess.run(
            ["qlmanage", "-t", "-s", "1024", "-o", tmp_dir, SVG_SOURCE],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if os.path.exists(rendered_png):
            rendered_img = Image.open(rendered_png).convert("RGBA")
            fitted_screen = rendered_img.resize(body_size, Image.Resampling.LANCZOS)
            body_bg.paste(fitted_screen, (0, 0), fitted_screen)
    except Exception as e:
        print(f"[WARN] qlmanage rendering failed ({e}), using default fallback.")

    # 4. Solid Black Border on squircle (Neo-Raw structural stroke)
    draw_border = ImageDraw.Draw(body_bg)
    draw_border.rounded_rectangle(
        [2, 2, body_size[0] - 2, body_size[1] - 2],
        radius=radius,
        outline=(0, 0, 0, 255),
        width=4
    )

    # 5. Mask body to squircle
    masked_body = Image.new("RGBA", body_size, (0, 0, 0, 0))
    masked_body.paste(body_bg, (0, 0), squircle_mask)

    # 6. Composite onto canvas
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

    # Sync to Tiny Screen.app bundle if present
    if os.path.exists(os.path.dirname(APP_BUNDLE_ICON)):
        shutil.copy2(icns_path, APP_BUNDLE_ICON)
        print(f"[OK] Synced AppIcon.icns to bundle: {APP_BUNDLE_ICON}")

    return icns_path

if __name__ == "__main__":
    build_iconset_and_icns()
