"""Renders a place tile (everything except the cell block, see build_cellblock.py).

Usage (headless, from repo root):
    blender --factory-startup -b --python art/scripts/build_place.py -- --place cafeteria [--with-figure]

Outputs:
    art/blender/places/<place>.blend
    art/renders/place.<place>.png           (1024x1024, transparent)
    art/renders/place.<place>.preview.png   (with --with-figure) – scale check, not an asset
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from digout_art import camera_place, light_rig, new_scene, render, save_blend  # noqa: E402
from places import PLACES  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--place", required=True, choices=sorted(PLACES))
    parser.add_argument("--with-figure", action="store_true")
    args = parser.parse_args(argv)

    scene = new_scene()
    camera_place(scene)
    light_rig(scene, "place")
    PLACES[args.place]()

    if args.with_figure:
        from characters import CHARACTERS, build_character
        build_character(CHARACTERS["char.03"], location=(-0.4, -1.1, 0.025), rot_z=math.radians(35))
        render(scene, f"place.{args.place}.preview.png")
        return
    save_blend(os.path.join("places", f"{args.place}.blend"))
    render(scene, f"place.{args.place}.png")


main()
