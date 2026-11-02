"""Renders the combined board: all six rooms on one soil block, connected by corridors, in dice order.

Back row (left -> right): rooms 1, 2, 3. Front row (right -> left): rooms 4, 5, 6 – so neighbours on
the die ring are neighbours on the board.

Usage (headless, from repo root):
    blender --factory-startup -b --python art/scripts/build_board.py -- [--preview]

Outputs:
    art/renders/board.png           (3200 px wide, transparent)
    art/renders/board.layout.json   room outlines, figure slots and scale in image coordinates (0..1)
    art/blender/board.blend
"""

import json
import math
import os
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from digout_art import RENDER_DIR, box, light_rig, new_scene, render, rock, save_blend  # noqa: E402
from places import PLACES  # noqa: E402

RING = ["cellblock", "cafeteria", "showers", "infirmary", "recreation", "yard"]
ROOM = 4.0          # room tile size
GAP = 1.4           # corridor width between rooms
STEP = ROOM + GAP
WIDTH = 3200
# Where figures stand inside a room (room-local, front half = free floor), drawn back to front.
SLOTS = [(-1.2, -0.35), (0.2, -0.45), (1.3, -0.3), (-0.6, -1.2), (0.7, -1.35), (-1.5, -1.55)]
ISO = Euler((math.radians(54.736), 0, math.radians(45)))


def room_offset(index: int) -> Vector:
    if index < 3:  # back row, left to right
        return Vector(((index - 1) * STEP, STEP / 2, 0))
    return Vector(((4 - index) * STEP, -STEP / 2, 0))  # front row, right to left


def build_room(place: str, offset: Vector) -> None:
    before = set(bpy.data.objects)
    PLACES[place](standalone=False)
    for obj in set(bpy.data.objects) - before:
        if obj.parent is None:
            obj.location += offset


def build_shared_ground(half_x: float, half_y: float) -> None:
    box("board_earth", (2 * half_x, 2 * half_y, 0.8), (0, 0, -0.5), "earth", bevel=0.0)
    box("board_slab", (2 * half_x, 2 * half_y, 0.1), (0, 0, -0.056), "concrete", bevel=0.0)
    # Yellow walking lines along the corridors (the paths between neighbouring rooms).
    box("line_mid", (3 * STEP, 0.06, 0.004), (0, 0, 0.0), "court_line", bevel=0.0)
    for x in (-1.5 * STEP, 1.5 * STEP):
        box(f"line_end_{x}", (0.06, STEP, 0.004), (x - math.copysign(0.0, x), 0, 0.0), "court_line", bevel=0.0)
    for i in range(14):
        x = -half_x + 0.4 + i * (2 * half_x - 0.8) / 13
        rock(f"board_stone_{i}", 0.06 + (i % 3) * 0.02, (x, -half_y, -0.3 - (i % 4) * 0.12), "stone")
    for i in range(8):
        y = -half_y + 0.4 + i * (2 * half_y - 0.8) / 7
        rock(f"board_stone_side_{i}", 0.06 + (i % 3) * 0.02, (half_x, y, -0.35 - (i % 3) * 0.13), "stone")


def setup_camera(scene, half_x: float, half_y: float):
    """Isometric camera fitted to the board's bounding box; returns the camera."""
    rot = ISO.to_matrix()
    inv = rot.transposed()
    corners = [Vector((sx * half_x, sy * half_y, z)) for sx in (-1, 1) for sy in (-1, 1) for z in (-0.9, 2.7)]
    local = [inv @ c for c in corners]
    xs, ys = [p.x for p in local], [p.y for p in local]
    x_range, y_range = max(xs) - min(xs), max(ys) - min(ys)
    center = rot @ Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, 0))
    margin = 1.03
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = round(WIDTH * y_range / x_range)
    data = bpy.data.cameras.new("cam_board")
    data.type = "ORTHO"
    data.ortho_scale = x_range * margin
    data.clip_end = 200
    cam = bpy.data.objects.new("cam_board", data)
    scene.collection.objects.link(cam)
    cam.rotation_euler = ISO
    cam.location = center + rot @ Vector((0, 0, 60))
    scene.camera = cam
    return cam


def to_image(scene, cam, point: Vector) -> list[float]:
    """World point -> normalized image coords, origin top-left."""
    p = world_to_camera_view(scene, cam, point)
    return [round(p.x, 5), round(1 - p.y, 5)]


def export_layout(scene, cam) -> None:
    rooms = {}
    for index, place in enumerate(RING):
        o = room_offset(index)
        h = ROOM / 2
        outline = [to_image(scene, cam, o + Vector(c)) for c in ((-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0))]
        rooms[place] = {
            "index": index + 1,
            "outline": outline,                                  # floor corners: front-left, front-right, back-right, back-left
            "label": to_image(scene, cam, o + Vector((h, -h, 0))),  # front corner (bottom tip of the diamond)
            "top": to_image(scene, cam, o + Vector((-h, h, 2.4))),  # top of the back corner
            "slots": [to_image(scene, cam, o + Vector((x, y, 0))) for x, y in SLOTS],
        }
    ground = to_image(scene, cam, Vector((0, 0, 0)))
    up = to_image(scene, cam, Vector((0, 0, 1)))
    layout = {
        "image": {"width": scene.render.resolution_x, "height": scene.render.resolution_y},
        "unit_height": round(ground[1] - up[1], 5),  # image-height fraction of 1 world unit upwards
        "rooms": rooms,
    }
    path = os.path.join(RENDER_DIR, "board.layout.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(layout, fh, indent=2)
    print(f"Wrote {path}")


def main() -> None:
    preview = "--preview" in sys.argv
    scene = new_scene(samples=48 if preview else 160)
    light_rig(scene, "place")
    half_x = 1.5 * ROOM + GAP + 0.6
    half_y = ROOM + GAP / 2 + 0.6
    build_shared_ground(half_x, half_y)
    for index, place in enumerate(RING):
        build_room(place, room_offset(index))
    cam = setup_camera(scene, half_x, half_y)
    bpy.context.view_layer.update()
    export_layout(scene, cam)
    if preview:
        scene.render.resolution_percentage = 40
        render(scene, "board.preview.png")
        return
    save_blend("board.blend")
    render(scene, "board.png")


main()
