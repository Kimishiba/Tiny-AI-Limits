#!/usr/bin/env python3
"""
generate_technical_drawing_svg.py
Generates a comprehensive ANSI/ISO engineering blueprint (SVG & PNG)
with all orthographic views, cross-sections, dimensions, and title block
for the GC9A01 1.28" Round Screen Cyberdeck 3D Enclosure.
"""

import os
import math
import subprocess
import xml.etree.ElementTree as ET

def create_svg_blueprint(output_svg_path):
    W, H = 1600, 1100
    
    svg = []
    svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
    <defs>
        <style><![CDATA[
            .bg {{ fill: #0B1118; }}
            .grid {{ stroke: #16222F; stroke-width: 0.75; stroke-dasharray: 2,4; }}
            .major-grid {{ stroke: #1D2D3E; stroke-width: 1.0; }}
            .border-thick {{ stroke: #38BDF8; stroke-width: 3.0; fill: none; }}
            .border-thin {{ stroke: #0284C7; stroke-width: 1.0; fill: none; }}
            
            /* Engineering Geometry Styles */
            .object-visible {{ stroke: #F8FAFC; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
            .object-fill {{ fill: #131E2B; stroke: #38BDF8; stroke-width: 1.8; }}
            .object-hidden {{ stroke: #64748B; stroke-width: 1.2; stroke-dasharray: 4,3; fill: none; }}
            .center-line {{ stroke: #EF4444; stroke-width: 1.0; stroke-dasharray: 14,3,3,3; fill: none; opacity: 0.85; }}
            .section-hatch {{ stroke: #38BDF8; stroke-width: 0.9; opacity: 0.4; }}
            
            /* Dimension & Annotation Styles */
            .dim-line {{ stroke: #38BDF8; stroke-width: 1.0; fill: none; }}
            .dim-ext {{ stroke: #0284C7; stroke-width: 0.8; stroke-dasharray: 2,2; fill: none; }}
            .dim-text {{ fill: #38BDF8; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; font-weight: 600; text-anchor: middle; }}
            .dim-text-sm {{ fill: #38BDF8; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 9.5px; font-weight: 500; }}
            .dim-text-vert {{ fill: #38BDF8; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; font-weight: 600; text-anchor: middle; }}
            .callout-leader {{ stroke: #F59E0B; stroke-width: 1.2; fill: none; }}
            .callout-text {{ fill: #FBBF24; font-family: 'JetBrains Mono', monospace; font-size: 10.5px; font-weight: 700; }}
            
            /* View Titles & Labels */
            .view-title {{ fill: #FFFFFF; font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 14px; font-weight: 700; letter-spacing: 1.5px; text-anchor: middle; }}
            .view-subtitle {{ fill: #94A3B8; font-family: 'JetBrains Mono', monospace; font-size: 10px; text-anchor: middle; }}
            
            /* Title Block */
            .tb-title {{ fill: #FFFFFF; font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 800; letter-spacing: 0.5px; }}
            .tb-label {{ fill: #64748B; font-family: 'JetBrains Mono', monospace; font-size: 8.5px; font-weight: 600; text-transform: uppercase; }}
            .tb-value {{ fill: #38BDF8; font-family: 'JetBrains Mono', monospace; font-size: 10.5px; font-weight: 600; }}
            .tb-brand {{ fill: #F59E0B; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 800; }}
            .accent-gold {{ fill: #F59E0B; stroke: #D97706; }}
            .accent-screen {{ fill: #0F172A; stroke: #0284C7; stroke-width: 1.5; }}
        ]]></style>
        
        <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38BDF8"/>
        </marker>
        <marker id="arrow-gold" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#F59E0B"/>
        </marker>
        <pattern id="hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="8" class="section-hatch" />
        </pattern>
    </defs>
    
    <!-- Dark Engineering Drawing Background -->
    <rect width="{W}" height="{H}" class="bg"/>
    ''')
    
    for x in range(40, W-40, 50):
        cls = "major-grid" if x % 200 == 0 else "grid"
        svg.append(f'<line x1="{x}" y1="40" x2="{x}" y2="{H-40}" class="{cls}"/>')
    for y in range(40, H-40, 50):
        cls = "major-grid" if y % 200 == 0 else "grid"
        svg.append(f'<line x1="40" y1="{y}" x2="{W-40}" y2="{y}" class="{cls}"/>')
        
    svg.append(f'<rect x="30" y="30" width="{W-60}" height="{H-60}" class="border-thick"/>')
    svg.append(f'<rect x="36" y="36" width="{W-72}" height="{H-72}" class="border-thin"/>')
    
    def dim_h(x1, x2, y, val_str, ext_y1=None, ext_y2=None, text_offset_y=3.5):
        out = []
        if ext_y1 is not None and ext_y2 is not None:
            out.append(f'<line x1="{x1}" y1="{ext_y1}" x2="{x1}" y2="{y}" class="dim-ext"/>')
            out.append(f'<line x1="{x2}" y1="{ext_y2}" x2="{x2}" y2="{y}" class="dim-ext"/>')
        out.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
        mid_x = (x1 + x2) / 2.0
        text_w = max(40, len(val_str) * 7.5 + 10)
        out.append(f'<rect x="{mid_x - text_w/2}" y="{y-7.5}" width="{text_w}" height="15" fill="#0B1118" opacity="0.95"/>')
        out.append(f'<text x="{mid_x}" y="{y + text_offset_y}" class="dim-text">{val_str}</text>')
        return "".join(out)

    def dim_v(y1, y2, x, val_str, ext_x1=None, ext_x2=None):
        out = []
        if ext_x1 is not None and ext_x2 is not None:
            out.append(f'<line x1="{ext_x1}" y1="{y1}" x2="{x}" y2="{y1}" class="dim-ext"/>')
            out.append(f'<line x1="{ext_x2}" y1="{y2}" x2="{x}" y2="{y2}" class="dim-ext"/>')
        out.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
        mid_y = (y1 + y2) / 2.0
        text_w = max(40, len(val_str) * 7.5 + 10)
        out.append(f'<rect x="{x - text_w/2}" y="{mid_y-7.5}" width="{text_w}" height="15" fill="#0B1118" opacity="0.95"/>')
        out.append(f'<text x="{x}" y="{mid_y+3.5}" class="dim-text-vert">{val_str}</text>')
        return "".join(out)

    def dim_radius(cx, cy, r, angle_deg, val_str, leader_len=35, anchor_override=None, text_dx=5):
        rad = math.radians(angle_deg)
        px = cx + r * math.cos(rad)
        py = cy - r * math.sin(rad)
        lx = px + leader_len * math.cos(rad)
        ly = py - leader_len * math.sin(rad)
        horiz_len = 35 if lx > cx else -35
        hx = lx + horiz_len
        out = []
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{px}" y2="{py}" class="dim-line" stroke-dasharray="2,2"/>')
        out.append(f'<line x1="{px}" y1="{py}" x2="{lx}" y2="{ly}" class="dim-line" marker-start="url(#arrow)"/>')
        out.append(f'<line x1="{lx}" y1="{ly}" x2="{hx}" y2="{ly}" class="dim-line"/>')
        anchor = anchor_override if anchor_override else ("start" if horiz_len > 0 else "end")
        tx = hx + (text_dx if horiz_len > 0 else -text_dx)
        out.append(f'<text x="{tx}" y="{ly-4}" class="dim-text-sm" text-anchor="{anchor}">{val_str}</text>')
        return "".join(out)

    def draw_octagonal_profile(cx, cy, w, c, cls="object-visible"):
        hw = w / 2.0
        pts = [
            (cx - hw + c, cy - hw), (cx + hw - c, cy - hw),
            (cx + hw, cy - hw + c), (cx + hw, cy + hw - c),
            (cx + hw - c, cy + hw), (cx - hw + c, cy + hw),
            (cx - hw, cy + hw - c), (cx - hw, cy - hw + c)
        ]
        pts_str = " ".join([f"{x},{y}" for x, y in pts])
        return f'<polygon points="{pts_str}" class="{cls}"/>'

    # VIEW 1: FRONT ELEVATION
    SCALE = 3.6
    v1_cx, v1_cy = 230, 240
    hw = 54.0 * SCALE / 2.0
    c_px = 6.0 * SCALE
    
    svg.append(f'''
    <!-- VIEW 1: FRONT ELEVATION -->
    <g id="view-front">
        <text x="{v1_cx}" y="65" class="view-title">VIEW A: FRONT ELEVATION</text>
        <text x="{v1_cx}" y="82" class="view-subtitle">BEZEL PLATE &amp; DISPLAY APERTURE (SCALE 1:1)</text>
        
        <line x1="{v1_cx - hw - 30}" y1="{v1_cy}" x2="{v1_cx + hw + 30}" y2="{v1_cy}" class="center-line"/>
        <line x1="{v1_cx}" y1="{v1_cy - hw - 30}" x2="{v1_cx}" y2="{v1_cy + hw + 30}" class="center-line"/>
        
        {draw_octagonal_profile(v1_cx, v1_cy, 54.0 * SCALE, c_px, "object-fill")}
        <circle cx="{v1_cx}" cy="{v1_cy}" r="{44.0 * SCALE / 2.0}" class="object-visible" stroke-dasharray="0" fill="#182535"/>
        <circle cx="{v1_cx}" cy="{v1_cy}" r="{36.0 * SCALE / 2.0}" class="object-hidden"/>
        <circle cx="{v1_cx}" cy="{v1_cy}" r="{34.6 * SCALE / 2.0}" class="object-visible" stroke-width="1.0" opacity="0.6"/>
        <circle cx="{v1_cx}" cy="{v1_cy}" r="{32.6 * SCALE / 2.0}" class="accent-screen"/>
        
        <text x="{v1_cx}" y="{v1_cy - 25}" fill="#64748B" font-family="JetBrains Mono" font-size="8" text-anchor="middle" font-weight="700">RAIN: 2h</text>
        <text x="{v1_cx - 16}" y="{v1_cy + 5}" fill="#F8FAFC" font-family="JetBrains Mono" font-size="20" text-anchor="middle" font-weight="900">12</text>
        <text x="{v1_cx + 16}" y="{v1_cy + 5}" fill="#F8FAFC" font-family="JetBrains Mono" font-size="20" text-anchor="middle" font-weight="900">45</text>
        <path d="M {v1_cx - 38} {v1_cy - 12} A 42 42 0 0 1 {v1_cx - 28} {v1_cy + 36}" fill="none" stroke="#00F0FF" stroke-width="4" stroke-linecap="round"/>
        <path d="M {v1_cx + 38} {v1_cy - 12} A 42 42 0 0 0 {v1_cx + 28} {v1_cy + 36}" fill="none" stroke="#FF7700" stroke-width="4" stroke-linecap="round"/>
    ''')
    
    bolt_dist = 21.0 * SCALE
    for sx in [-bolt_dist, bolt_dist]:
        for sy in [-bolt_dist, bolt_dist]:
            px, py = v1_cx + sx, v1_cy + sy
            svg.append(f'''
            <circle cx="{px}" cy="{py}" r="{4.8 * SCALE / 2.0}" class="accent-gold" fill="#F59E0B" stroke="#D97706" stroke-width="1.2"/>
            <circle cx="{px}" cy="{py}" r="{2.6 * SCALE / 2.0}" class="bg" stroke="#1E293B" stroke-width="1.0"/>
            <circle cx="{px}" cy="{py}" r="{1.2 * SCALE / 2.0}" fill="#0B1118"/>
            <line x1="{px-7}" y1="{py}" x2="{px+7}" y2="{py}" stroke="#D97706" stroke-width="0.8"/>
            <line x1="{px}" y1="{py-7}" x2="{px}" y2="{py+7}" stroke="#D97706" stroke-width="0.8"/>
            ''')
            
    accent_screws = [
        (v1_cx + 15.5 * SCALE, v1_cy - 21.0 * SCALE),
        (v1_cx + 21.0 * SCALE, v1_cy - 15.5 * SCALE),
        (v1_cx - 15.5 * SCALE, v1_cy - 21.0 * SCALE),
        (v1_cx + 21.0 * SCALE, v1_cy + 15.5 * SCALE),
    ]
    for px, py in accent_screws:
        svg.append(f'''
        <circle cx="{px}" cy="{py}" r="{3.4 * SCALE / 2.0}" fill="#F59E0B" stroke="#D97706" stroke-width="1.0"/>
        <circle cx="{px}" cy="{py}" r="{1.8 * SCALE / 2.0}" fill="#0B1118"/>
        ''')
        
    for bx in [-9.63 * SCALE, 9.63 * SCALE]:
        by = -18.91 * SCALE
        svg.append(f'<circle cx="{v1_cx + bx}" cy="{v1_cy + by}" r="{1.8 * SCALE / 2.0}" class="object-hidden" stroke="#EF4444"/>')
        
    svg.append(dim_h(v1_cx - hw, v1_cx + hw, v1_cy + hw + 26, "54.00 mm", ext_y1=v1_cy+hw, ext_y2=v1_cy+hw))
    svg.append(dim_v(v1_cy - hw, v1_cy + hw, v1_cx + hw + 26, "54.00 mm", ext_x1=v1_cx+hw, ext_x2=v1_cx+hw))
    svg.append(dim_h(v1_cx - bolt_dist, v1_cx + bolt_dist, v1_cy - hw - 22, "42.00 mm (PITCH)", ext_y1=v1_cy-bolt_dist, ext_y2=v1_cy-bolt_dist))
    svg.append(dim_radius(v1_cx, v1_cy, 32.6 * SCALE / 2.0, 38, "Ø 32.60 (ACTIVE LCD)", leader_len=60))
    svg.append(dim_radius(v1_cx, v1_cy, 44.0 * SCALE / 2.0, 215, "Ø 44.00 (BEZEL RING)", leader_len=40))
    svg.append(dim_radius(v1_cx - bolt_dist, v1_cy - bolt_dist, 4.8 * SCALE / 2.0, 135, "4x M2 CB Ø4.80", leader_len=25))
    svg.append(f'</g>')

    # VIEW 2: REAR ELEVATION
    v2_cx, v2_cy = 600, 240
    svg.append(f'''
    <!-- VIEW 2: REAR ELEVATION -->
    <g id="view-rear">
        <text x="{v2_cx}" y="65" class="view-title">VIEW B: REAR ELEVATION</text>
        <text x="{v2_cx}" y="82" class="view-subtitle">CHASSIS BACK &amp; DEBOSSED BRANDING (SCALE 1:1)</text>
        
        <line x1="{v2_cx - hw - 30}" y1="{v2_cy}" x2="{v2_cx + hw + 30}" y2="{v2_cy}" class="center-line"/>
        <line x1="{v2_cx}" y1="{v2_cy - hw - 30}" x2="{v2_cx}" y2="{v2_cy + hw + 30}" class="center-line"/>
        
        {draw_octagonal_profile(v2_cx, v2_cy, 54.0 * SCALE, c_px, "object-fill")}
    ''')
    
    for sx in [-bolt_dist, bolt_dist]:
        for sy in [-bolt_dist, bolt_dist]:
            px, py = v2_cx + sx, v2_cy + sy
            svg.append(f'''
            <circle cx="{px}" cy="{py}" r="{4.8 * SCALE / 2.0}" class="accent-gold" fill="#F59E0B" stroke="#D97706" stroke-width="1.2"/>
            <circle cx="{px}" cy="{py}" r="{3.2 * SCALE / 2.0}" fill="#0B1118"/>
            <circle cx="{px}" cy="{py}" r="{1.5 * SCALE / 2.0}" fill="#F59E0B" opacity="0.4"/>
            ''')
            
    svg.append(f'''
        <g transform="translate({v2_cx}, {v2_cy})">
            <polygon points="-8,-28 0,-33 8,-28 8,-18 0,-13 -8,-18" fill="none" stroke="#64748B" stroke-width="1.5"/>
            <circle cx="0" cy="-23" r="2.5" fill="#38BDF8"/>
            <text x="0" y="-2" fill="#94A3B8" font-family="Inter, sans-serif" font-size="12" font-weight="800" letter-spacing="2" text-anchor="middle">CYBER-DECK</text>
            <text x="0" y="14" fill="#64748B" font-family="JetBrains Mono" font-size="9.5" font-weight="700" letter-spacing="3" text-anchor="middle">UNIT 01</text>
            <text x="0" y="32" fill="#475569" font-family="JetBrains Mono" font-size="7" text-anchor="middle">GC9A01 / ESP32-C3 SUPERMINI</text>
        </g>
        <rect x="{v2_cx - hw - 2}" y="{v2_cy - 12}" width="4" height="24" fill="#38BDF8" opacity="0.8"/>
    ''')
    
    cav_px = 44.0 * SCALE
    svg.append(f'<rect x="{v2_cx - cav_px/2}" y="{v2_cy - cav_px/2}" width="{cav_px}" height="{cav_px}" class="object-hidden" rx="4"/>')
    svg.append(dim_h(v2_cx - cav_px/2, v2_cx + cav_px/2, v2_cy + hw + 26, "44.00 mm (CAVITY)", ext_y1=v2_cy+cav_px/2, ext_y2=v2_cy+cav_px/2))
    svg.append(dim_h(v2_cx - bolt_dist, v2_cx + bolt_dist, v2_cy - hw - 22, "42.00 mm (PITCH)", ext_y1=v2_cy-bolt_dist, ext_y2=v2_cy-bolt_dist))
    svg.append(f'</g>')

    # VIEW 3: LEFT SIDE ELEVATION
    v3_cx, v3_cy = 980, 240
    depth_px = 36.0 * SCALE
    bezel_t_px = 4.5 * SCALE
    housing_d_px = depth_px - bezel_t_px
    
    svg.append(f'''
    <!-- VIEW 3: LEFT SIDE ELEVATION -->
    <g id="view-side">
        <text x="{v3_cx}" y="65" class="view-title">VIEW C: LEFT SIDE ELEVATION</text>
        <text x="{v3_cx}" y="82" class="view-subtitle">USB-C PORT, BUTTON PORTS &amp; SEAM (SCALE 1:1)</text>
        
        <line x1="{v3_cx - depth_px/2 - 25}" y1="{v3_cy}" x2="{v3_cx + depth_px/2 + 25}" y2="{v3_cy}" class="center-line"/>
        
        <rect x="{v3_cx - depth_px/2}" y="{v3_cy - hw}" width="{housing_d_px}" height="{54.0 * SCALE}" class="object-fill"/>
        <rect x="{v3_cx - depth_px/2 + housing_d_px}" y="{v3_cy - hw}" width="{bezel_t_px}" height="{54.0 * SCALE}" class="object-visible" fill="#1E293B"/>
        <rect x="{v3_cx + depth_px/2}" y="{v3_cy - 44.0*SCALE/2}" width="{1.5 * SCALE}" height="{44.0 * SCALE}" class="object-visible" fill="#38BDF8"/>
        
        <rect x="{v3_cx - depth_px/2 + 2.5*SCALE}" y="{v3_cy - 4.0*SCALE}" width="{13.0 * SCALE}" height="{8.0 * SCALE}" rx="{4.0 * SCALE}" class="accent-screen" stroke="#38BDF8" stroke-width="1.8"/>
        <text x="{v3_cx - depth_px/2 + 9.0*SCALE}" y="{v3_cy + 3.0}" fill="#38BDF8" font-family="JetBrains Mono" font-size="8" font-weight="700" text-anchor="middle">USB-C</text>
        
        <circle cx="{v3_cx - depth_px/2 + 20.0*SCALE}" cy="{v3_cy - 14.0*SCALE}" r="{3.2 * SCALE / 2.0}" class="object-visible" fill="#0B1118"/>
        <circle cx="{v3_cx - depth_px/2 + 20.0*SCALE}" cy="{v3_cy + 14.0*SCALE}" r="{3.2 * SCALE / 2.0}" class="object-visible" fill="#0B1118"/>
    ''')
    
    svg.append(dim_h(v3_cx - depth_px/2, v3_cx + depth_px/2, v3_cy + hw + 26, "36.00 mm (POD DEPTH)", ext_y1=v3_cy+hw, ext_y2=v3_cy+hw))
    svg.append(dim_h(v3_cx + depth_px/2 - bezel_t_px, v3_cx + depth_px/2, v3_cy - hw - 22, "4.50", ext_y1=v3_cy-hw, ext_y2=v3_cy-hw))
    svg.append(dim_h(v3_cx - depth_px/2, v3_cx + depth_px/2 - bezel_t_px, v3_cy - hw - 22, "31.50 mm", ext_y1=v3_cy-hw, ext_y2=v3_cy-hw))
    svg.append(dim_v(v3_cy - 4.0*SCALE, v3_cy + 4.0*SCALE, v3_cx + depth_px/2 + 26, "8.00 (USB-C)", ext_x1=v3_cx-depth_px/2+15.5*SCALE, ext_x2=v3_cx-depth_px/2+15.5*SCALE))
    svg.append(f'</g>')

    # VIEW 4: SECTION A-A CROSS-SECTION
    v4_cx, v4_cy = 1350, 240
    svg.append(f'''
    <!-- VIEW 4: SECTION A-A -->
    <g id="view-section">
        <text x="{v4_cx}" y="65" class="view-title">SECTION A-A: CROSS SECTION</text>
        <text x="{v4_cx}" y="82" class="view-subtitle">INTERNAL POCKET STEPS &amp; DUPONT CAVITY</text>
        
        <line x1="{v4_cx - depth_px/2 - 25}" y1="{v4_cy}" x2="{v4_cx + depth_px/2 + 25}" y2="{v4_cy}" class="center-line"/>
        
        <path d="M {v4_cx - depth_px/2} {v4_cy - hw} 
                 L {v4_cx + depth_px/2} {v4_cy - hw} 
                 L {v4_cx + depth_px/2} {v4_cy - 32.6*SCALE/2} 
                 L {v4_cx + depth_px/2 - 1.5*SCALE} {v4_cy - 36.0*SCALE/2} 
                 L {v4_cx + depth_px/2 - bezel_t_px} {v4_cy - 38.6*SCALE/2} 
                 L {v4_cx + depth_px/2 - bezel_t_px - 4.0*SCALE} {v4_cy - 44.0*SCALE/2} 
                 L {v4_cx - depth_px/2 + 2.5*SCALE} {v4_cy - 44.0*SCALE/2} 
                 L {v4_cx - depth_px/2 + 2.5*SCALE} {v4_cy - hw + 5*SCALE}
                 L {v4_cx - depth_px/2} {v4_cy - hw} Z" 
              fill="url(#hatch)" stroke="#38BDF8" stroke-width="1.8"/>
              
        <path d="M {v4_cx - depth_px/2} {v4_cy + hw} 
                 L {v4_cx + depth_px/2} {v4_cy + hw} 
                 L {v4_cx + depth_px/2} {v4_cy + 32.6*SCALE/2} 
                 L {v4_cx + depth_px/2 - 1.5*SCALE} {v4_cy + 36.0*SCALE/2} 
                 L {v4_cx + depth_px/2 - bezel_t_px} {v4_cy + 38.6*SCALE/2} 
                 L {v4_cx + depth_px/2 - bezel_t_px - 4.0*SCALE} {v4_cy + 44.0*SCALE/2} 
                 L {v4_cx - depth_px/2 + 2.5*SCALE} {v4_cy + 44.0*SCALE/2} 
                 L {v4_cx - depth_px/2 + 2.5*SCALE} {v4_cy + hw - 5*SCALE}
                 L {v4_cx - depth_px/2} {v4_cy + hw} Z" 
              fill="url(#hatch)" stroke="#38BDF8" stroke-width="1.8"/>
              
        <rect x="{v4_cx - depth_px/2 + 2.5*SCALE}" y="{v4_cy - 12*SCALE}" width="{23.0*SCALE}" height="{2.5*SCALE}" fill="#F59E0B" stroke="#D97706"/>
        <rect x="{v4_cx - depth_px/2 + 2.5*SCALE}" y="{v4_cy + 9.5*SCALE}" width="{23.0*SCALE}" height="{2.5*SCALE}" fill="#F59E0B" stroke="#D97706"/>
        <rect x="{v4_cx - depth_px/2 + 25.5*SCALE}" y="{v4_cy - 12*SCALE}" width="{2.5*SCALE}" height="{24*SCALE}" fill="#F59E0B" stroke="#D97706"/>
        
        <rect x="{v4_cx + depth_px/2 - 3.5*SCALE}" y="{v4_cy - 35.6*SCALE/2}" width="{1.6*SCALE}" height="{35.6*SCALE}" fill="#00F0FF" opacity="0.8"/>
        <rect x="{v4_cx + depth_px/2 - 5.1*SCALE}" y="{v4_cy - 38.0*SCALE/2}" width="{1.6*SCALE}" height="{38.0*SCALE}" fill="#10B981" opacity="0.8"/>
    ''')
    
    svg.append(dim_h(v4_cx - depth_px/2 + 2.5*SCALE, v4_cx + depth_px/2 - bezel_t_px - 4.0*SCALE, v4_cy + 15, "29.50 mm (CAVITY DEPTH)", ext_y1=v4_cy-44*SCALE/2, ext_y2=v4_cy-44*SCALE/2))
    svg.append(dim_v(v4_cy - 44*SCALE/2, v4_cy + 44*SCALE/2, v4_cx - depth_px/2 - 35, "44.00 (CAVITY)", ext_x1=v4_cx-depth_px/2+2.5*SCALE, ext_x2=v4_cx-depth_px/2+2.5*SCALE))
    svg.append(dim_h(v4_cx - depth_px/2, v4_cx - depth_px/2 + 2.5*SCALE, v4_cy + hw + 26, "2.50", ext_y1=v4_cy+hw, ext_y2=v4_cy+hw))
    svg.append(f'</g>')

    # VIEW 5: DESK STAND ELEVATION
    S2 = 3.2
    v5_cx, v5_cy = 320, 710
    st_w_px = 64.0 * S2
    st_h_px = 34.0 * S2
    tier1_h_px = 6.0 * S2
    
    svg.append(f'''
    <!-- VIEW 5: DESK STAND ELEVATION & V-SADDLE -->
    <g id="view-stand">
        <text x="{v5_cx}" y="515" class="view-title">VIEW D: TWO-TIER DESK STAND &amp; 22° V-SADDLE</text>
        <text x="{v5_cx}" y="532" class="view-subtitle">ERGONOMIC TILT CRADLE &amp; CABLE CHANNEL (SCALE 1:1)</text>
        
        <line x1="{v5_cx}" y1="545" x2="{v5_cx}" y2="845" class="center-line"/>
        
        <rect x="{v5_cx - st_w_px/2}" y="{v5_cy + st_h_px/2 - tier1_h_px}" width="{st_w_px}" height="{tier1_h_px}" rx="6" fill="#78350F" stroke="#D97706" stroke-width="1.8"/>
        
        <polygon points="{v5_cx - st_w_px/2 + 4*S2},{v5_cy + st_h_px/2 - tier1_h_px} 
                        {v5_cx + st_w_px/2 - 4*S2},{v5_cy + st_h_px/2 - tier1_h_px} 
                        {v5_cx + 27.0*S2},{v5_cy - st_h_px/2} 
                        {v5_cx - 27.0*S2},{v5_cy - st_h_px/2}" 
                 class="object-fill"/>
                 
        <polygon points="{v5_cx - 27.0*S2},{v5_cy - st_h_px/2} 
                        {v5_cx + 27.0*S2},{v5_cy - st_h_px/2} 
                        {v5_cx + 24.0*S2},{v5_cy - st_h_px/2 + 18*S2} 
                        {v5_cx},{v5_cy - st_h_px/2 + 24*S2} 
                        {v5_cx - 24.0*S2},{v5_cy - st_h_px/2 + 18*S2}" 
                 fill="#0B1118" stroke="#38BDF8" stroke-width="1.8"/>
                 
        <rect x="{v5_cx - 8.0*S2}" y="{v5_cy + st_h_px/2 - 14.0*S2}" width="{16.0*S2}" height="{14.0*S2}" class="object-hidden" stroke="#F59E0B"/>
        <rect x="{v5_cx - st_w_px/2 + 6*S2}" y="{v5_cy + st_h_px/2 - 1.5*S2}" width="{8.2*S2}" height="{1.5*S2}" fill="#0284C7"/>
        <rect x="{v5_cx + st_w_px/2 - 6*S2 - 8.2*S2}" y="{v5_cy + st_h_px/2 - 1.5*S2}" width="{8.2*S2}" height="{1.5*S2}" fill="#0284C7"/>
    ''')
    
    svg.append(dim_h(v5_cx - st_w_px/2, v5_cx + st_w_px/2, v5_cy + st_h_px/2 + 32, "64.00 mm (BASE WIDTH)", ext_y1=v5_cy+st_h_px/2, ext_y2=v5_cy+st_h_px/2))
    svg.append(dim_v(v5_cy - st_h_px/2, v5_cy + st_h_px/2, v5_cx + st_w_px/2 + 32, "34.00 mm", ext_x1=v5_cy-st_h_px/2, ext_x2=v5_cy+st_h_px/2))
    svg.append(dim_v(v5_cy + st_h_px/2 - tier1_h_px, v5_cy + st_h_px/2, v5_cx - st_w_px/2 - 28, "6.00", ext_x1=v5_cy+st_h_px/2-tier1_h_px, ext_x2=v5_cy+st_h_px/2))
    svg.append(dim_h(v5_cx - 8.0*S2, v5_cx + 8.0*S2, v5_cy - 10, "16.00 (SLOT)", ext_y1=v5_cy+st_h_px/2-14*S2, ext_y2=v5_cy+st_h_px/2-14*S2))
    svg.append(f'</g>')

    # VIEW 6: ISOMETRIC ASSEMBLY
    iso_cx, iso_cy = 800, 710
    svg.append(f'''
    <!-- VIEW 6: ISOMETRIC 3D CAD PROJECTION -->
    <g id="view-iso">
        <text x="{iso_cx}" y="515" class="view-title">ISOMETRIC 3D DESK CONSOLE ASSEMBLY</text>
        <text x="{iso_cx}" y="532" class="view-subtitle">ORTHOGRAPHIC 30° AXONOMETRIC PERSPECTIVE</text>
        
        <path d="M {iso_cx - 70} {iso_cy + 85} L {iso_cx} {iso_cy + 120} L {iso_cx + 70} {iso_cy + 85} L {iso_cx + 70} {iso_cy + 75} L {iso_cx} {iso_cy + 110} L {iso_cx - 70} {iso_cy + 75} Z" fill="#78350F" stroke="#D97706" stroke-width="1.8"/>
        <path d="M {iso_cx - 50} {iso_cy + 60} L {iso_cx} {iso_cy + 85} L {iso_cx + 50} {iso_cy + 60} L {iso_cx + 40} {iso_cy + 25} L {iso_cx} {iso_cy + 45} L {iso_cx - 40} {iso_cy + 25} Z" fill="#1E293B" stroke="#38BDF8" stroke-width="1.8"/>
        
        <g transform="translate({iso_cx}, {iso_cy}) rotate(-14)">
            <polygon points="-50,-50 50,-50 65,-35 65,35 50,50 -50,50 -65,35 -65,-35" fill="#131E2B" stroke="#38BDF8" stroke-width="2.2"/>
            <circle cx="0" cy="0" r="42" fill="#1E293B" stroke="#38BDF8" stroke-width="1.8"/>
            <circle cx="0" cy="0" r="32" fill="#0B1118" stroke="#00F0FF" stroke-width="1.5"/>
            <text x="-12" y="8" fill="#FFFFFF" font-family="JetBrains Mono" font-size="16" font-weight="900" text-anchor="middle">12</text>
            <text x="12" y="8" fill="#FFFFFF" font-family="JetBrains Mono" font-size="16" font-weight="900" text-anchor="middle">45</text>
            <circle cx="-38" cy="-38" r="4" fill="#F59E0B" stroke="#D97706"/>
            <circle cx="38" cy="-38" r="4" fill="#F59E0B" stroke="#D97706"/>
            <circle cx="-38" cy="38" r="4" fill="#F59E0B" stroke="#D97706"/>
            <circle cx="38" cy="38" r="4" fill="#F59E0B" stroke="#D97706"/>
        </g>
        
        <line x1="{iso_cx - 55}" y1="{iso_cy - 40}" x2="{iso_cx - 100}" y2="{iso_cy - 70}" class="callout-leader" marker-start="url(#arrow-gold)"/>
        <line x1="{iso_cx - 100}" y1="{iso_cy - 70}" x2="{iso_cx - 140}" y2="{iso_cy - 70}" class="callout-leader"/>
        <text x="{iso_cx - 145}" y="{iso_cy - 66}" class="callout-text" text-anchor="end">[1] FRONT BEZEL PLATE (54x54x4.5mm)</text>
        
        <line x1="{iso_cx + 10}" y1="{iso_cy - 5}" x2="{iso_cx + 80}" y2="{iso_cy - 40}" class="callout-leader" marker-start="url(#arrow-gold)"/>
        <line x1="{iso_cx + 80}" y1="{iso_cy - 40}" x2="{iso_cx + 130}" y2="{iso_cy - 40}" class="callout-leader"/>
        <text x="{iso_cx + 135}" y="{iso_cy - 36}" class="callout-text" text-anchor="start">[2] GC9A01 1.28" IPS DISPLAY (240x240)</text>
        
        <line x1="{iso_cx + 60}" y1="{iso_cy + 25}" x2="{iso_cx + 110}" y2="{iso_cy + 15}" class="callout-leader" marker-start="url(#arrow-gold)"/>
        <line x1="{iso_cx + 110}" y1="{iso_cy + 15}" x2="{iso_cx + 150}" y2="{iso_cy + 15}" class="callout-leader"/>
        <text x="{iso_cx + 155}" y="{iso_cy + 19}" class="callout-text" text-anchor="start">[3] DEEP CHASSIS POD (36mm DEPTH)</text>
        
        <line x1="{iso_cx - 40}" y1="{iso_cy + 55}" x2="{iso_cx - 90}" y2="{iso_cy + 50}" class="callout-leader" marker-start="url(#arrow-gold)"/>
        <line x1="{iso_cx - 90}" y1="{iso_cy + 50}" x2="{iso_cx - 130}" y2="{iso_cy + 50}" class="callout-leader"/>
        <text x="{iso_cx - 135}" y="{iso_cy + 54}" class="callout-text" text-anchor="end">[4] 22° TILT STAND CRADLE</text>
        
        <line x1="{iso_cx - 50}" y1="{iso_cy + 85}" x2="{iso_cx - 90}" y2="{iso_cy + 105}" class="callout-leader" marker-start="url(#arrow-gold)"/>
        <line x1="{iso_cx - 90}" y1="{iso_cy + 105}" x2="{iso_cx - 130}" y2="{iso_cy + 105}" class="callout-leader"/>
        <text x="{iso_cx - 135}" y="{iso_cy + 109}" class="callout-text" text-anchor="end">[5] WALNUT ACCENT BASE PLATE</text>
    </g>
    ''')

    # ENGINEERING TITLE BLOCK
    tb_x, tb_y = 1140, 520
    tb_w, tb_h = 420, 520
    
    svg.append(f'''
    <!-- ENGINEERING TITLE BLOCK -->
    <g id="title-block">
        <rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="{tb_h}" fill="#101823" stroke="#38BDF8" stroke-width="2.0"/>
        
        <rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="45" fill="#1E293B" stroke="#38BDF8" stroke-width="1.0"/>
        <text x="{tb_x + 15}" y="{tb_y + 28}" class="tb-brand">KIMISHIBA CYBER-DECK SYSTEMS</text>
        <text x="{tb_x + tb_w - 15}" y="{tb_y + 28}" fill="#38BDF8" font-family="JetBrains Mono" font-size="11" font-weight="700" text-anchor="end">DOC: CD-240-DWG</text>
        
        <rect x="{tb_x}" y="{tb_y + 45}" width="{tb_w}" height="55" fill="#0B1118" stroke="#1E293B" stroke-width="1.0"/>
        <text x="{tb_x + 15}" y="{tb_y + 68}" class="tb-label">PROJECT / PART DESCRIPTION</text>
        <text x="{tb_x + 15}" y="{tb_y + 90}" class="tb-title">GC9A01 1.28″ CYBERDECK DESK ENCLOSURE</text>
        
        <line x1="{tb_x}" y1="{tb_y + 100}" x2="{tb_x + tb_w}" y2="{tb_y + 100}" stroke="#1E293B"/>
        
        <rect x="{tb_x}" y="{tb_y + 100}" width="140" height="40" fill="#101823" stroke="#1E293B"/>
        <text x="{tb_x + 10}" y="{tb_y + 115}" class="tb-label">DESIGNED BY</text>
        <text x="{tb_x + 10}" y="{tb_y + 132}" class="tb-value">Alex Longoni</text>
        
        <rect x="{tb_x + 140}" y="{tb_y + 100}" width="140" height="40" fill="#101823" stroke="#1E293B"/>
        <text x="{tb_x + 150}" y="{tb_y + 115}" class="tb-label">RELEASE DATE</text>
        <text x="{tb_x + 150}" y="{tb_y + 132}" class="tb-value">2026-08-24</text>
        
        <rect x="{tb_x + 280}" y="{tb_y + 100}" width="140" height="40" fill="#101823" stroke="#1E293B"/>
        <text x="{tb_x + 290}" y="{tb_y + 115}" class="tb-label">REVISION</text>
        <text x="{tb_x + 290}" y="{tb_y + 132}" class="tb-value">v2.4 (DuPont)</text>
        
        <rect x="{tb_x}" y="{tb_y + 140}" width="{tb_w}" height="40" fill="#0B1118" stroke="#1E293B"/>
        <text x="{tb_x + 10}" y="{tb_y + 155}" class="tb-label">MATERIAL / PROCESS</text>
        <text x="{tb_x + 10}" y="{tb_y + 172}" class="tb-value">FDM 3D PRINT (MATTE CHARCOAL PLA / WALNUT)</text>
        
        <rect x="{tb_x}" y="{tb_y + 180}" width="{tb_w}" height="110" fill="#101823" stroke="#1E293B"/>
        <text x="{tb_x + 10}" y="{tb_y + 200}" class="tb-label">GENERAL FDM 3D PRINTING TOLERANCES</text>
        <text x="{tb_x + 10}" y="{tb_y + 222}" fill="#94A3B8" font-family="JetBrains Mono" font-size="10.5">X/Y DIMENSIONAL TOLERANCE: <tspan fill="#38BDF8">±0.15 mm</tspan></text>
        <text x="{tb_x + 10}" y="{tb_y + 242}" fill="#94A3B8" font-family="JetBrains Mono" font-size="10.5">HOLE DIAMETER CLEARANCE:   <tspan fill="#38BDF8">+0.25 mm / -0.00 mm</tspan></text>
        <text x="{tb_x + 10}" y="{tb_y + 262}" fill="#94A3B8" font-family="JetBrains Mono" font-size="10.5">WALL THICKNESS / WALLS:    <tspan fill="#38BDF8">2.50 mm (4 WALLS)</tspan></text>
        <text x="{tb_x + 10}" y="{tb_y + 282}" fill="#94A3B8" font-family="JetBrains Mono" font-size="10.5">LAYER HEIGHT / INFILL:     <tspan fill="#38BDF8">0.16 mm / 20% GYROID</tspan></text>
        
        <rect x="{tb_x}" y="{tb_y + 290}" width="{tb_w}" height="230" fill="#0B1118" stroke="#1E293B"/>
        <text x="{tb_x + 10}" y="{tb_y + 312}" class="tb-label">HARDWARE BILL OF MATERIALS (BOM)</text>
        <text x="{tb_x + 10}" y="{tb_y + 336}" fill="#CBD5E1" font-family="JetBrains Mono" font-size="10">1. [1x] GC9A01 1.28″ IPS Display (240x240 SPI)</text>
        <text x="{tb_x + 10}" y="{tb_y + 356}" fill="#CBD5E1" font-family="JetBrains Mono" font-size="10">2. [1x] ESP32-C3 SuperMini MCU (USB-C)</text>
        <text x="{tb_x + 10}" y="{tb_y + 376}" fill="#CBD5E1" font-family="JetBrains Mono" font-size="10">3. [4x] M2 x 14mm Socket Head Screws (Brass)</text>
        <text x="{tb_x + 10}" y="{tb_y + 396}" fill="#CBD5E1" font-family="JetBrains Mono" font-size="10">4. [4x] M2 Brass Heat-Set Threaded Inserts</text>
        <text x="{tb_x + 10}" y="{tb_y + 416}" fill="#CBD5E1" font-family="JetBrains Mono" font-size="10">5. [2x] M2 x 4mm Display Fastening Screws</text>
        <text x="{tb_x + 10}" y="{tb_y + 436}" fill="#CBD5E1" font-family="JetBrains Mono" font-size="10">6. [7x] Female DuPont Jumpers (10cm length)</text>
        <text x="{tb_x + 10}" y="{tb_y + 456}" fill="#CBD5E1" font-family="JetBrains Mono" font-size="10">7. [4x] Ø 8.0mm x 1.5mm Rubber Anti-Slip Feet</text>
        <text x="{tb_x + 10}" y="{tb_y + 476}" fill="#CBD5E1" font-family="JetBrains Mono" font-size="10">8. [1x] Type-C 90° or Braided USB Cable</text>
        
        <rect x="{tb_x + tb_w - 110}" y="{tb_y + tb_h - 35}" width="95" height="22" rx="4" fill="#0284C7"/>
        <text x="{tb_x + tb_w - 62}" y="{tb_y + tb_h - 20}" fill="#FFFFFF" font-family="JetBrains Mono" font-size="10" font-weight="800" text-anchor="middle">APPROVED</text>
    </g>
    ''')
    
    svg.append('</svg>')
    
    with open(output_svg_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(svg))
        
    print(f"Generated Vector Technical Drawing: {output_svg_path}")

if __name__ == "__main__":
    out_dir = "/Users/alessandro.longoni/Library/CloudStorage/GoogleDrive-mag8mag8@gmail.com/My Drive/Antigravity/Desktop Tiny Screen/round 240x240/enclosure"
    svg_file = os.path.join(out_dir, "gc9a01_cyberdeck_technical_drawing.svg")
    create_svg_blueprint(svg_file)
    
    # Validate XML
    ET.parse(svg_file)
    print("SVG XML is 100% Valid!")
    
    png_file = os.path.join(out_dir, "gc9a01_cyberdeck_technical_drawing.png")
    cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--headless",
        f"--screenshot={png_file}",
        "--window-size=1600,1100",
        "--default-background-color=000000",
        svg_file
    ]
    subprocess.run(cmd, check=True)
    print(f"Rendered High-Res PNG Blueprint: {png_file}")
