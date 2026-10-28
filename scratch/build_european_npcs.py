import bpy
import bmesh
import os
import gzip
import json
import math
import glob
import re
from mathutils import Vector, Euler, Matrix

ROOT_DIR = "/Users/dianjulie/Documents/Map Project"
MH_DIR = os.path.join(ROOT_DIR, "scratch", "mh_assets")
PREP_TEX_DIR = os.path.join(MH_DIR, "prepared_tex")
BLEND_OUT = os.path.join(ROOT_DIR, "arlecchino_npcs_european.blend")
GLB_OUT = os.path.join(ROOT_DIR, "arlecchino_npcs_european.glb")
PREVIEW_OUT = os.path.join(ROOT_DIR, "scratch", "npcs_realistic_preview.png")

# ---------------------------------------------------------------------------
# 1. CLEAR SCENE & APPLY MANDATORY ARLECCHINO LIGHTING & WORLD STANDARDS
# ---------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 24

world = bpy.data.worlds.new("Arlecchino_World")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.96, 0.94, 0.90, 1.0)
    bg_node.inputs[1].default_value = 0.92

try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure = 0.22

# Add standard ceiling SPOT lights + shadowless warm AREA room-bounce fill lights
light_col = bpy.data.collections.new("00_Preview_Lighting")
scene.collection.children.link(light_col)

for i, lx in enumerate([-4.0, 0.0, 4.0]):
    ld = bpy.data.lights.new(f"Preview_Spot_{i}", type='SPOT')
    ld.energy = 98.0
    ld.color = (1.0, 0.95, 0.88)
    ld.spot_size = math.radians(75.0)
    ld.spot_blend = 0.45
    ld.use_custom_distance = True
    ld.cutoff_distance = 8.5
    ld.use_shadow = True
    lo = bpy.data.objects.new(f"Preview_Spot_{i}", ld)
    lo.location = (lx, -2.2, 3.2)
    lo.rotation_euler = (math.radians(32.0), 0.0, 0.0)
    light_col.objects.link(lo)

for i, lx in enumerate([-3.5, 3.5]):
    ad = bpy.data.lights.new(f"Preview_Bounce_Area_{i}", type='AREA')
    ad.energy = 68.0
    ad.color = (1.0, 0.96, 0.90)
    ad.shape = 'RECTANGLE'
    ad.size = 4.5
    ad.size_y = 3.0
    ad.use_shadow = False
    if hasattr(ad, "specular_factor"):
        ad.specular_factor = 0.0
    ao = bpy.data.objects.new(f"Preview_Bounce_Area_{i}", ad)
    ao.location = (lx, -3.2, 1.8)
    ao.rotation_euler = (math.radians(70.0), 0.0, 0.0)
    light_col.objects.link(ao)

npc_col = bpy.data.collections.new("07_NPC_Humans_European")
scene.collection.children.link(npc_col)

# ---------------------------------------------------------------------------
# 2. LOAD MAKEHUMAN BASE MESH, JOINT CUBES, WEIGHTS & TARGETS
# ---------------------------------------------------------------------------
base_obj_path = os.path.join(MH_DIR, "3dobjs", "base.obj")
raw_verts = []
raw_uvs = []
raw_faces = []
cube_v_indices = {}
cur_group = "body"

with open(base_obj_path, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("v "):
            p = line.split()
            raw_verts.append([float(p[1]), float(p[2]), float(p[3])])
        elif line.startswith("vt "):
            p = line.split()
            raw_uvs.append((float(p[1]), float(p[2])))
        elif line.startswith("g "):
            cur_group = line.split()[1]
        elif line.startswith("f "):
            p = line.split()[1:]
            fv = [int(w.split("/")[0]) - 1 for w in p]
            if cur_group == "body":
                fuv = [int(w.split("/")[1]) - 1 for w in p]
                raw_faces.append((fv, fuv))
            else:
                s = cube_v_indices.setdefault(cur_group, set())
                for vi in fv:
                    s.add(vi)

with open(os.path.join(MH_DIR, "rigs", "rig.game_engine.json"), "r") as f:
    rig_json = json.load(f)

def eval_rig_point(pt_spec, b_verts):
    strat = pt_spec.get("strategy", "CUBE")
    if strat == "CUBE":
        vlist = list(cube_v_indices.get(pt_spec["cube_name"], []))
    elif strat == "MEAN":
        vlist = pt_spec.get("vertex_indices", [])
    elif strat == "VERTEX":
        vlist = [pt_spec.get("vertex_index", 0)]
    else:
        vlist = []
    if not vlist:
        dp = pt_spec.get("default_position", [0.0, 0.0, 0.0])
        return Vector((dp[0], dp[1], dp[2]))
    acc = Vector((0.0, 0.0, 0.0))
    for vi in vlist:
        acc += b_verts[vi]
    return acc / len(vlist)

with open(os.path.join(MH_DIR, "rigs", "weights.game_engine.json"), "r") as f:
    w_json = json.load(f)

base_v_weights = [{} for _ in range(len(raw_verts))]
for bname, pairs in w_json["weights"].items():
    for vi, w in pairs:
        if vi < len(base_v_weights) and w > 0.0001:
            base_v_weights[vi][bname] = w

for vi in range(len(base_v_weights)):
    tot = sum(base_v_weights[vi].values())
    if tot > 0:
        for k in base_v_weights[vi]:
            base_v_weights[vi][k] /= tot

def load_target(rel_path):
    full_p = os.path.join(MH_DIR, "targets", rel_path)
    offsets = {}
    with gzip.open(full_p, "rt") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            if len(p) == 4:
                offsets[int(p[0])] = (float(p[1]), float(p[2]), float(p[3]))
    return offsets

TARGET_CACHE = {}
def get_target(rel_path):
    if rel_path not in TARGET_CACHE:
        TARGET_CACHE[rel_path] = load_target(rel_path)
    return TARGET_CACHE[rel_path]

# ---------------------------------------------------------------------------
# 3. PARSE .MHCLO & HELPER FUNCTIONS FOR CLOTHING, HAIR, EYES & SHOES
# ---------------------------------------------------------------------------
MHCLO_SKIP_KEYS = (
    "material", "vertexboneweights", "x_scale", "y_scale", "z_scale",
    "max_pole", "z_depth", "uuid", "name", "tag", "obj_file"
)

def parse_mhclo(mhclo_path):
    verts_map = []
    del_verts = set()
    status = None
    with open(mhclo_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("verts"):
                status = "v"
                continue
            if line.startswith("delete_verts"):
                status = "d"
                continue
            if any(line.startswith(k) for k in MHCLO_SKIP_KEYS):
                continue
            if status == "v":
                p = line.split()
                if len(p) == 9:
                    verts_map.append((
                        int(p[0]), int(p[1]), int(p[2]),
                        float(p[3]), float(p[4]), float(p[5]),
                        float(p[6]), float(p[7]), float(p[8])
                    ))
                elif len(p) == 1:
                    vi = int(p[0])
                    verts_map.append((vi, vi, vi, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            elif status == "d":
                for m in re.finditer(r"(\d+)\s*-\s*(\d+)|(\d+)", line):
                    if m.group(1) and m.group(2):
                        for k in range(int(m.group(1)), int(m.group(2)) + 1):
                            del_verts.add(k)
                    elif m.group(3):
                        del_verts.add(int(m.group(3)))
    return verts_map, del_verts

def parse_obj_with_components(obj_path):
    verts = []
    uvs = []
    faces = []
    with open(obj_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("vt "):
                p = line.split()
                uvs.append((float(p[1]), float(p[2])))
            elif line.startswith("f "):
                p = line.split()[1:]
                fv = [int(w.split("/")[0]) - 1 for w in p]
                fuv = [int(w.split("/")[1]) - 1 if "/" in w and w.split("/")[1] else 0 for w in p]
                faces.append((fv, fuv))
    # Connected components for Top/Bottom & inner-sock filtering
    adj = {i: set() for i in range(len(verts))}
    for fv, _ in faces:
        for a in fv:
            for b in fv:
                if a != b:
                    adj[a].add(b)
    visited = set()
    v_comp_info = {}
    for i in range(len(verts)):
        if i not in visited and len(adj[i]) > 0:
            q = [i]
            visited.add(i)
            comp = []
            while q:
                cur = q.pop()
                comp.append(cur)
                for nxt in adj[cur]:
                    if nxt not in visited:
                        visited.add(nxt)
                        q.append(nxt)
            ys = [verts[v][1] for v in comp]
            info = (len(comp), min(ys), max(ys), sum(ys) / len(ys))
            for v in comp:
                v_comp_info[v] = info
    return verts, uvs, faces, v_comp_info

ASSET_CACHE = {}
def load_mh_asset(folder_rel, asset_name):
    key = (folder_rel, asset_name)
    if key not in ASSET_CACHE:
        adir = os.path.join(MH_DIR, folder_rel, asset_name)
        if os.path.isdir(adir):
            mhclo_p = os.path.join(adir, f"{asset_name}.mhclo")
            obj_p = os.path.join(adir, f"{asset_name}.obj")
        else:
            mhclo_p = os.path.join(MH_DIR, folder_rel, f"{asset_name}.mhclo")
            obj_p = os.path.join(MH_DIR, folder_rel, f"{asset_name}.obj")
        vmap, del_v = parse_mhclo(mhclo_p)
        ov, ouv, ofaces, vcomp = parse_obj_with_components(obj_p)
        ASSET_CACHE[key] = (vmap, del_v, ov, ouv, ofaces, vcomp)
    return ASSET_CACHE[key]

# Pre-filter high-poly eyes to keep only opaque inner sclera/iris/pupil faces (skip outer cornea shell)
eye_vmap, _, eye_ov, eye_ouv, eye_ofaces, _ = load_mh_asset("eyes", "high-poly")
eye_img_check = bpy.data.images.load(os.path.join(MH_DIR, "eyes", "blue_eye.png"))
ew, eh = eye_img_check.size
epix = list(eye_img_check.pixels)
eye_inner_faces = []
for fv, fuv in eye_ofaces:
    u = sum(eye_ouv[i][0] for i in fuv) / len(fuv)
    v = sum(eye_ouv[i][1] for i in fuv) / len(fuv)
    px = min(ew - 1, max(0, int(u * ew)))
    py = min(eh - 1, max(0, int(v * eh)))
    if epix[(py * ew + px) * 4 + 3] > 0.5:
        eye_inner_faces.append((fv, fuv))

# ---------------------------------------------------------------------------
# 4. MATERIAL BUILDER (GLTF-COMPATIBLE IMAGE + TINT MULTIPLY)
# ---------------------------------------------------------------------------
IMG_CACHE = {}
def get_bpy_image(abs_path):
    if abs_path not in IMG_CACHE:
        img = bpy.data.images.load(abs_path)
        IMG_CACHE[abs_path] = img
    return IMG_CACHE[abs_path]

MAT_CACHE = {}
def make_textured_mat(mat_name, img_path, tint_rgb=None, roughness=0.65, specular=0.25, alpha_blend=False):
    if mat_name in MAT_CACHE:
        return MAT_CACHE[mat_name]
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    mat.use_backface_culling = False
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular

    tex_node = nt.nodes.new("ShaderNodeTexImage")
    tex_node.image = get_bpy_image(img_path)

    if tint_rgb is not None:
        mix_node = nt.nodes.new("ShaderNodeMix")
        mix_node.data_type = 'RGBA'
        mix_node.blend_type = 'MULTIPLY'
        mix_node.inputs[0].default_value = 1.0
        mix_node.inputs[7].default_value = (tint_rgb[0], tint_rgb[1], tint_rgb[2], 1.0)
        nt.links.new(tex_node.outputs["Color"], mix_node.inputs[6])
        nt.links.new(mix_node.outputs[2], bsdf.inputs["Base Color"])
    else:
        nt.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

    if alpha_blend:
        nt.links.new(tex_node.outputs["Alpha"], bsdf.inputs["Alpha"])
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = 'BLENDED'
        elif hasattr(mat, "blend_method"):
            mat.blend_method = 'HASHED'

    MAT_CACHE[mat_name] = mat
    return mat

# ---------------------------------------------------------------------------
# 5. BONE HIERARCHY & LBS A-POSE RELAXATION
# ---------------------------------------------------------------------------
# Map MakeHuman game_engine 53 bones to clean consistent bone names
BONE_Defs = [
    ("Hips", "pelvis", "spine_01", None),
    ("Spine", "spine_01", "spine_02", "Hips"),
    ("Spine1", "spine_02", "spine_03", "Spine"),
    ("Chest", "spine_03", "neck_01", "Spine1"),
    ("Neck", "neck_01", "head", "Chest"),
    ("Head", "head", None, "Neck"),
    ("Clavicle.L", "clavicle_l", "upperarm_l", "Chest"),
    ("UpperArm.L", "upperarm_l", "lowerarm_l", "Clavicle.L"),
    ("ForeArm.L", "lowerarm_l", "hand_l", "UpperArm.L"),
    ("Hand.L", "hand_l", "middle_01_l", "ForeArm.L"),
    ("Clavicle.R", "clavicle_r", "upperarm_r", "Chest"),
    ("UpperArm.R", "upperarm_r", "lowerarm_r", "Clavicle.R"),
    ("ForeArm.R", "lowerarm_r", "hand_r", "UpperArm.R"),
    ("Hand.R", "hand_r", "middle_01_r", "ForeArm.R"),
    ("UpLeg.L", "thigh_l", "calf_l", "Hips"),
    ("LowLeg.L", "calf_l", "foot_l", "UpLeg.L"),
    ("Foot.L", "foot_l", "ball_l", "LowLeg.L"),
    ("Toe.L", "ball_l", None, "Foot.L"),
    ("UpLeg.R", "thigh_r", "calf_r", "Hips"),
    ("LowLeg.R", "calf_r", "foot_r", "UpLeg.R"),
    ("Foot.R", "foot_r", "ball_r", "LowLeg.R"),
    ("Toe.R", "ball_r", None, "Foot.R"),
]

# Add all 30 finger bones so 5-fingered hands have full skeletal hierarchy
for side_s, side_mh in [(".L", "_l"), (".R", "_r")]:
    for fname in ["thumb", "index", "middle", "ring", "pinky"]:
        b1 = f"{fname}_01{side_mh}"
        b2 = f"{fname}_02{side_mh}"
        b3 = f"{fname}_03{side_mh}"
        BONE_Defs.append((f"{fname.capitalize()}1{side_s}", b1, b2, f"Hand{side_s}"))
        BONE_Defs.append((f"{fname.capitalize()}2{side_s}", b2, b3, f"{fname.capitalize()}1{side_s}"))
        BONE_Defs.append((f"{fname.capitalize()}3{side_s}", b3, None, f"{fname.capitalize()}2{side_s}"))

MH_TO_OUR_BONE = {mh_b: our_b for our_b, mh_b, _, _ in BONE_Defs}

def rot_around(pivot, rx_deg, ry_deg, rz_deg):
    eul = Euler((math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg)), 'XYZ')
    return Matrix.Translation(pivot) @ eul.to_matrix().to_4x4() @ Matrix.Translation(-pivot)

def build_relaxed_transforms(jpos):
    """Computes LBS matrices to relax MakeHuman's A-pose arms & slightly bent elbows into a natural standing rest pose."""
    T = {}
    for side, sgn in [("_l", 1.0), ("_r", -1.0)]:
        sh = jpos[f"upperarm{side}"]
        el = jpos[f"lowerarm{side}"]
        hd = jpos[f"hand{side}"]
        th = jpos[f"thumb_01{side}"]

        # Bring arm down from A-pose (ry = +34° for L, -34° for R)
        T_up = rot_around(sh, 0.0, sgn * 34.0, 0.0)
        # Straighten the 32° pre-bent elbow so rest pose has a relaxed 8° bend
        T_lo = T_up @ rot_around(el, 26.0, -sgn * 6.0, 0.0)
        T_hd = T_lo @ rot_around(hd, 10.0, -sgn * 5.0, 0.0)
        T_th = T_hd @ rot_around(th, 8.0, -sgn * 22.0, sgn * 14.0)

        T[f"upperarm{side}"] = T_up
        T[f"lowerarm{side}"] = T_lo
        T[f"hand{side}"] = T_hd
        T[f"thumb_01{side}"] = T_th
        T[f"thumb_02{side}"] = T_th
        T[f"thumb_03{side}"] = T_th

        for fn in ["index", "middle", "ring", "pinky"]:
            f1 = jpos[f"{fn}_01{side}"]
            f2 = jpos[f"{fn}_02{side}"]
            T_f1 = T_hd @ rot_around(f1, 6.0, -sgn * 8.0, 0.0)
            T_f2 = T_f1 @ rot_around(f2, 8.0, -sgn * 10.0, 0.0)
            T[f"{fn}_01{side}"] = T_f1
            T[f"{fn}_02{side}"] = T_f2
            T[f"{fn}_03{side}"] = T_f2

        # Bring legs from slight A-stance to natural parallel stance
        ul = jpos[f"thigh{side}"]
        T_leg = rot_around(ul, 0.0, sgn * 4.8, 0.0)
        T[f"thigh{side}"] = T_leg
        T[f"calf{side}"] = T_leg
        T[f"foot{side}"] = T_leg
        T[f"ball{side}"] = T_leg

    return T

def apply_lbs_point(pt, wdict, T_map):
    res = Vector((0.0, 0.0, 0.0))
    tot = 0.0
    for bname, w in wdict.items():
        M = T_map.get(bname)
        if M is not None:
            res += w * (M @ pt)
        else:
            res += w * pt
        tot += w
    if tot < 0.999:
        res += (1.0 - tot) * pt
    return res

# ---------------------------------------------------------------------------
# 6. BUILD SINGLE REALISTIC MAKEHUMAN CHARACTER
# ---------------------------------------------------------------------------
def build_character(cfg):
    cid = cfg["id"]
    target_h = cfg["height"]

    # 1. Morph base vertices with target offsets
    m_verts = [list(v) for v in raw_verts]
    for t_rel, weight in cfg["targets"]:
        toff = get_target(t_rel)
        for vi, (dx, dy, dz) in toff.items():
            if vi < len(m_verts):
                m_verts[vi][0] += dx * weight
                m_verts[vi][1] += dy * weight
                m_verts[vi][2] += dz * weight

    # Compute scale so standing height matches target_h (1 Blender unit = 1m)
    body_ys = [m_verts[vi][1] for vi in range(13380)]
    min_y, max_y = min(body_ys), max(body_ys)
    raw_h = max_y - min_y
    sc = target_h / raw_h

    # Convert OBJ coords (x, y_up, z_fwd) to Blender coords (x_left, y_back=-z, z_up=y-min_y)
    b_verts = [Vector((v[0] * sc, -v[2] * sc, (v[1] - min_y) * sc)) for v in m_verts]

    # Joint centers in Blender coordinates from rig.game_engine.json
    jpos = {}
    for bname, bspec in rig_json.items():
        jpos[bname] = eval_rig_point(bspec["head"], b_verts)

    # Relax A-pose via LBS
    T_relax = build_relaxed_transforms(jpos)
    b_verts_relaxed = [apply_lbs_point(b_verts[i], base_v_weights[i], T_relax) for i in range(len(b_verts))]
    jpos_relaxed = {jn: apply_lbs_point(jp, {jn: 1.0}, T_relax) for jn, jp in jpos.items()}

    # Helper to fit any .mhclo asset to morphed b_verts and relax with LBS
    def fit_asset(vmap):
        fitted_v = []
        fitted_w = []
        for (v0, v1, v2, w0, w1, w2, d0, d1, d2) in vmap:
            # Interpolate in morphed OBJ space then convert to Blender space
            ox = w0 * m_verts[v0][0] + w1 * m_verts[v1][0] + w2 * m_verts[v2][0] + d0
            oy = w0 * m_verts[v0][1] + w1 * m_verts[v1][1] + w2 * m_verts[v2][1] + d1
            oz = w0 * m_verts[v0][2] + w1 * m_verts[v1][2] + w2 * m_verts[v2][2] + d2
            pt_b = Vector((ox * sc, -oz * sc, (oy - min_y) * sc))
            w_comb = {}
            for vi, wi in ((v0, w0), (v1, w1), (v2, w2)):
                for bn, bw in base_v_weights[vi].items():
                    w_comb[bn] = w_comb.get(bn, 0.0) + wi * bw
            pt_rel = apply_lbs_point(pt_b, w_comb, T_relax)
            fitted_v.append(pt_rel)
            fitted_w.append(w_comb)
        return fitted_v, fitted_w

    # Load clothing, shoes, hair
    cloth_vmap, cloth_del, cloth_ov, cloth_ouv, cloth_ofaces, cloth_vcomp = load_mh_asset("clothes", cfg["clothes"])
    shoe_vmap, shoe_del, shoe_ov, shoe_ouv, shoe_ofaces, shoe_vcomp = load_mh_asset("clothes", cfg["shoes"])
    hair_vmap, _, hair_ov, hair_ouv, hair_ofaces, _ = load_mh_asset("hair", cfg["hair"])

    # If female_elegantsuit01 is selected, pair its long-sleeve silk blouse top with female_casualsuit01's full-length tailored trousers
    use_hybrid_blouse_trousers = (cfg["clothes"] == "female_elegantsuit01")
    if use_hybrid_blouse_trousers:
        pants_vmap, pants_del, pants_ov, pants_ouv, pants_ofaces, pants_vcomp = load_mh_asset("clothes", "female_casualsuit01")
        safe_cloth_del = {vi for vi in cloth_del if m_verts[vi][1] > 0.2} | {vi for vi in pants_del if m_verts[vi][1] <= 0.8}
    else:
        safe_cloth_del = cloth_del
    safe_shoe_del = {vi for vi in shoe_del if m_verts[vi][1] < -7.35}
    hide_verts = safe_cloth_del | safe_shoe_del

    # Create combined Mesh & Materials
    mesh_data = bpy.data.meshes.new(f"{cid}_MeshData")
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    deform_layer = bm.verts.layers.deform.new()

    our_bone_idx = {our_b: idx for idx, (our_b, _, _, _) in enumerate(BONE_Defs)}

    def add_part_to_bmesh(verts_list, weights_list, uvs_list, faces_list, mat_idx_fn):
        bm_verts_local = []
        for vi, co in enumerate(verts_list):
            bv = bm.verts.new(co)
            dvert = bv[deform_layer]
            for mh_b, w in weights_list[vi].items():
                our_b = MH_TO_OUR_BONE.get(mh_b)
                if our_b is not None and w > 0.001:
                    dvert[our_bone_idx[our_b]] = w
            bm_verts_local.append(bv)

        for fv, fuv in faces_list:
            m_idx = mat_idx_fn(fv, fuv)
            if m_idx is None:
                continue
            try:
                f_verts = [bm_verts_local[i] for i in fv]
                if len(set(f_verts)) < 3:
                    continue
                bf = bm.faces.new(f_verts)
                bf.material_index = m_idx
                bf.smooth = True
                for loop, uvi in zip(bf.loops, fuv):
                    loop[uv_layer].uv = uvs_list[uvi]
            except ValueError:
                pass

    # Materials list for this character:
    # 0: Skin, 1: Eye, 2: Hair, 3: Cloth_Top, 4: Cloth_Bottom, 5: Shoes
    mat_skin = make_textured_mat(
        f"Mat_Skin_{cid}",
        os.path.join(PREP_TEX_DIR, cfg["skin"]),
        tint_rgb=cfg.get("skin_tint"),
        roughness=0.58, specular=0.22
    )
    mat_eye = make_textured_mat(
        f"Mat_Eye_{cfg['eye']}",
        os.path.join(MH_DIR, "eyes", cfg["eye"]),
        roughness=0.06, specular=0.55
    )
    mat_hair = make_textured_mat(
        f"Mat_Hair_{cfg['hair_color_name']}",
        os.path.join(PREP_TEX_DIR, "hair_universal_strand.jpg"),
        tint_rgb=cfg["hair_rgb"],
        roughness=0.52, specular=0.30
    )

    if cfg.get("cloth_custom_jpg"):
        mat_top = make_textured_mat(
            f"Mat_Suit_{cfg['cloth_custom_jpg']}",
            os.path.join(PREP_TEX_DIR, cfg["cloth_custom_jpg"]),
            roughness=0.68, specular=0.18
        )
        mat_bot = mat_top
    else:
        mat_top = make_textured_mat(
            f"Mat_Top_{cid}",
            os.path.join(PREP_TEX_DIR, "cloth_universal_weave.jpg"),
            tint_rgb=cfg["top_rgb"],
            roughness=0.68, specular=0.18
        )
        mat_bot = make_textured_mat(
            f"Mat_Bot_{cid}",
            os.path.join(PREP_TEX_DIR, "cloth_universal_weave.jpg"),
            tint_rgb=cfg["bot_rgb"],
            roughness=0.72, specular=0.15
        )

    mat_shoe = make_textured_mat(
        f"Mat_Shoe_{cfg['shoes']}_{cfg.get('shoe_tint_name', 'std')}",
        os.path.join(PREP_TEX_DIR, f"{cfg['shoes']}_diffuse.jpg"),
        tint_rgb=cfg.get("shoe_rgb"),
        roughness=0.38, specular=0.42
    )

    for m in (mat_skin, mat_eye, mat_hair, mat_top, mat_bot, mat_shoe):
        mesh_data.materials.append(m)

    # 1. Add visible body skin faces (excluding faces hidden under clothes/shoes)
    body_faces_vis = [(fv, fuv) for (fv, fuv) in raw_faces if not all(v in hide_verts for v in fv)]
    add_part_to_bmesh(b_verts_relaxed[:13380], base_v_weights[:13380], raw_uvs, body_faces_vis, lambda fv, fuv: 0)

    # 2. Add high-poly eyes (opaque sclera/iris/pupil faces)
    eye_v, eye_w = fit_asset(eye_vmap)
    add_part_to_bmesh(eye_v, eye_w, eye_ouv, eye_inner_faces, lambda fv, fuv: 1)

    # 3. Add 3D hair
    hair_v, hair_w = fit_asset(hair_vmap)
    add_part_to_bmesh(hair_v, hair_w, hair_ouv, hair_ofaces, lambda fv, fuv: 2)

    # 4. Add clothing (split Top vs Bottom by component avg_y or vertex height in OBJ)
    cloth_v, cloth_w = fit_asset(cloth_vmap)
    if use_hybrid_blouse_trousers:
        # Add only the silk blouse top from female_elegantsuit01
        add_part_to_bmesh(
            cloth_v, cloth_w, cloth_ouv, cloth_ofaces,
            lambda fv, fuv: 3 if cloth_vcomp.get(fv[0], (0,0,0,1))[3] > 0.05 else None
        )
        # Add the full-length tailored trousers bottom from female_casualsuit01
        pants_v, pants_w = fit_asset(pants_vmap)
        add_part_to_bmesh(
            pants_v, pants_w, pants_ouv, pants_ofaces,
            lambda fv, fuv: 4 if pants_vcomp.get(fv[0], (0,0,0,-1))[3] <= 0.05 else None
        )
    else:
        def cloth_mat_selector(fv, fuv):
            c_info = cloth_vcomp.get(fv[0])
            if c_info and c_info[0] < 6000:
                return 3 if c_info[3] > 0.05 else 4
            avg_oy = sum(cloth_ov[v][1] for v in fv) / len(fv)
            return 3 if avg_oy > 0.65 else 4

        add_part_to_bmesh(cloth_v, cloth_w, cloth_ouv, cloth_ofaces, cloth_mat_selector)

    # 5. Add shoes (always skip the 144-vert high-ankle white sock tube so shoes look sleek and never poke through pants)
    shoe_v, shoe_w = fit_asset(shoe_vmap)
    def shoe_mat_selector(fv, fuv):
        c_info = shoe_vcomp.get(fv[0])
        if c_info and c_info[0] == 144 and c_info[2] > -6.5:
            return None
        return 5

    add_part_to_bmesh(shoe_v, shoe_w, shoe_ouv, shoe_ofaces, shoe_mat_selector)

    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update()

    # Build Armature with our 53 bones using uniform vertical rest orientation (tail = head + (0, 0, L), roll = 0)
    arm_data = bpy.data.armatures.new(f"{cid}_ArmData")
    arm_obj = bpy.data.objects.new(cid, arm_data)
    npc_col.objects.link(arm_obj)

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    for our_b, mh_b, child_mh, parent_our in BONE_Defs:
        eb = arm_data.edit_bones.new(our_b)
        hd = jpos_relaxed[mh_b]
        if child_mh and child_mh in jpos_relaxed:
            blen = max(0.025, (jpos_relaxed[child_mh] - hd).length)
        else:
            blen = 0.05 * (target_h / 1.75)
        eb.head = hd
        eb.tail = hd + Vector((0.0, 0.0, blen))
        eb.roll = 0.0
        if parent_our and parent_our in arm_data.edit_bones:
            eb.parent = arm_data.edit_bones[parent_our]
            eb.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')

    mesh_obj = bpy.data.objects.new(f"{cid}_Mesh", mesh_data)
    npc_col.objects.link(mesh_obj)
    for our_b, _, _, _ in BONE_Defs:
        mesh_obj.vertex_groups.new(name=our_b)

    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    return arm_obj, mesh_obj

# ---------------------------------------------------------------------------
# 7. DEFINE ALL 15 EUROPEAN CHARACTERS (5 MEN, 5 WOMEN, 5 KIDS AGES 3-5)
# ---------------------------------------------------------------------------
CHARACTER_CONFIGS = [
    # --- 5 ADULT MEN (1.78m - 1.86m) ---
    {
        "id": "NPC_Man_01", "arch": "Man", "height": 1.82,
        "targets": [("caucasian-male-young.target.gz", 0.85), ("universal-male-young-maxmuscle-averageweight.target.gz", 0.22)],
        "skin": "young_lightskinned_male_diffuse.jpg", "eye": "blue_eye.png",
        "hair": "short02", "hair_color_name": "GoldenBlonde", "hair_rgb": (0.86, 0.72, 0.48),
        "clothes": "male_elegantsuit01", "cloth_custom_jpg": "male_elegantsuit01_navy.jpg",
        "shoes": "shoes01"
    },
    {
        "id": "NPC_Man_02", "arch": "Man", "height": 1.85,
        "targets": [("caucasian-male-young.target.gz", 0.60), ("caucasian-male-old.target.gz", 0.35), ("universal-male-young-maxmuscle-averageweight.target.gz", 0.25)],
        "skin": "middleage_lightskinned_male_diffuse.jpg", "eye": "green_eye.png",
        "hair": "short04", "hair_color_name": "Espresso", "hair_rgb": (0.24, 0.18, 0.14),
        "clothes": "male_elegantsuit01", "cloth_custom_jpg": "male_elegantsuit01_cream.jpg",
        "shoes": "shoes06"
    },
    {
        "id": "NPC_Man_03", "arch": "Man", "height": 1.79,
        "targets": [("caucasian-male-young.target.gz", 0.95), ("universal-male-young-maxmuscle-averageweight.target.gz", 0.18)],
        "skin": "young_lightskinned_male_diffuse2.jpg", "eye": "brownlight_eye.png",
        "hair": "short01", "hair_color_name": "Chestnut", "hair_rgb": (0.42, 0.28, 0.18),
        "clothes": "male_casualsuit01", "top_rgb": (0.68, 0.82, 0.95), "bot_rgb": (0.82, 0.76, 0.65),
        "shoes": "shoes05"
    },
    {
        "id": "NPC_Man_04", "arch": "Man", "height": 1.86,
        "targets": [("caucasian-male-old.target.gz", 0.55), ("caucasian-male-young.target.gz", 0.45), ("universal-male-young-maxmuscle-averageweight.target.gz", 0.20)],
        "skin": "middleage_lightskinned_male_diffuse.jpg", "eye": "grey_eye.png",
        "hair": "short02", "hair_color_name": "SilverGrey", "hair_rgb": (0.78, 0.79, 0.82),
        "clothes": "male_elegantsuit01", "cloth_custom_jpg": "male_elegantsuit01_charcoal.jpg",
        "shoes": "shoes01"
    },
    {
        "id": "NPC_Man_05", "arch": "Man", "height": 1.80,
        "targets": [("caucasian-male-young.target.gz", 0.90), ("universal-male-young-maxmuscle-averageweight.target.gz", 0.28)],
        "skin": "young_lightskinned_male_diffuse.jpg", "eye": "blue_eye.png",
        "hair": "short04", "hair_color_name": "WarmAuburn", "hair_rgb": (0.52, 0.32, 0.20),
        "clothes": "male_casualsuit05", "top_rgb": (0.22, 0.32, 0.48), "bot_rgb": (0.86, 0.82, 0.74),
        "shoes": "shoes06"
    },

    # --- 5 ADULT WOMEN (1.65m - 1.74m) ---
    {
        "id": "NPC_Woman_01", "arch": "Woman", "height": 1.69,
        "targets": [("caucasian-female-young.target.gz", 0.95)],
        "skin": "young_lightskinned_female_diffuse.jpg", "eye": "blue_eye.png",
        "hair": "long01", "hair_color_name": "GoldenBlonde", "hair_rgb": (0.88, 0.75, 0.50),
        "clothes": "female_elegantsuit01", "top_rgb": (0.20, 0.58, 0.48), "bot_rgb": (0.92, 0.88, 0.82),
        "shoes": "shoes02"
    },
    {
        "id": "NPC_Woman_02", "arch": "Woman", "height": 1.66,
        "targets": [("caucasian-female-young.target.gz", 0.80), ("caucasian-female-old.target.gz", 0.20)],
        "skin": "young_lightskinned_female_diffuse.jpg", "skin_tint": (0.98, 0.95, 0.92), "eye": "green_eye.png",
        "hair": "braid01", "hair_color_name": "Chestnut", "hair_rgb": (0.48, 0.30, 0.18),
        "clothes": "female_casualsuit01", "top_rgb": (0.95, 0.88, 0.80), "bot_rgb": (0.58, 0.18, 0.24),
        "shoes": "shoes04"
    },
    {
        "id": "NPC_Woman_03", "arch": "Woman", "height": 1.73,
        "targets": [("caucasian-female-young.target.gz", 0.92)],
        "skin": "young_lightskinned_female_diffuse.jpg", "eye": "brownlight_eye.png",
        "hair": "ponytail01", "hair_color_name": "CopperAuburn", "hair_rgb": (0.64, 0.34, 0.20),
        "clothes": "female_casualsuit01", "top_rgb": (0.90, 0.44, 0.42), "bot_rgb": (0.92, 0.90, 0.86),
        "shoes": "shoes02"
    },
    {
        "id": "NPC_Woman_04", "arch": "Woman", "height": 1.68,
        "targets": [("caucasian-female-old.target.gz", 0.40), ("caucasian-female-young.target.gz", 0.60)],
        "skin": "middleage_lightskinned_female_diffuse.jpg", "eye": "blue_eye.png",
        "hair": "long01", "hair_color_name": "HoneyBlonde", "hair_rgb": (0.82, 0.66, 0.42),
        "clothes": "female_elegantsuit01", "top_rgb": (0.24, 0.36, 0.62), "bot_rgb": (0.18, 0.26, 0.46),
        "shoes": "shoes02"
    },
    {
        "id": "NPC_Woman_05", "arch": "Woman", "height": 1.71,
        "targets": [("caucasian-female-young.target.gz", 1.0)],
        "skin": "young_lightskinned_female_diffuse.jpg", "skin_tint": (1.0, 0.96, 0.94), "eye": "green_eye.png",
        "hair": "braid01", "hair_color_name": "DarkBrown", "hair_rgb": (0.28, 0.20, 0.15),
        "clothes": "female_casualsuit01", "top_rgb": (0.78, 0.66, 0.88), "bot_rgb": (0.22, 0.28, 0.42),
        "shoes": "shoes04"
    },

    # --- 5 CHILDREN AGES 3-5 (2 TODDLERS 3YO + 3 KIDS 4-5YO) ---
    {
        "id": "NPC_Kid_01", "arch": "Kid3", "height": 0.98,
        "targets": [("caucasian-male-child.target.gz", 0.65), ("caucasian-male-baby.target.gz", 0.35)],
        "skin": "young_lightskinned_male_diffuse.jpg", "eye": "blue_eye.png",
        "hair": "short02", "hair_color_name": "GoldenBlonde", "hair_rgb": (0.90, 0.78, 0.52),
        "clothes": "male_casualsuit03", "top_rgb": (0.96, 0.82, 0.30), "bot_rgb": (0.32, 0.54, 0.82),
        "shoes": "shoes03"
    },
    {
        "id": "NPC_Kid_02", "arch": "Kid3", "height": 1.00,
        "targets": [("caucasian-female-child.target.gz", 0.65), ("caucasian-female-baby.target.gz", 0.35)],
        "skin": "young_lightskinned_female_diffuse.jpg", "eye": "green_eye.png",
        "hair": "ponytail01", "hair_color_name": "HoneyBlonde", "hair_rgb": (0.86, 0.70, 0.45),
        "clothes": "female_casualsuit01", "top_rgb": (0.96, 0.58, 0.70), "bot_rgb": (0.94, 0.90, 0.84),
        "shoes": "shoes04"
    },
    {
        "id": "NPC_Kid_03", "arch": "Kid45", "height": 1.09,
        "targets": [("caucasian-male-child.target.gz", 0.88), ("caucasian-male-baby.target.gz", 0.12)],
        "skin": "young_lightskinned_male_diffuse2.jpg", "eye": "brownlight_eye.png",
        "hair": "short01", "hair_color_name": "Chestnut", "hair_rgb": (0.46, 0.30, 0.20),
        "clothes": "male_casualsuit06", "top_rgb": (0.36, 0.78, 0.68), "bot_rgb": (0.20, 0.28, 0.46),
        "shoes": "shoes05"
    },
    {
        "id": "NPC_Kid_04", "arch": "Kid45", "height": 1.12,
        "targets": [("caucasian-female-child.target.gz", 0.95)],
        "skin": "young_lightskinned_female_diffuse.jpg", "eye": "blue_eye.png",
        "hair": "ponytail01", "hair_color_name": "GoldenBlonde", "hair_rgb": (0.88, 0.75, 0.50),
        "clothes": "female_elegantsuit01", "top_rgb": (0.96, 0.64, 0.52), "bot_rgb": (0.94, 0.92, 0.88),
        "shoes": "shoes04"
    },
    {
        "id": "NPC_Kid_05", "arch": "Kid45", "height": 1.14,
        "targets": [("caucasian-male-child.target.gz", 0.95)],
        "skin": "young_lightskinned_male_diffuse.jpg", "eye": "blue_eye.png",
        "hair": "short04", "hair_color_name": "DarkBrown", "hair_rgb": (0.28, 0.20, 0.15),
        "clothes": "male_casualsuit03", "top_rgb": (0.88, 0.28, 0.30), "bot_rgb": (0.80, 0.72, 0.58),
        "shoes": "shoes03"
    },
]

# ---------------------------------------------------------------------------
# 8. ARCHETYPE ANIMATION GENERATOR
# ---------------------------------------------------------------------------
# Remember verified Bone Local Axes for vertical bones (tail = head + (0,0,L), roll = 0):
# - Hips.location = (dx, dy_vert, dz_fwd) where index 1 (Y) is Vertical Up/Down and index 2 (Z) is Forward/Back!
# - Downward limbs (UpLeg, LowLeg, UpperArm, ForeArm): rx < 0 swings FORWARD, rx > 0 swings BACKWARD.
# - Upward spine/head (Hips, Spine, Chest, Neck, Head): rx > 0 leans FORWARD, rx < 0 leans BACKWARD, ry twists Left/Right.

ANIM_BONES = [
    "Hips", "Spine", "Chest", "Neck", "Head",
    "UpperArm.L", "ForeArm.L", "Hand.L",
    "UpperArm.R", "ForeArm.R", "Hand.R",
    "UpLeg.L", "LowLeg.L", "Foot.L",
    "UpLeg.R", "LowLeg.R", "Foot.R"
]

SEAT_HIP_DY = {
    "Man": -0.43,
    "Woman": -0.35,
    "Kid45": -0.05,
    "Kid3": 0.01,
}

def reset_pose(arm_obj):
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)

def key_pose(arm_obj, frame, hip_loc, rot_dict):
    reset_pose(arm_obj)
    pb_hips = arm_obj.pose.bones["Hips"]
    pb_hips.location = hip_loc
    pb_hips.keyframe_insert(data_path="location", frame=frame)
    for bname in ANIM_BONES:
        pb = arm_obj.pose.bones[bname]
        r = rot_dict.get(bname, (0.0, 0.0, 0.0))
        pb.rotation_euler = Euler(r, 'XYZ')
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)

def set_linear_or_bezier(action):
    try:
        for fc in action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
    except Exception:
        pass

def push_to_nla(arm_obj, action):
    if not arm_obj.animation_data:
        arm_obj.animation_data_create()
    track = arm_obj.animation_data.nla_tracks.new()
    track.name = action.name
    strip = track.strips.new(action.name, int(action.frame_range[0]), action)
    strip.name = action.name
    track.mute = False

def create_archetype_actions(arm_obj, arch):
    if not arm_obj.animation_data:
        arm_obj.animation_data_create()
    s_dy = SEAT_HIP_DY[arch]
    is_kid = arch in ("Kid45", "Kid3")

    # 1. Walk_Cycle_{arch} (Frames 1..25, looping)
    act_walk = bpy.data.actions.new(name=f"Walk_Cycle_{arch}")
    arm_obj.animation_data.action = act_walk
    for f, ph in [(1, 0.0), (7, 0.5 * math.pi), (13, math.pi), (19, 1.5 * math.pi), (25, 2.0 * math.pi)]:
        s = math.sin(ph)
        c = math.cos(ph)
        bob = abs(c) * (0.018 if not is_kid else 0.012)
        sway = s * 0.012
        ul_l = -0.42 * s
        ul_r = 0.42 * s
        ll_l = max(0.05, 0.58 * c + 0.25) if s < 0 else 0.10
        ll_r = max(0.05, -0.58 * c + 0.25) if s > 0 else 0.10
        key_pose(arm_obj, f, (sway, bob, 0.0), {
            "Spine": (0.04, -0.06 * s, 0.0),
            "Chest": (0.02, -0.08 * s, 0.0),
            "Head": (0.0, 0.04 * s, 0.0),
            "UpperArm.L": (0.28 * s, 0.0, 0.0),
            "ForeArm.L": (-0.25 - 0.10 * max(0.0, -s), 0.0, 0.0),
            "UpperArm.R": (-0.28 * s, 0.0, 0.0),
            "ForeArm.R": (-0.25 - 0.10 * max(0.0, s), 0.0, 0.0),
            "UpLeg.L": (ul_l, 0.0, 0.0),
            "LowLeg.L": (ll_l, 0.0, 0.0),
            "Foot.L": (-0.15 * s, 0.0, 0.0),
            "UpLeg.R": (ul_r, 0.0, 0.0),
            "LowLeg.R": (ll_r, 0.0, 0.0),
            "Foot.R": (0.15 * s, 0.0, 0.0),
        })
    set_linear_or_bezier(act_walk)
    push_to_nla(arm_obj, act_walk)

    # Seated base pose dictionary
    leg_bend = -1.46 if not is_kid else -1.42
    knee_bend = 1.46 if not is_kid else 1.32
    seated_base = {
        "Spine": (0.05, 0.0, 0.0),
        "Chest": (0.04, 0.0, 0.0),
        "Neck": (0.02, 0.0, 0.0),
        "Head": (-0.04, 0.0, 0.0),
        "UpperArm.L": (-0.24, 0.0, 0.04),
        "ForeArm.L": (-0.72, 0.26, 0.0),
        "Hand.L": (0.08, 0.0, 0.0),
        "UpperArm.R": (-0.24, 0.0, -0.04),
        "ForeArm.R": (-0.72, -0.26, 0.0),
        "Hand.R": (0.08, 0.0, 0.0),
        "UpLeg.L": (leg_bend, -0.05, 0.0),
        "LowLeg.L": (knee_bend, 0.0, 0.0),
        "Foot.L": (0.0, 0.0, 0.0),
        "UpLeg.R": (leg_bend, 0.05, 0.0),
        "LowLeg.R": (knee_bend, 0.0, 0.0),
        "Foot.R": (0.0, 0.0, 0.0),
    }

    # 2. Sit_{arch} (Frames 1..55)
    act_sit = bpy.data.actions.new(name=f"Sit_{arch}")
    arm_obj.animation_data.action = act_sit
    if arch in ("Man", "Woman"):
        # Frame 1: Arrive behind chair (dz_fwd = -0.32)
        key_pose(arm_obj, 1, (0.0, 0.0, -0.32), {})
        # Frame 12: Reach hands forward to grasp backrest
        key_pose(arm_obj, 12, (0.0, -0.02, -0.34), {
            "Spine": (0.14, 0.0, 0.0), "Chest": (0.10, 0.0, 0.0),
            "UpperArm.L": (-0.58, 0.0, 0.0), "ForeArm.L": (-0.42, 0.15, 0.0),
            "UpperArm.R": (-0.58, 0.0, 0.0), "ForeArm.R": (-0.42, -0.15, 0.0),
            "UpLeg.L": (-0.10, 0.0, 0.0), "LowLeg.L": (0.18, 0.0, 0.0),
        })
        # Frame 22: Pull chair backward (dz_fwd = -0.46)
        key_pose(arm_obj, 22, (0.0, -0.03, -0.46), {
            "Spine": (0.12, 0.0, 0.0), "Chest": (0.08, 0.0, 0.0),
            "UpperArm.L": (-0.48, 0.0, 0.0), "ForeArm.L": (-0.50, 0.15, 0.0),
            "UpperArm.R": (-0.48, 0.0, 0.0), "ForeArm.R": (-0.50, -0.15, 0.0),
            "UpLeg.R": (-0.22, 0.0, 0.0), "LowLeg.R": (0.35, 0.0, 0.0),
        })
        # Frame 34: Step into gap in front of cushion (dz_fwd = -0.10)
        key_pose(arm_obj, 34, (0.0, -0.08, -0.10), {
            "Spine": (0.18, 0.0, 0.0), "Chest": (0.10, 0.0, 0.0),
            "UpperArm.L": (-0.32, 0.0, 0.0), "ForeArm.L": (-0.55, 0.20, 0.0),
            "UpperArm.R": (-0.32, 0.0, 0.0), "ForeArm.R": (-0.55, -0.20, 0.0),
            "UpLeg.L": (-0.55, 0.0, 0.0), "LowLeg.L": (0.65, 0.0, 0.0),
            "UpLeg.R": (-0.45, 0.0, 0.0), "LowLeg.R": (0.55, 0.0, 0.0),
        })
        # Frame 45: Lower onto seat & scoot chair forward
        key_pose(arm_obj, 45, (0.0, s_dy * 0.95, -0.04), {
            **seated_base,
            "Spine": (0.14, 0.0, 0.0),
            "UpperArm.L": (-0.35, 0.0, 0.05), "ForeArm.L": (-0.65, 0.20, 0.0),
            "UpperArm.R": (-0.35, 0.0, -0.05), "ForeArm.R": (-0.65, -0.20, 0.0),
        })
        # Frame 55: Settled in comfortable dining pose
        key_pose(arm_obj, 55, (0.0, s_dy, 0.0), seated_base)
    elif arch == "Kid45":
        # Boost_Hop_Sit_4_5yo: Brace hands on chair edge and hop up onto cushion
        key_pose(arm_obj, 1, (0.0, 0.0, -0.22), {})
        key_pose(arm_obj, 14, (0.0, -0.06, -0.16), {
            "Spine": (0.25, 0.0, 0.0), "Chest": (0.15, 0.0, 0.0),
            "UpperArm.L": (-0.65, 0.0, 0.10), "ForeArm.L": (-0.35, 0.15, 0.0),
            "UpperArm.R": (-0.65, 0.0, -0.10), "ForeArm.R": (-0.35, -0.15, 0.0),
            "UpLeg.L": (-0.45, 0.0, 0.0), "LowLeg.L": (0.75, 0.0, 0.0),
            "UpLeg.R": (-0.45, 0.0, 0.0), "LowLeg.R": (0.75, 0.0, 0.0),
        })
        key_pose(arm_obj, 28, (0.0, 0.07, -0.04), {
            "Spine": (0.18, 0.0, 0.0),
            "UpperArm.L": (-0.30, 0.0, 0.12), "ForeArm.L": (-0.45, 0.20, 0.0),
            "UpperArm.R": (-0.30, 0.0, -0.12), "ForeArm.R": (-0.45, -0.20, 0.0),
            "UpLeg.L": (-1.25, 0.0, 0.0), "LowLeg.L": (1.45, 0.0, 0.0),
            "UpLeg.R": (-1.25, 0.0, 0.0), "LowLeg.R": (1.45, 0.0, 0.0),
        })
        key_pose(arm_obj, 42, (0.0, s_dy + 0.02, 0.0), seated_base)
        key_pose(arm_obj, 55, (0.0, s_dy, 0.0), seated_base)
    else:
        # Climb_Crawl_Onto_Chair_3yo: Climb onto cushion with hands & knees, turn around, sit
        key_pose(arm_obj, 1, (0.0, 0.0, -0.24), {"Hips": (0.0, 0.85, 0.0)})
        key_pose(arm_obj, 16, (0.0, -0.02, -0.14), {
            "Hips": (0.0, 1.15, 0.0), "Spine": (0.45, 0.0, 0.0), "Chest": (0.25, 0.0, 0.0),
            "UpperArm.L": (-1.05, 0.0, 0.0), "ForeArm.L": (-0.35, 0.0, 0.0),
            "UpperArm.R": (-1.05, 0.0, 0.0), "ForeArm.R": (-0.35, 0.0, 0.0),
            "UpLeg.L": (-1.35, 0.0, 0.0), "LowLeg.L": (1.55, 0.0, 0.0),
            "UpLeg.R": (-0.75, 0.0, 0.0), "LowLeg.R": (0.95, 0.0, 0.0),
        })
        key_pose(arm_obj, 32, (0.0, 0.06, -0.04), {
            "Hips": (0.0, 0.55, 0.0), "Spine": (0.35, 0.0, 0.0),
            "UpperArm.L": (-0.75, 0.0, 0.0), "ForeArm.L": (-0.55, 0.0, 0.0),
            "UpperArm.R": (-0.75, 0.0, 0.0), "ForeArm.R": (-0.55, 0.0, 0.0),
            "UpLeg.L": (-1.40, 0.0, 0.0), "LowLeg.L": (1.50, 0.0, 0.0),
            "UpLeg.R": (-1.40, 0.0, 0.0), "LowLeg.R": (1.50, 0.0, 0.0),
        })
        key_pose(arm_obj, 45, (0.0, s_dy + 0.02, 0.0), {
            **seated_base, "Hips": (0.0, 0.12, 0.0)
        })
        key_pose(arm_obj, 55, (0.0, s_dy, 0.0), seated_base)

    set_linear_or_bezier(act_sit)
    push_to_nla(arm_obj, act_sit)

    # 3. Idle_A_{arch} & Idle_B_{arch} (Frames 1..96, natural seated conversation + leg swings for kids)
    for var_idx, var_name in enumerate(["A", "B"]):
        act_idle = bpy.data.actions.new(name=f"Idle_{var_name}_{arch}")
        arm_obj.animation_data.action = act_idle
        sgn = 1.0 if var_idx == 0 else -1.0
        for f, ph in [(1, 0.0), (25, 0.5 * math.pi), (49, math.pi), (73, 1.5 * math.pi), (96, 2.0 * math.pi)]:
            s = math.sin(ph)
            c = math.cos(ph)
            pose = dict(seated_base)
            pose["Spine"] = (0.05 + 0.03 * s, 0.05 * s * sgn, 0.0)
            pose["Chest"] = (0.04 + 0.03 * c, 0.09 * s * sgn, 0.02 * c)
            pose["Neck"] = (0.02 + 0.04 * s, 0.12 * s * sgn, 0.0)
            pose["Head"] = (-0.04 + 0.06 * math.sin(ph * 2.0), 0.18 * s * sgn + 0.06 * c, 0.04 * s)
            pose["UpperArm.L"] = (-0.24 - 0.10 * max(0.0, s * sgn), 0.0, 0.04)
            pose["ForeArm.L"] = (-0.72 - 0.18 * max(0.0, s * sgn), 0.26 - 0.10 * s, 0.0)
            pose["Hand.L"] = (0.08 + 0.12 * s, 0.15 * c, 0.0)
            pose["UpperArm.R"] = (-0.24 - 0.10 * max(0.0, -s * sgn), 0.0, -0.04)
            pose["ForeArm.R"] = (-0.72 - 0.18 * max(0.0, -s * sgn), -0.26 + 0.10 * c, 0.0)
            pose["Hand.R"] = (0.08 - 0.12 * c, -0.15 * s, 0.0)
            if is_kid:
                # Cheerful dangling leg swing for children
                pose["LowLeg.L"] = (knee_bend + 0.22 * math.sin(ph * 2.0), 0.0, 0.0)
                pose["LowLeg.R"] = (knee_bend - 0.22 * math.sin(ph * 2.0), 0.0, 0.0)
            key_pose(arm_obj, f, (0.0, s_dy, 0.0), pose)
        set_linear_or_bezier(act_idle)
        push_to_nla(arm_obj, act_idle)

    # 4. Exit_A_{arch} & Exit_B_{arch} (Frames 1..48: Stand up, step out, tidy chair)
    for var_idx, var_name in enumerate(["A", "B"]):
        act_exit = bpy.data.actions.new(name=f"Exit_{var_name}_{arch}")
        arm_obj.animation_data.action = act_exit
        turn_sgn = 1.0 if var_idx == 0 else -1.0
        key_pose(arm_obj, 1, (0.0, s_dy, 0.0), seated_base)
        key_pose(arm_obj, 14, (0.0, s_dy * 0.65, -0.08), {
            **seated_base,
            "Spine": (0.22, 0.0, 0.0), "Chest": (0.14, 0.0, 0.0),
            "UpLeg.L": (-0.85, 0.0, 0.0), "LowLeg.L": (0.95, 0.0, 0.0),
            "UpLeg.R": (-0.85, 0.0, 0.0), "LowLeg.R": (0.95, 0.0, 0.0),
        })
        key_pose(arm_obj, 28, (0.0, 0.0, -0.34), {
            "Hips": (0.0, 0.15 * turn_sgn, 0.0),
            "Spine": (0.10, 0.0, 0.0),
            "UpperArm.L": (-0.42, 0.0, 0.0), "ForeArm.L": (-0.45, 0.15, 0.0),
            "UpperArm.R": (-0.42, 0.0, 0.0), "ForeArm.R": (-0.45, -0.15, 0.0),
        })
        key_pose(arm_obj, 38, (0.0, -0.02, -0.28), {
            "Spine": (0.12, 0.0, 0.0),
            "UpperArm.L": (-0.52, 0.0, 0.0), "ForeArm.L": (-0.35, 0.12, 0.0),
            "UpperArm.R": (-0.52, 0.0, 0.0), "ForeArm.R": (-0.35, -0.12, 0.0),
        })
        key_pose(arm_obj, 48, (0.0, 0.0, -0.32), {})
        set_linear_or_bezier(act_exit)
        push_to_nla(arm_obj, act_exit)

    arm_obj.animation_data.action = None
    reset_pose(arm_obj)

# ---------------------------------------------------------------------------
# 9. BUILD ALL 15 NPCS, BAKE ARCHETYPE ANIMATIONS & EXPORT .BLEND + .GLB
# ---------------------------------------------------------------------------
built_arms = []
built_ARCHS = set()

for idx, cfg in enumerate(CHARACTER_CONFIGS):
    arm_obj, mesh_obj = build_character(cfg)
    arch = cfg["arch"]
    if arch not in built_ARCHS:
        create_archetype_actions(arm_obj, arch)
        built_ARCHS.add(arch)
    else:
        # Link existing archetype actions as NLA tracks so any character can preview them in Blender
        for act_prefix in ["Walk_Cycle", "Sit", "Idle_A", "Idle_B", "Exit_A", "Exit_B"]:
            act = bpy.data.actions.get(f"{act_prefix}_{arch}")
            if act:
                push_to_nla(arm_obj, act)
        reset_pose(arm_obj)

    # Arrange neatly in 2 rows for Blender inspection & preview render, then reset to (0,0,0) before GLB export
    built_arms.append((arm_obj, cfg))

# Arrange in two staggered showcase rows for our visual verification render
# Back row (8 adults): standing pose (use_nla = False); Front row (2 women + 5 kids): seated pose (use_nla = True)
for idx, (arm_obj, cfg) in enumerate(built_arms):
    if idx < 8:
        if arm_obj.animation_data:
            arm_obj.animation_data.use_nla = False
        reset_pose(arm_obj)
        arm_obj.location = ((idx - 3.5) * 0.72, 0.0, 0.0)
        pb = arm_obj.pose.bones
        pb["Head"].rotation_euler = (0.0, math.radians((idx % 3 - 1) * 8.0), 0.0)
        pb["ForeArm.L"].rotation_euler = (math.radians(-18.0), math.radians(10.0), 0.0)
        pb["ForeArm.R"].rotation_euler = (math.radians(-18.0), math.radians(-10.0), 0.0)
    else:
        if arm_obj.animation_data:
            arm_obj.animation_data.use_nla = True
            for trk in arm_obj.animation_data.nla_tracks:
                trk.mute = False
        arm_obj.location = ((idx - 11.0) * 0.72, -1.15, 0.0)

# Set up camera & render preview
cam_d = bpy.data.cameras.new("Preview_Cam")
cam_d.lens = 38.0
cam_o = bpy.data.objects.new("Preview_Cam", cam_d)
scene.collection.objects.link(cam_o)
cam_o.location = (0.0, -5.2, 1.45)
cam_o.rotation_euler = (math.radians(82.0), 0.0, 0.0)
scene.camera = cam_o

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.filepath = PREVIEW_OUT
bpy.ops.render.render(write_still=True)

# Reset all 15 armatures to origin (0,0,0), enable NLA tracks, and reset pose before exporting GLB
for arm_obj, _ in built_arms:
    arm_obj.location = (0.0, 0.0, 0.0)
    reset_pose(arm_obj)
    if arm_obj.animation_data:
        arm_obj.animation_data.use_nla = True
        for trk in arm_obj.animation_data.nla_tracks:
            trk.mute = False

# Remove temporary preview camera & lights before exporting GLB, then keep lights in .blend for Material Preview / Rendered inspection
for obj in list(light_col.objects):
    obj.hide_render = False
cam_o.select_set(False)

# Select only the 15 NPC armatures and meshes for GLB export
bpy.ops.object.select_all(action='DESELECT')
for arm_obj, _ in built_arms:
    arm_obj.select_set(True)
    for ch in arm_obj.children:
        ch.select_set(True)

bpy.ops.export_scene.gltf(
    filepath=GLB_OUT,
    use_selection=True,
    export_format='GLB',
    export_yup=True,
    export_skins=True,
    export_all_influences=False,
    export_morph=False,
    export_animations=True,
    export_animation_mode='NLA_TRACKS',
    export_optimize_animation_size=True,
    export_image_format='AUTO'
)

# Arrange characters along X = -4.9..+4.9 in the saved .blend file so opening arlecchino_npcs_european.blend shows all 15 side by side
for idx, (arm_obj, _) in enumerate(built_arms):
    arm_obj.location = ((idx - 7.0) * 0.75, 0.0, 0.0)

bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
print(f"SUCCESS! Saved {BLEND_OUT} and {GLB_OUT} ({os.path.getsize(GLB_OUT)/(1024*1024):.2f} MB)")
