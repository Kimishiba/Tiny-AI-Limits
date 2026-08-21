#!/usr/bin/env python3
"""
GC9A01 1.28" Round Display & ESP32-C3 SuperMini Cyberdeck Enclosure
3D Printable STL Generator (Binary STL Format)
"""

import math
import struct
import os

class STLMesh:
    def __init__(self):
        self.triangles = [] # List of ((nx,ny,nz), (x1,y1,z1), (x2,y2,z2), (x3,y3,z3))

    def add_triangle(self, v1, v2, v3, normal=None):
        if normal is None:
            # Compute outward normal
            ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
            bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 1e-9:
                normal = (nx/length, ny/length, nz/length)
            else:
                normal = (0.0, 0.0, 1.0)
        self.triangles.append((normal, v1, v2, v3))

    def add_quad(self, v1, v2, v3, v4):
        # Adds quad with vertices v1, v2, v3, v4 in counter-clockwise winding
        self.add_triangle(v1, v2, v3)
        self.add_triangle(v1, v3, v4)

    def write_binary(self, filepath, header_text="GC9A01 Cyberdeck Enclosure"):
        header = header_text.encode('ascii')[:80].ljust(80, b'\0')
        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(struct.pack('<I', len(self.triangles)))
            for normal, v1, v2, v3 in self.triangles:
                f.write(struct.pack('<3f', *normal))
                f.write(struct.pack('<3f', *v1))
                f.write(struct.pack('<3f', *v2))
                f.write(struct.pack('<3f', *v3))
                f.write(struct.pack('<H', 0))
        print(f"Generated: {filepath} ({len(self.triangles)} triangles, {os.path.getsize(filepath) / 1024:.1f} KB)")


def create_octagonal_cylinder(mesh, x_center, y_center, z_min, z_max, width, chamfer):
    # Creates an 8-sided chamfered box (cyberdeck aesthetic)
    hw = width / 2.0
    c = chamfer
    pts_2d = [
        (-hw + c, -hw), (hw - c, -hw),
        (hw, -hw + c), (hw, hw - c),
        (hw - c, hw), (-hw + c, hw),
        (-hw, hw - c), (-hw, -hw + c)
    ]
    n = len(pts_2d)

    # Bottom face (z_min, normal pointing down)
    center_bot = (x_center, y_center, z_min)
    for i in range(n):
        p1 = (x_center + pts_2d[i][0], y_center + pts_2d[i][1], z_min)
        p2 = (x_center + pts_2d[(i+1)%n][0], y_center + pts_2d[(i+1)%n][1], z_min)
        mesh.add_triangle(center_bot, p2, p1)

    # Top face (z_max, normal pointing up)
    center_top = (x_center, y_center, z_max)
    for i in range(n):
        p1 = (x_center + pts_2d[i][0], y_center + pts_2d[i][1], z_max)
        p2 = (x_center + pts_2d[(i+1)%n][0], y_center + pts_2d[(i+1)%n][1], z_max)
        mesh.add_triangle(center_top, p1, p2)

    # Side walls
    for i in range(n):
        b1 = (x_center + pts_2d[i][0], y_center + pts_2d[i][1], z_min)
        b2 = (x_center + pts_2d[(i+1)%n][0], y_center + pts_2d[(i+1)%n][1], z_min)
        t1 = (x_center + pts_2d[i][0], y_center + pts_2d[i][1], z_max)
        t2 = (x_center + pts_2d[(i+1)%n][0], y_center + pts_2d[(i+1)%n][1], z_max)
        mesh.add_quad(b1, b2, t2, t1)


def create_cylinder_surface(mesh, xc, yc, z1, z2, r, segments=36, inward=False):
    for i in range(segments):
        a1 = 2 * math.pi * i / segments
        a2 = 2 * math.pi * (i + 1) / segments
        x1, y1 = xc + r * math.cos(a1), yc + r * math.sin(a1)
        x2, y2 = xc + r * math.cos(a2), yc + r * math.sin(a2)

        b1, b2 = (x1, y1, z1), (x2, y2, z1)
        t1, t2 = (x1, y1, z2), (x2, y2, z2)

        if inward:
            mesh.add_quad(b2, b1, t1, t2)
        else:
            mesh.add_quad(b1, b2, t2, t1)


def create_annulus_ring(mesh, xc, yc, z, r_inner, r_outer, segments=36, facing_up=True):
    for i in range(segments):
        a1 = 2 * math.pi * i / segments
        a2 = 2 * math.pi * (i + 1) / segments

        xi1, yi1 = xc + r_inner * math.cos(a1), yc + r_inner * math.sin(a1)
        xi2, yi2 = xc + r_inner * math.cos(a2), yc + r_inner * math.sin(a2)
        xo1, yo1 = xc + r_outer * math.cos(a1), yc + r_outer * math.sin(a1)
        xo2, yo2 = xc + r_outer * math.cos(a2), yc + r_outer * math.sin(a2)

        p_i1 = (xi1, yi1, z)
        p_i2 = (xi2, yi2, z)
        p_o1 = (xo1, yo1, z)
        p_o2 = (xo2, yo2, z)

        if facing_up:
            mesh.add_quad(p_i1, p_o1, p_o2, p_i2)
        else:
            mesh.add_quad(p_i1, p_i2, p_o2, p_o1)


def generate_front_bezel():
    mesh = STLMesh()
    width = 48.0
    chamfer = 4.0
    thickness = 4.0
    r_aperture = 16.3  # 32.6mm display window (1.28" active area)
    r_bezel_outer = 20.0 # 40mm decorative front raised ring
    r_lip_pocket = 18.5  # 37mm rear retention lip for glass & PCB

    # 1. Base Plate Perimeter (Chamfered octagonal box)
    create_octagonal_cylinder(mesh, 0, 0, 0, thickness, width, chamfer)

    # 2. Front Raised Bezel Trim Ring (z = 4.0 to 5.5)
    create_cylinder_surface(mesh, 0, 0, thickness, thickness + 1.5, r_bezel_outer, segments=48)
    create_annulus_ring(mesh, 0, 0, thickness + 1.5, r_aperture, r_bezel_outer, segments=48, facing_up=True)

    # 3. Center Screen Aperture Bore (z = 1.5 to 5.5)
    create_cylinder_surface(mesh, 0, 0, 1.5, thickness + 1.5, r_aperture, segments=48, inward=True)

    # 4. Rear Internal Retention Lip for GC9A01 Display (z = 0 to 1.5)
    create_cylinder_surface(mesh, 0, 0, 0, 1.5, r_lip_pocket, segments=48, inward=True)
    create_annulus_ring(mesh, 0, 0, 1.5, r_aperture, r_lip_pocket, segments=48, facing_up=False)

    # 5. 4 Corner M2 Screw Through-Holes
    screw_dist = 18.0
    for sx in [-screw_dist, screw_dist]:
        for sy in [-screw_dist, screw_dist]:
            # Screw through-hole r = 1.3mm (M2.5 clearance)
            create_cylinder_surface(mesh, sx, sy, 0, thickness, 1.3, segments=16, inward=True)
            # Front counterbore pocket r = 2.4mm (M2 socket cap head) from z=2.0 to 4.0
            create_cylinder_surface(mesh, sx, sy, 2.0, thickness, 2.4, segments=16, inward=True)
            create_annulus_ring(mesh, sx, sy, 2.0, 1.3, 2.4, segments=16, facing_up=True)

    return mesh


def generate_main_housing():
    mesh = STLMesh()
    width = 48.0
    chamfer = 4.0
    depth = 22.0
    wall = 3.0
    r_pcb_pocket = 18.5 # 37mm diameter circular pocket for GC9A01 PCB

    # 1. Main Outer Chassis (Octagonal Chamfered Box)
    create_octagonal_cylinder(mesh, 0, 0, 0, depth, width, chamfer)

    # 2. Front Display Pocket (z = depth - 4.5 to depth)
    create_cylinder_surface(mesh, 0, 0, depth - 4.5, depth, r_pcb_pocket, segments=48, inward=True)
    create_annulus_ring(mesh, 0, 0, depth - 4.5, 14.0, r_pcb_pocket, segments=48, facing_up=True)

    # 3. Main Internal Electronics Cavity (Houses ESP32-C3 SuperMini)
    cw, ch = 28.0, 34.0
    z_cav_bot = 2.5
    z_cav_top = depth - 4.5
    
    # Internal cavity walls (inward facing)
    c_pts = [(-cw/2, -ch/2), (cw/2, -ch/2), (cw/2, ch/2), (-cw/2, ch/2)]
    for i in range(4):
        p1 = c_pts[i]
        p2 = c_pts[(i+1)%4]
        b1 = (p1[0], p1[1], z_cav_bot)
        b2 = (p2[0], p2[1], z_cav_bot)
        t1 = (p1[0], p1[1], z_cav_top)
        t2 = (p2[0], p2[1], z_cav_top)
        mesh.add_quad(b2, b1, t1, t2)

    # Cavity bottom face
    cb1 = (-cw/2, -ch/2, z_cav_bot)
    cb2 = (cw/2, -ch/2, z_cav_bot)
    cb3 = (cw/2, ch/2, z_cav_bot)
    cb4 = (-cw/2, ch/2, z_cav_bot)
    mesh.add_quad(cb1, cb2, cb3, cb4)

    # 4. USB-C Port Cutout on Left Flank
    uw, uh = 11.0, 6.5
    uz_mid = 8.5
    ux_out = -width/2.0
    ux_in = -cw/2.0
    uy1, uy2 = -uw/2.0, uw/2.0
    uz1, uz2 = uz_mid - uh/2.0, uz_mid + uh/2.0

    mesh.add_quad((ux_out, uy1, uz1), (ux_in, uy1, uz1), (ux_in, uy2, uz1), (ux_out, uy2, uz1))
    mesh.add_quad((ux_out, uy1, uz2), (ux_out, uy2, uz2), (ux_in, uy2, uz2), (ux_in, uy1, uz2))
    mesh.add_quad((ux_out, uy1, uz1), (ux_out, uy1, uz2), (ux_in, uy1, uz2), (ux_in, uy1, uz1))
    mesh.add_quad((ux_out, uy2, uz1), (ux_in, uy2, uz1), (ux_in, uy2, uz2), (ux_out, uy2, uz2))

    # 5. 4 Corner M2 Screw Pilot Posts
    screw_dist = 18.0
    for sx in [-screw_dist, screw_dist]:
        for sy in [-screw_dist, screw_dist]:
            create_cylinder_surface(mesh, sx, sy, depth - 10.0, depth, 1.6, segments=16, inward=True)

    # 6. Rear Stand Attachment Tabs
    for bx in [-10.0, 10.0]:
        create_cylinder_surface(mesh, bx, -15.0, 0, 3.0, 2.5, segments=16)

    return mesh


def generate_desk_stand():
    mesh = STLMesh()
    base_w = 54.0
    base_d = 56.0
    base_h = 10.0
    cradle_top_z = 26.0

    bw2 = base_w / 2.0
    bd2 = base_d / 2.0
    
    # Bottom face
    mesh.add_quad((-bw2, -bd2, 0), (bw2, -bd2, 0), (bw2, bd2, 0), (-bw2, bd2, 0))

    # Base side walls
    mesh.add_quad((-bw2, -bd2, 0), (-bw2, bd2, 0), (-bw2, bd2, base_h), (-bw2, -bd2, base_h))
    mesh.add_quad((bw2, -bd2, 0), (bw2, -bd2, base_h), (bw2, bd2, base_h), (bw2, bd2, 0))
    mesh.add_quad((-bw2, -bd2, 0), (bw2, -bd2, 0), (bw2, -bd2, base_h), (-bw2, -bd2, base_h))
    mesh.add_quad((-bw2, bd2, 0), (-bw2, bd2, base_h), (bw2, bd2, base_h), (bw2, bd2, 0))

    # 2. Angled Upright Rest Plane
    p_f1 = (-bw2 + 4, -bd2 + 8, base_h)
    p_f2 = (bw2 - 4, -bd2 + 8, base_h)
    p_t1 = (-bw2 + 4, bd2 - 6, cradle_top_z)
    p_t2 = (bw2 - 4, bd2 - 6, cradle_top_z)
    mesh.add_quad(p_f1, p_f2, p_t2, p_t1)

    p_b1 = (-bw2 + 4, bd2 - 6, base_h)
    p_b2 = (bw2 - 4, bd2 - 6, base_h)
    mesh.add_quad(p_b1, p_b2, p_t2, p_t1)

    mesh.add_triangle(p_f1, p_t1, (-bw2 + 4, bd2 - 6, base_h))
    mesh.add_triangle(p_f2, (bw2 - 4, bd2 - 6, base_h), p_t2)

    # 3. Rear Cable Relief Channel
    cw2 = 7.0
    mesh.add_quad((-cw2, -bd2, 0), (cw2, -bd2, 0), (cw2, bd2, 0), (-cw2, bd2, 0))

    # 4. Anti-Slip Rubber Foot Recesses
    for fx in [-bw2 + 8, bw2 - 8]:
        for fy in [-bd2 + 8, bd2 - 8]:
            create_cylinder_surface(mesh, fx, fy, 0, 1.2, 4.0, segments=16, inward=True)
            create_annulus_ring(mesh, fx, fy, 1.2, 0.1, 4.0, segments=16, facing_up=True)

    return mesh


def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Front Bezel Plate
    bezel_path = os.path.join(output_dir, "gc9a01_front_bezel.stl")
    bezel_mesh = generate_front_bezel()
    bezel_mesh.write_binary(bezel_path, "GC9A01 Front Bezel Plate")

    # 2. Main Housing Enclosure
    housing_path = os.path.join(output_dir, "gc9a01_main_housing.stl")
    housing_mesh = generate_main_housing()
    housing_mesh.write_binary(housing_path, "GC9A01 Main Housing")

    # 3. 20-Degree Angled Desk Stand
    stand_path = os.path.join(output_dir, "gc9a01_desk_stand.stl")
    stand_mesh = generate_desk_stand()
    stand_mesh.write_binary(stand_path, "GC9A01 20-Degree Desk Stand")

    print("\n[SUCCESS] All 3 STL models generated successfully in 'enclosure/' directory!")

if __name__ == "__main__":
    main()
