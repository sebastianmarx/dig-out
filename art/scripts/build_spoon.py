"""Builds the improvised digging spoon (tool.spoon): bent steel spoon, handle extended
with a wooden stick and duct tape. The bowl is empty – it is the digging tool, not the result.

Usage (headless, from repo root):
    blender --factory-startup -b --python art/scripts/build_spoon.py

Outputs:
    art/blender/props/tool.spoon.blend
    art/renders/tool.spoon.png   (1024x1024, transparent, contact shadow) – @2x of the 512 card art
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from digout_art import (camera_object, light_rig, new_scene, render, save_blend,  # noqa: E402
                        shadow_catcher)
from props import build_spoon  # noqa: E402


def main():
    scene = new_scene(resolution=(1024, 1024))
    light_rig(scene, "studio", target=(0, 0, 0.1))
    spoon = build_spoon()
    # Diagonal in the object camera's view: bowl upper right, stick lower left.
    spoon.rotation_euler = (0, 0, math.radians(-10))
    spoon.location = (0.05, 0.25, 0)
    shadow_catcher()
    camera_object(scene, target=(0, 0, 0.08), ortho_scale=1.9)
    save_blend(os.path.join("props", "tool.spoon.blend"))
    render(scene, "tool.spoon.png")


main()
