"""Shared art library: palette, materials, primitives, cameras, light rigs, rendering.

Every build script imports this module so all assets share one look
(gritty soft 3D, night mood – see project.md, chapter 8.6.2).
"""

import math
import os

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RENDER_DIR = os.path.join(ROOT, "art", "renders")
BLEND_DIR = os.path.join(ROOT, "art", "blender")

# Palette (sRGB hex). CSS tokens are picked from the final renders (AgX shifts colors slightly).
PALETTE = {
    # Architecture
    "concrete": "#5e626a",
    "corridor": "#8a8f97",
    "corridor_alt": "#4f545d",
    "wall_upper": "#b3ab9b",
    "wall_lower": "#285552",
    "bars": "#16181e",
    "metal": "#565d69",
    "earth": "#6e4529",
    "earth_dark": "#40271a",
    "tunnel": "#0f0906",
    "stone": "#8c8478",
    # Furniture & props
    "mattress": "#c4baa4",
    "blanket": "#d4581f",
    "pillow": "#d9d2c2",
    "porcelain": "#dcdad4",
    "poster_bg": "#b8962c",
    "poster_fg": "#a52f47",
    "wood": "#7a5334",
    "book": "#2b5299",
    "lamp": "#ffcf8a",
    "tape": "#8b8f95",
    "steel": "#a7adb6",
    # Wear
    "grime": "#8a7f6b",
    "grime_dark": "#5e5444",
    "rust": "#7a4526",
    "scratch": "#2e261f",
    "spray": "#c0262d",
    # Characters
    "skin": "#c58b64",
    "jumpsuit": "#d4581f",
    "jumpsuit_dark": "#a8431a",
    "shoe": "#202228",
    "eye": "#0e0e10",
    "hair": "#2a211c",
    "tattoo": "#2c3b55",
    "patch": "#d9d2c2",
    "zipper": "#3a2a20",
    "scar": "#b5655a",
    "glasses": "#2a2a2e",
    "plaster": "#e2c9a6",
    # Places
    "wall_green": "#34503f",
    "wall_pale": "#9fb0a6",
    "cafe_floor": "#6b3a2c",
    "cafe_floor_alt": "#4a2820",
    "counter": "#6d747d",
    "tray": "#b0622a",
    "food": "#c8b46a",
    "food_green": "#6f8f3e",
    "chalkboard": "#1f2b24",
    "chalk": "#d6d6cc",
    "glass": "#dfe8ea",
    "tile_white": "#c3c8c2",
    "tile_floor": "#3e4d52",
    "puddle": "#4f6670",
    "soap": "#e3cf6e",
    "towel": "#cfc6b6",
    "lino": "#6c8a80",
    "sheet": "#dedbd2",
    "cross": "#b3262a",
    "curtain": "#6f9c96",
    "cabinet": "#cfd3cd",
    "pill": "#e9e3d6",
    "wood_floor": "#6a4a32",
    "wood_floor_alt": "#57392a",
    "sofa": "#563b58",
    "card": "#ece6d8",
    "cigarette": "#f1ede4",
    "ember": "#ff7a2a",
    "tv": "#18191d",
    "screen": "#8ab8ff",
    "vending": "#8e2a2a",
    "vending_light": "#ffd98a",
    "asphalt": "#3a3c40",
    "fence": "#8f969d",
    "fence_mesh": "#a3a9af",
    "court_line": "#cfcabb",
    "hoop": "#c4501e",
    "board": "#d6d6d2",
    "tire": "#1c1c1e",
    "floodlight": "#fff3d0",
    # Items, tokens, branding
    "tin": "#8d949b",
    "label": "#b59a62",
    "cloth_red": "#9b1f24",
    "cap": "#26304a",
    "gold": "#d4a640",
    "leather": "#4a2f20",
    "plastic_blue": "#2f7fc0",
    "phone": "#1c1d21",
    "phone_screen": "#6fd0ff",
    "id_card": "#e3dcc6",
    "photo": "#8d7a6a",
    "paper": "#e3d8bd",
    "cardboard": "#a77b4f",
    "chocolate": "#4a2a1a",
    "beam": "#fff2c0",
    "first_aid": "#c22a2a",
    "clock": "#38463c",
    "envelope": "#d6c6a0",
    "seal": "#9a1c1c",
    "glove": "#b11e24",
    "helmet": "#d9a52a",
    "cloud": "#565b69",
    "lightning": "#ffd84a",
    "pack": "#c7312b",
    "filter": "#d98b3a",
    "die": "#e6dcc6",
    "pip": "#1a1714",
    "red_card": "#c42a2a",
    "bandage": "#ece7dc",
    "icon_bg": "#1d3a3d",
    # Gang patches (also used as UI colours)
    "gang_crew": "#2b5c8a",
    "gang_cartel": "#2f6b3a",
    "gang_bikers": "#232328",
    "gang_bratva": "#8a1f24",
    "gang_triad": "#b07a1c",
    "gang_shadow": "#4a2f6b",
    "thread": "#e8d9b0",
    "logo_stone": "#9c9488",
}

# Material key -> (blotch strength, vertical streak strength) for procedural dirt.
GRIME = {
    "wall_upper": (0.75, 0.6),
    "wall_lower": (0.6, 0.35),
    "concrete": (0.5, 0.0),
    "corridor": (0.45, 0.0),
    "corridor_alt": (0.35, 0.0),
    "jumpsuit": (0.35, 0.0),
    "steel": (0.45, 0.0),
    "wood": (0.3, 0.0),
    "tile_white": (0.55, 0.45),
    "tile_floor": (0.4, 0.0),
    "cafe_floor": (0.45, 0.0),
    "cafe_floor_alt": (0.35, 0.0),
    "wall_green": (0.6, 0.35),
    "wall_pale": (0.55, 0.3),
    "lino": (0.5, 0.0),
    "wood_floor": (0.35, 0.0),
    "wood_floor_alt": (0.35, 0.0),
    "asphalt": (0.6, 0.0),
    "sofa": (0.3, 0.0),
    "counter": (0.4, 0.0),
    "tin": (0.4, 0.0),
    "cardboard": (0.35, 0.0),
    "leather": (0.3, 0.0),
    "die": (0.35, 0.0),
    "logo_stone": (0.6, 0.3),
}
METALLIC = {"bars": (0.55, 0.38), "metal": (0.55, 0.38), "steel": (0.8, 0.42), "glasses": (0.8, 0.3),
            "counter": (0.6, 0.45), "fence": (0.7, 0.4), "hoop": (0.5, 0.4),
            "tin": (0.75, 0.4), "gold": (1.0, 0.25), "seal": (0.0, 0.4)}
FABRIC = {"jumpsuit", "jumpsuit_dark"}
GLOSSY = {"porcelain", "poster_bg", "poster_fg", "book", "eye", "tray", "tile_white", "tile_floor",
          "cabinet", "tv", "board", "plastic_blue", "phone", "id_card", "first_aid", "glove", "helmet",
          "pack", "die", "red_card"}
EMISSIVE = {"lamp": 6.0, "screen": 4.0, "vending_light": 3.0, "floodlight": 10.0, "ember": 3.0,
            "phone_screen": 3.0, "lightning": 5.0, "beam": 1.5}
# Material key -> (grout colour, tiles per unit, plane): procedural tiles via a brick texture.
TILED = {"tile_white": ("#7d837f", 6.0, "wall"), "tile_floor": ("#1c2428", 8.0, "floor")}

WARM_LIGHT = "#ffb560"
MOONLIGHT = "#b9c8ff"
RIM_LIGHT = "#8fb0ff"
NIGHT_SKY = "#3a4a6e"


# ---------------------------------------------------------------- helpers ---

def srgb(hex_color):
    """Hex sRGB -> linear RGBA tuple for Blender."""
    h = hex_color.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def socket(sockets, identifier):
    return next(s for s in sockets if s.identifier == identifier)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


# -------------------------------------------------------------- materials ---

_MATS = {}


def material(key):
    if key in _MATS:
        return _MATS[key]
    hex_color = PALETTE[key]
    mat = bpy.data.materials.new(key)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = srgb(hex_color)
    bsdf.inputs["Roughness"].default_value = 0.65
    if key in METALLIC:
        metallic, roughness = METALLIC[key]
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    elif key in GLOSSY:
        bsdf.inputs["Roughness"].default_value = 0.3
    elif key == "skin":
        bsdf.inputs["Roughness"].default_value = 0.5
    if key in EMISSIVE:
        bsdf.inputs["Emission Color"].default_value = srgb(hex_color)
        bsdf.inputs["Emission Strength"].default_value = EMISSIVE[key]
    if key in GRIME:
        _add_grime(mat, bsdf, hex_color, *GRIME[key])
    if key in FABRIC:
        bsdf.inputs["Roughness"].default_value = 0.85
        _add_fabric_bump(mat, bsdf)
    if key in TILED:
        _add_tiles(mat, bsdf, *TILED[key])
    if key == "glass":
        bsdf.inputs["Transmission Weight"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.05
    if key == "puddle":
        bsdf.inputs["Roughness"].default_value = 0.12
    if key == "fence_mesh":
        _add_wire_mesh(mat, bsdf)
    if key == "beam":  # translucent light cone
        bsdf.inputs["Alpha"].default_value = 0.18
    _MATS[key] = mat
    return mat


def _add_grime(mat, bsdf, hex_color, blotch_strength, streak_strength):
    """Procedural dirt: soft blotches plus vertical water/rust streaks."""
    nt = mat.node_tree
    coords = nt.nodes.new("ShaderNodeTexCoord")

    def noise_mask(scale_xyz, noise_scale, detail, lo, hi):
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = scale_xyz
        nt.links.new(coords.outputs["Object"], mapping.inputs["Vector"])
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = noise_scale
        noise.inputs["Detail"].default_value = detail
        noise.inputs["Roughness"].default_value = 0.6
        nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = lo
        ramp.color_ramp.elements[1].position = hi
        nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        return ramp.outputs["Color"]

    def scaled(value_socket, factor):
        node = nt.nodes.new("ShaderNodeMath")
        node.operation = "MULTIPLY"
        node.inputs[1].default_value = factor
        nt.links.new(value_socket, node.inputs[0])
        return node.outputs["Value"]

    fac = scaled(noise_mask((1, 1, 1), 2.2, 6, 0.48, 0.7), blotch_strength)
    if streak_strength:
        streaks = scaled(noise_mask((7, 7, 0.4), 3.5, 3, 0.52, 0.72), streak_strength)
        combined = nt.nodes.new("ShaderNodeMath")
        combined.operation = "MAXIMUM"
        nt.links.new(fac, combined.inputs[0])
        nt.links.new(streaks, combined.inputs[1])
        fac = combined.outputs["Value"]

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    socket(mix.inputs, "A_Color").default_value = srgb(hex_color)
    socket(mix.inputs, "B_Color").default_value = srgb("#6e5f48")  # brownish dirt
    nt.links.new(fac, mix.inputs["Factor"])
    nt.links.new(socket(mix.outputs, "Result_Color"), bsdf.inputs["Base Color"])


def _plane_coords(nt, plane, scale):
    """Object coords flattened for walls (x+y, z) or floors (x, y), scaled to tiles per unit."""
    coords = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coords.outputs["Object"], sep.inputs["Vector"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    if plane == "wall":
        add = nt.nodes.new("ShaderNodeMath")
        nt.links.new(sep.outputs["X"], add.inputs[0])
        nt.links.new(sep.outputs["Y"], add.inputs[1])
        nt.links.new(add.outputs["Value"], comb.inputs["X"])
        nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
    else:
        nt.links.new(sep.outputs["X"], comb.inputs["X"])
        nt.links.new(sep.outputs["Y"], comb.inputs["Y"])
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(comb.outputs["Vector"], mapping.inputs["Vector"])
    return mapping.outputs["Vector"]


def _add_tiles(mat, bsdf, grout_hex, scale, plane):
    """Square tiles with darker grout, multiplied over the (grimy) base colour."""
    nt = mat.node_tree
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.0
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 1.0
    brick.inputs["Row Height"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.04
    brick.inputs["Color1"].default_value = (1, 1, 1, 1)
    brick.inputs["Color2"].default_value = (0.92, 0.92, 0.92, 1)
    brick.inputs["Mortar"].default_value = srgb(grout_hex)
    nt.links.new(_plane_coords(nt, plane, scale), brick.inputs["Vector"])
    base_link = bsdf.inputs["Base Color"].links
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    if base_link:
        nt.links.new(base_link[0].from_socket, socket(mix.inputs, "A_Color"))
    else:
        socket(mix.inputs, "A_Color").default_value = bsdf.inputs["Base Color"].default_value
    nt.links.new(brick.outputs["Color"], socket(mix.inputs, "B_Color"))
    nt.links.new(socket(mix.outputs, "Result_Color"), bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.invert = True  # grout lies deeper than the tiles
    bump.inputs["Strength"].default_value = 0.3
    nt.links.new(brick.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def _add_wire_mesh(mat, bsdf):
    """Chain-link fence: the mortar of a rotated brick texture is the wire, the bricks are holes."""
    nt = mat.node_tree
    coords = _plane_coords(nt, "wall", 1.0)
    rotate = nt.nodes.new("ShaderNodeVectorRotate")
    rotate.rotation_type = "Z_AXIS"
    rotate.inputs["Angle"].default_value = math.radians(45)
    nt.links.new(coords, rotate.inputs["Vector"])
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.0
    brick.inputs["Scale"].default_value = 14.0
    brick.inputs["Brick Width"].default_value = 1.0
    brick.inputs["Row Height"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.06
    nt.links.new(rotate.outputs["Vector"], brick.inputs["Vector"])
    nt.links.new(brick.outputs["Fac"], bsdf.inputs["Alpha"])
    bsdf.inputs["Metallic"].default_value = 0.7
    bsdf.inputs["Roughness"].default_value = 0.4


def _add_fabric_bump(mat, bsdf):
    """Soft, mostly vertical folds plus fine weave."""
    nt = mat.node_tree
    coords = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 0.35)
    nt.links.new(coords.outputs["Object"], mapping.inputs["Vector"])
    folds = nt.nodes.new("ShaderNodeTexNoise")
    folds.inputs["Scale"].default_value = 14
    folds.inputs["Detail"].default_value = 2
    nt.links.new(mapping.outputs["Vector"], folds.inputs["Vector"])
    weave = nt.nodes.new("ShaderNodeTexNoise")
    weave.inputs["Scale"].default_value = 400
    bump_folds = nt.nodes.new("ShaderNodeBump")
    bump_folds.inputs["Strength"].default_value = 0.35
    nt.links.new(folds.outputs["Fac"], bump_folds.inputs["Height"])
    bump_weave = nt.nodes.new("ShaderNodeBump")
    bump_weave.inputs["Strength"].default_value = 0.08
    nt.links.new(weave.outputs["Fac"], bump_weave.inputs["Height"])
    nt.links.new(bump_folds.outputs["Normal"], bump_weave.inputs["Normal"])
    nt.links.new(bump_weave.outputs["Normal"], bsdf.inputs["Normal"])


# ------------------------------------------------------------- primitives ---

def finish(obj, material_key, bevel=0.012, parent=None):
    """Assign material, round the edges (toy look) and smooth-shade."""
    obj.data.materials.append(material(material_key))
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = max(bevel * 2.0, 0.012)
    mod.segments = 3
    mod.limit_method = "ANGLE"
    mod.harden_normals = True
    bpy.ops.object.shade_smooth()
    if parent:
        obj.parent = parent
    return obj


def box(name, size, loc, material_key, rot=(0, 0, 0), bevel=0.012, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material_key, bevel, parent)


def cylinder(name, radius, depth, loc, material_key, rot=(0, 0, 0), verts=24, bevel=0.012,
             parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=max(verts, 24), radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    return finish(obj, material_key, bevel, parent)


def sphere(name, radius, loc, material_key, scale=(1, 1, 1), rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=radius,
                                         location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material_key, 0.0, parent)


def torus(name, major, minor, loc, material_key, rot=(0, 0, 0), scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=32,
                                     minor_segments=12, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    return finish(obj, material_key, 0.0, parent)


def cone(name, radius_bottom, radius_top, depth, loc, material_key, rot=(0, 0, 0), verts=24, bevel=0.0,
         parent=None):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius_bottom, radius2=radius_top, depth=depth,
                                    location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    return finish(obj, material_key, bevel, parent)


def rock(name, radius, loc, material_key, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (1.0, 0.8, 0.7)
    return finish(obj, material_key, 0.0, parent)


def bowl(name, radii, loc, material_key, thickness=0.02, rot=(0, 0, 0), parent=None):
    """Lower half of an ellipsoid, opening upwards, with wall thickness."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1.0, location=loc,
                                         rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_outer=True)
    bm.to_mesh(obj.data)
    bm.free()
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    solid = obj.modifiers.new("thickness", "SOLIDIFY")
    solid.thickness = thickness
    return finish(obj, material_key, 0.0, parent)


def boolean_cut(target, cutter, cutter_material_key=None):
    mod = target.modifiers.new(f"cut_{cutter.name}", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "EXACT"
    if cutter_material_key and hasattr(mod, "material_mode"):
        mod.material_mode = "TRANSFER"
        cutter.data.materials.append(material(cutter_material_key))
    # Booleans must run before the bevel.
    target.modifiers.move(len(target.modifiers) - 1, 0)
    cutter.hide_render = True
    cutter.hide_viewport = True


def group(name, location=(0, 0, 0), rotation=(0, 0, 0)):
    """Empty used as parent for multi-part models; move/rotate it after building."""
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    empty.location = location
    empty.rotation_euler = rotation
    return empty


def shadow_catcher(size=6.0, z=0.0):
    """Invisible ground that only keeps the soft contact shadow (transparent renders)."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    plane = bpy.context.active_object
    plane.name = "shadow_catcher"
    plane.is_shadow_catcher = True
    return plane


# ------------------------------------------------------------------ scene ---

def new_scene(resolution=(1024, 1024), samples=160):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()  # cached materials died with the old scene
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue

    world = bpy.data.worlds.new("world")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = srgb(NIGHT_SKY)
    bg.inputs["Strength"].default_value = 0.3
    return scene


def _ortho_camera(scene, name, rot_x_deg, rot_z_deg, target, ortho_scale):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    data.clip_end = 100
    cam = bpy.data.objects.new(name, data)
    scene.collection.objects.link(cam)
    rx, rz = math.radians(rot_x_deg), math.radians(rot_z_deg)
    cam.rotation_euler = (rx, 0, rz)
    back = Vector((math.sin(rx) * math.sin(rz), -math.sin(rx) * math.cos(rz), math.cos(rx)))
    cam.location = Vector(target) + back * 30
    scene.camera = cam
    return cam


def camera_place(scene, target=(0, 0, 0.55), ortho_scale=7.6):
    """True isometric camera shared by all place tiles."""
    return _ortho_camera(scene, "cam_place", 54.736, 45, target, ortho_scale)


def camera_object(scene, target=(0, 0, 0), ortho_scale=2.4):
    """Three-quarter top-down view (40° above the ground) for items, tools and tokens."""
    return _ortho_camera(scene, "cam_object", 50, 30, target, ortho_scale)


def camera_character(scene, target=(0, 0, 0.8), ortho_scale=1.9):
    """Front-ish view, slightly from the right, for standees and portraits."""
    return _ortho_camera(scene, "cam_character", 82, 20, target, ortho_scale)


def _sun(scene, name, hex_color, energy, angle_deg, coming_from):
    data = bpy.data.lights.new(name, "SUN")
    data.energy = energy
    data.angle = math.radians(angle_deg)
    data.color = srgb(hex_color)[:3]
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.rotation_euler = (-Vector(coming_from).normalized()).to_track_quat("-Z", "Y").to_euler()
    return obj


def point_light(scene, name, loc, energy=45, hex_color=WARM_LIGHT, radius=0.08):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.color = srgb(hex_color)[:3]
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    scene.collection.objects.link(obj)
    return obj


def area_light(scene, name, loc, target, energy, hex_color=WARM_LIGHT, size=1.5):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size
    data.color = srgb(hex_color)[:3]
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    scene.collection.objects.link(obj)
    look_at(obj, target)
    return obj


def light_rig(scene, preset="place", target=(0, 0, 0)):
    """Night rig: cold moonlight key + cold rim. 'studio' adds a warm fill for items/characters."""
    _sun(scene, "key", MOONLIGHT, 2.6, 6, (0.35, -0.8, 0.9))
    _sun(scene, "rim", RIM_LIGHT, 1.6, 4, (-0.7, 0.9, 0.6))
    if preset == "studio":
        t = Vector(target)
        area_light(scene, "warm_fill", t + Vector((2.2, -1.2, 1.4)), t, energy=160, size=1.8)


# ----------------------------------------------------------------- output ---

def render(scene, filename):
    path = os.path.join(RENDER_DIR, filename)
    os.makedirs(RENDER_DIR, exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {path}")
    return path


def save_blend(relative_path):
    path = os.path.join(BLEND_DIR, relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    backup = path + "1"
    if os.path.exists(backup):
        os.remove(backup)
    return path
