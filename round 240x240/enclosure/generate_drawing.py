#!/usr/bin/env python3
"""
GC9A01 Round Display & ESP32-C3 Main Case Technical Drawing SVG Generator
Generates a fully dimensioned 2D engineering drawing blueprint (SVG format) with pin clearances.
"""

import os

def create_technical_drawing():
    svg_width = 1200
    svg_height = 900

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}" style="background-color: #0f172a; font-family: Inter, -apple-system, sans-serif;">')

    # Definitions for markers and patterns
    svg.append('''
    <defs>
        <!-- Arrowhead Marker (Cyan) -->
        <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#38bdf8" />
        </marker>
        <!-- Arrowhead Marker (Yellow) -->
        <marker id="arrow-yellow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#fbbf24" />
        </marker>
        <!-- Arrowhead Marker (Green) -->
        <marker id="arrow-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#22c55e" />
        </marker>
        <!-- Hatch Pattern for Cross Section -->
        <pattern id="hatch" width="10" height="10" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="10" stroke="#475569" stroke-width="1.2" />
        </pattern>
        <!-- Grid Background Pattern -->
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="1" />
        </pattern>
    </defs>
    ''')

    # Grid background
    svg.append(f'<rect width="{svg_width}" height="{svg_height}" fill="url(#grid)" />')

    # Outer Blueprint Border
    svg.append('<rect x="20" y="20" width="1160" height="860" fill="none" stroke="#38bdf8" stroke-width="2" opacity="0.6" />')
    svg.append('<rect x="25" y="25" width="1150" height="850" fill="none" stroke="#38bdf8" stroke-width="1" opacity="0.3" />')

    # Header Title Block
    svg.append('''
    <g transform="translate(40, 40)">
        <text x="0" y="25" fill="#f8fafc" font-size="22" font-weight="700" letter-spacing="1">GC9A01 1.28" ROUND DISPLAY &amp; ESP32-C3 MAIN ENCLOSURE</text>
        <text x="0" y="48" fill="#94a3b8" font-size="14" font-weight="500">2D TECHNICAL DRAWING BLUEPRINT — SOLDERED PIN &amp; WIRE HARNESS CLEARANCES</text>
        <text x="1100" y="25" text-anchor="end" fill="#38bdf8" font-size="14" font-weight="600">SCALE: 2:1 | UNITS: mm | TOLERANCE: ±0.15mm</text>
        <line x1="0" y1="60" x2="1120" y2="60" stroke="#334155" stroke-width="1.5" />
    </g>
    ''')

    # -------------------------------------------------------------------------
    # VIEW 1: FRONT ELEVATION & PIN NOTCH (Left Top, Center = 260, 300)
    # Scale: 3.8x
    # -------------------------------------------------------------------------
    sc = 3.8
    cx1, cy1 = 260, 300

    svg.append(f'''
    <!-- VIEW 1 CONTAINER -->
    <g id="view1">
        <text x="{cx1}" y="{cy1 - 160}" text-anchor="middle" fill="#38bdf8" font-size="15" font-weight="700">VIEW 1: FRONT BEZEL ELEVATION (WITH PIN NOTCH)</text>
        
        <!-- Centerlines -->
        <line x1="{cx1 - 130}" y1="{cy1}" x2="{cx1 + 130}" y2="{cy1}" stroke="#0284c7" stroke-width="1" stroke-dasharray="8,4,2,4" />
        <line x1="{cx1}" y1="{cy1 - 130}" x2="{cx1}" y2="{cy1 + 130}" stroke="#0284c7" stroke-width="1" stroke-dasharray="8,4,2,4" />

        <!-- Outer Octagonal Profile (48mm x 48mm, 4.5mm chamfers) -->
        <polygon points="
            {cx1 - 19.5*sc},{cy1 - 24*sc} {cx1 + 19.5*sc},{cy1 - 24*sc}
            {cx1 + 24*sc},{cy1 - 19.5*sc} {cx1 + 24*sc},{cy1 + 19.5*sc}
            {cx1 + 19.5*sc},{cy1 + 24*sc} {cx1 - 19.5*sc},{cy1 + 24*sc}
            {cx1 - 24*sc},{cy1 + 19.5*sc} {cx1 - 24*sc},{cy1 - 19.5*sc}
        " fill="#1e293b" fill-opacity="0.5" stroke="#f8fafc" stroke-width="2.5" />

        <!-- Raised Bezel Accent Ring (40mm Dia) -->
        <circle cx="{cx1}" cy="{cy1}" r="{20*sc}" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="6,3" />

        <!-- Display Active View Aperture (32.6mm Dia) -->
        <circle cx="{cx1}" cy="{cy1}" r="{16.3*sc}" fill="#0f172a" stroke="#38bdf8" stroke-width="2" />
        
        <!-- GC9A01 Screen PCB Underneath (37.0mm Dia, dashed) -->
        <circle cx="{cx1}" cy="{cy1}" r="{18.5*sc}" fill="none" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,4" />

        <!-- TOP DISPLAY PIN HEADER WIRE PASS-THROUGH NOTCH (24mm x 8mm) -->
        <rect x="{cx1 - 12*sc}" y="{cy1 - 19*sc}" width="{24*sc}" height="{8*sc}" fill="#0f172a" fill-opacity="0.8" stroke="#22c55e" stroke-width="1.8" stroke-dasharray="4,2" rx="2" />
        <text x="{cx1}" y="{cy1 - 13*sc}" text-anchor="middle" fill="#22c55e" font-size="10" font-weight="700">7-PIN SPI HEADER NOTCH</text>

        <!-- 4 Corner M2 Screw Holes & Counterbores -->
    ''')

    for sx in [-18, 18]:
        for sy in [-18, 18]:
            px, py = cx1 + sx*sc, cy1 + sy*sc
            svg.append(f'''
                <circle cx="{px}" cy="{py}" r="{2.4*sc}" fill="none" stroke="#fbbf24" stroke-width="1.5" />
                <circle cx="{px}" cy="{py}" r="{1.3*sc}" fill="none" stroke="#38bdf8" stroke-width="1.2" />
                <line x1="{px-8}" y1="{py}" x2="{px+8}" y2="{py}" stroke="#0284c7" stroke-width="0.8" />
                <line x1="{px}" y1="{py-8}" x2="{px}" y2="{py+8}" stroke="#0284c7" stroke-width="0.8" />
            ''')

    # View 1 Dimensions
    svg.append(f'''
        <!-- Dim 1: Outer Width 48.0mm -->
        <line x1="{cx1 - 24*sc}" y1="{cy1 + 24*sc + 20}" x2="{cx1 - 24*sc}" y2="{cy1 + 24*sc + 45}" stroke="#38bdf8" stroke-width="0.8" />
        <line x1="{cx1 + 24*sc}" y1="{cy1 + 24*sc + 20}" x2="{cx1 + 24*sc}" y2="{cy1 + 24*sc + 45}" stroke="#38bdf8" stroke-width="0.8" />
        <line x1="{cx1 - 24*sc}" y1="{cy1 + 24*sc + 35}" x2="{cx1 + 24*sc}" y2="{cy1 + 24*sc + 35}" stroke="#38bdf8" stroke-width="1.2" marker-start="url(#arrow)" marker-end="url(#arrow)" />
        <rect x="{cx1 - 35}" y="{cy1 + 24*sc + 24}" width="70" height="20" fill="#0f172a" rx="4" />
        <text x="{cx1}" y="{cy1 + 24*sc + 38}" text-anchor="middle" fill="#38bdf8" font-size="13" font-weight="700">48.0 mm</text>

        <!-- Callout: Top Pin Relief Notch 24x8mm -->
        <line x1="{cx1 + 10*sc}" y1="{cy1 - 15*sc}" x2="{cx1 + 80}" y2="{cy1 - 100}" stroke="#22c55e" stroke-width="1.2" marker-start="url(#arrow-green)" />
        <line x1="{cx1 + 80}" y1="{cy1 - 100}" x2="{cx1 + 180}" y2="{cy1 - 100}" stroke="#22c55e" stroke-width="1.2" />
        <text x="{cx1 + 85}" y="{cy1 - 106}" fill="#22c55e" font-size="12" font-weight="700">24x8mm PIN HEADER NOTCH</text>
    </g>
    ''')

    # -------------------------------------------------------------------------
    # VIEW 2: SECTION A-A (Expanded 24mm Depth + Pin Clearances, Center = 800, 300)
    # Scale: 3.8x
    # -------------------------------------------------------------------------
    cx2, cy2 = 800, 300

    svg.append(f'''
    <!-- VIEW 2 CONTAINER: SECTION A-A -->
    <g id="view2">
        <text x="{cx2}" y="{cy2 - 160}" text-anchor="middle" fill="#38bdf8" font-size="15" font-weight="700">VIEW 2: SECTION A-A (WITH PIN CLEARANCES &amp; STANDOFFS)</text>

        <!-- Centerline -->
        <line x1="{cx2 - 150}" y1="{cy2}" x2="{cx2 + 150}" y2="{cy2}" stroke="#0284c7" stroke-width="1" stroke-dasharray="8,4,2,4" />

        <!-- Housing Outer Profile in Section (Depth = 24.0mm [-12 to +12]) -->
        <!-- Front Bezel: x = cx2 - 12*sc to cx2 - 7.5*sc (4.5mm) -->
        <!-- Main Housing: x = cx2 - 7.5*sc to cx2 + 12*sc (19.5mm) -->

        <!-- Top Wall Section -->
        <path d="
            M {cx2 - 12*sc} {cy2 - 24*sc}
            L {cx2 + 12*sc} {cy2 - 24*sc}
            L {cx2 + 12*sc} {cy2 - 17*sc}
            L {cx2 + 9.5*sc} {cy2 - 17*sc}
            L {cx2 + 9.5*sc} {cy2 - 18.5*sc}
            L {cx2 - 7.5*sc} {cy2 - 18.5*sc}
            L {cx2 - 7.5*sc} {cy2 - 16.3*sc}
            L {cx2 - 12*sc} {cy2 - 16.3*sc}
            Z
        " fill="url(#hatch)" stroke="#f8fafc" stroke-width="2" />

        <!-- Bottom Wall Section -->
        <path d="
            M {cx2 - 12*sc} {cy2 + 24*sc}
            L {cx2 + 12*sc} {cy2 + 24*sc}
            L {cx2 + 12*sc} {cy2 + 17*sc}
            L {cx2 + 9.5*sc} {cy2 + 17*sc}
            L {cx2 + 9.5*sc} {cy2 + 18.5*sc}
            L {cx2 - 7.5*sc} {cy2 + 18.5*sc}
            L {cx2 - 7.5*sc} {cy2 + 16.3*sc}
            L {cx2 - 12*sc} {cy2 + 16.3*sc}
            Z
        " fill="url(#hatch)" stroke="#f8fafc" stroke-width="2" />

        <!-- Back Floor Wall (2.5mm thick with pin trenches) -->
        <rect x="{cx2 + 9.5*sc}" y="{cy2 - 17*sc}" width="{2.5*sc}" height="{34*sc}" fill="url(#hatch)" stroke="#f8fafc" stroke-width="1.5" />

        <!-- ESP32 Solder Pin Relief Trenches (1.5mm deep into floor) -->
        <rect x="{cx2 + 8.0*sc}" y="{cy2 - 11.25*sc}" width="{1.5*sc}" height="{3.0*sc}" fill="#0f172a" stroke="#22c55e" stroke-width="1.2" />
        <rect x="{cx2 + 8.0*sc}" y="{cy2 + 8.25*sc}" width="{1.5*sc}" height="{3.0*sc}" fill="#0f172a" stroke="#22c55e" stroke-width="1.2" />

        <!-- Front Bezel Joint Line (at z = 4.5mm from front => x = cx2 - 7.5*sc) -->
        <line x1="{cx2 - 7.5*sc}" y1="{cy2 - 24*sc}" x2="{cx2 - 7.5*sc}" y2="{cy2 + 24*sc}" stroke="#e2e8f0" stroke-width="1.5" stroke-dasharray="4,2" />

        <!-- INTERNAL COMPONENTS SCHEMATIC IN SECTION -->
        
        <!-- 1. GC9A01 Screen Module & Soldered Pin Header -->
        <rect x="{cx2 - 11.5*sc}" y="{cy2 - 18.5*sc}" width="{4.0*sc}" height="{37.0*sc}" fill="#0284c7" fill-opacity="0.3" stroke="#38bdf8" stroke-width="1.5" rx="2" />
        <rect x="{cx2 - 11.5*sc}" y="{cy2 - 16.3*sc}" width="{1.5*sc}" height="{32.6*sc}" fill="#38bdf8" fill-opacity="0.7" stroke="#7dd3fc" stroke-width="1" />
        
        <!-- Rear Soldered Pin Header on Display (Sticks out into top notch) -->
        <rect x="{cx2 - 7.5*sc}" y="{cy2 - 18.0*sc}" width="{6.0*sc}" height="{5.0*sc}" fill="#22c55e" fill-opacity="0.6" stroke="#22c55e" stroke-width="1.5" rx="1" />
        <text x="{cx2 - 4.5*sc}" y="{cy2 - 15.5*sc}" text-anchor="middle" fill="#22c55e" font-size="9" font-weight="700">PINS</text>

        <!-- 2. ESP32-C3 SuperMini Board on 2mm Corner Standoff Ledges -->
        <!-- Standoff Ledges under board (at x = cx2 + 7.5*sc) -->
        <rect x="{cx2 + 7.5*sc}" y="{cy2 - 12.0*sc}" width="{2.0*sc}" height="{2.5*sc}" fill="#38bdf8" stroke="#f8fafc" stroke-width="1" />
        <rect x="{cx2 + 7.5*sc}" y="{cy2 + 9.5*sc}" width="{2.0*sc}" height="{2.5*sc}" fill="#38bdf8" stroke-width="1" />

        <!-- ESP32 Board PCB -->
        <rect x="{cx2 - 1.0*sc}" y="{cy2 - 11.25*sc}" width="{8.5*sc}" height="{22.5*sc}" fill="#166534" fill-opacity="0.4" stroke="#22c55e" stroke-width="1.5" rx="2" />
        <!-- Bottom Soldered Pin Tails (extending 2mm under board into relief trenches) -->
        <line x1="{cx2 + 7.5*sc}" y1="{cy2 - 9.5*sc}" x2="{cx2 + 9.2*sc}" y2="{cy2 - 9.5*sc}" stroke="#22c55e" stroke-width="2" />
        <line x1="{cx2 + 7.5*sc}" y1="{cy2 + 9.5*sc}" x2="{cx2 + 9.2*sc}" y2="{cy2 + 9.5*sc}" stroke="#22c55e" stroke-width="2" />

        <!-- USB-C Receptacle -->
        <rect x="{cx2 - 4.0*sc}" y="{cy2 - 4.5*sc}" width="{5.0*sc}" height="{9.0*sc}" fill="#94a3b8" stroke="#f8fafc" stroke-width="1" />
        <text x="{cx2 + 3.0*sc}" y="{cy2 + 4}" text-anchor="middle" fill="#22c55e" font-size="11" font-weight="700" transform="rotate(-90 {cx2 + 3.0*sc} {cy2 + 4})">ESP32-C3 SUPERMINI</text>

        <!-- DIMENSIONS FOR SECTION VIEW -->
        <!-- Total Depth = 24.0mm -->
        <line x1="{cx2 - 12*sc}" y1="{cy2 + 24*sc + 15}" x2="{cx2 - 12*sc}" y2="{cy2 + 24*sc + 45}" stroke="#38bdf8" stroke-width="0.8" />
        <line x1="{cx2 + 12*sc}" y1="{cy2 + 24*sc + 15}" x2="{cx2 + 12*sc}" y2="{cy2 + 24*sc + 45}" stroke="#38bdf8" stroke-width="0.8" />
        <line x1="{cx2 - 12*sc}" y1="{cy2 + 24*sc + 35}" x2="{cx2 + 12*sc}" y2="{cy2 + 24*sc + 35}" stroke="#38bdf8" stroke-width="1.2" marker-start="url(#arrow)" marker-end="url(#arrow)" />
        <rect x="{cx2 - 35}" y="{cy2 + 24*sc + 24}" width="70" height="20" fill="#0f172a" rx="4" />
        <text x="{cx2}" y="{cy2 + 24*sc + 38}" text-anchor="middle" fill="#38bdf8" font-size="13" font-weight="700">24.0 mm DEPTH</text>

        <!-- Callout: ESP32 Bottom Pin Relief Trench -->
        <line x1="{cx2 + 8.5*sc}" y1="{cy2 - 10*sc}" x2="{cx2 + 60}" y2="{cy2 - 60}" stroke="#22c55e" stroke-width="1.2" marker-start="url(#arrow-green)" />
        <line x1="{cx2 + 60}" y1="{cy2 - 60}" x2="{cx2 + 150}" y2="{cy2 - 60}" stroke="#22c55e" stroke-width="1.2" />
        <text x="{cx2 + 65}" y="{cy2 - 66}" fill="#22c55e" font-size="12" font-weight="700">PIN TRENCH + 2mm STANDOFF GAP</text>
    </g>
    ''')

    # -------------------------------------------------------------------------
    # VIEW 3: LEFT SIDE ELEVATION & USB-C PORT (Left Bottom, Center = 260, 670)
    # Scale: 3.8x
    # -------------------------------------------------------------------------
    cx3, cy3 = 260, 670

    svg.append(f'''
    <!-- VIEW 3 CONTAINER: LEFT SIDE ELEVATION -->
    <g id="view3">
        <text x="{cx3}" y="{cy3 - 150}" text-anchor="middle" fill="#38bdf8" font-size="15" font-weight="700">VIEW 3: LEFT SIDE ELEVATION (USB-C CUTOUT)</text>

        <line x1="{cx3 - 130}" y1="{cy3}" x2="{cx3 + 130}" y2="{cy3}" stroke="#0284c7" stroke-width="1" stroke-dasharray="8,4,2,4" />

        <!-- Side Outer Chassis Box Profile (Width = 24mm depth [-12 to +12], Height = 48mm [-24 to +24]) -->
        <rect x="{cx3 - 12*sc}" y="{cy3 - 24*sc}" width="{24*sc}" height="{48*sc}" fill="#1e293b" fill-opacity="0.6" stroke="#f8fafc" stroke-width="2" rx="3" />

        <!-- Bezel Seam Line (at Front 4.5mm => x = cx3 - 7.5*sc) -->
        <line x1="{cx3 - 7.5*sc}" y1="{cy3 - 24*sc}" x2="{cx3 - 7.5*sc}" y2="{cy3 + 24*sc}" stroke="#e2e8f0" stroke-width="1.5" />

        <!-- USB-C Port Window Cutout -->
        <rect x="{cx3 - 1.0*sc}" y="{cy3 - 6.0*sc}" width="{7.0*sc}" height="{12.0*sc}" fill="#0f172a" stroke="#fbbf24" stroke-width="2" rx="3" />
        <path d="M {cx3 - 0.2*sc} {cy3 - 3.5*sc} L {cx3 + 5.2*sc} {cy3 - 3.5*sc} A 2.5 2.5 0 0 1 {cx3 + 5.2*sc} {cy3 + 3.5*sc} L {cx3 - 0.2*sc} {cy3 + 3.5*sc} A 2.5 2.5 0 0 1 {cx3 - 0.2*sc} {cy3 - 3.5*sc} Z" fill="#334155" stroke="#fbbf24" stroke-width="1" />
        <text x="{cx3 + 2.5*sc}" y="{cy3 + 3}" text-anchor="middle" fill="#fbbf24" font-size="10" font-weight="700">USB-C</text>
    </g>
    ''')

    # -------------------------------------------------------------------------
    # VIEW 4: REAR HOUSING ELEVATION (Right Bottom, Center = 800, 670)
    # Scale: 3.8x
    # -------------------------------------------------------------------------
    cx4, cy4 = 800, 670

    svg.append(f'''
    <!-- VIEW 4 CONTAINER: REAR ELEVATION -->
    <g id="view4">
        <text x="{cx4}" y="{cy4 - 150}" text-anchor="middle" fill="#38bdf8" font-size="15" font-weight="700">VIEW 4: REAR HOUSING ELEVATION &amp; PIN TRENCHES</text>

        <line x1="{cx4 - 130}" y1="{cy4}" x2="{cx4 + 130}" y2="{cy4}" stroke="#0284c7" stroke-width="1" stroke-dasharray="8,4,2,4" />
        <line x1="{cx4}" y1="{cy4 - 130}" x2="{cx4}" y2="{cy4 + 130}" stroke="#0284c7" stroke-width="1" stroke-dasharray="8,4,2,4" />

        <!-- Outer Octagonal Profile (48mm x 48mm) -->
        <polygon points="
            {cx4 - 19.5*sc},{cy4 - 24*sc} {cx4 + 19.5*sc},{cy4 - 24*sc}
            {cx4 + 24*sc},{cy4 - 19.5*sc} {cx4 + 24*sc},{cy4 + 19.5*sc}
            {cx4 + 19.5*sc},{cy4 + 24*sc} {cx4 - 19.5*sc},{cy4 + 24*sc}
            {cx4 - 24*sc},{cy4 + 19.5*sc} {cx4 - 24*sc},{cy4 - 19.5*sc}
        " fill="#1e293b" fill-opacity="0.6" stroke="#f8fafc" stroke-width="2.5" />

        <!-- Dual Longitudinal Bottom Pin Relief Trenches (5.0mm x 28.0mm) -->
        <rect x="{cx4 - 10*sc}" y="{cy4 - 14*sc}" width="{5*sc}" height="{28*sc}" fill="#0f172a" stroke="#22c55e" stroke-width="1.5" stroke-dasharray="4,2" rx="2" />
        <rect x="{cx4 + 5*sc}" y="{cy4 - 14*sc}" width="{5*sc}" height="{28*sc}" fill="#0f172a" stroke="#22c55e" stroke-width="1.5" stroke-dasharray="4,2" rx="2" />
        <text x="{cx4}" y="{cy4 - 4}" text-anchor="middle" fill="#22c55e" font-size="10" font-weight="700">BOTTOM PIN TRENCHES</text>

        <!-- 4 Corner Screw Blind Pilot Holes -->
    ''')

    for sx in [-18, 18]:
        for sy in [-18, 18]:
            px, py = cx4 + sx*sc, cy4 + sy*sc
            svg.append(f'''
                <circle cx="{px}" cy="{py}" r="{1.0*sc}" fill="#0f172a" stroke="#fbbf24" stroke-width="1.5" />
                <line x1="{px-6}" y1="{py}" x2="{px+6}" y2="{py}" stroke="#fbbf24" stroke-width="0.8" />
                <line x1="{px}" y1="{py-6}" x2="{px}" y2="{py+6}" stroke="#fbbf24" stroke-width="0.8" />
            ''')

    svg.append('</g>')

    # -------------------------------------------------------------------------
    # SUMMARY SPECIFICATIONS & TOLERANCE TABLE BLOCK (Bottom Center)
    # -------------------------------------------------------------------------
    svg.append('''
    <g transform="translate(40, 800)">
        <rect x="0" y="0" width="1120" height="65" fill="#1e293b" stroke="#334155" stroke-width="1.5" rx="6" />
        <text x="20" y="24" fill="#22c55e" font-size="13" font-weight="700">UPDATED PIN HEADER &amp; SOLDER TAIL FIT SPECIFICATIONS:</text>
        <text x="20" y="48" fill="#cbd5e1" font-size="12" font-weight="500">
            • Display Pin Notch: 24.0 x 8.0mm top pass-through &nbsp;&nbsp;|&nbsp;&nbsp; 
            • ESP32 Solder Relief: 2x 5.0mm trenches + 2.0mm corner standoff ledges &nbsp;&nbsp;|&nbsp;&nbsp; 
            • Expanded Housing Depth: 24.0mm total
        </text>
        <text x="1100" y="38" text-anchor="end" fill="#fbbf24" font-size="13" font-weight="700">DESIGN READY FOR SOLDERED HEADER PINS &amp; HARNESS</text>
    </g>
    ''')

    svg.append('</svg>')

    return '\n'.join(svg)

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "gc9a01_main_case_technical_drawing.svg")

    drawing_content = create_technical_drawing()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(drawing_content)

    print(f"[SUCCESS] Technical Drawing SVG updated with pin clearances: {output_path}")

if __name__ == "__main__":
    main()
