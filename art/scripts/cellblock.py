"""Cell block diorama (place.cellblock): two cells, bars cut at mid height, a tunnel hole with a spoon."""

import math

import bpy
from mathutils import Vector

from digout_art import boolean_cut, box, cylinder, point_light, rock, sphere, torus


def build_cellblock(standalone=True):
    """standalone=True: own soil block with the tunnel in the cross-section (single tile render).
    standalone=False: only the room on its slab, for the combined board."""
    hole = build_ground(standalone)
    build_walls()
    build_bars()
    build_left_cell(hole)
    build_right_cell()
    build_lamps()
    build_wear()


def build_ground(standalone):
    earth = box("earth", (4, 4, 0.8), (0, 0, -0.5), "earth", bevel=0.0) if standalone else None
    slab = box("slab", (4, 4, 0.1), (0, 0, -0.05), "concrete", bevel=0.0)
    # Checkered floor tiles in the corridor; the gaps show the concrete slab as grout.
    tile, gap = 0.5, 0.025
    for ix in range(8):
        for iy in range(4):
            key = "corridor" if (ix + iy) % 2 == 0 else "corridor_alt"
            box(f"tile_{ix}_{iy}", (tile - gap, tile - gap, 0.025),
                (-2 + tile * (ix + 0.5), -2 + tile * (iy + 0.5), 0.0125), key, bevel=0.004)

    hole = (-1.3, 0.5)  # visible through the open cell door
    shaft = cylinder("shaft_cut", 0.26, 0.9, (hole[0], hole[1], -0.35), "tunnel", verts=16)
    boolean_cut(slab, shaft, "tunnel")
    if earth is not None:  # standalone tile: the tunnel shows in the soil cross-section
        boolean_cut(earth, shaft, "tunnel")
        tunnel = cylinder("tunnel_cut", 0.26, 2.8, (hole[0], -0.8, -0.48), "tunnel",
                          rot=(math.radians(90), 0, 0), verts=16)
        boolean_cut(earth, tunnel, "tunnel")

    # Rubble around the hole and stones in the soil cross-section.
    for i, (dx, dy, r) in enumerate([(0.33, 0.05, 0.07), (0.25, -0.22, 0.05), (-0.3, 0.2, 0.06),
                                     (0.1, 0.32, 0.045)]):
        rock(f"rubble_{i}", r, (hole[0] + dx, hole[1] + dy, 0.03), "earth_dark")
    if standalone:
        for i, (x, z, r) in enumerate([(1.2, -0.3, 0.09), (1.6, -0.72, 0.07), (-0.4, -0.62, 0.08),
                                       (0.4, -0.78, 0.06)]):
            rock(f"stone_{i}", r, (x, -2.0, z), "stone")
        for i, (y, z, r) in enumerate([(-1.2, -0.4, 0.08), (0.3, -0.7, 0.06), (1.4, -0.35, 0.07)]):
            rock(f"stone_side_{i}", r, (2.0, y, z), "stone")
    return hole


def wall(name, size, loc):
    """Two-tone prison wall: teal lower part, beige upper part."""
    sx, sy, sz = size
    lower_h = 0.9
    box(f"{name}_lower", (sx, sy, lower_h), (loc[0], loc[1], lower_h / 2), "wall_lower")
    box(f"{name}_upper", (sx, sy, sz - lower_h), (loc[0], loc[1], lower_h + (sz - lower_h) / 2),
        "wall_upper")


def build_walls():
    height = 2.4
    wall("wall_left", (0.2, 4.0, height), (-1.9, 0, 0))
    wall("wall_back", (3.8, 0.2, height), (0.1, 1.9, 0))
    wall("wall_divider", (0.16, 1.8, height), (0, 0.9, 0))


def build_bars():
    """Cell bars, cut away at mid height so the cell interiors stay readable."""
    y = 0.0
    top = 1.3
    door_left = (-1.6, -1.0)  # open door gap in the left cell
    x = -1.72
    while x < 1.9:
        if not (door_left[0] < x < door_left[1]) and abs(x) > 0.12:
            cylinder(f"bar_{x:.2f}", 0.026, top, (x, y, top / 2), "bars", verts=8)
        x += 0.22
    for z in (0.12, top):
        for x0, x1 in ((-1.8, door_left[0]), (door_left[1], -0.08), (0.08, 1.95)):
            box(f"rail_{x0}_{z}", (x1 - x0, 0.06, 0.06), ((x0 + x1) / 2, y, z), "bars", bevel=0.0)

    # Open door, swung into the corridor.
    width = door_left[1] - door_left[0]
    angle = math.radians(-70)
    hinge = Vector((door_left[0], y, 0))
    door_dir = Vector((math.cos(angle), math.sin(angle), 0))
    for i in range(3):
        p = hinge + door_dir * (0.08 + i * (width - 0.12) / 2)
        cylinder(f"door_bar_{i}", 0.026, top, (p.x, p.y, top / 2), "bars", verts=8)
    for z in (0.12, top):
        mid = hinge + door_dir * (width / 2)
        box(f"door_rail_{z}", (width, 0.06, 0.06), (mid.x, mid.y, z), "bars",
            rot=(0, 0, angle), bevel=0.0)
    box("lock", (0.12, 0.08, 0.16), (1.0, y - 0.04, 0.75), "metal")


def build_left_cell(hole):
    # Bunk bed against the back wall.
    x0, x1, y0, y1 = -1.75, -0.55, 1.05, 1.75
    for px in (x0 + 0.04, x1 - 0.04):
        for py in (y0 + 0.04, y1 - 0.04):
            box(f"bunk_post_{px:.2f}_{py:.2f}", (0.06, 0.06, 1.75), (px, py, 0.875), "metal", bevel=0.0)
    for z, blanket in ((0.45, "blanket"), (1.35, "mattress")):
        box(f"bunk_frame_{z}", (x1 - x0, y1 - y0, 0.06), ((x0 + x1) / 2, (y0 + y1) / 2, z), "metal")
        box(f"bunk_mattress_{z}", (x1 - x0 - 0.08, y1 - y0 - 0.06, 0.12),
            ((x0 + x1) / 2, (y0 + y1) / 2, z + 0.09), "mattress", bevel=0.03)
        box(f"bunk_blanket_{z}", (0.75, y1 - y0 - 0.02, 0.05),
            (x1 - 0.42, (y0 + y1) / 2, z + 0.17), blanket, bevel=0.02)
        box(f"bunk_pillow_{z}", (0.28, 0.45, 0.1), (x0 + 0.2, (y0 + y1) / 2, z + 0.2), "pillow", bevel=0.04)

    # Poster on the left wall, hiding nothing in particular.
    box("poster", (0.02, 0.55, 0.75), (-1.79, 0.45, 1.55), "poster_bg", bevel=0.0)
    box("poster_motif", (0.02, 0.3, 0.3), (-1.775, 0.45, 1.62), "poster_fg", bevel=0.0)

    # Spoon next to the hole – the escape tool of choice.
    sx, sy = hole[0] + 0.38, hole[1] - 0.2
    sphere("spoon_bowl", 0.06, (sx, sy, 0.02), "metal", scale=(1.0, 1.5, 0.3))
    box("spoon_handle", (0.025, 0.24, 0.015), (sx + 0.0, sy - 0.2, 0.015), "metal", bevel=0.0)


def build_right_cell():
    # Single bed.
    x0, x1, y0, y1 = 0.85, 1.95, 1.1, 1.75
    box("bed_frame", (x1 - x0, y1 - y0, 0.06), ((x0 + x1) / 2, (y0 + y1) / 2, 0.42), "metal")
    for px in (x0 + 0.04, x1 - 0.04):
        for py in (y0 + 0.04, y1 - 0.04):
            box(f"bed_leg_{px:.2f}_{py:.2f}", (0.05, 0.05, 0.42), (px, py, 0.21), "metal", bevel=0.0)
    box("bed_mattress", (x1 - x0 - 0.06, y1 - y0 - 0.06, 0.12), ((x0 + x1) / 2, (y0 + y1) / 2, 0.51),
        "mattress", bevel=0.03)
    box("bed_blanket", (0.7, y1 - y0, 0.05), (x0 + 0.4, (y0 + y1) / 2, 0.59), "blanket", bevel=0.02)
    box("bed_pillow", (0.26, 0.42, 0.1), (x1 - 0.18, (y0 + y1) / 2, 0.62), "pillow", bevel=0.04)

    # Steel toilet and sink against the divider wall.
    cylinder("toilet_base", 0.14, 0.38, (0.3, 1.45, 0.19), "porcelain", verts=14)
    cylinder("toilet_seat", 0.19, 0.06, (0.33, 1.42, 0.4), "porcelain", verts=14)
    box("toilet_tank", (0.12, 0.32, 0.3), (0.13, 1.45, 0.55), "porcelain", bevel=0.02)
    box("sink", (0.3, 0.38, 0.12), (0.24, 0.75, 0.85), "porcelain", bevel=0.03)
    box("mirror", (0.02, 0.3, 0.38), (0.09, 0.75, 1.45), "metal", bevel=0.0)

    # Small shelf with a book on the back wall.
    box("shelf", (0.6, 0.18, 0.04), (1.45, 1.71, 1.35), "wood")
    box("book_1", (0.08, 0.14, 0.24), (1.25, 1.71, 1.49), "book", bevel=0.0)
    box("book_2", (0.07, 0.14, 0.2), (1.35, 1.71, 1.47), "poster_fg", bevel=0.0)


def build_lamps():
    for x in (-1.0, 1.0):
        box(f"lamp_{x}", (0.3, 0.08, 0.1), (x, 1.76, 2.15), "lamp", bevel=0.0)
        box(f"lamp_cage_{x}", (0.34, 0.1, 0.03), (x, 1.75, 2.08), "bars", bevel=0.0)
        # Warm pools of light on the walls against the cold moonlight.
        point_light(bpy.context.scene, f"lamp_light_{x}", (x, 1.62, 2.02))


def build_wear():
    """Small storytelling details: tally marks, gang tag, cracks (dirt lives in the materials)."""
    # Tally marks scratched into the corridor wall: 3 full groups + 2 strokes.
    wall_x = -1.795
    y, z = -0.35, 1.45
    for group in range(4):
        strokes = 4 if group < 3 else 2
        y0 = y
        for _ in range(strokes):
            box(f"tally_{group}_{y:.2f}", (0.01, 0.022, 0.24), (wall_x, y, z), "scratch",
                bevel=0.0)
            y -= 0.06
        if strokes == 4:
            mid = (y0 + y + 0.06) / 2
            box(f"tally_cross_{group}", (0.01, 0.022, 0.3), (wall_x - 0.002, mid, z), "scratch",
                rot=(math.radians(55), 0, 0), bevel=0.0)
        y -= 0.1

    # Gang tag sprayed on the back wall of the right cell: crossed-out circle.
    torus("gang_tag_ring", 0.19, 0.022, (0.55, 1.79, 1.82), "spray",
          rot=(math.radians(90), 0, 0), scale=(1.0, 1.0, 0.25))
    for angle in (35, -35):
        box(f"gang_tag_slash_{angle}", (0.5, 0.01, 0.04), (0.55, 1.791, 1.82), "spray",
            rot=(0, math.radians(angle), 0), bevel=0.0)

    # Hairline crack running down the left wall.
    crack = [(1.25, 2.4), (1.15, 2.2), (1.22, 2.0), (1.08, 1.82), (1.12, 1.65)]
    for i in range(len(crack) - 1):
        (y0, z0), (y1, z1) = crack[i], crack[i + 1]
        length = math.hypot(y1 - y0, z1 - z0)
        angle = math.atan2(y1 - y0, z1 - z0)
        box(f"crack_{i}", (0.01, 0.014, length), (-1.795, (y0 + y1) / 2 - 1.9, (z0 + z1) / 2),
            "scratch", rot=(-angle, 0, 0), bevel=0.0)
