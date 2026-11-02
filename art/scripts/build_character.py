"""Renders characters: board standee, portrait (avatar) and the game poses.

Usage (headless, from repo root; one Blender process per character):
    blender --factory-startup -b --python art/scripts/build_character.py -- --char char.01 [--poses dig fight]

Outputs per character (art/renders/):
    <id>.standee.png         768x1152, relaxed pose, contact shadow
    <id>.portrait.png        768x768
    <id>.pose.<pose>.png     1024x1024 (@2x of the 512 pose art) for dig | fight | beaten | victory
    art/blender/characters/<id>.blend
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import CHARACTERS, apply_pose, build_character  # noqa: E402
from digout_art import (camera_character, light_rig, new_scene, render,  # noqa: E402
                        save_blend, shadow_catcher)

# pose -> (camera target z, ortho scale)
POSE_FRAMING = {"dig": (0.55, 1.8), "fight": (0.95, 2.1), "beaten": (0.85, 2.0), "victory": (1.1, 2.6)}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--char", default="char.01", choices=sorted(CHARACTERS))
    parser.add_argument("--poses", nargs="*", default=list(POSE_FRAMING))
    args = parser.parse_args(argv)

    scene = new_scene(resolution=(768, 1152))
    light_rig(scene, "studio", target=(0, 0, 0.9))
    char = build_character(CHARACTERS[args.char])
    shadow_catcher()
    cid = char.spec.id

    camera_character(scene, target=(0, 0, 0.9), ortho_scale=2.0)
    save_blend(os.path.join("characters", f"{cid}.blend"))
    render(scene, f"{cid}.standee.png")

    scene.render.resolution_x, scene.render.resolution_y = 768, 768
    camera_character(scene, target=(0, 0, char.eye_z * char.spec.scale[2] - 0.03), ortho_scale=0.55)
    render(scene, f"{cid}.portrait.png")

    scene.render.resolution_x, scene.render.resolution_y = 1024, 1024
    for pose in args.poses:
        apply_pose(char, pose)
        target_z, ortho = POSE_FRAMING[pose]
        camera_character(scene, target=(0, 0, target_z), ortho_scale=ortho)
        render(scene, f"{cid}.pose.{pose}.png")


main()
