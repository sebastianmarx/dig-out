"""Renders card illustrations, tokens, dice faces, tunnel stages, logo and app icon.

Usage (headless, from repo root):
    blender --factory-startup -b --python art/scripts/build_items.py -- [--only ID [ID ...]]

IDs: everything in items.ITEMS plus dice, tunnel, logo, appicon. Outputs go to art/renders/:
    <id>.png (1024x1024, @2x of the 512 card art), dice.face<N>.png (512x512),
    tunnel.stage<N>.png (1024x512), brand.logo.png (1600x600), brand.appicon.png (1024x1024)
"""

import argparse
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from digout_art import (_ortho_camera, box, camera_object, finish, light_rig, new_scene,  # noqa: E402
                        render, rock, shadow_catcher, sphere)
from items import FACE_UP, GANG_EMBLEMS, ITEMS, build_die, build_shovel, build_tunnel_stage  # noqa: E402


def render_item(item_id):
    builder, ortho, target_z = ITEMS[item_id]
    scene = new_scene()
    light_rig(scene, "studio", target=(0, 0, target_z))
    builder(item_id)
    shadow_catcher()
    camera_object(scene, target=(0, 0, target_z), ortho_scale=ortho)
    render(scene, f"{item_id}.png")


def render_dice():
    for value, rotation in FACE_UP.items():
        scene = new_scene(resolution=(512, 512), samples=96)
        light_rig(scene, "studio", target=(0, 0, 0.3))
        die = build_die("dice", faces=[value])
        die.rotation_euler = rotation
        die.location = (0, 0, 0.3)
        _ortho_camera(scene, "top", 0, 0, (0, 0, 0.3), 0.72)
        render(scene, f"dice.face{value}.png")


def render_tunnel(stages=5):
    for stage in range(stages + 1):
        scene = new_scene(resolution=(1024, 512), samples=96)
        light_rig(scene, "studio", target=(0, 0, 0.6))
        build_tunnel_stage(f"tunnel.stage{stage}", stage, stages)
        _ortho_camera(scene, "front", 90, 0, (0, 0, 0.82), 2.3)
        render(scene, f"tunnel.stage{stage}.png")


def render_logo():
    scene = new_scene(resolution=(1600, 600))
    light_rig(scene, "studio", target=(0, 0, 0.4))
    bpy.ops.object.text_add(location=(0, 0, 0.42), rotation=(math.radians(90), 0, 0))
    text = bpy.context.active_object
    text.data.body = "DIG OUT"
    text.data.align_x = "CENTER"
    text.data.align_y = "CENTER"
    text.data.extrude = 0.14
    text.data.bevel_depth = 0.02
    text.data.size = 1.0
    bpy.ops.object.convert(target="MESH")
    finish(text, "logo_stone", 0.0)
    import random
    rnd = random.Random(9)
    box("logo_ground", (5.0, 0.9, 0.12), (-0.2, 0.1, -0.06), "earth", bevel=0.03)
    # Dug-out pile with the shovel stuck in it, loose rubble around the letters.
    sphere("logo_pile", 0.45, (2.45, 0.1, -0.12), "earth", scale=(1.3, 1.0, 0.6))
    for i in range(22):
        near_pile = i < 12
        x = rnd.uniform(1.8, 3.0) if near_pile else rnd.uniform(-2.5, 1.6)
        rock(f"logo_rubble_{i}", rnd.uniform(0.03, 0.08), (x, rnd.uniform(-0.3, 0.3), rnd.uniform(0.0, 0.12)),
             "earth_dark" if i % 3 else "stone")
    shovel = build_shovel("logo_shovel")
    shovel.rotation_euler = (math.radians(-90), math.radians(18), 0)  # blade down, leaning
    shovel.location = (2.5, 0.05, 0.62)
    shadow_catcher(size=12, z=-0.12)
    _ortho_camera(scene, "front", 80, 0, (0.25, 0, 0.45), 6.2)
    render(scene, "brand.logo.png")


def render_appicon():
    scene = new_scene(resolution=(1024, 1024))
    scene.render.film_transparent = False
    light_rig(scene, "studio", target=(0, 0, 0))
    box("plate", (2.4, 2.4, 0.1), (0, 0, -0.05), "icon_bg", bevel=0.0)
    from digout_art import cylinder
    for i in range(4):
        cylinder(f"bar_{i}", 0.07, 2.4, (-0.66 + i * 0.44, 0, 0.07), "bars", rot=(math.radians(90), 0, 0), bevel=0.0)
    for y in (-0.6, 0.6):
        box(f"rail_{y}", (2.4, 0.1, 0.1), (0, y, 0.16), "bars", bevel=0.01)
    shovel = build_shovel("icon_shovel")
    shovel.scale = (1.15, 1.15, 1.15)
    shovel.rotation_euler = (0, 0, math.radians(-45))
    shovel.location = (0.05, -0.05, 0.22)
    _ortho_camera(scene, "top", 0, 0, (0, 0, 0), 1.9)
    render(scene, "brand.appicon.png")


def render_gangs():
    """Gang patches, seen almost from above so the symbol reads at icon size."""
    for gang_id, builder in GANG_EMBLEMS.items():
        scene = new_scene(resolution=(512, 512), samples=96)
        light_rig(scene, "studio", target=(0, 0, 0.1))
        builder(gang_id)
        _ortho_camera(scene, "top", 20, 0, (0, 0, 0.12), 1.15)
        render(scene, f"{gang_id}.png")


SPECIAL = {"gangs": render_gangs, "dice": render_dice, "tunnel": render_tunnel, "logo": render_logo, "appicon": render_appicon}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args(argv)
    targets = args.only or [*ITEMS, *SPECIAL]
    for target in targets:
        if target in SPECIAL:
            SPECIAL[target]()
        else:
            render_item(target)


main()
