"""Card illustrations, tokens and small props (project.md 8.6.5 / 8.6.6).

Every builder creates its object around the origin, resting on z=0, roughly 1.5 units across,
and returns the parent empty. ITEMS maps asset id -> (builder, ortho scale, camera target z).
"""

import math
import random

import bpy

from digout_art import boolean_cut, bowl, box, cone, cylinder, group, rock, sphere, torus
from props import build_spoon

R90 = math.radians(90)
PI = math.pi


# --------------------------------------------------------------- material ---

def build_container(name):
    p = group(name)
    cylinder(f"{name}.can", 0.32, 0.6, (0, 0, 0.3), "tin", bevel=0.005, parent=p)
    for z in (0.02, 0.59):
        torus(f"{name}.rim_{z}", 0.32, 0.016, (0, 0, z), "tin", parent=p)
    cylinder(f"{name}.label", 0.325, 0.32, (0, 0, 0.3), "label", bevel=0.0, parent=p)
    cylinder(f"{name}.inside", 0.3, 0.006, (0, 0, 0.597), "pip", bevel=0.0, parent=p)
    cylinder(f"{name}.lid", 0.3, 0.012, (0, 0.27, 0.8), "tin", rot=(math.radians(-62), 0, 0), bevel=0.003,
             parent=p)
    return p


def build_pike(name):
    p = group(name)
    cylinder(f"{name}.rod", 0.035, 1.3, (0, -0.1, 0.035), "steel", rot=(R90, 0, 0), bevel=0.004, parent=p)
    cone(f"{name}.tip", 0.035, 0.0, 0.28, (0, 0.69, 0.035), "steel", rot=(-R90, 0, 0), parent=p)
    cylinder(f"{name}.grip", 0.05, 0.4, (0, -0.5, 0.05), "tape", rot=(R90, 0, 0), bevel=0.006, parent=p)
    p.rotation_euler = (0, 0, math.radians(-25))
    return p


def build_chain(name):
    p = group(name)
    for i in range(5):
        x = -0.72 + i * 0.36
        if i % 2 == 0:
            torus(f"{name}.link_{i}", 0.16, 0.035, (x, 0, 0.035), "steel", scale=(1.6, 1, 1), parent=p)
        else:
            torus(f"{name}.link_{i}", 0.16, 0.035, (x, 0, 0.195), "steel", rot=(R90, 0, 0), scale=(1.6, 1, 1),
                  parent=p)
    p.rotation_euler = (0, 0, math.radians(30))
    return p


# ---------------------------------------------------------------- weapons ---

def build_blade(name):
    p = group(name)
    box(f"{name}.blade", (0.55, 0.24, 0.012), (0, 0.04, 0.012), "steel", bevel=0.002, parent=p)
    box(f"{name}.slot", (0.3, 0.05, 0.013), (0, 0.06, 0.013), "pip", bevel=0.0, parent=p)
    box(f"{name}.tape", (0.6, 0.11, 0.045), (0, -0.09, 0.025), "tape", bevel=0.01, parent=p)
    p.rotation_euler = (0, 0, math.radians(20))
    return p


def build_knife(name):
    p = group(name)
    box(f"{name}.blade", (0.62, 0.11, 0.02), (0.22, 0, 0.03), "steel", bevel=0.004, parent=p)
    cone(f"{name}.tip", 0.055, 0.0, 0.22, (0.64, 0, 0.03), "steel", rot=(0, R90, 0), verts=4, parent=p)
    cylinder(f"{name}.handle", 0.055, 0.45, (-0.3, 0, 0.055), "cloth_red", rot=(0, R90, 0), bevel=0.01, parent=p)
    for x in (-0.45, -0.15):
        cylinder(f"{name}.wrap_{x}", 0.06, 0.04, (x, 0, 0.055), "tape", rot=(0, R90, 0), bevel=0.004, parent=p)
    p.rotation_euler = (0, 0, math.radians(25))
    return p


# ------------------------------------------------------------ accessories ---

def build_cap(name):
    p = group(name)
    bowl(f"{name}.dome", (0.34, 0.37, 0.28), (0, 0, 0.02), "cap", thickness=0.02, rot=(PI, 0, 0), parent=p)
    brim = cylinder(f"{name}.brim", 0.3, 0.02, (0, -0.4, 0.04), "cap", rot=(math.radians(-8), 0, 0), bevel=0.006,
                    parent=p)
    brim.scale = (1.0, 0.75, 1.0)
    sphere(f"{name}.button", 0.03, (0, 0, 0.3), "cap", parent=p)
    box(f"{name}.logo", (0.12, 0.01, 0.08), (0, -0.33, 0.16), "paper", rot=(math.radians(25), 0, 0), bevel=0.0,
        parent=p)
    p.rotation_euler = (0, 0, math.radians(-30))
    return p


def build_bandana(name):
    p = group(name)
    torus(f"{name}.roll", 0.33, 0.07, (0, 0, 0.055), "cloth_red", scale=(1, 0.8, 0.7), parent=p)
    sphere(f"{name}.knot", 0.08, (0, -0.27, 0.07), "cloth_red", scale=(1.2, 1, 0.8), parent=p)
    for side in (-1, 1):
        box(f"{name}.tail_{side}", (0.07, 0.3, 0.02), (0.08 * side, -0.42, 0.02), "cloth_red",
            rot=(0, 0, math.radians(20 * side)), bevel=0.01, parent=p)
    for i in range(10):
        a = i / 10 * 2 * PI
        sphere(f"{name}.dot_{i}", 0.014, (0.33 * math.cos(a), 0.264 * math.sin(a), 0.1), "paper",
               scale=(1, 1, 0.4), parent=p)
    return p


def build_necklace(name):
    p = group(name)
    torus(f"{name}.chain", 0.4, 0.014, (0, 0.1, 0.014), "gold", scale=(1, 1.25, 1), parent=p)
    torus(f"{name}.bail", 0.03, 0.008, (0, -0.42, 0.02), "gold", rot=(R90, 0, 0), parent=p)
    box(f"{name}.cross_v", (0.06, 0.22, 0.025), (0, -0.56, 0.015), "gold", bevel=0.006, parent=p)
    box(f"{name}.cross_h", (0.15, 0.06, 0.025), (0, -0.52, 0.015), "gold", bevel=0.006, parent=p)
    return p


def build_watch(name):
    p = group(name)
    for side in (-1, 1):
        box(f"{name}.strap_{side}", (0.24, 0.42, 0.03), (0, 0.36 * side, 0.03), "leather",
            rot=(math.radians(-8 * side), 0, 0), bevel=0.01, parent=p)
    cylinder(f"{name}.case", 0.22, 0.08, (0, 0, 0.08), "gold", bevel=0.01, parent=p)
    cylinder(f"{name}.face", 0.19, 0.01, (0, 0, 0.122), "paper", bevel=0.0, parent=p)
    box(f"{name}.hand_h", (0.018, 0.1, 0.006), (0.025, 0.035, 0.13), "pip", rot=(0, 0, math.radians(-40)),
        bevel=0.0, parent=p)
    box(f"{name}.hand_m", (0.012, 0.15, 0.006), (-0.03, 0.06, 0.134), "pip", rot=(0, 0, math.radians(25)),
        bevel=0.0, parent=p)
    cylinder(f"{name}.crown", 0.025, 0.05, (0.24, 0, 0.08), "gold", rot=(0, R90, 0), bevel=0.0, parent=p)
    p.rotation_euler = (0, 0, math.radians(-35))
    return p


def _boot(name, p, x, rot_z):
    b = group(f"{name}.boot", (x, 0, 0), (0, 0, rot_z))
    b.parent = p
    box(f"{name}.sole", (0.25, 0.52, 0.06), (0, -0.02, 0.03), "shoe", bevel=0.02, parent=b)
    box(f"{name}.foot", (0.23, 0.44, 0.16), (0, -0.04, 0.13), "leather", bevel=0.06, parent=b)
    cylinder(f"{name}.shaft", 0.125, 0.36, (0, 0.13, 0.34), "leather", bevel=0.02, parent=b)
    torus(f"{name}.collar", 0.125, 0.02, (0, 0.13, 0.52), "leather", parent=b)
    for i in range(4):
        box(f"{name}.lace_{i}", (0.15, 0.015, 0.012), (0, -0.05 + i * 0.07, 0.215 + i * 0.05), "paper",
            rot=(math.radians(-35), 0, 0), bevel=0.0, parent=b)


def build_boots(name):
    p = group(name)
    _boot(f"{name}.l", p, -0.2, math.radians(8))
    _boot(f"{name}.r", p, 0.2, math.radians(-12))
    return p


def build_ring(name):
    p = group(name)
    torus(f"{name}.band", 0.2, 0.045, (0, 0, 0.245), "gold", rot=(R90, 0, 0), parent=p)
    box(f"{name}.setting", (0.12, 0.1, 0.06), (0, 0, 0.47), "gold", bevel=0.02, parent=p)
    sphere(f"{name}.gem", 0.07, (0, 0, 0.53), "seal", scale=(1, 1, 0.8), parent=p)
    p.rotation_euler = (0, 0, math.radians(-30))
    return p


# ------------------------------------------------------------- rare items ---

def build_gold_tooth(name):
    p = group(name)
    sphere(f"{name}.crown", 0.2, (0, 0, 0.42), "gold", scale=(1, 0.85, 0.85), parent=p)
    for x in (-0.08, 0.08):
        cone(f"{name}.root_{x}", 0.09, 0.03, 0.3, (x, 0, 0.17), "porcelain", rot=(PI, 0, 0), parent=p)
    return p


def build_handle(name):
    p = group(name)
    cylinder(f"{name}.wood", 0.07, 0.7, (-0.05, 0, 0.07), "wood", rot=(0, R90, 0), bevel=0.02, parent=p)
    cylinder(f"{name}.ferrule", 0.082, 0.14, (0.35, 0, 0.082), "tin", rot=(0, R90, 0), bevel=0.01, parent=p)
    cylinder(f"{name}.socket", 0.03, 0.08, (0.45, 0, 0.082), "pip", rot=(0, R90, 0), bevel=0.0, parent=p)
    torus(f"{name}.hang", 0.04, 0.012, (-0.43, 0, 0.07), "tin", rot=(0, R90, 0), parent=p)
    p.rotation_euler = (0, 0, math.radians(25))
    return p


def build_wire(name):
    p = group(name)
    rnd = random.Random(3)
    for i in range(7):
        torus(f"{name}.loop_{i}", 0.3 + rnd.uniform(-0.02, 0.02), 0.011,
              (rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), 0.012 + i * 0.022), "steel",
              rot=(rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), 0), parent=p)
    cylinder(f"{name}.end", 0.011, 0.5, (0.42, -0.28, 0.02), "steel", rot=(0, R90, math.radians(-40)),
             bevel=0.0, parent=p)
    return p


def build_phone(name):
    p = group(name)
    box(f"{name}.body", (0.36, 0.75, 0.08), (0, 0, 0.04), "phone", bevel=0.03, parent=p)
    box(f"{name}.screen", (0.27, 0.28, 0.006), (0, 0.17, 0.082), "phone_screen", bevel=0.0, parent=p)
    for r in range(4):
        for c in range(3):
            box(f"{name}.key_{r}_{c}", (0.06, 0.04, 0.012), (-0.08 + c * 0.08, -0.06 - r * 0.065, 0.085), "tin",
                bevel=0.004, parent=p)
    cylinder(f"{name}.antenna", 0.018, 0.14, (0.12, 0.43, 0.06), "phone", rot=(-R90, 0, 0), bevel=0.005, parent=p)
    box(f"{name}.tape", (0.4, 0.1, 0.09), (0, -0.33, 0.04), "tape", bevel=0.01, parent=p)
    p.rotation_euler = (0, 0, math.radians(-25))
    return p


def build_fake_id(name):
    p = group(name)
    box(f"{name}.card", (0.86, 0.55, 0.012), (0, 0, 0.006), "id_card", bevel=0.004, parent=p)
    box(f"{name}.band", (0.86, 0.08, 0.004), (0, 0.235, 0.013), "seal", bevel=0.0, parent=p)
    box(f"{name}.photo", (0.22, 0.28, 0.004), (-0.25, 0.0, 0.014), "photo", bevel=0.0, parent=p)
    sphere(f"{name}.face", 0.05, (-0.25, 0.03, 0.016), "skin", scale=(1, 1.2, 0.1), parent=p)
    for i, w in enumerate((0.36, 0.3, 0.38, 0.2)):
        box(f"{name}.text_{i}", (w, 0.025, 0.004), (0.02 + w / 2, 0.11 - i * 0.07, 0.014), "pip", bevel=0.0, parent=p)
    torus(f"{name}.stamp", 0.09, 0.008, (0.27, -0.15, 0.014), "seal", scale=(1, 1, 0.3), parent=p)
    p.rotation_euler = (0, 0, math.radians(15))
    return p


def build_shiv(name):
    p = group(name)
    box(f"{name}.handle", (0.07, 0.75, 0.035), (0, 0, 0.03), "plastic_blue", bevel=0.012, parent=p)
    cone(f"{name}.point", 0.04, 0.0, 0.26, (0, -0.5, 0.03), "plastic_blue", rot=(R90, 0, 0), verts=6, parent=p)
    box(f"{name}.head", (0.08, 0.18, 0.03), (0, 0.46, 0.03), "plastic_blue", bevel=0.01, parent=p)
    for r in range(5):
        for c in range(2):
            cylinder(f"{name}.bristle_{r}_{c}", 0.012, 0.08, (-0.018 + c * 0.036, 0.39 + r * 0.035, 0.085),
                     "paper", verts=8, bevel=0.0, parent=p)
    cylinder(f"{name}.grip", 0.05, 0.22, (0, -0.14, 0.03), "tape", rot=(R90, 0, 0), bevel=0.006, parent=p)
    p.rotation_euler = (0, 0, math.radians(-35))
    return p


# ------------------------------------------------------------------ tools ---

def build_pickaxe(name):
    p = group(name)
    cylinder(f"{name}.handle", 0.045, 1.2, (0, -0.1, 0.06), "wood", rot=(R90, 0, 0), bevel=0.01, parent=p)
    box(f"{name}.hub", (0.15, 0.15, 0.13), (0, 0.5, 0.075), "steel", bevel=0.02, parent=p)
    for side in (-1, 1):
        cone(f"{name}.pick_{side}", 0.06, 0.008, 0.45, (0.29 * side, 0.5, 0.075), "steel",
             rot=(0, R90 * side, 0), parent=p)
    for i, y in enumerate((0.38, 0.42)):
        cylinder(f"{name}.tape_{i}", 0.06, 0.035, (0, y, 0.06), "tape", rot=(R90, 0, 0), bevel=0.004, parent=p)
    p.rotation_euler = (0, 0, math.radians(-30))
    return p


def build_shovel(name):
    p = group(name)
    bowl(f"{name}.blade", (0.3, 0.4, 0.06), (0, 0.5, 0.06), "tin", thickness=0.02, parent=p)
    cylinder(f"{name}.stick", 0.04, 1.1, (0, -0.35, 0.07), "wood", rot=(R90, 0, 0), bevel=0.01, parent=p)
    cylinder(f"{name}.tape", 0.058, 0.25, (0, 0.18, 0.07), "tape", rot=(R90, 0, 0), bevel=0.006, parent=p)
    for x in (-0.1, 0.1):
        cylinder(f"{name}.nail_{x}", 0.008, 0.04, (x, 0.32, 0.09), "steel", verts=8, bevel=0.0, parent=p)
    p.rotation_euler = (0, 0, math.radians(-30))
    return p


def build_spoon_card(name):
    p = build_spoon(name)
    p.rotation_euler = (0, 0, math.radians(-10))
    p.location = (0.05, 0.25, 0)
    return p


# ---------------------------------------------------------- action motifs ---

def build_time_clock(name):
    p = group(name)
    box(f"{name}.body", (0.6, 0.35, 0.8), (0, 0, 0.4), "clock", bevel=0.03, parent=p)
    cylinder(f"{name}.face", 0.2, 0.02, (0, -0.18, 0.52), "paper", rot=(R90, 0, 0), bevel=0.004, parent=p)
    torus(f"{name}.bezel", 0.2, 0.015, (0, -0.19, 0.52), "steel", rot=(R90, 0, 0), parent=p)
    box(f"{name}.hand_h", (0.02, 0.012, 0.11), (0.02, -0.195, 0.56), "pip", rot=(0, math.radians(30), 0),
        bevel=0.0, parent=p)
    box(f"{name}.hand_m", (0.015, 0.012, 0.16), (-0.03, -0.198, 0.58), "pip", rot=(0, math.radians(-25), 0),
        bevel=0.0, parent=p)
    box(f"{name}.slot", (0.3, 0.06, 0.01), (0, 0, 0.805), "pip", bevel=0.0, parent=p)
    box(f"{name}.card", (0.22, 0.012, 0.3), (0.0, 0, 0.92), "paper", rot=(0, 0, 0.1), bevel=0.0, parent=p)
    box(f"{name}.card_line", (0.16, 0.014, 0.012), (0.0, 0, 0.98), "seal", rot=(0, 0, 0.1), bevel=0.0, parent=p)
    p.rotation_euler = (0, 0, math.radians(-20))
    return p


def build_vent(name):
    p = group(name)
    box(f"{name}.hole", (0.7, 0.7, 0.02), (0, 0, 0.01), "tunnel", bevel=0.0, parent=p)
    grate = group(f"{name}.grate", (0, 0.36, 0.02), (math.radians(-60), 0, 0))
    grate.parent = p
    for i, (sx, sy, x, y) in enumerate([(0.8, 0.06, 0, -0.03), (0.8, 0.06, 0, -0.77), (0.06, 0.8, -0.37, -0.4),
                                        (0.06, 0.8, 0.37, -0.4)]):
        box(f"{name}.frame_{i}", (sx, sy, 0.04), (x, y, 0.02), "metal", bevel=0.008, parent=grate)
    for i in range(6):
        box(f"{name}.slat_{i}", (0.68, 0.06, 0.012), (0, -0.12 - i * 0.11, 0.02), "metal",
            rot=(math.radians(35), 0, 0), bevel=0.003, parent=grate)
    for i, (x, y) in enumerate([(-0.38, -0.38), (0.4, -0.45), (0.5, 0.2)]):
        cylinder(f"{name}.screw_{i}", 0.02, 0.05, (x, y, 0.01), "steel", rot=(R90, 0, i), verts=8, bevel=0.0, parent=p)
    return p


def build_package(name):
    p = group(name)
    box(f"{name}.box", (0.7, 0.5, 0.4), (0, 0, 0.2), "cardboard", bevel=0.01, parent=p)
    box(f"{name}.inside", (0.66, 0.46, 0.01), (0, 0, 0.4), "pip", bevel=0.0, parent=p)
    for i, (size, loc, rot) in enumerate([((0.7, 0.25, 0.01), (0, -0.36, 0.45), (math.radians(-40), 0, 0)),
                                          ((0.7, 0.25, 0.01), (0, 0.36, 0.45), (math.radians(40), 0, 0)),
                                          ((0.25, 0.5, 0.01), (-0.46, 0, 0.45), (0, math.radians(40), 0)),
                                          ((0.25, 0.5, 0.01), (0.46, 0, 0.45), (0, math.radians(-40), 0))]):
        box(f"{name}.flap_{i}", size, loc, "cardboard", rot=rot, bevel=0.003, parent=p)
    box(f"{name}.tape", (0.12, 0.26, 0.012), (0, -0.36, 0.455), "tape", rot=(math.radians(-40), 0, 0), bevel=0.0,
        parent=p)
    box(f"{name}.pack", (0.16, 0.08, 0.24), (0.15, 0.05, 0.47), "pack", rot=(0.2, -0.2, 0.3), bevel=0.01, parent=p)
    box(f"{name}.choc", (0.28, 0.1, 0.03), (-0.13, -0.05, 0.45), "chocolate", rot=(0.4, 0.3, -0.2), bevel=0.005,
        parent=p)
    p.rotation_euler = (0, 0, math.radians(-20))
    return p


def build_flashlight(name):
    p = group(name)
    cylinder(f"{name}.body", 0.07, 0.5, (-0.25, 0, 0.11), "phone", rot=(0, R90, 0), bevel=0.01, parent=p)
    cone(f"{name}.head", 0.07, 0.11, 0.12, (0.06, 0, 0.11), "phone", rot=(0, R90, 0), bevel=0.005, parent=p)
    cylinder(f"{name}.lens", 0.1, 0.01, (0.125, 0, 0.11), "floodlight", rot=(0, R90, 0), bevel=0.0, parent=p)
    cone(f"{name}.beam", 0.1, 0.55, 1.1, (0.68, 0, 0.18), "beam", rot=(0, R90 - 0.12, 0), verts=32, parent=p)
    p.rotation_euler = (0, 0, math.radians(25))
    p.location = (-0.25, -0.15, 0)
    return p


def build_bribe(name):
    p = group(name)
    box(f"{name}.envelope", (0.7, 0.45, 0.03), (0, 0, 0.015), "envelope", bevel=0.006, parent=p)
    cone(f"{name}.flap", 0.42, 0.0, 0.01, (0, 0.08, 0.035), "envelope", rot=(0, 0, math.radians(-90)), verts=3,
         parent=p).scale = (0.6, 1.0, 1.0)
    for i, x in enumerate((-0.18, -0.06, 0.06, 0.18)):
        y = 0.25 + (i % 2) * 0.05
        cylinder(f"{name}.cig_{i}", 0.028, 0.32, (x, y, 0.04), "cigarette", rot=(R90, 0, 0), verts=12, bevel=0.0,
                 parent=p)
        cylinder(f"{name}.filter_{i}", 0.029, 0.08, (x, y + 0.2, 0.04), "filter", rot=(R90, 0, 0), verts=12,
                 bevel=0.0, parent=p)
    p.rotation_euler = (0, 0, math.radians(-15))
    return p


def build_spilled_tray(name):
    p = group(name)
    rnd = random.Random(4)
    box(f"{name}.tray", (0.6, 0.42, 0.025), (0.1, 0.05, 0.12), "tray", rot=(0, math.radians(22), 0.2), bevel=0.006,
        parent=p)
    sphere(f"{name}.mash", 0.12, (-0.25, -0.1, 0.03), "food", scale=(1.3, 1, 0.35), parent=p)
    for i in range(14):
        sphere(f"{name}.pea_{i}", 0.025, (rnd.uniform(-0.5, 0.3), rnd.uniform(-0.45, 0.2), 0.025), "food_green",
               parent=p)
    cylinder(f"{name}.cup", 0.06, 0.15, (0.35, -0.3, 0.06), "steel", rot=(R90, 0, 0.7), bevel=0.006, parent=p)
    return p


def build_first_aid(name):
    p = group(name)
    box(f"{name}.case", (0.7, 0.45, 0.3), (0, 0, 0.15), "cabinet", bevel=0.03, parent=p)
    box(f"{name}.cross_v", (0.08, 0.26, 0.01), (0, 0, 0.305), "cross", bevel=0.0, parent=p)
    box(f"{name}.cross_h", (0.26, 0.08, 0.01), (0, 0, 0.305), "cross", bevel=0.0, parent=p)
    torus(f"{name}.handle", 0.08, 0.018, (0, -0.24, 0.22), "metal", rot=(0, 0, 0), scale=(1, 0.5, 1), parent=p)
    for x in (-0.25, 0.25):
        box(f"{name}.latch_{x}", (0.06, 0.02, 0.06), (x, -0.23, 0.2), "steel", bevel=0.005, parent=p)
    p.rotation_euler = (0, 0, math.radians(-20))
    return p


def build_snitch(name):
    p = group(name)
    box(f"{name}.door", (1.1, 0.1, 1.0), (0, 0.1, 0.5), "metal", bevel=0.02, parent=p)
    box(f"{name}.slot", (0.5, 0.11, 0.14), (0, 0.1, 0.65), "pip", bevel=0.0, parent=p)
    box(f"{name}.cover", (0.52, 0.02, 0.16), (0.42, 0.04, 0.65), "steel", bevel=0.005, parent=p)
    for x in (-0.1, 0.1):
        sphere(f"{name}.eye_{x}", 0.05, (x, 0.08, 0.65), "porcelain", parent=p)
        sphere(f"{name}.iris_{x}", 0.024, (x + 0.01, 0.034, 0.645), "pip", parent=p)
    for i in range(8):
        sphere(f"{name}.rivet_{i}", 0.018, (-0.5 + (i % 4) * 0.33, 0.045, 0.1 + (i // 4) * 0.8), "steel", parent=p)
    return p


def build_cave_in(name):
    p = group(name)
    earth = box(f"{name}.earth", (1.3, 0.8, 0.75), (0, 0.15, 0.375), "earth", bevel=0.0, parent=p)
    cut = cylinder(f"{name}.cut", 0.32, 1.2, (0, 0.0, 0.25), "tunnel", rot=(R90, 0, 0), bevel=0.0)
    boolean_cut(earth, cut, "tunnel")
    for x in (-0.3, 0.3):
        box(f"{name}.post_{x}", (0.07, 0.07, 0.5), (x, -0.23, 0.25), "wood", bevel=0.01, parent=p)
    box(f"{name}.beam_a", (0.4, 0.08, 0.07), (-0.15, -0.23, 0.48), "wood", rot=(0, math.radians(-12), 0), bevel=0.01,
        parent=p)
    box(f"{name}.beam_b", (0.38, 0.08, 0.07), (0.2, -0.27, 0.3), "wood", rot=(0, math.radians(40), 0.2), bevel=0.01,
        parent=p)
    rnd = random.Random(7)
    for i in range(14):
        rock(f"{name}.rock_{i}", rnd.uniform(0.04, 0.1), (rnd.uniform(-0.35, 0.35), rnd.uniform(-0.45, 0.0),
                                                        rnd.uniform(0.03, 0.15)),
             "earth_dark" if i % 2 else "stone", parent=p)
    return p


# ----------------------------------------------------------------- tokens ---

def build_cig1(name):
    p = group(name)
    cylinder(f"{name}.paper", 0.06, 0.65, (0.08, 0, 0.06), "cigarette", rot=(0, R90, 0), bevel=0.004, parent=p)
    cylinder(f"{name}.filter", 0.061, 0.22, (-0.36, 0, 0.06), "filter", rot=(0, R90, 0), bevel=0.004, parent=p)
    cylinder(f"{name}.ember", 0.058, 0.04, (0.42, 0, 0.06), "ember", rot=(0, R90, 0), bevel=0.004, parent=p)
    p.rotation_euler = (0, 0, math.radians(25))
    return p


def build_cig5(name):
    p = group(name)
    box(f"{name}.pack", (0.5, 0.25, 0.7), (0, 0, 0.35), "pack", bevel=0.02, parent=p)
    box(f"{name}.band", (0.51, 0.26, 0.16), (0, 0, 0.48), "paper", bevel=0.01, parent=p)
    for i, x in enumerate((-0.12, 0.0, 0.12)):
        h = 0.78 + i % 2 * 0.06
        cylinder(f"{name}.cig_{i}", 0.04, 0.2, (x, 0, h), "cigarette", verts=12, bevel=0.0, parent=p)
        cylinder(f"{name}.filter_{i}", 0.041, 0.07, (x, 0, h + 0.13), "filter", verts=12, bevel=0.0, parent=p)
    p.rotation_euler = (0, 0, math.radians(-25))
    return p


def _plaster_cross(name, p, loc, rot_z):
    c = group(f"{name}.cross", loc, (0, 0, rot_z))
    c.parent = p
    for ang in (40, -40):
        box(f"{name}.strip_{ang}", (0.6, 0.16, 0.02), (0, 0, 0.01 + (ang > 0) * 0.012), "plaster",
            rot=(0, 0, math.radians(ang)), bevel=0.01, parent=c)
    box(f"{name}.pad", (0.16, 0.12, 0.03), (0, 0, 0.03), "bandage", bevel=0.008, parent=c)


def build_beating1(name):
    p = group(name)
    _plaster_cross(name, p, (0, 0, 0), 0.2)
    return p


def build_beating2(name):
    p = group(name)
    _plaster_cross(f"{name}.a", p, (-0.22, 0.1, 0), 0.2)
    _plaster_cross(f"{name}.b", p, (0.25, -0.12, 0.03), -0.5)
    return p


def build_warning(name):
    p = group(name)
    box(f"{name}.card", (0.5, 0.7, 0.012), (0, 0, 0.006), "red_card", bevel=0.004, parent=p)
    box(f"{name}.bang", (0.07, 0.3, 0.004), (0, 0.08, 0.014), "paper", bevel=0.0, parent=p)
    cylinder(f"{name}.dot", 0.04, 0.004, (0, -0.17, 0.014), "paper", bevel=0.0, parent=p)
    p.rotation_euler = (0, 0, math.radians(-20))
    return p


def build_favor(name):
    p = group(name)
    box(f"{name}.envelope", (0.6, 0.4, 0.03), (0, 0, 0.015), "envelope", bevel=0.006, parent=p)
    cone(f"{name}.flap", 0.36, 0.0, 0.01, (0, 0.07, 0.035), "envelope", rot=(0, 0, math.radians(-90)), verts=3,
         parent=p).scale = (0.6, 1.0, 1.0)
    cylinder(f"{name}.seal", 0.08, 0.03, (0, -0.02, 0.05), "seal", bevel=0.01, parent=p)
    p.rotation_euler = (0, 0, math.radians(15))
    return p


def build_bandage(name):
    p = group(name)
    cylinder(f"{name}.roll", 0.18, 0.25, (0, 0.2, 0.18), "bandage", rot=(0, R90, 0), bevel=0.01, parent=p)
    cylinder(f"{name}.core", 0.05, 0.26, (0, 0.2, 0.18), "pip", rot=(0, R90, 0), bevel=0.0, parent=p)
    box(f"{name}.strip", (0.24, 0.55, 0.01), (0, -0.25, 0.005), "bandage", bevel=0.002, parent=p)
    p.rotation_euler = (0, 0, math.radians(-30))
    return p


def build_glove(name):
    p = group(name)
    sphere(f"{name}.fist", 0.3, (0.05, 0, 0.3), "glove", scale=(1.1, 0.85, 0.85), parent=p)
    sphere(f"{name}.thumb", 0.12, (0.15, -0.22, 0.3), "glove", scale=(1.3, 0.8, 0.8), parent=p)
    cylinder(f"{name}.cuff", 0.2, 0.3, (-0.35, 0, 0.26), "glove", rot=(0, R90, 0), bevel=0.04, parent=p)
    cylinder(f"{name}.band", 0.205, 0.08, (-0.28, 0, 0.26), "paper", rot=(0, R90, 0), bevel=0.01, parent=p)
    p.rotation_euler = (0, 0, math.radians(-30))
    return p


def build_helmet(name):
    p = group(name)
    bowl(f"{name}.dome", (0.34, 0.4, 0.3), (0, 0, 0.04), "helmet", thickness=0.02, rot=(PI, 0, 0), parent=p)
    torus(f"{name}.brim", 0.38, 0.03, (0, 0, 0.04), "helmet", scale=(1, 1.12, 1), parent=p)
    cylinder(f"{name}.lamp", 0.08, 0.09, (0, -0.33, 0.22), "metal", rot=(math.radians(70), 0, 0), bevel=0.01, parent=p)
    cylinder(f"{name}.lens", 0.065, 0.01, (0, -0.375, 0.24), "floodlight", rot=(math.radians(70), 0, 0), bevel=0.0,
             parent=p)
    p.rotation_euler = (0, 0, math.radians(-25))
    return p


def build_trauma(name):
    p = group(name)
    for i, (x, y, z, r) in enumerate([(0, 0, 0.75, 0.25), (-0.25, 0.05, 0.7, 0.2), (0.25, 0.02, 0.7, 0.22),
                                      (-0.1, -0.08, 0.88, 0.2), (0.12, 0.05, 0.9, 0.18)]):
        sphere(f"{name}.puff_{i}", r, (x, y, z), "cloud", parent=p)
    for i, (x, z, ang) in enumerate([(0.02, 0.48, 25), (-0.04, 0.3, -30), (0.03, 0.12, 25)]):
        box(f"{name}.bolt_{i}", (0.05, 0.03, 0.22), (x, -0.05, z), "lightning", rot=(0, math.radians(ang), 0),
            bevel=0.0, parent=p)
    return p


# ------------------------------------------------------------------ dice ---

PIPS = {  # face normal -> pip offsets (u, v) in units of the face
    1: [(0, 0)],
    2: [(-1, -1), (1, 1)],
    3: [(-1, -1), (0, 0), (1, 1)],
    4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)],
    6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)],
}
# face value -> (normal axis, sign); opposite faces sum to 7.
FACES = {1: ("z", 1), 6: ("z", -1), 2: ("y", -1), 5: ("y", 1), 3: ("x", 1), 4: ("x", -1)}
# rotation that brings each face to the top (+z)
FACE_UP = {1: (0, 0, 0), 6: (PI, 0, 0), 2: (-R90, 0, 0), 5: (R90, 0, 0), 3: (0, -R90, 0), 4: (0, R90, 0)}


def build_die(name, faces=FACES):
    """Rounded bone die. faces: which faces get pips (the face renders only need the top one)."""
    p = group(name)
    h = 0.3
    box(f"{name}.cube", (2 * h, 2 * h, 2 * h), (0, 0, 0), "die", bevel=0.05, parent=p)
    step = 0.15
    for value, (axis, sign) in ((v, FACES[v]) for v in faces):
        for u, v in PIPS[value]:
            depth = sign * (h - 0.03)  # sunk in: only a shallow cap shows, nothing pokes past the edge
            if axis == "z":
                loc = (u * step, v * step, depth)
            elif axis == "y":
                loc = (u * step, depth, v * step)
            else:
                loc = (depth, u * step, v * step)
            sphere(f"{name}.pip_{value}_{u}_{v}", 0.048, loc, "pip", parent=p)
    return p


# ---------------------------------------------------------- tunnel stages ---

def build_tunnel_stage(name, stage, stages=5):
    """Soil cross-section, prison wall on the left; the tunnel grows to the right and breaks out."""
    p = group(name)
    earth = box(f"{name}.earth", (2.0, 0.4, 1.0), (0, 0, 0.5), "earth", bevel=0.0, parent=p)
    box(f"{name}.grass", (2.0, 0.42, 0.06), (0, 0, 1.03), "food_green", bevel=0.01, parent=p)
    box(f"{name}.wall", (0.12, 0.44, 0.35), (-0.94, 0, 1.23), "wall_upper", bevel=0.01, parent=p)
    rnd = random.Random(11)
    for i in range(10):
        rock(f"{name}.stone_{i}", rnd.uniform(0.03, 0.06), (rnd.uniform(-0.95, 0.95), -0.2, rnd.uniform(0.1, 0.9)),
             "stone", parent=p)
    if stage > 0:
        length = 1.75 * stage / stages
        cut = cylinder(f"{name}.cut", 0.13, length, (-1.0 + length / 2, -0.1, 0.45), "tunnel", rot=(0, R90, 0),
                       bevel=0.0)
        boolean_cut(earth, cut, "tunnel")
        shaft = cylinder(f"{name}.shaft", 0.13, 0.65, (-0.82, -0.1, 0.77), "tunnel", bevel=0.0)  # up into the cell
        boolean_cut(earth, shaft, "tunnel")
    if stage == stages:
        exit_cut = cylinder(f"{name}.exit", 0.13, 0.65, (0.75, -0.1, 0.77), "tunnel", bevel=0.0)
        boolean_cut(earth, exit_cut, "tunnel")
        sphere(f"{name}.moon", 0.07, (0.75, 0.0, 1.3), "floodlight", parent=p)
    return p


# ------------------------------------------------------------ gang emblems ---

def _patch(name, gang):
    """Embroidered round patch: coloured base with a thread border; symbol is added on top."""
    p = group(name)
    cylinder(f"{name}.base", 0.5, 0.06, (0, 0, 0.03), f"gang_{gang}", bevel=0.02, parent=p)
    torus(f"{name}.border", 0.48, 0.025, (0, 0, 0.06), "thread", parent=p)
    return p


def build_gang_crew(name):
    p = _patch(name, "crew")
    for sign in (-1, 1):
        box(f"{name}.handle_{sign}", (0.06, 0.62, 0.03), (0, 0, 0.09), "wood", rot=(0, 0, math.radians(40 * sign)),
            bevel=0.01, parent=p)
    sphere(f"{name}.spoon", 0.08, (0.2, 0.24, 0.1), "steel", scale=(0.8, 1.2, 0.4), rot=(0, 0, math.radians(-40)),
           parent=p)
    box(f"{name}.pick", (0.3, 0.06, 0.04), (-0.2, 0.24, 0.1), "steel", rot=(0, 0, math.radians(40)), bevel=0.01,
        parent=p)
    return p


def build_gang_cartel(name):
    p = _patch(name, "cartel")
    for i, (x, y) in enumerate([(-0.1, 0.0), (-0.1, 0.0), (-0.1, 0.0), (0.14, 0.08), (0.14, 0.08)]):
        z = 0.08 + (i if i < 3 else i - 3) * 0.045
        cylinder(f"{name}.coin_{i}", 0.13, 0.04, (x, y, z), "gold", bevel=0.008, parent=p)
    return p


def build_gang_bikers(name):
    p = _patch(name, "bikers")
    torus(f"{name}.tyre", 0.27, 0.045, (0, 0, 0.1), "tire", parent=p)
    torus(f"{name}.rim", 0.22, 0.015, (0, 0, 0.1), "steel", parent=p)
    for angle in (0, 45, 90, 135):
        box(f"{name}.spoke_{angle}", (0.44, 0.015, 0.015), (0, 0, 0.1), "steel",
            rot=(0, 0, math.radians(angle)), bevel=0.0, parent=p)
    cylinder(f"{name}.hub", 0.05, 0.05, (0, 0, 0.1), "steel", bevel=0.01, parent=p)
    return p


def build_gang_bratva(name):
    p = _patch(name, "bratva")
    for angle in (0, 45):
        box(f"{name}.star_{angle}", (0.42, 0.42, 0.04), (0, 0, 0.09), "gold", rot=(0, 0, math.radians(angle)),
            bevel=0.01, parent=p)
    sphere(f"{name}.center", 0.09, (0, 0, 0.12), "seal", scale=(1, 1, 0.5), parent=p)
    return p


def build_gang_triad(name):
    p = _patch(name, "triad")
    box(f"{name}.die", (0.34, 0.34, 0.34), (0, 0, 0.24), "die", rot=(0, 0, math.radians(20)), bevel=0.04, parent=p)
    for i, (u, v) in enumerate(PIPS[5]):
        a = math.radians(20)
        x, y = u * 0.09, v * 0.09
        sphere(f"{name}.pip_{i}", 0.03, (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), 0.405),
               "pip", parent=p)
    return p


def build_gang_shadow(name):
    p = _patch(name, "shadow")
    moon = cylinder(f"{name}.moon", 0.26, 0.05, (0, 0, 0.1), "paper", bevel=0.01, parent=p)
    cut = cylinder(f"{name}.moon_cut", 0.24, 0.2, (0.12, 0.08, 0.1), "paper", bevel=0.0)
    cut.parent = p
    boolean_cut(moon, cut)
    return p


ITEMS = {
    # id: (builder, ortho scale, camera target z)
    "item.container": (build_container, 1.5, 0.35),
    "item.pike": (build_pike, 1.7, 0.05),
    "item.chain": (build_chain, 1.9, 0.1),
    "weapon.blade": (build_blade, 1.1, 0.02),
    "weapon.knife": (build_knife, 1.5, 0.05),
    "acc.cap": (build_cap, 1.3, 0.15),
    "acc.bandana": (build_bandana, 1.2, 0.05),
    "acc.necklace": (build_necklace, 1.4, 0.0),
    "acc.watch": (build_watch, 1.3, 0.06),
    "acc.boots": (build_boots, 1.4, 0.2),
    "acc.ring": (build_ring, 1.0, 0.28),
    "rare.gold_tooth": (build_gold_tooth, 0.9, 0.3),
    "rare.handle": (build_handle, 1.3, 0.07),
    "rare.wire": (build_wire, 1.2, 0.08),
    "rare.phone": (build_phone, 1.2, 0.05),
    "rare.fake_id": (build_fake_id, 1.2, 0.0),
    "rare.shiv": (build_shiv, 1.3, 0.04),
    "tool.spoon": (build_spoon_card, 1.9, 0.08),
    "tool.pickaxe": (build_pickaxe, 1.8, 0.06),
    "tool.shovel": (build_shovel, 1.8, 0.06),
    "action.shift_change": (build_time_clock, 1.4, 0.5),
    "action.shortcut": (build_vent, 1.4, 0.15),
    "action.package": (build_package, 1.3, 0.3),
    "action.raid": (build_flashlight, 1.8, 0.12),
    "action.bribe": (build_bribe, 1.2, 0.03),
    "action.distraction": (build_spilled_tray, 1.3, 0.06),
    "action.first_aid": (build_first_aid, 1.2, 0.15),
    "action.snitch": (build_snitch, 1.5, 0.5),
    "action.cave_in": (build_cave_in, 1.6, 0.35),
    "token.cig1": (build_cig1, 1.2, 0.06),
    "token.cig5": (build_cig5, 1.2, 0.45),
    "token.beating1": (build_beating1, 0.9, 0.02),
    "token.beating2": (build_beating2, 1.2, 0.02),
    "token.warning": (build_warning, 1.0, 0.0),
    "token.favor": (build_favor, 0.9, 0.03),
    "token.bandage": (build_bandage, 1.1, 0.1),
    "token.combat": (build_glove, 1.1, 0.28),
    "token.digbonus": (build_helmet, 1.1, 0.18),
    "token.trauma": (build_trauma, 1.2, 0.55),
}
GANG_EMBLEMS = {
    "gang.crew": build_gang_crew,
    "gang.cartel": build_gang_cartel,
    "gang.bikers": build_gang_bikers,
    "gang.bratva": build_gang_bratva,
    "gang.triad": build_gang_triad,
    "gang.shadow": build_gang_shadow,
}
