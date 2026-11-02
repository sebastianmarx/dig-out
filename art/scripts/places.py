"""Place tile builders (besides the cell block, see build_cellblock.py).

Each builder fills an empty scene; build_place.py adds camera, lights and renders.
"""

import math
import random

import bpy

from diorama import back_walls, bench, ground, table, wall, wall_lamp
from digout_art import box, cylinder, look_at, point_light, rock, sphere, torus

R90 = math.radians(90)


# -------------------------------------------------------------- cafeteria ---

def build_cafeteria(standalone=True):
    """Serving counter with pots and the cutlery tub (spoons!), steel tables with trays."""
    rnd = random.Random(2)
    ground("cafe_floor", "cafe_floor_alt", earth=standalone)
    back_walls(lower="wall_green")

    # Serving counter along the back wall, sneeze guard, pots with food.
    box("counter", (3.2, 0.6, 0.9), (0.15, 1.45, 0.45), "counter", bevel=0.015)
    box("counter_top", (3.25, 0.66, 0.04), (0.15, 1.45, 0.92), "steel", bevel=0.008)
    for i, x in enumerate((-0.8, -0.1, 0.6)):
        cylinder(f"pot_{i}", 0.17, 0.24, (x, 1.47, 1.06), "steel", bevel=0.01)
        cylinder(f"pot_food_{i}", 0.155, 0.02, (x, 1.47, 1.16), ("food", "food_green", "food")[i],
                 bevel=0.004)
    for x in (-1.25, 0.15, 1.55):
        cylinder(f"guard_post_{x}", 0.012, 0.42, (x, 1.18, 1.15), "steel", verts=12, bevel=0.0)
    box("sneeze_guard", (2.9, 0.012, 0.32), (0.15, 1.16, 1.3), "glass", rot=(math.radians(-15), 0, 0),
        bevel=0.0)

    # The cutlery tub – where the escape begins.
    cylinder("cutlery_tub", 0.08, 0.17, (1.45, 1.5, 1.02), "steel", bevel=0.01)
    for i in range(6):
        ang = rnd.uniform(0, 2 * math.pi)
        tilt = (rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), ang)
        x, y = 1.45 + 0.03 * math.cos(ang), 1.5 + 0.03 * math.sin(ang)
        box(f"spoon_handle_{i}", (0.012, 0.004, 0.2), (x, y, 1.15), "steel", rot=tilt, bevel=0.0)
        sphere(f"spoon_bowl_{i}", 0.022, (x + tilt[1] * 0.1, y - tilt[0] * 0.1, 1.25), "steel",
               scale=(1.0, 0.45, 1.4), rot=tilt)

    # Tray stack and chalkboard menu.
    for i in range(6):
        box(f"tray_stack_{i}", (0.4, 0.3, 0.02), (-1.45, 1.45, 0.96 + i * 0.025), "tray", bevel=0.006)
    box("menu", (1.1, 0.03, 0.6), (-0.3, 1.79, 1.85), "chalkboard", bevel=0.01)
    for i, w in enumerate((0.7, 0.5, 0.8, 0.4)):
        box(f"menu_line_{i}", (w, 0.01, 0.025), (-0.55 + w / 2, 1.77, 2.02 - i * 0.11), "chalk", bevel=0.0)

    # Steel tables with fixed benches and trays.
    for t, (cx, cy) in enumerate(((-0.6, 0.35), (0.95, -0.75))):
        table(f"table_{t}", (cx, cy), (1.6, 0.6), 0.72, top_key="counter")
        bench(f"bench_{t}_a", (cx, cy - 0.5), 1.6)
        bench(f"bench_{t}_b", (cx, cy + 0.5), 1.6)
        for k in range(2):
            tx = cx - 0.4 + k * 0.75 + rnd.uniform(-0.05, 0.05)
            ty = cy + (0.12 if k == 0 else -0.12)
            box(f"tray_{t}_{k}", (0.38, 0.28, 0.025), (tx, ty, 0.76), "tray", rot=(0, 0, rnd.uniform(-0.2, 0.2)),
                bevel=0.006)
            sphere(f"mash_{t}_{k}", 0.06, (tx - 0.08, ty, 0.79), "food", scale=(1.0, 1.0, 0.5))
            sphere(f"peas_{t}_{k}", 0.045, (tx + 0.07, ty + 0.05, 0.785), "food_green", scale=(1.2, 0.8, 0.4))
            cylinder(f"cup_{t}_{k}", 0.035, 0.09, (tx + 0.1, ty - 0.07, 0.82), "steel", bevel=0.004)

    wall_lamp(-0.9)
    wall_lamp(1.1)


# ---------------------------------------------------------------- showers ---

def build_showers(standalone=True):
    """Tiled shower room: three stalls, pipes, puddles – and the soap on the floor."""
    ground("tile_floor", earth=standalone)
    back_walls(lower="tile_white", upper="tile_white", lower_h=2.4)
    for x in (-0.55, 0.55):
        wall(f"stall_{x}", (0.08, 0.9, 1.7), (x, 1.35, 0), "tile_white", "tile_white", lower_h=1.7)

    # Water pipe along the back wall, three shower heads with valves.
    cylinder("pipe_main", 0.03, 3.6, (0.1, 1.74, 2.05), "steel", rot=(0, R90, 0), bevel=0.0)
    for i, x in enumerate((-1.15, 0.0, 1.15)):
        cylinder(f"pipe_drop_{i}", 0.022, 0.2, (x, 1.74, 1.95), "steel", bevel=0.0)
        cylinder(f"pipe_arm_{i}", 0.02, 0.18, (x, 1.66, 1.85), "steel", rot=(R90, 0, 0), bevel=0.0)
        cylinder(f"shower_head_{i}", 0.07, 0.05, (x, 1.56, 1.82), "steel", rot=(math.radians(-35), 0, 0),
                 bevel=0.01)
        torus(f"valve_{i}", 0.04, 0.008, (x, 1.78, 1.15), "steel", rot=(R90, 0, 0))
        cylinder(f"drain_{i}", 0.07, 0.01, (x, 1.25, 0.022), "bars", verts=16, bevel=0.0)

    # Puddles (glossy), soap bar, towel and wooden bench on the left wall.
    for i, (x, y, r, sx) in enumerate([(0.1, 1.05, 0.22, 1.6), (-1.0, 0.5, 0.14, 1.3), (0.9, -0.2, 0.18, 1.4)]):
        cylinder(f"puddle_{i}", r, 0.004, (x, y, 0.022), "puddle", bevel=0.0)
        bpy.context.active_object.scale = (sx, 1.0, 1.0)
    box("soap", (0.17, 0.1, 0.06), (0.35, -0.35, 0.05), "soap", rot=(0, 0, 0.5), bevel=0.018)
    cylinder("towel_hook", 0.012, 0.08, (-1.76, 0.25, 1.75), "steel", rot=(0, R90, 0), bevel=0.0)
    box("towel", (0.03, 0.36, 0.7), (-1.74, 0.25, 1.38), "towel", bevel=0.01)
    bench("bench", (-1.5, -0.6), length=1.4, axis="y", key="wood")

    wall_lamp(0.0, z=2.25, energy=40)
    point_light(bpy.context.scene, "steam_glow", (0.0, 1.0, 1.6), energy=15, hex_color="#cfe2ff", radius=0.6)


# -------------------------------------------------------------- infirmary ---

def build_infirmary(standalone=True):
    """Hospital bed, IV stand, medicine cabinet with red cross, curtain rail."""
    ground("lino", earth=standalone)
    back_walls(lower="wall_pale")

    # Bed with sheet and pillow along the back wall.
    bx, by = -0.6, 1.35
    box("bed_frame", (1.9, 0.85, 0.08), (bx, by, 0.55), "metal", bevel=0.01)
    for dx in (-0.9, 0.9):
        for dy in (-0.38, 0.38):
            cylinder(f"bed_leg_{dx}_{dy}", 0.02, 0.5, (bx + dx, by + dy, 0.27), "metal", verts=12, bevel=0.0)
            sphere(f"bed_wheel_{dx}_{dy}", 0.035, (bx + dx, by + dy, 0.035), "tire")
    box("bed_mattress", (1.85, 0.8, 0.14), (bx, by, 0.66), "mattress", bevel=0.03)
    box("bed_sheet", (1.3, 0.84, 0.04), (bx + 0.25, by, 0.74), "sheet", bevel=0.015)
    box("bed_pillow", (0.3, 0.5, 0.11), (bx - 0.75, by, 0.78), "pillow", bevel=0.04)
    for dx in (-0.95, 0.95):
        box(f"bed_rail_{dx}", (0.04, 0.85, 0.3), (bx + dx, by, 0.75), "metal", bevel=0.01)

    # IV stand with bag.
    ix, iy = 0.65, 1.55
    cylinder("iv_pole", 0.014, 1.8, (ix, iy, 0.9), "steel", verts=12, bevel=0.0)
    for ang in (0, 90):
        box(f"iv_foot_{ang}", (0.45, 0.04, 0.03), (ix, iy, 0.03), "steel", rot=(0, 0, math.radians(ang)),
            bevel=0.005)
    box("iv_hook", (0.18, 0.015, 0.015), (ix, iy, 1.78), "steel", bevel=0.0)
    box("iv_bag", (0.11, 0.04, 0.2), (ix + 0.07, iy, 1.62), "glass", bevel=0.015)
    cylinder("iv_tube", 0.004, 0.9, (ix + 0.07, iy - 0.1, 1.1), "glass", rot=(math.radians(20), 0, 0),
             verts=8, bevel=0.0)

    # Medicine cabinet with red cross on the left wall, side table with pill bottles.
    box("cabinet", (0.28, 0.8, 1.0), (-1.65, 0.25, 1.35), "cabinet", bevel=0.015)
    box("cabinet_split", (0.01, 0.01, 0.95), (-1.505, 0.25, 1.35), "metal", bevel=0.0)
    box("cross_v", (0.01, 0.08, 0.28), (-1.5, 0.25, 1.55), "cross", bevel=0.0)
    box("cross_h", (0.01, 0.28, 0.08), (-1.5, 0.25, 1.55), "cross", bevel=0.0)
    table("side_table", (1.25, 1.45), (0.5, 0.4), 0.7, top_key="cabinet")
    for i, (dx, dy) in enumerate([(-0.12, 0.05), (0.0, -0.08), (0.12, 0.06), (0.05, 0.1)]):
        cylinder(f"pill_{i}", 0.03, 0.08, (1.25 + dx, 1.45 + dy, 0.77), "pill", bevel=0.005)
        cylinder(f"pill_cap_{i}", 0.032, 0.02, (1.25 + dx, 1.45 + dy, 0.82), "cross", bevel=0.004)

    # Red cross sign on the back wall and a curtain rail with a bunched curtain on the right.
    box("sign", (0.5, 0.03, 0.5), (-0.6, 1.79, 1.9), "sheet", bevel=0.01)
    box("sign_v", (0.12, 0.01, 0.38), (-0.6, 1.775, 1.9), "cross", bevel=0.0)
    box("sign_h", (0.38, 0.01, 0.12), (-0.6, 1.775, 1.9), "cross", bevel=0.0)
    cylinder("curtain_rail", 0.012, 1.8, (1.75, 0.9, 2.1), "steel", rot=(R90, 0, 0), bevel=0.0)
    for i in range(7):
        box(f"curtain_fold_{i}", (0.05, 0.07, 1.75), (1.75 + (0.02 if i % 2 else -0.02), 1.55 + i * 0.045, 1.2),
            "curtain", bevel=0.02)

    wall_lamp(0.6)


# ------------------------------------------------------------- recreation ---

def build_recreation(standalone=True):
    """TV corner with sofa, card table with cigarettes (the currency), vending machine."""
    rnd = random.Random(5)
    ground("wood_floor", "wood_floor_alt", plank=True, earth=standalone)
    back_walls()

    # TV on a wall bracket + sofa facing it.
    box("tv_bracket", (0.1, 0.12, 0.1), (0.9, 1.74, 1.8), "metal", bevel=0.0)
    box("tv", (0.95, 0.1, 0.58), (0.9, 1.66, 1.8), "tv", rot=(math.radians(-8), 0, 0), bevel=0.015)
    box("tv_screen", (0.85, 0.01, 0.48), (0.9, 1.605, 1.795), "screen", rot=(math.radians(-8), 0, 0), bevel=0.0)
    point_light(bpy.context.scene, "tv_glow", (0.9, 1.3, 1.6), energy=20, hex_color="#8ab8ff", radius=0.3)
    sx, sy = 0.9, 0.55
    box("sofa_seat", (1.5, 0.65, 0.4), (sx, sy, 0.22), "sofa", bevel=0.05)
    box("sofa_back", (1.5, 0.2, 0.45), (sx, sy - 0.3, 0.6), "sofa", bevel=0.05)
    for dx in (-0.78, 0.78):
        box(f"sofa_arm_{dx}", (0.18, 0.65, 0.55), (sx + dx, sy, 0.3), "sofa", bevel=0.05)
    box("sofa_cushion_tear", (0.12, 0.1, 0.02), (sx - 0.3, sy + 0.1, 0.43), "mattress", bevel=0.01)

    # Card table: cards, cigarette packs and loose cigarettes.
    tx, ty = -0.9, 0.95
    cylinder("card_table_top", 0.45, 0.05, (tx, ty, 0.72), "wood", bevel=0.01)
    cylinder("card_table_leg", 0.05, 0.7, (tx, ty, 0.35), "metal", bevel=0.0)
    cylinder("card_table_foot", 0.25, 0.03, (tx, ty, 0.015), "metal", bevel=0.005)
    for i in range(7):
        ang = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.05, 0.3)
        box(f"card_{i}", (0.09, 0.13, 0.003), (tx + r * math.cos(ang), ty + r * math.sin(ang), 0.75 + i * 0.001),
            "card", rot=(0, 0, rnd.uniform(0, math.pi)), bevel=0.0)
    for i in range(3):
        box(f"cig_pack_{i}", (0.08, 0.05, 0.11), (tx - 0.2 + i * 0.12, ty + 0.25, 0.8), "cigarette",
            rot=(0, 0, rnd.uniform(-0.3, 0.3)), bevel=0.008)
    for i in range(6):
        ang = rnd.uniform(0, 2 * math.pi)
        x, y = tx + 0.2 * math.cos(ang), ty - 0.1 + 0.12 * math.sin(ang)
        cylinder(f"cig_{i}", 0.007, 0.08, (x, y, 0.755), "cigarette", rot=(R90, 0, ang), verts=8, bevel=0.0)
    for i, ang in enumerate((0.3, 2.5)):
        cx, cy = tx + 0.65 * math.cos(ang), ty + 0.65 * math.sin(ang)
        box(f"chair_seat_{i}", (0.4, 0.4, 0.05), (cx, cy, 0.45), "wood", bevel=0.01)
        for dx in (-0.16, 0.16):
            for dy in (-0.16, 0.16):
                box(f"chair_leg_{i}_{dx}_{dy}", (0.03, 0.03, 0.45), (cx + dx, cy + dy, 0.225), "metal", bevel=0.0)

    # Vending machine against the left wall (front panel faces the room).
    box("vending", (0.6, 0.8, 1.85), (-1.48, -0.55, 0.93), "vending", bevel=0.02)
    box("vending_window", (0.02, 0.5, 1.0), (-1.17, -0.62, 1.15), "vending_light", bevel=0.0)
    box("vending_slot", (0.02, 0.4, 0.12), (-1.17, -0.62, 0.3), "tv", bevel=0.0)

    wall_lamp(-0.8)
    wall_lamp(0.6, on_left_wall=True, y=0.6)


# ------------------------------------------------------------------- yard ---

def build_yard(standalone=True):
    """Outdoor yard: asphalt, chain-link fence with barbed wire, basketball hoop, weights, floodlight."""
    ground("asphalt", earth=standalone)
    # Court markings.
    box("line_base", (3.6, 0.04, 0.004), (0.1, 1.3, 0.022), "court_line", bevel=0.0)
    box("line_side", (0.04, 2.6, 0.004), (0.7, 0.0, 0.022), "court_line", bevel=0.0)
    torus("line_circle", 0.6, 0.02, (0.7, 1.3, 0.022), "court_line", scale=(1.0, 1.0, 0.1))

    # Fence along the back and left edge.
    for side, (axis, fixed) in {"back": ("x", 1.92), "left": ("y", -1.92)}.items():
        for i, t in enumerate((-1.9, -0.95, 0.0, 0.95, 1.9)):
            loc = (t, fixed, 1.1) if axis == "x" else (fixed, t, 1.1)
            cylinder(f"post_{side}_{i}", 0.035, 2.2, loc, "fence", verts=12, bevel=0.0)
        rail = (3.84, 0.02, 0.02) if axis == "x" else (0.02, 3.84, 0.02)
        mesh = (3.84, 0.004, 2.0) if axis == "x" else (0.004, 3.84, 2.0)
        center = (0, fixed) if axis == "x" else (fixed, 0)
        box(f"rail_{side}", rail, (*center, 2.18), "fence", bevel=0.0)
        box(f"mesh_{side}", mesh, (*center, 1.1), "fence_mesh", bevel=0.0)
        for i in range(24):  # barbed wire coil on top
            t = -1.9 + i * (3.8 / 23)
            loc = (t, fixed, 2.32) if axis == "x" else (fixed, t, 2.32)
            rot = (0, R90, 0) if axis == "x" else (R90, 0, 0)
            torus(f"barb_{side}_{i}", 0.1, 0.006, loc, "fence", rot=rot)

    # Basketball hoop.
    cylinder("hoop_pole", 0.05, 2.3, (1.2, 1.75, 1.15), "metal", bevel=0.0)
    box("hoop_board", (0.75, 0.04, 0.48), (1.2, 1.6, 2.15), "board", bevel=0.01)
    box("hoop_square", (0.3, 0.01, 0.2), (1.2, 1.578, 2.08), "hoop", bevel=0.0)
    torus("hoop_ring", 0.13, 0.012, (1.2, 1.43, 1.98), "hoop")

    # Weight bench with barbell, tyre, scattered gravel.
    bench("weight_bench", (-0.9, 0.9), length=1.0, axis="y", key="vending")
    cylinder("barbell_bar", 0.015, 1.4, (-0.9, 1.2, 0.95), "steel", rot=(0, R90, 0), bevel=0.0)
    for x in (-1.45, -1.35, -0.45, -0.35):
        cylinder(f"plate_{x}", 0.16, 0.05, (x, 1.2, 0.95), "tire", rot=(0, R90, 0), bevel=0.01)
    for dx in (-0.25, 0.25):
        box(f"barbell_rack_{dx}", (0.04, 0.04, 0.95), (-0.9 + dx, 1.25, 0.47), "metal", bevel=0.0)
    torus("tyre", 0.22, 0.08, (-1.2, -1.2, 0.08), "tire")
    for i in range(12):
        rnd = random.Random(i)
        rock(f"gravel_{i}", rnd.uniform(0.02, 0.04), (rnd.uniform(-1.8, 1.8), rnd.uniform(-1.8, 1.0), 0.03),
             "stone")

    # Floodlight in the right corner.
    cylinder("flood_pole", 0.05, 2.6, (1.8, 1.8, 1.3), "metal", bevel=0.0)
    box("flood_head", (0.35, 0.18, 0.2), (1.65, 1.65, 2.55), "metal", rot=(math.radians(35), 0, math.radians(45)),
        bevel=0.02)
    box("flood_lens", (0.3, 0.01, 0.16), (1.6, 1.58, 2.5), "floodlight", rot=(math.radians(35), 0, math.radians(45)),
        bevel=0.0)
    spot = bpy.data.lights.new("flood", "SPOT")
    spot.energy = 900
    spot.spot_size = math.radians(70)
    spot.spot_blend = 0.6
    spot.shadow_soft_size = 0.15
    spot.color = (1.0, 0.93, 0.8)
    obj = bpy.data.objects.new("flood", spot)
    obj.location = (1.55, 1.55, 2.45)
    bpy.context.scene.collection.objects.link(obj)
    look_at(obj, (-0.3, -0.3, 0))


from cellblock import build_cellblock  # noqa: E402

PLACES = {
    "cellblock": build_cellblock,
    "cafeteria": build_cafeteria,
    "showers": build_showers,
    "infirmary": build_infirmary,
    "recreation": build_recreation,
    "yard": build_yard,
}
