"""Builds the isometric cell block diorama (place.cellblock) and renders it.

Usage (headless, from repo root):
    blender --factory-startup -b --python art/scripts/build_cellblock.py -- [--with-figure]

Outputs:
    art/blender/places/cellblock.blend
    art/renders/place.cellblock.png          (1024x1024, transparent) – the asset
    art/renders/place.cellblock.preview.png  (with --with-figure) – scale check, not an asset
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cellblock import build_cellblock  # noqa: E402
from digout_art import camera_place, light_rig, new_scene, render, save_blend  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WITH_FIGURE = "--with-figure" in ARGS


def main():
    scene = new_scene()
    camera_place(scene)
    light_rig(scene, "place")
    build_cellblock(standalone=True)

    if WITH_FIGURE:
        from characters import build_brute
        build_brute(location=(0.7, -1.0, 0.025), rot_z=math.radians(35))  # face the camera
        render(scene, "place.cellblock.preview.png")
        return
    save_blend(os.path.join("places", "cellblock.blend"))
    render(scene, "place.cellblock.png")


main()
