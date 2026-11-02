"""Character builders. Characters are based on Blender Studio's CC0 'Human Base Meshes'
(art/vendor/human-base-meshes) and dressed procedurally: jumpsuit as an inflated cloth layer,
skin details (beard, brows, scar, tattoos, bruise) as point attributes read by the skin shader,
hair as geometry-nodes curves, a generated skeleton and pose functions.

Usage:
    char = build_character(CHARACTERS["char.01"])
    apply_pose(char, "dig")     # relaxed | dig | fight | beaten | victory

Figures stand on z=0 and face -y.
"""

import math
import os
from dataclasses import dataclass, field

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

from digout_art import ROOT, box, cylinder, material, srgb, torus

BASE_BLEND = os.path.join(ROOT, "art", "vendor", "human-base-meshes",
                          "human-base-meshes-bundle-v1.4.1", "human_base_meshes_bundle.blend")
BASE_MESHES = {"male": "GEO-body_male_realistic", "female": "GEO-body_female_realistic"}

# Face sets shared by the realistic male and female base meshes (see project.md 8.6.4).
FS_TORSO, FS_HIPS, FS_BELLY = 1, 18, 19
FS_HEAD = {17, 2, 3, 4, 5, 7, 8, 22}  # skull, eyelids, ears, nose, lips, muzzle
FS_EARS = {4, 5}
FS_LIPS = 8
FS_UPPER_ARM = {"L": 21, "R": 20}
FS_FOREARM = {"L": 12, "R": 11}
FS_HAND = {"L": 9, "R": 10}
FS_FINGERS = {"L": range(64, 84), "R": range(84, 104)}
# Four face sets per finger. pinky -> index define the knuckle line; the thumb stays on the hand.
FS_PINKY = {"L": range(64, 68), "R": range(100, 104)}
FS_INDEX = {"L": range(76, 80), "R": range(88, 92)}
FS_THUMB = {"L": range(80, 84), "R": range(84, 88)}
FS_UPPER_LEG = {"L": 24, "R": 23}
FS_LOWER_LEG = {"L": 15, "R": 16}
FS_FOOT = {"L": 14, "R": 13}
FS_TOES = {"L": {25, *range(46, 64)}, "R": {26, *range(27, 46)}}
SIDE_SIGN = {"L": 1.0, "R": -1.0}  # character's left is +x (figure faces -y)
SUIT_SETS = {FS_TORSO, FS_HIPS, FS_BELLY, *FS_UPPER_ARM.values(), *FS_UPPER_LEG.values(),
             *FS_LOWER_LEG.values()}
SHOE_SETS = {*FS_FOOT.values(), *FS_TOES["L"], *FS_TOES["R"]}


@dataclass
class CharacterSpec:
    id: str
    name: str
    base: str = "male"                      # male | female
    scale: tuple = (1.0, 1.0, 1.0)
    skin: str = "#c58b64"
    eyes: str = "#4a3424"
    hair: str = "bald"                      # bald | buzz | short | slick | curly
    hair_melanin: float = 0.9
    hair_redness: float | None = None       # None = Blender default
    hair_color: str | None = None           # direct colour instead of melanin (grey/white hair)
    beard: str = "none"                     # none | full | stubble | mustache | goatee
    brows: str = "normal"                   # normal | angry | raised
    brow_melanin: float | None = None
    scar: bool = False
    tattoos: set = field(default_factory=set)  # forearm_L, forearm_R, neck, tear
    glasses: bool = False
    sleeves: str = "rolled"                 # rolled | long


CHARACTERS = {spec.id: spec for spec in (
    CharacterSpec("char.01", "Der Riese", scale=(1.14, 1.14, 1.04), skin="#b97a58", beard="full",
                  brows="angry", scar=True, tattoos={"forearm_L"}),
    CharacterSpec("char.02", "Die Alte", base="female", scale=(1.02, 1.02, 0.96), skin="#e3b9a0",
                  eyes="#3c5368", hair="curly", hair_color="#9a9a96", glasses=True,
                  sleeves="long"),
    CharacterSpec("char.03", "Der Nerd", scale=(0.94, 0.9, 1.0), skin="#efc7a8", eyes="#3d5a3a",
                  hair="short", hair_melanin=0.55, glasses=True, sleeves="long"),
    CharacterSpec("char.04", "Die Tätowierte", base="female", scale=(1.04, 1.04, 1.0), skin="#d6a07a",
                  hair="buzz", hair_melanin=0.95, brows="angry",
                  tattoos={"forearm_L", "forearm_R", "neck", "tear"}),
    CharacterSpec("char.05", "Der Dandy", scale=(1.0, 0.98, 1.02), skin="#c9906c", hair="slick",
                  hair_melanin=0.97, beard="mustache", brows="raised", sleeves="long"),
    CharacterSpec("char.06", "Der Junge", scale=(0.93, 0.92, 0.96), skin="#8a5a3c", eyes="#2a1a10",
                  hair="curly", hair_melanin=0.98, beard="stubble"),
)}


# ------------------------------------------------------------ base mesh ---

def _load_body(name):
    with bpy.data.libraries.load(BASE_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == name or n.startswith(name + ".eye")]
    for obj in dst.objects:
        bpy.context.scene.collection.objects.link(obj)
        obj.animation_data_clear()
    body = next(o for o in dst.objects if o.parent is None)
    body.location = (0, 0, 0)

    # Bake the sculpted detail (multires level 2 ≈ 170k faces).
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    multires = next(m for m in body.modifiers if m.type == "MULTIRES")
    multires.levels = 2
    bpy.ops.object.modifier_apply(modifier=multires.name)
    return body


def _mesh_arrays(me):
    n_v, n_p = len(me.vertices), len(me.polygons)
    co = np.empty(n_v * 3, np.float32)
    me.vertices.foreach_get("co", co)
    fs = np.empty(n_p, np.int32)
    me.attributes[".sculpt_face_set"].data.foreach_get("value", fs)
    centers = np.empty(n_p * 3, np.float32)
    me.polygons.foreach_get("center", centers)
    loop_total = np.empty(n_p, np.int32)
    me.polygons.foreach_get("loop_total", loop_total)
    loop_vert = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", loop_vert)
    loop_face = np.repeat(np.arange(n_p), loop_total)
    return co.reshape(-1, 3), fs, centers.reshape(-1, 3), loop_vert, loop_face


def _verts_of(face_mask, loop_vert, loop_face, n_verts):
    out = np.zeros(n_verts, bool)
    out[loop_vert[face_mask[loop_face]]] = True
    return out


def _smooth(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _band(x, lo, hi, soft):
    return _smooth(lo - soft, lo, x) * (1 - _smooth(hi, hi + soft, x))


def _distance_to(co, query_idx, target_idx):
    """Distance of each query vertex to the nearest target vertex."""
    if len(target_idx) == 0:
        return np.full(len(query_idx), 1.0, np.float32)
    tree = KDTree(len(target_idx))
    for i, v in enumerate(target_idx):
        tree.insert(co[v], i)
    tree.balance()
    return np.array([tree.find(co[v])[2] for v in query_idx], np.float32)


def _weighted_group(obj, name, verts, weights):
    group = obj.vertex_groups.new(name=name)
    rounded = np.round(weights, 2)
    for w in np.unique(rounded):
        group.add(verts[rounded == w].tolist(), float(w), "REPLACE")
    return group


def _set_point_attr(me, name, values):
    attr = me.attributes.new(name, "FLOAT", "POINT")
    attr.data.foreach_set("value", values.astype(np.float32))


# ------------------------------------------------------------- shaders ---

def _skin_material(name, skin_hex, hair_hex):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.48
    bsdf.inputs["Subsurface Weight"].default_value = 0.12
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.25)
    bsdf.inputs["Subsurface Scale"].default_value = 0.01

    def attr(attr_name):
        node = nt.nodes.new("ShaderNodeAttribute")
        node.attribute_name = attr_name
        return node.outputs["Fac"]

    def mix_color(fac, a, b):
        node = nt.nodes.new("ShaderNodeMix")
        node.data_type = "RGBA"
        nt.links.new(fac, node.inputs["Factor"])
        for ident, value in (("A_Color", a), ("B_Color", b)):
            sock = next(s for s in node.inputs if s.identifier == ident)
            if isinstance(value, tuple):
                sock.default_value = value
            else:
                nt.links.new(value, sock)
        return next(s for s in node.outputs if s.identifier == "Result_Color")

    def math_node(op, a, b):
        node = nt.nodes.new("ShaderNodeMath")
        node.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, float):
                node.inputs[i].default_value = v
            else:
                nt.links.new(v, node.inputs[i])
        return node.outputs["Value"]

    hair = math_node("MAXIMUM", attr("beard"), attr("brow"))
    # Tattoo: noisy ink inside the band mask.
    ink_noise = nt.nodes.new("ShaderNodeTexNoise")
    ink_noise.inputs["Scale"].default_value = 60
    ink_ramp = nt.nodes.new("ShaderNodeValToRGB")
    ink_ramp.color_ramp.elements[0].position = 0.45
    ink_ramp.color_ramp.elements[1].position = 0.55
    nt.links.new(ink_noise.outputs["Fac"], ink_ramp.inputs["Fac"])
    tattoo = math_node("MULTIPLY", attr("tattoo"), ink_ramp.outputs["Color"])

    color = mix_color(hair, srgb(skin_hex), srgb(hair_hex))
    color = mix_color(attr("scar"), color, srgb("#c4806f"))
    color = mix_color(math_node("MULTIPLY", tattoo, 0.85), color, srgb("#26324a"))
    bruise_amount = nt.nodes.new("ShaderNodeValue")
    bruise_amount.name = "bruise_amount"  # set by the 'beaten' pose
    bruise_amount.outputs[0].default_value = 0.0
    color = mix_color(math_node("MULTIPLY", attr("bruise"), bruise_amount.outputs[0]), color, srgb("#4a2638"))
    nt.links.new(color, bsdf.inputs["Base Color"])

    rough = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(hair, rough.inputs["Value"])
    rough.inputs["To Min"].default_value = 0.48
    rough.inputs["To Max"].default_value = 0.75
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])

    # Stubble/hair texture where hair grows, faint pores elsewhere.
    hair_noise = nt.nodes.new("ShaderNodeTexNoise")
    hair_noise.inputs["Scale"].default_value = 700
    bump = nt.nodes.new("ShaderNodeBump")
    nt.links.new(math_node("ADD", math_node("MULTIPLY", hair, 0.5), 0.04), bump.inputs["Strength"])
    nt.links.new(hair_noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _eye_material(iris_hex, forward_local):
    """Sclera, iris and pupil by the angle to the eye's forward axis (given in eye-local space,
    the eye meshes are rotated differently per base mesh)."""
    mat = bpy.data.materials.new("eye_" + iris_hex)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.08
    coords = nt.nodes.new("ShaderNodeTexCoord")
    norm = nt.nodes.new("ShaderNodeVectorMath")
    norm.operation = "NORMALIZE"
    nt.links.new(coords.outputs["Object"], norm.inputs[0])
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = tuple(forward_local)
    nt.links.new(norm.outputs["Vector"], dot.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.74, srgb("#e6dfd4")
    els[1].position, els[1].color = 0.8, srgb(iris_hex)
    pupil = els.new(0.93)
    pupil.color = srgb("#050505")
    nt.links.new(dot.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


# --------------------------------------------------------------- hair ---

def _hair_material(name, melanin, redness=None, color=None):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    hair = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    if color:  # direct colour, e.g. grey hair (melanin alone turns warm under the fill light)
        hair.parametrization = "COLOR"
        hair.inputs["Color"].default_value = srgb(color)
        hair.inputs["Roughness"].default_value = 0.35
        nt.links.new(hair.outputs[0], out.inputs["Surface"])
        return mat
    hair.parametrization = "MELANIN"
    hair.inputs["Melanin"].default_value = melanin
    if redness is not None:  # 0 = neutral grey/white for low melanin
        hair.inputs["Melanin Redness"].default_value = redness
    hair.inputs["Roughness"].default_value = 0.35
    nt.links.new(hair.outputs[0], out.inputs["Surface"])
    return mat


def add_hair(body, name, mask_attr, density, length, radius, tilt, mat, jitter_amount=0.2):
    """Short hair (beard, brows, stubble) grown from a point-attribute mask with geometry nodes.

    tilt: vector added to the surface normal before normalizing – combs the hair
    (e.g. (0, 0, -0.8) points beard hair downwards). x is mirrored per side.
    """
    tree = bpy.data.node_groups.new(f"{name}.gn", "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n, links = tree.nodes, tree.links

    info = n.new("GeometryNodeObjectInfo")
    info.transform_space = "RELATIVE"
    info.inputs["Object"].default_value = body
    mask = n.new("GeometryNodeInputNamedAttribute")
    mask.data_type = "FLOAT"
    mask.inputs["Name"].default_value = mask_attr
    dens = n.new("ShaderNodeMath")
    dens.operation = "MULTIPLY"
    dens.inputs[1].default_value = density
    links.new(mask.outputs["Attribute"], dens.inputs[0])
    dist = n.new("GeometryNodeDistributePointsOnFaces")
    links.new(info.outputs["Geometry"], dist.inputs["Mesh"])
    links.new(dens.outputs["Value"], dist.inputs["Density"])

    # Direction: normal + tilt (x mirrored by the side of the face).
    pos = n.new("GeometryNodeInputPosition")
    sep = n.new("ShaderNodeSeparateXYZ")
    links.new(pos.outputs["Position"], sep.inputs["Vector"])
    sign = n.new("ShaderNodeMath")
    sign.operation = "SIGN"
    links.new(sep.outputs["X"], sign.inputs[0])
    tilt_x = n.new("ShaderNodeMath")
    tilt_x.operation = "MULTIPLY"
    tilt_x.inputs[1].default_value = tilt[0]
    links.new(sign.outputs["Value"], tilt_x.inputs[0])
    tilt_vec = n.new("ShaderNodeCombineXYZ")
    links.new(tilt_x.outputs["Value"], tilt_vec.inputs["X"])
    tilt_vec.inputs["Y"].default_value = tilt[1]
    tilt_vec.inputs["Z"].default_value = tilt[2]
    jitter = n.new("FunctionNodeRandomValue")
    jitter.data_type = "FLOAT_VECTOR"
    jitter.inputs["Min"].default_value = (-jitter_amount,) * 3
    jitter.inputs["Max"].default_value = (jitter_amount,) * 3
    add1 = n.new("ShaderNodeVectorMath")
    add1.operation = "ADD"
    links.new(dist.outputs["Normal"], add1.inputs[0])
    links.new(tilt_vec.outputs["Vector"], add1.inputs[1])
    add2 = n.new("ShaderNodeVectorMath")
    add2.operation = "ADD"
    links.new(add1.outputs["Vector"], add2.inputs[0])
    links.new(jitter.outputs["Value"], add2.inputs[1])
    align = n.new("FunctionNodeAlignRotationToVector")
    align.axis = "Z"
    links.new(add2.outputs["Vector"], align.inputs["Vector"])

    strand = n.new("GeometryNodeCurvePrimitiveLine")
    strand.inputs["Start"].default_value = (0, 0, 0)
    strand.inputs["End"].default_value = (0, 0, length)
    scale = n.new("FunctionNodeRandomValue")
    scale.data_type = "FLOAT"
    scale.inputs["Min"].default_value = 0.6
    scale.inputs["Max"].default_value = 1.3
    inst = n.new("GeometryNodeInstanceOnPoints")
    links.new(dist.outputs["Points"], inst.inputs["Points"])
    links.new(strand.outputs["Curve"], inst.inputs["Instance"])
    links.new(align.outputs["Rotation"], inst.inputs["Rotation"])
    links.new(scale.outputs["Value"], inst.inputs["Scale"])
    realize = n.new("GeometryNodeRealizeInstances")
    links.new(inst.outputs["Instances"], realize.inputs["Geometry"])
    rad = n.new("GeometryNodeSetCurveRadius")
    rad.inputs["Radius"].default_value = radius
    links.new(realize.outputs["Geometry"], rad.inputs["Curve"])
    setmat = n.new("GeometryNodeSetMaterial")
    setmat.inputs["Material"].default_value = mat
    links.new(rad.outputs["Curve"], setmat.inputs["Geometry"])
    out = n.new("NodeGroupOutput")
    links.new(setmat.outputs["Geometry"], out.inputs[0])

    # Must be a hair Curves object, otherwise Cycles does not render the strands.
    holder = bpy.data.objects.new(name, bpy.data.hair_curves.new(name))
    bpy.context.scene.collection.objects.link(holder)
    holder.parent = body
    mod = holder.modifiers.new("hair", "NODES")
    mod.node_group = tree
    return holder


# ----------------------------------------------------------- clothing ---

def _attach(obj, parent):
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()


def _ring(name, body, points_world, axis, material_key, minor, extra=0.0):
    """Torus fitted around a loop of points (rolled sleeve, cuff)."""
    center = Vector(points_world.mean(axis=0))
    axis = Vector(axis).normalized()
    rel = points_world - np.array(center)
    rel -= np.outer(rel @ np.array(axis), np.array(axis))
    radius = float(np.linalg.norm(rel, axis=1).mean()) + extra
    rot = axis.to_track_quat("Z", "Y").to_euler()
    ring = torus(name, radius, minor, center, material_key, rot=rot)
    _attach(ring, body)
    return ring


def _surface_point(origin, direction):
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    hit, loc, normal, *_ = bpy.context.scene.ray_cast(depsgraph, Vector(origin), Vector(direction))
    return (loc, normal) if hit else (None, None)


def _patch(body, name, x, z):
    """Prisoner number patch glued onto the chest surface (raycast from the front)."""
    loc, normal = _surface_point((x, -2, z), (0, 1, 0))
    if loc is None:
        return []
    rot = normal.to_track_quat("-Y", "Z")
    base = loc + normal * 0.002
    parts = [box(f"{name}.patch", (0.085, 0.004, 0.05), base, "patch", rot=rot.to_euler(), bevel=0.002)]
    for i, w in enumerate((0.008, 0.004, 0.011, 0.006, 0.008)):
        offset = rot @ Vector((-0.024 + i * 0.012, -0.0025, 0))
        parts.append(box(f"{name}.code_{i}", (w, 0.002, 0.032), base + offset, "eye",
                         rot=rot.to_euler(), bevel=0.0))
    for part in parts:
        _attach(part, body)
    return parts


def _glasses(name, eyes_world):
    """Thin metal glasses in front of the eyes."""
    parts = []
    for i, eye in enumerate(eyes_world):
        side = 1 if eye.x > 0 else -1
        center = eye + Vector((0, -0.021, 0.001))
        parts.append(torus(f"{name}.glasses_rim_{i}", 0.02, 0.0017, center, "glasses",
                           rot=(math.radians(90), 0, 0), scale=(1.15, 0.85, 1.0)))
        temple_x = eye.x + side * 0.042
        parts.append(box(f"{name}.glasses_hinge_{i}", (0.02, 0.003, 0.003),
                         (eye.x + side * 0.031, center.y, center.z + 0.004), "glasses", bevel=0.0))
        parts.append(box(f"{name}.glasses_temple_{i}", (0.003, 0.105, 0.003),
                         (temple_x, center.y + 0.052, center.z + 0.004), "glasses", bevel=0.0))
    left, right = eyes_world
    mid = (left + right) / 2 + Vector((0, -0.023, 0.006))
    parts.append(cylinder(f"{name}.glasses_bridge", 0.0015, abs(left.x - right.x) - 0.042, mid,
                          "glasses", rot=(0, math.radians(90), 0), bevel=0.0))
    return parts


# ------------------------------------------------------------------ rig ---

@dataclass
class Character:
    spec: CharacterSpec
    body: object
    rig: object
    eye_z: float
    eyes_world: list
    eye_objects: list
    extras: dict = field(default_factory=dict)


def _skeleton_joints(co, fs, verts, eye_z):
    """Joint positions from the seams between face sets (body-local, unscaled)."""
    torso, hips = verts(fs == FS_TORSO), verts(np.isin(fs, [FS_HIPS, FS_BELLY, FS_TORSO]))
    joints = {}
    for side, sign in SIDE_SIGN.items():
        upper, fore = verts(fs == FS_UPPER_ARM[side]), verts(fs == FS_FOREARM[side])
        hand, fingers = verts(fs == FS_HAND[side]), verts(np.isin(fs, list(FS_FINGERS[side])))
        thumb = verts(np.isin(fs, list(FS_THUMB[side])))
        uleg, lleg = verts(fs == FS_UPPER_LEG[side]), verts(fs == FS_LOWER_LEG[side])
        foot, toes = verts(fs == FS_FOOT[side]), verts(np.isin(fs, list(FS_TOES[side])))

        shoulder = co[upper & torso].mean(axis=0)
        shoulder[0] -= 0.02 * sign  # the joint sits inside the deltoid
        knuckle = co[hand & fingers & ~thumb].mean(axis=0)
        finger_dir = co[fingers & ~thumb].mean(axis=0) - knuckle
        finger_dir /= np.linalg.norm(finger_dir)
        knuckle_axis = (co[verts(np.isin(fs, list(FS_INDEX[side])))].mean(axis=0)
                        - co[verts(np.isin(fs, list(FS_PINKY[side])))].mean(axis=0))
        knuckle_axis -= finger_dir * (knuckle_axis @ finger_dir)  # pinky -> index, across the hand
        knuckle_axis /= np.linalg.norm(knuckle_axis)
        hip = co[uleg & hips].mean(axis=0)
        hip[2] += 0.05
        joints[side] = {
            "shoulder": shoulder,
            "elbow": co[upper & fore].mean(axis=0),
            "wrist": co[fore & hand].mean(axis=0),
            "knuckle": knuckle,
            "tip": knuckle + 2 * (co[fingers & ~thumb].mean(axis=0) - knuckle),
            "knuckle_axis": knuckle_axis,
            "hip": hip,
            "knee": co[uleg & lleg].mean(axis=0),
            "ankle": co[lleg & foot].mean(axis=0),
            "toe": co[toes].mean(axis=0),
            "arm_verts": upper | fore | hand | fingers,
            "leg_verts": uleg | lleg | foot | toes,
            "foot_verts": foot | toes,
            "fingers_verts": fingers & ~thumb,
        }
    hip_z = (joints["L"]["hip"][2] + joints["R"]["hip"][2]) / 2
    shoulder_z = (joints["L"]["shoulder"][2] + joints["R"]["shoulder"][2]) / 2
    joints["spine"] = {
        "pelvis": np.array([0, 0.0, hip_z]),
        "spine": np.array([0, 0.0, hip_z + 0.12]),
        "chest": np.array([0, -0.005, shoulder_z - 0.17]),
        "neck": np.array([0, -0.02, eye_z - 0.144]),
        "skull": np.array([0, -0.03, eye_z - 0.07]),
        "top": np.array([0, -0.03, eye_z + 0.13]),
    }
    return joints


def _skin_weights(co, joints, verts_hips_belly, eye_z):
    """Skin weights with soft blends at every joint; spine chain split by height."""
    def along(p, q, lo, hi):
        axis = (q - p) / np.linalg.norm(q - p)
        return _smooth(lo, hi, (co - p) @ axis)

    z = co[:, 2]
    weights = {}
    limbs = np.zeros(len(co), np.float32)
    for side, sign in SIDE_SIGN.items():
        j = joints[side]
        on_side = co[:, 0] * sign > 0.005

        near_shoulder = np.linalg.norm(co - j["shoulder"], axis=1) < 0.13
        region = (j["arm_verts"] | near_shoulder) & (co[:, 0] * sign > 0.04)
        arm = along(j["shoulder"], j["elbow"], -0.05, 0.03) * region
        fore = along(j["elbow"], j["wrist"], -0.03, 0.03)
        hand = along(j["wrist"], j["knuckle"], -0.02, 0.01)
        fingers = along(j["knuckle"], j["tip"], -0.006, 0.006) * j["fingers_verts"]
        weights[f"upper_arm.{side}"] = arm * (1 - fore)
        weights[f"forearm.{side}"] = arm * fore * (1 - hand)
        weights[f"hand.{side}"] = arm * fore * hand * (1 - fingers)
        weights[f"fingers.{side}"] = arm * fore * hand * fingers
        limbs += arm

        near_hip = np.linalg.norm(co - j["hip"], axis=1) < 0.14
        region = (j["leg_verts"] | (verts_hips_belly & near_hip)) & on_side
        leg = along(j["hip"], j["knee"], -0.07, 0.02) * region
        shin = along(j["knee"], j["ankle"], -0.04, 0.04)
        foot = j["foot_verts"] * _smooth(j["ankle"][2] + 0.03, j["ankle"][2] - 0.01, z)
        weights[f"thigh.{side}"] = leg * (1 - shin)
        weights[f"shin.{side}"] = leg * shin * (1 - foot)
        weights[f"foot.{side}"] = leg * shin * foot
        limbs += leg

    rest = np.clip(1 - limbs, 0, 1)
    s = joints["spine"]
    b1 = _smooth(s["spine"][2] - 0.05, s["spine"][2] + 0.05, z)
    b2 = _smooth(s["chest"][2] - 0.06, s["chest"][2] + 0.06, z)
    b3 = _smooth(s["neck"][2] - 0.02, s["neck"][2] + 0.03, z)
    b4 = _smooth(eye_z - 0.15, eye_z - 0.09, z)
    weights["pelvis"] = rest * (1 - b1)
    weights["spine"] = rest * b1 * (1 - b2)
    weights["chest"] = rest * b2 * (1 - b3)
    weights["neck"] = rest * b3 * (1 - b4)
    weights["head"] = rest * b4
    return weights


BONES = (
    # name, head joint, tail joint, parent, connected
    ("pelvis", "spine.pelvis", "spine.spine", None, False),
    ("spine", "spine.spine", "spine.chest", "pelvis", True),
    ("chest", "spine.chest", "spine.neck", "spine", True),
    ("neck", "spine.neck", "spine.skull", "chest", True),
    ("head", "spine.skull", "spine.top", "neck", True),
    ("upper_arm.{s}", "{s}.shoulder", "{s}.elbow", "chest", False),
    ("forearm.{s}", "{s}.elbow", "{s}.wrist", "upper_arm.{s}", True),
    ("hand.{s}", "{s}.wrist", "{s}.knuckle", "forearm.{s}", True),
    ("fingers.{s}", "{s}.knuckle", "{s}.tip", "hand.{s}", True),
    ("thigh.{s}", "{s}.hip", "{s}.knee", "pelvis", False),
    ("shin.{s}", "{s}.knee", "{s}.ankle", "thigh.{s}", True),
    ("foot.{s}", "{s}.ankle", "{s}.toe", "shin.{s}", True),
)


def _build_rig(body, joints, weights):
    """Armature in body-local space (child of the body) + Armature modifier first in the stack."""
    data = bpy.data.armatures.new(f"{body.name}.rig")
    rig = bpy.data.objects.new(f"{body.name}.rig", data)
    bpy.context.scene.collection.objects.link(rig)
    rig.parent = body
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")

    def joint(ref):
        group_name, key = ref.split(".")
        return Vector(joints[group_name][key])

    for name, head, tail, parent, connected in BONES:
        for side in (("L", "R") if "{s}" in name else (None,)):
            fmt = (lambda t: t.format(s=side)) if side else (lambda t: t)
            bone = data.edit_bones.new(fmt(name))
            bone.head, bone.tail = joint(fmt(head)), joint(fmt(tail))
            if parent:
                bone.parent = data.edit_bones[fmt(parent)]
                bone.use_connect = connected
    bpy.ops.object.mode_set(mode="OBJECT")
    for side in SIDE_SIGN:
        rig[f"knuckle_axis.{side}"] = [float(v) for v in joints[side]["knuckle_axis"]]

    for bone_name, w in weights.items():
        idx = np.flatnonzero(w > 0.005)
        _weighted_group(body, bone_name, idx, w[idx])
    mod = body.modifiers.new("rig", "ARMATURE")
    mod.object = rig
    body.modifiers.move(len(body.modifiers) - 1, 0)
    return rig


def _parent_to_bone(obj, rig, bone_name):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    obj.matrix_world = world


# ---------------------------------------------------------------- poses ---

def rotate_bone(rig, bone_name, axis, degrees):
    """Rotate a pose bone around its current head. axis: armature-space 'X'/'Y'/'Z', a Vector,
    or 'TWIST' for a roll around the bone's own (posed) direction."""
    bpy.context.view_layer.update()
    pose_bone = rig.pose.bones[bone_name]
    head = pose_bone.head.copy()
    if axis == "TWIST":
        axis = (pose_bone.tail - pose_bone.head).normalized()
    rotation = Matrix.Rotation(math.radians(degrees), 4, axis)
    pose_bone.matrix = Matrix.Translation(head) @ rotation @ Matrix.Translation(-head) @ pose_bone.matrix
    bpy.context.view_layer.update()


def move_bone(rig, bone_name, offset):
    bpy.context.view_layer.update()
    pose_bone = rig.pose.bones[bone_name]
    pose_bone.matrix = Matrix.Translation(Vector(offset)) @ pose_bone.matrix
    bpy.context.view_layer.update()


def _posed_knuckle_axis(rig, side):
    pose_bone, bone = rig.pose.bones[f"hand.{side}"], rig.data.bones[f"hand.{side}"]
    delta = pose_bone.matrix.to_3x3() @ bone.matrix_local.to_3x3().inverted()
    return (delta @ Vector(rig[f"knuckle_axis.{side}"])).normalized()


def curl_fingers(rig, side, degrees):
    """Bend all fingers around the knuckle line (90° ≈ fist)."""
    bpy.context.view_layer.update()
    rotate_bone(rig, f"fingers.{side}", _posed_knuckle_axis(rig, side), -degrees * SIDE_SIGN[side])


def crouch(rig, degrees):
    """Bend the knees while the feet stay planted: pelvis drops, thigh/shin/foot compensate."""
    bones = rig.data.bones
    legs = bones["thigh.L"].length + bones["shin.L"].length
    move_bone(rig, "pelvis", (0, 0, -legs * (1 - math.cos(math.radians(degrees)))))
    for side in SIDE_SIGN:
        rotate_bone(rig, f"thigh.{side}", "X", -degrees)
        rotate_bone(rig, f"shin.{side}", "X", 2 * degrees)
        rotate_bone(rig, f"foot.{side}", "X", -degrees)


def _arms_relaxed(rig, sides=("L", "R")):
    for side in sides:
        sign = SIDE_SIGN[side]
        rotate_bone(rig, f"upper_arm.{side}", "Y", 15 * sign)  # towards the body
        rotate_bone(rig, f"upper_arm.{side}", "X", -3)  # a little forward
        rotate_bone(rig, f"forearm.{side}", "X", -10)  # relaxed elbow
        rotate_bone(rig, f"forearm.{side}", "TWIST", 40 * sign)  # palms towards the thighs
        rotate_bone(rig, f"hand.{side}", "Y", 6 * sign)
        curl_fingers(rig, side, 15)


def pose_relaxed(char):
    """Natural standing pose (board standee)."""
    _arms_relaxed(char.rig)


def pose_dig(char):
    """Crouching, digging with the spoon in the left hand (the side the camera sees)."""
    rig = char.rig
    crouch(rig, 55)
    rotate_bone(rig, "spine", "X", 28)
    rotate_bone(rig, "chest", "X", 20)
    rotate_bone(rig, "neck", "X", -10)
    rotate_bone(rig, "head", "X", 15)
    # Digging arm reaches down in front of the feet.
    rotate_bone(rig, "upper_arm.L", "Y", 12)
    rotate_bone(rig, "upper_arm.L", "X", -35)
    rotate_bone(rig, "forearm.L", "X", -20)
    rotate_bone(rig, "forearm.L", "TWIST", 40)
    curl_fingers(rig, "L", 95)
    # Other hand braced on the knee.
    rotate_bone(rig, "upper_arm.R", "Y", -12)
    rotate_bone(rig, "upper_arm.R", "X", -30)
    rotate_bone(rig, "forearm.R", "X", -40)
    curl_fingers(rig, "R", 40)
    char.extras["spoon"] = _hold_spoon(char, "L")


def pose_fight(char):
    """Boxing stance: fists up, left foot forward."""
    rig = char.rig
    move_bone(rig, "pelvis", (0, 0, -0.03))
    rotate_bone(rig, "thigh.L", "X", -14)
    rotate_bone(rig, "shin.L", "X", 18)
    rotate_bone(rig, "foot.L", "X", -4)
    rotate_bone(rig, "thigh.R", "X", 12)
    rotate_bone(rig, "shin.R", "X", 12)
    rotate_bone(rig, "foot.R", "X", -24)
    rotate_bone(rig, "spine", "X", 6)
    rotate_bone(rig, "chest", "Z", 10)
    rotate_bone(rig, "head", "X", 6)
    for side, sign in SIDE_SIGN.items():
        lead = side == "L"
        rotate_bone(rig, f"upper_arm.{side}", "Y", 22 * sign)
        rotate_bone(rig, f"upper_arm.{side}", "X", -60 if lead else -45)
        rotate_bone(rig, f"forearm.{side}", "X", -85 if lead else -105)
        curl_fingers(rig, side, 95)


def pose_beaten(char):
    """Hunched over after a beating: head down, one arm holding the belly, black eye, plaster."""
    rig = char.rig
    crouch(rig, 10)
    rotate_bone(rig, "spine", "X", 18)
    rotate_bone(rig, "chest", "X", 12)
    rotate_bone(rig, "neck", "X", 12)
    rotate_bone(rig, "head", "X", 10)
    rotate_bone(rig, "head", "Y", 10)
    rotate_bone(rig, "upper_arm.L", "Y", 18)
    rotate_bone(rig, "upper_arm.L", "X", -20)
    rotate_bone(rig, "forearm.L", "X", -80)
    rotate_bone(rig, "forearm.L", "Z", -60)
    curl_fingers(rig, "L", 25)
    _arms_relaxed(rig, sides=("R",))
    rotate_bone(rig, "upper_arm.R", "X", -8)
    _set_bruise(char, 1.0)
    char.extras["plaster"] = _plaster(char)


def pose_victory(char):
    """Both fists raised, looking up."""
    rig = char.rig
    rotate_bone(rig, "spine", "X", -6)
    rotate_bone(rig, "chest", "X", -6)
    rotate_bone(rig, "head", "X", -12)
    rotate_bone(rig, "thigh.L", "X", -8)
    rotate_bone(rig, "shin.L", "X", 10)
    for side, sign in SIDE_SIGN.items():
        rotate_bone(rig, f"upper_arm.{side}", "Y", -120 * sign)  # V shape
        rotate_bone(rig, f"upper_arm.{side}", "X", -15)
        rotate_bone(rig, f"forearm.{side}", "Y", -15 * sign)
        curl_fingers(rig, side, 95)


POSES = {"relaxed": pose_relaxed, "dig": pose_dig, "fight": pose_fight, "beaten": pose_beaten,
         "victory": pose_victory}


def apply_pose(char, pose):
    """Reset to rest pose (and remove pose props), then apply one of POSES."""
    for pose_bone in char.rig.pose.bones:
        pose_bone.matrix_basis = Matrix.Identity(4)
    for key in ("spoon", "plaster"):
        for obj in char.extras.pop(key, []):
            bpy.data.objects.remove(obj, do_unlink=True)
    _set_bruise(char, 0.0)
    POSES[pose](char)
    bpy.context.view_layer.update()


def _hold_spoon(char, side):
    """Spoon gripped in the fist like a trowel, bowl pointing down."""
    from props import SPOON_GRIP, build_spoon

    rig = char.rig
    bpy.context.view_layer.update()
    to_world = rig.matrix_world
    knuckle = to_world @ rig.pose.bones[f"fingers.{side}"].head
    wrist = to_world @ rig.pose.bones[f"hand.{side}"].head
    grip = knuckle.lerp(wrist, 0.25)
    axis = (to_world.to_3x3() @ _posed_knuckle_axis(rig, side)).normalized()
    if axis.z > 0:
        axis = -axis
    spoon = build_spoon(f"{char.spec.id}.spoon")
    size = 0.26
    spoon.matrix_world = (Matrix.Translation(grip) @ axis.to_track_quat("Y", "Z").to_matrix().to_4x4()
                          @ Matrix.Diagonal((size, size, size, 1)) @ Matrix.Translation(-Vector(SPOON_GRIP)))
    _parent_to_bone(spoon, rig, f"hand.{side}")
    return [spoon, *spoon.children_recursive]


def _plaster(char):
    """Sticking plaster on the forehead (beaten pose)."""
    bpy.context.view_layer.update()
    eye = max((o.matrix_world.translation for o in char.eye_objects), key=lambda v: v.x)  # posed left eye
    loc, normal = _surface_point((eye.x * 0.8, eye.y - 2, eye.z + 0.05), (0, 1, 0))
    if loc is None:
        return []
    rot = normal.to_track_quat("-Y", "Z") @ Matrix.Rotation(math.radians(30), 3, "Y").to_quaternion()
    plaster = box(f"{char.spec.id}.plaster", (0.05, 0.003, 0.016), loc + normal * 0.002, "plaster",
                  rot=rot.to_euler(), bevel=0.002)
    _parent_to_bone(plaster, char.rig, "head")
    return [plaster]


def _set_bruise(char, amount):
    node = char.body.data.materials[0].node_tree.nodes.get("bruise_amount")
    if node:
        node.outputs[0].default_value = amount


# ----------------------------------------------------------- characters ---

HAIR_STYLES = {
    "buzz": dict(density=7e6, length=0.004, radius=0.00022, tilt=(0.0, 0.5, 0.3), jitter_amount=0.15),
    "short": dict(density=3e6, length=0.014, radius=0.0003, tilt=(0.5, 1.4, 0.8), jitter_amount=0.25),
    "slick": dict(density=4e6, length=0.016, radius=0.00028, tilt=(0.2, 2.6, 0.2), jitter_amount=0.08),
    "curly": dict(density=3.5e6, length=0.011, radius=0.00038, tilt=(0.0, 0.2, 0.6), jitter_amount=0.9),
}
BEARD_STYLES = {
    "full": dict(density=3.5e6, length=0.008, radius=0.0003, tilt=(0.0, -0.2, -1.6), jitter_amount=0.15),
    "stubble": dict(density=1.2e6, length=0.0011, radius=0.00016, tilt=(0.0, -0.2, -0.8), jitter_amount=0.2),
    "mustache": dict(density=2.5e6, length=0.007, radius=0.00024, tilt=(1.2, -0.3, -1.0), jitter_amount=0.12),
}
BROW_SLOPE = {"angry": 0.2, "normal": -0.05, "raised": -0.2}


def build_character(spec, location=(0, 0, 0), rot_z=0.0):
    body = _load_body(BASE_MESHES[spec.base])
    body.name = spec.id
    eyes = list(body.children)
    bpy.context.view_layer.update()
    eyes_local = sorted((e.matrix_world.translation.copy() for e in eyes), key=lambda v: -v.x)
    eye_z = sum(e.z for e in eyes_local) / len(eyes_local)
    body.scale = spec.scale
    me = body.data
    co, fs, centers, loop_vert, loop_face = _mesh_arrays(me)
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    ax = np.abs(x)
    n_v = len(co)

    def verts(face_mask):
        return _verts_of(face_mask, loop_vert, loop_face, n_v)

    # Materials per region.
    suit_sets = set(SUIT_SETS) | (set(FS_FOREARM.values()) if spec.sleeves == "long" else set())
    neck_z = eye_z - 0.144
    suit_faces = np.isin(fs, list(suit_sets)) & ~((fs == FS_TORSO) & (centers[:, 2] > neck_z))
    shoe_faces = np.isin(fs, list(SHOE_SETS))
    me.materials.clear()
    me.materials.append(_skin_material(f"{spec.id}.skin", spec.skin, "#1d1612"))
    me.materials.append(material("jumpsuit"))
    me.materials.append(material("shoe"))
    index = np.zeros(len(fs), np.int32)
    index[suit_faces] = 1
    index[shoe_faces] = 2
    me.polygons.foreach_set("material_index", index)

    # Cloth layer: smooth away anatomy (muscles, toes), then inflate along the normals
    # so the jumpsuit hangs loose and the feet become shoes. Both fade out towards the
    # cloth edge so hems stay attached to the skin.
    skin_verts = verts(~(suit_faces | shoe_faces))
    for group_name, faces, iterations, strength in (("suit", suit_faces, 120, 0.03),
                                                    ("shoe", shoe_faces, 160, 0.02)):
        members = verts(faces)
        idx = np.flatnonzero(members)
        edge_dist = _distance_to(co, idx, np.flatnonzero(members & skin_verts))
        smooth_group = _weighted_group(body, f"{group_name}_smooth", idx, _smooth(0.0, 0.04, edge_dist))
        inflate_group = _weighted_group(body, f"{group_name}_inflate", idx, _smooth(0.0, 0.015, edge_dist))
        smooth = body.modifiers.new(f"smooth_{group_name}", "SMOOTH")
        smooth.vertex_group = smooth_group.name
        smooth.factor = 1.0
        smooth.iterations = iterations
        inflate = body.modifiers.new(f"inflate_{group_name}", "DISPLACE")
        inflate.vertex_group = inflate_group.name
        inflate.mid_level = 0.0
        inflate.strength = strength

    joints = _skeleton_joints(co, fs, verts, eye_z)
    _skin_masks(spec, me, co, fs, verts, eye_z, eyes_local, joints)

    # Eyes.
    bpy.context.view_layer.update()
    for eye in eyes:
        forward = (eye.matrix_world.to_3x3().inverted() @ Vector((0, -1, 0))).normalized()
        eye.data.materials.clear()
        eye.data.materials.append(_eye_material(spec.eyes, forward))

    # Sleeves: rolled up at the elbow, or a cuff at the wrist.
    world = co * np.array(body.scale)
    extras = {}
    for side in SIDE_SIGN:
        upper = verts(fs == FS_UPPER_ARM[side])
        fore = verts(fs == FS_FOREARM[side])
        hand = verts(fs == FS_HAND[side])
        if spec.sleeves == "rolled":
            seam, axis = upper & fore, world[upper].mean(axis=0) - world[fore].mean(axis=0)
            ring = _ring(f"{spec.id}.cuff_{side}", body, world[seam], axis, "jumpsuit_dark", 0.026, extra=0.03)
            extras[f"cuff_{side}"] = (ring, f"upper_arm.{side}")
        else:
            seam, axis = fore & hand, world[fore].mean(axis=0) - world[hand].mean(axis=0)
            ring = _ring(f"{spec.id}.cuff_{side}", body, world[seam], axis, "jumpsuit_dark", 0.012, extra=0.026)
            extras[f"cuff_{side}"] = (ring, f"forearm.{side}")

    bpy.context.view_layer.update()
    eyes_world = sorted((e.matrix_world.translation.copy() for e in eyes), key=lambda v: -v.x)
    patch = _patch(body, spec.id, x=-0.1 * spec.scale[0], z=(eye_z - 0.214) * spec.scale[2])
    glasses = _glasses(spec.id, eyes_world) if spec.glasses else []

    rig = _build_rig(body, joints, _skin_weights(co, joints, verts(np.isin(fs, [FS_HIPS, FS_BELLY])), eye_z))
    for ring, bone in extras.values():
        _parent_to_bone(ring, rig, bone)
    for obj in patch:
        _parent_to_bone(obj, rig, "chest")
    for obj in (*eyes, *glasses):
        _parent_to_bone(obj, rig, "head")

    # Hair.
    brow_melanin = spec.brow_melanin if spec.brow_melanin is not None else (
        spec.hair_melanin if spec.hair != "bald" else 0.92)
    brow_mat = _hair_material(f"{spec.id}.brow_hair", melanin=brow_melanin, redness=spec.hair_redness,
                              color=spec.hair_color)
    add_hair(body, f"{spec.id}.brows", "brow_density", density=3e6, length=0.005, radius=0.00022,
             tilt=(1.8, 0.0, 0.5), mat=brow_mat, jitter_amount=0.15)
    hair_mat = _hair_material(f"{spec.id}.hair", melanin=spec.hair_melanin, redness=spec.hair_redness,
                              color=spec.hair_color)
    if spec.beard != "none":
        beard_mat = hair_mat if spec.hair != "bald" else _hair_material(f"{spec.id}.beard_hair", 0.92)
        add_hair(body, f"{spec.id}.beard", "beard_density", mat=beard_mat, **BEARD_STYLES[spec.beard])
    if spec.hair != "bald":
        add_hair(body, f"{spec.id}.scalp", "scalp_density", mat=hair_mat, **HAIR_STYLES[spec.hair])

    body.location = location
    body.rotation_euler = (0, 0, rot_z)
    char = Character(spec, body, rig, eye_z, eyes_world, eyes)
    apply_pose(char, "relaxed")
    return char


def _skin_masks(spec, me, co, fs, verts, eye_z, eyes_local, joints):
    """Point-attribute masks (body-local, unscaled) for hair density and skin shading."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    ax = np.abs(x)
    head = verts(np.isin(fs, list(FS_HEAD))).astype(np.float32)
    lips = verts(fs == FS_LIPS).astype(np.float32)
    ears = verts(np.isin(fs, list(FS_EARS))).astype(np.float32)
    ez = z - eye_z  # height relative to the eyes – works for male and female heads

    # Beard: from just under the jaw line up to a diagonal edge (low at the mouth, high at the
    # sideburns). Neck and ears stay bare.
    upper = -0.072 + 0.6 * np.maximum(0.0, ax - 0.03)
    jaw = -0.137 + (y + 0.11) * 0.45
    full = _smooth(jaw - 0.008, jaw + 0.002, ez) * (1 - _smooth(upper - 0.004, upper + 0.006, ez))
    full *= _smooth(-0.015, -0.035, y)
    mustache = _band(ez, -0.074, -0.061, 0.006) * _band(ax, -1, 0.03, 0.012) * _smooth(-0.1, -0.12, y)
    sideburns = _band(ez, -0.044, -0.002, 0.008) * _band(ax, 0.062, 0.088, 0.006) * _band(y, -0.075, -0.054, 0.006)
    if spec.beard == "mustache":
        # Thin moustache tapering to the mouth corners; no lip cut-out (it would split it).
        top = -0.063 - ax * 0.12
        beard = _band(ez, top - 0.009, top, 0.004) * _band(ax, -1, 0.03, 0.008) * _smooth(-0.1, -0.12, y)
    elif spec.beard in ("full", "stubble"):
        beard = np.maximum(np.maximum(full, mustache), sideburns)
    else:
        beard = np.zeros_like(z)
    beard = beard * head * (1 - ears) * (1.0 if spec.beard == "mustache" else (1 - 0.95 * lips))
    _set_point_attr(me, "beard_density", beard)
    _set_point_attr(me, "beard", beard * {"full": 0.55, "stubble": 0.12, "mustache": 0.2}.get(spec.beard, 0.0))

    # Brows.
    slope = BROW_SLOPE[spec.brows]
    brow_z = 0.024 + (0.004 if spec.brows == "raised" else 0.0) + (ax - 0.015) * slope
    half = 0.003 - np.clip(ax - 0.013, 0, 0.05) * 0.035  # thick inner end, thin outer tail
    brow = _band(ez - brow_z, -half, half, 0.0016) * _band(ax, 0.013, 0.06, 0.006) \
        * _smooth(-0.085, -0.1, y) * head * 0.95
    _set_point_attr(me, "brow_density", brow)
    _set_point_attr(me, "brow", brow * 0.5)

    # Scalp hair: hairline high at the forehead, lower towards the neck, above the ears.
    hairline = 0.06 - np.clip(y + 0.1, 0, 0.2) * 0.6
    hairline = np.where((ax > 0.055) & (y < 0.02), np.maximum(hairline, 0.015), hairline)
    scalp = _smooth(hairline - 0.004, hairline + 0.004, ez) * head * (1 - ears)
    _set_point_attr(me, "scalp_density", scalp)

    # Scar over the left eye.
    scar = np.zeros_like(z)
    if spec.scar:
        p0, p1 = np.array([0.055, 0.041]), np.array([0.04, -0.019])
        scar = _segment_mask(np.stack([x, ez], 1), p0, p1, 0.001, 0.0025) * _smooth(-0.07, -0.09, y) * head
    _set_point_attr(me, "scar", scar)

    # Tattoos.
    tattoo = np.zeros_like(z)
    for side, sign in SIDE_SIGN.items():
        if f"forearm_{side}" in spec.tattoos:
            j = joints[side]
            axis = j["wrist"] - j["elbow"]
            t = ((co - j["elbow"]) @ axis) / (axis @ axis)
            tattoo = np.maximum(tattoo, _band(t, 0.2, 0.6, 0.03) * verts(fs == FS_FOREARM[side]))
    if "neck" in spec.tattoos:
        # Between the collar (ez ≈ -0.144) and the jaw.
        tattoo = np.maximum(tattoo, _band(ez, -0.14, -0.1, 0.008) * (1 - head) * (ax < 0.09)
                            * verts(fs == FS_TORSO))
    if "tear" in spec.tattoos:
        eye = eyes_local[0]
        d = np.hypot(x - eye.x, ez + 0.03)
        tattoo = np.maximum(tattoo, (1 - _smooth(0.004, 0.006, d)) * _smooth(-0.08, -0.1, y) * 2.0)
    _set_point_attr(me, "tattoo", np.clip(tattoo, 0, 1))

    # Black eye around the right eye (shown in the 'beaten' pose).
    eye = eyes_local[-1]
    d = np.hypot(x - eye.x, ez + 0.004)
    _set_point_attr(me, "bruise", (1 - _smooth(0.012, 0.026, d)) * _smooth(-0.07, -0.09, y) * head)


def _segment_mask(points, p0, p1, inner, outer):
    seg = p1 - p0
    t = np.clip(((points - p0) @ seg) / (seg @ seg), 0, 1)
    dist = np.linalg.norm(points - (p0 + np.outer(t, seg)), axis=1)
    return 1 - _smooth(inner, outer, dist)


def build_brute(name="char.01", location=(0, 0, 0), rot_z=0.0):
    """Kept for the board preview: 'Der Riese' in the relaxed pose."""
    return build_character(CHARACTERS["char.01"], location, rot_z).body
