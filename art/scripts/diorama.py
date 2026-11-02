"""Shared building blocks for the isometric place tiles (4x4 units, back walls at x=-1.9 / y=1.9).

Convention: the front half (y < 0) stays mostly free – that is where the figures stand.
"""

import bpy

from digout_art import box, cylinder, point_light, rock

WALL_HEIGHT = 2.4


def ground(floor="concrete", floor_alt=None, tile=0.5, plank=False, earth=True):
    """Concrete slab + floor (floor_alt -> checkered tiles; plank -> boards).
    earth=True adds the soil cross-section below (single tile); the board has one shared soil block."""
    if earth:
        box("earth", (4, 4, 0.8), (0, 0, -0.5), "earth", bevel=0.0)
    box("slab", (4, 4, 0.1), (0, 0, -0.05), "concrete", bevel=0.0)
    if floor_alt and plank:
        width = 0.25
        for i in range(int(4 / width)):
            key = floor if i % 2 == 0 else floor_alt
            box(f"plank_{i}", (3.99, width - 0.012, 0.025), (0, -2 + width * (i + 0.5), 0.0125), key,
                bevel=0.003)
    elif floor_alt:
        gap = 0.025
        n = int(4 / tile)
        for ix in range(n):
            for iy in range(n):
                key = floor if (ix + iy) % 2 == 0 else floor_alt
                box(f"tile_{ix}_{iy}", (tile - gap, tile - gap, 0.025),
                    (-2 + tile * (ix + 0.5), -2 + tile * (iy + 0.5), 0.0125), key, bevel=0.004)
    else:
        box("floor", (3.99, 3.99, 0.02), (0, 0, 0.01), floor, bevel=0.003)

    if not earth:
        return
    for i, (x, z, r) in enumerate([(1.2, -0.3, 0.09), (1.6, -0.72, 0.07), (-1.4, -0.62, 0.08),
                                   (0.4, -0.78, 0.06), (-0.5, -0.35, 0.05)]):
        rock(f"stone_{i}", r, (x, -2.0, z), "stone")
    for i, (y, z, r) in enumerate([(-1.2, -0.4, 0.08), (0.3, -0.7, 0.06), (1.4, -0.35, 0.07)]):
        rock(f"stone_side_{i}", r, (2.0, y, z), "stone")


def wall(name, size, loc, lower="wall_lower", upper="wall_upper", lower_h=0.9):
    """Two-tone prison wall (lower paint, upper paint)."""
    sx, sy, sz = size
    box(f"{name}_lower", (sx, sy, lower_h), (loc[0], loc[1], lower_h / 2), lower)
    if sz > lower_h:
        box(f"{name}_upper", (sx, sy, sz - lower_h), (loc[0], loc[1], lower_h + (sz - lower_h) / 2), upper)


def back_walls(lower="wall_lower", upper="wall_upper", lower_h=0.9, height=WALL_HEIGHT):
    wall("wall_left", (0.2, 4.0, height), (-1.9, 0, 0), lower, upper, lower_h)
    wall("wall_back", (3.8, 0.2, height), (0.1, 1.9, 0), lower, upper, lower_h)


def wall_lamp(x, y=1.76, z=2.15, energy=45, on_left_wall=False):
    """Caged strip lamp on the back wall (or the left wall) with a warm point light."""
    if on_left_wall:
        box(f"lamp_{y}", (0.08, 0.3, 0.1), (-1.76, y, z), "lamp", bevel=0.0)
        box(f"lamp_cage_{y}", (0.1, 0.34, 0.03), (-1.75, y, z - 0.07), "bars", bevel=0.0)
        point_light(bpy.context.scene, f"lamp_light_{y}", (-1.62, y, z - 0.13), energy=energy)
    else:
        box(f"lamp_{x}", (0.3, 0.08, 0.1), (x, y, z), "lamp", bevel=0.0)
        box(f"lamp_cage_{x}", (0.34, 0.1, 0.03), (x, y - 0.01, z - 0.07), "bars", bevel=0.0)
        point_light(bpy.context.scene, f"lamp_light_{x}", (x, y - 0.14, z - 0.13), energy=energy)


def table(name, center, size=(1.6, 0.6), height=0.75, top_key="counter", leg_key="metal"):
    x, y = center
    sx, sy = size
    box(f"{name}_top", (sx, sy, 0.05), (x, y, height), top_key, bevel=0.01)
    for dx in (-sx / 2 + 0.08, sx / 2 - 0.08):
        for dy in (-sy / 2 + 0.08, sy / 2 - 0.08):
            cylinder(f"{name}_leg_{dx}_{dy}", 0.025, height, (x + dx, y + dy, height / 2), leg_key,
                     verts=12, bevel=0.0)


def bench(name, center, length=1.6, height=0.45, axis="x", key="counter"):
    x, y = center
    size = (length, 0.28, 0.05) if axis == "x" else (0.28, length, 0.05)
    box(f"{name}_seat", size, (x, y, height), key, bevel=0.01)
    for d in (-length / 2 + 0.1, length / 2 - 0.1):
        loc = (x + d, y, height / 2) if axis == "x" else (x, y + d, height / 2)
        box(f"{name}_leg_{d}", (0.05, 0.05, height), loc, "metal", bevel=0.0)
