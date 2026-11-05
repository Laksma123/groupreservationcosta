import bpy
import bmesh
import json
import math
import os
from mathutils import Vector, Matrix, Euler
from mathutils.geometry import tessellate_polygon

# ==============================================================================
# COSTA SMERALDA — DECK 6 ("MATERA / ROMA") 3D ARCHITECTURAL DECK PLAN MODEL
# - Ristorante Arlecchino (#308): Embossed as a clean, solid flat-topped 3D block
#   ("hanya bidang polos mengikuti outline restoran") highlighted in Emerald Green
# - All other Deck 6 zones & hull: Curated Black, White & Grey monochrome palette
# - 100% Accurate Hull Curves (Bow, Lifeboat Bays, Colosseo Bulge, Cruiser Stern)
#   and Floor Plan Geometry extracted directly from official Costa CAD vectors
# ==============================================================================

PROJ_DIR = "/Users/dianjulie/Documents/Map Project"
SCRATCH_DIR = os.path.join(PROJ_DIR, "scratch")
VEC_JSON = os.path.join(SCRATCH_DIR, "deck6_vector_data.json")
TEX_PLAN = os.path.join(SCRATCH_DIR, "deck6_monochrome_plan_8k.png")
TEX_BUMP = os.path.join(SCRATCH_DIR, "deck6_monochrome_bump_8k.png")

with open(VEC_JSON, "r") as f:
    vdata = json.load(f)

CLIP = vdata["clip"]  # [x0, y0, x1, y1]
X_CENTER = vdata["x_center"]  # 286.30
Y_MID = vdata["y_mid"]        # 464.885
SCALE = 0.10                  # 1 PDF pt = 0.10 Blender meters (Full ship length = 67.33m)


def pdf_to_bl(x_pdf, y_pdf):
    """
    Maps PDF (x_pdf, y_pdf) to right-handed Blender (X, Y) coordinates:
    - X_bl = (Y_MID - y_pdf) * SCALE  -> Stern at -33.67m, Bow at +33.67m
    - Y_bl = (X_CENTER - x_pdf) * SCALE -> Port (left) at +Y, Starboard (right) at -Y
    """
    return ((Y_MID - y_pdf) * SCALE, (X_CENTER - x_pdf) * SCALE)


def bl_to_uv(x_bl, y_bl):
    """
    Exact inverse mapping from Blender (X, Y) back to UV [0..1] on TEX_PLAN.
    In Blender image space, V=0 is bottom (y_pdf = CLIP[3]) and V=1 is top (y_pdf = CLIP[1]).
    """
    x_pdf = X_CENTER - (y_bl / SCALE)
    y_pdf = Y_MID - (x_bl / SCALE)
    u = (x_pdf - CLIP[0]) / (CLIP[2] - CLIP[0])
    v = 1.0 - (y_pdf - CLIP[1]) / (CLIP[3] - CLIP[1])
    return (u, v)


# Reset Blender scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

# Create Root Collection & Empty
root_col = bpy.data.collections.new("Deck6_3D_Plan_Collection")
scene.collection.children.link(root_col)

ROOT_EMPTY = bpy.data.objects.new("Deck6_Architectural_Model_Root", None)
ROOT_EMPTY.empty_display_type = 'PLAIN_AXES'
root_col.objects.link(ROOT_EMPTY)


def link_obj(obj, mat=None, parent=ROOT_EMPTY):
    if obj.name not in root_col.objects:
        root_col.objects.link(obj)
    if parent:
        obj.parent = parent
    if mat:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    return obj


# ==============================================================================
# 1. PBR MATERIALS (MONOCHROME BLACK/WHITE/GREY + EMERALD GREEN ARLECCHINO)
# ==============================================================================
def make_pbr_mat(name, rgba, rough=0.32, metal=0.05, emit_rgba=None, emit_strength=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.55
    if emit_rgba and emit_strength > 0.0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emit_rgba
            bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(mat, "blend_method"):
            mat.blend_method = 'BLEND'
    return mat


def make_plan_textured_mat(name, tint_rgba=(1.0, 1.0, 1.0, 1.0), rough=0.38, bump_dist=0.015):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.04

    tex_color = nodes.new("ShaderNodeTexImage")
    tex_color.image = bpy.data.images.load(TEX_PLAN)
    tex_color.interpolation = 'Smart'

    if tint_rgba != (1.0, 1.0, 1.0, 1.0):
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs["B"].default_value = tint_rgba
        links.new(tex_color.outputs["Color"], mix.inputs["A"])
        links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    else:
        links.new(tex_color.outputs["Color"], bsdf.inputs["Base Color"])

    if os.path.exists(TEX_BUMP):
        tex_bump = nodes.new("ShaderNodeTexImage")
        tex_bump.image = bpy.data.images.load(TEX_BUMP)
        tex_bump.image.colorspace_settings.name = 'Non-Color'
        bump_node = nodes.new("ShaderNodeBump")
        bump_node.inputs["Strength"].default_value = 0.22
        bump_node.inputs["Distance"].default_value = bump_dist
        links.new(tex_bump.outputs["Color"], bump_node.inputs["Height"])
        links.new(bump_node.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


# Curated Architectural Monochrome Materials
MAT_STUDIO_FLOOR   = make_pbr_mat("Studio_Dark_Slate_Backdrop", (0.075, 0.082, 0.095, 1.0), rough=0.42, metal=0.10)
MAT_HULL_OBSIDIAN  = make_pbr_mat("Hull_Plinth_Obsidian_Black", (0.045, 0.050, 0.060, 1.0), rough=0.28, metal=0.20)
MAT_HULL_TITANIUM  = make_pbr_mat("Hull_Waterline_Titanium_Grey", (0.28, 0.31, 0.36, 1.0), rough=0.32, metal=0.45)
MAT_HULL_WHITE     = make_pbr_mat("Hull_Sheer_Pure_White", (0.94, 0.95, 0.97, 1.0), rough=0.25, metal=0.06)

MAT_PLAN_FLOOR     = make_plan_textured_mat("Deck6_Monochrome_Plan_Floor", rough=0.36, bump_dist=0.012)
MAT_PLAN_ZONE_TOP  = make_plan_textured_mat("Deck6_Monochrome_Zone_Relief_Top", tint_rgba=(0.98, 0.99, 1.0, 1.0), rough=0.32, bump_dist=0.015)

MAT_WALL_WHITE_EXT = make_pbr_mat("Wall_Exterior_White", (0.95, 0.96, 0.98, 1.0), rough=0.26, metal=0.05)
MAT_WALL_BLACK_CAP = make_pbr_mat("Wall_TopCap_JetBlack", (0.035, 0.040, 0.048, 1.0), rough=0.22, metal=0.18)
MAT_WALL_CHARCOAL  = make_pbr_mat("Wall_Interior_Charcoal", (0.12, 0.135, 0.16, 1.0), rough=0.32, metal=0.15)
MAT_WALL_SILVER_CAP= make_pbr_mat("Wall_Interior_DarkGraphite_Cap", (0.055, 0.062, 0.075, 1.0), rough=0.24, metal=0.22)
MAT_ZONE_SIDE_GREY = make_pbr_mat("Zone_Relief_Side_Slate", (0.22, 0.25, 0.30, 1.0), rough=0.35, metal=0.12)

MAT_LIFEBOAT_GREY  = make_pbr_mat("Lifeboat_Monochrome_SlateGrey", (0.30, 0.34, 0.40, 1.0), rough=0.28, metal=0.25)
MAT_LIFEBOAT_CABIN = make_pbr_mat("Lifeboat_Monochrome_PearlWhite", (0.90, 0.92, 0.95, 1.0), rough=0.24, metal=0.08)
MAT_DAVIT_GRAPHITE = make_pbr_mat("Lifeboat_Davit_Graphite", (0.10, 0.11, 0.13, 1.0), rough=0.28, metal=0.65)
MAT_COLOSSEO_GLASS = make_pbr_mat("Colosseo_Smoked_Glass", (0.14, 0.17, 0.22, 1.0), rough=0.10, metal=0.40, alpha=0.76)

# HERO ARLECCHINO EMBOSSED GREEN HIGHLIGHT MATERIALS
MAT_ARL_TOP_GREEN  = make_pbr_mat(
    "Arlecchino_Emboss_Top_Green",
    (0.038, 0.65, 0.26, 1.0),
    rough=0.20,
    metal=0.06,
    emit_rgba=(0.05, 0.76, 0.32, 1.0),
    emit_strength=0.16,
)
MAT_ARL_SIDE_GREEN = make_pbr_mat(
    "Arlecchino_Emboss_Side_DeepGreen",
    (0.018, 0.38, 0.14, 1.0),
    rough=0.26,
    metal=0.08,
    emit_rgba=(0.025, 0.45, 0.18, 1.0),
    emit_strength=0.06,
)
MAT_ARL_RIM_GLOW   = make_pbr_mat(
    "Arlecchino_Emboss_Bevel_Rim_BrightGreen",
    (0.32, 0.96, 0.56, 1.0),
    rough=0.14,
    metal=0.12,
    emit_rgba=(0.35, 0.98, 0.60, 1.0),
    emit_strength=0.42,
)
MAT_ARL_BASE_COLLAR = make_pbr_mat(
    "Arlecchino_Base_Collar_White",
    (0.96, 0.98, 0.97, 1.0),
    rough=0.20,
    metal=0.10,
)


# ==============================================================================
# 2. GEOMETRY HELPER FUNCTIONS (POLYGON EXTRUSION & WALL SWEEPS)
# ==============================================================================
def create_extruded_polygon_mesh(
    name, poly_pdf, z_bot, z_top,
    mat_top, mat_side=None, mat_bevel=None,
    bevel_top_w=0.0, bevel_top_h=0.0,
    apply_plan_uv=False
):
    """
    Creates a clean, tessellated 3D extruded solid from a 2D polygon in PDF coords.
    Supports an optional top chamfer/bevel (inset by bevel_top_w, height bevel_top_h)
    with separate materials for top face, bevel rim, and vertical sides!
    """
    pts_2d = [Vector(pdf_to_bl(px, py)) for px, py in poly_pdf]
    # Ensure counter-clockwise winding in Blender XY plane so top normal points +Z
    area2 = 0.0
    n = len(pts_2d)
    for i in range(n):
        p1, p2 = pts_2d[i], pts_2d[(i + 1) % n]
        area2 += (p1.x * p2.y - p2.x * p1.y)
    if area2 < 0:
        pts_2d.reverse()

    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    mats = [mat_top]
    side_idx = 0
    bev_idx = 0
    if mat_side:
        mats.append(mat_side)
        side_idx = len(mats) - 1
    if mat_bevel:
        mats.append(mat_bevel)
        bev_idx = len(mats) - 1

    z_mid = z_top - bevel_top_h if bevel_top_h > 0.0 else z_top

    v_bot = [bm.verts.new((p.x, p.y, z_bot)) for p in pts_2d]
    v_mid = [bm.verts.new((p.x, p.y, z_mid)) for p in pts_2d]

    # Compute inset vertices for top bevel if requested
    if bevel_top_w > 0.0 and bevel_top_h > 0.0:
        pts_inset = []
        for i in range(n):
            p_prev = pts_2d[(i - 1) % n]
            p_curr = pts_2d[i]
            p_next = pts_2d[(i + 1) % n]
            e1 = (p_curr - p_prev).normalized()
            e2 = (p_next - p_curr).normalized()
            n1 = Vector((-e1.y, e1.x))
            n2 = Vector((-e2.y, e2.x))
            bis = n1 + n2
            if bis.length < 1e-4:
                inset_dir = n1
            else:
                bis.normalize()
                denom = max(0.35, bis.dot(n1))
                inset_dir = bis * (1.0 / denom)
            pts_inset.append(p_curr + inset_dir * bevel_top_w)
        v_top = [bm.verts.new((p.x, p.y, z_top)) for p in pts_inset]
    else:
        pts_inset = pts_2d
        v_top = v_mid

    bm.verts.ensure_lookup_table()

    # Side walls (bot -> mid)
    for i in range(n):
        j = (i + 1) % n
        f_side = bm.faces.new([v_bot[i], v_bot[j], v_mid[j], v_mid[i]])
        f_side.material_index = side_idx

    # Bevel rim (mid -> top)
    if bevel_top_w > 0.0 and bevel_top_h > 0.0:
        for i in range(n):
            j = (i + 1) % n
            f_bev = bm.faces.new([v_mid[i], v_mid[j], v_top[j], v_top[i]])
            f_bev.material_index = bev_idx

    # Tessellate top and bottom polygons using mathutils.geometry.tessellate_polygon
    tris = tessellate_polygon([pts_inset])
    for i0, i1, i2 in tris:
        try:
            ft = bm.faces.new([v_top[i0], v_top[i1], v_top[i2]])
            ft.material_index = 0
        except ValueError:
            pass
        try:
            fb = bm.faces.new([v_bot[i2], v_bot[i1], v_bot[i0]])
            fb.material_index = side_idx
        except ValueError:
            pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    if apply_plan_uv:
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
            for loop in f.loops:
                co = loop.vert.co
                loop[uv_layer].uv = bl_to_uv(co.x, co.y)

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    for m in mats:
        obj.data.materials.append(m)
    return link_obj(obj)


def create_polyline_wall_mesh(name, polylines_pdf, z_bot, z_top, thickness, mat_side, mat_cap):
    """
    Sweeps a list of 2D polylines (in PDF coordinates) into 3D rectangular walls
    with crisp top caps.
    """
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    half_t = 0.5 * thickness

    for poly_pdf in polylines_pdf:
        pts = [Vector(pdf_to_bl(px, py)) for px, py in poly_pdf]
        if len(pts) < 2:
            continue
        for k in range(len(pts) - 1):
            p1, p2 = pts[k], pts[k + 1]
            seg = p2 - p1
            if seg.length < 1e-4:
                continue
            d = seg.normalized()
            n = Vector((-d.y, d.x)) * half_t
            # Slight endpoint extension so corner joints overlap cleanly
            ext = d * (half_t * 0.45)
            a = p1 - ext
            b = p2 + ext

            c0 = bm.verts.new((a.x - n.x, a.y - n.y, z_bot))
            c1 = bm.verts.new((b.x - n.x, b.y - n.y, z_bot))
            c2 = bm.verts.new((b.x + n.x, b.y + n.y, z_bot))
            c3 = bm.verts.new((a.x + n.x, a.y + n.y, z_bot))

            t0 = bm.verts.new((a.x - n.x, a.y - n.y, z_top))
            t1 = bm.verts.new((b.x - n.x, b.y - n.y, z_top))
            t2 = bm.verts.new((b.x + n.x, b.y + n.y, z_top))
            t3 = bm.verts.new((a.x + n.x, a.y + n.y, z_top))

            # 4 side faces (material 0 = mat_side)
            for vs in ([c0, c1, t1, t0], [c1, c2, t2, t1], [c2, c3, t3, t2], [c3, c0, t0, t3]):
                f = bm.faces.new(vs)
                f.material_index = 0
            # Top cap face (material 1 = mat_cap)
            ft = bm.faces.new([t0, t1, t2, t3])
            ft.material_index = 1

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat_side)
    obj.data.materials.append(mat_cap)
    return link_obj(obj)


# ==============================================================================
# 3. BUILD LAYER 1: SCULPTED SHIP HULL PLINTH & MAIN DECK 6 FLOOR SLAB
# ==============================================================================
hull_loop = vdata["hull_outer_loop"]

# 3A. Lower Obsidian Architectural Hull Plinth (Z = -0.52m .. -0.16m)
create_extruded_polygon_mesh(
    "Deck6_Hull_Plinth_Obsidian", hull_loop,
    z_bot=-0.52, z_top=-0.16,
    mat_top=MAT_HULL_OBSIDIAN, mat_side=MAT_HULL_OBSIDIAN
)

# 3B. Brushed Titanium Waterline Trim Band (Z = -0.16m .. -0.04m)
create_extruded_polygon_mesh(
    "Deck6_Hull_Waterline_Titanium", hull_loop,
    z_bot=-0.16, z_top=-0.04,
    mat_top=MAT_HULL_TITANIUM, mat_side=MAT_HULL_TITANIUM
)

# 3C. Main Deck 6 Floor Plan Slab with 8K Monochrome Floor Plan Texture (Z = -0.04m .. +0.16m)
create_extruded_polygon_mesh(
    "Deck6_Main_Floor_Slab", hull_loop,
    z_bot=-0.04, z_top=0.16,
    mat_top=MAT_PLAN_FLOOR, mat_side=MAT_HULL_WHITE,
    apply_plan_uv=True
)


# ==============================================================================
# 4. BUILD LAYER 2: 3D STEPPED MONOCHROME ZONE RELIEFS & ARCHITECTURAL CORES
# ==============================================================================
for z_name, z_poly in vdata["zone_polys"].items():
    create_extruded_polygon_mesh(
        f"Deck6_ZoneRelief_{z_name}", z_poly,
        z_bot=0.155, z_top=0.205,
        mat_top=MAT_PLAN_ZONE_TOP, mat_side=MAT_ZONE_SIDE_GREY,
        apply_plan_uv=True
    )

# 3D Stepped Monochrome Architectural Cores (3 Elevator/Stair Banks + Engine Casing + Colosseo Stage + Mastroianni Oval Bar)
# a) Central Engine Casing 3D Volume (x_pdf=277.6..294.8, y_pdf=572.5..612.5)
engine_casing_poly = [
    (277.6, 572.5), (294.8, 572.5), (294.8, 612.5), (277.6, 612.5)
]
create_extruded_polygon_mesh(
    "Deck6_Engine_Casing_3D_Core", engine_casing_poly,
    z_bot=0.16, z_top=0.28,
    mat_top=MAT_PLAN_ZONE_TOP, mat_side=MAT_WALL_CHARCOAL,
    apply_plan_uv=True
)

# b) 6 Passenger Elevator Banks (2 rows of elevators at Forward, Mid-Forward, and Aft Lobbies)
elevator_rects_pdf = [
    # Forward Lobby (Mastroianni / Theatre): PL7..PL14
    (277.2, 341.8, 281.5, 364.2),
    (290.8, 341.8, 295.1, 364.2),
    # Midship Lobby (Arlecchino Forward / My Tours): PL17..PL24
    (277.2, 509.8, 281.5, 531.6),
    (290.8, 509.8, 295.1, 531.6),
    # Aft Lobby (Il Meneghino Forward): SL26..SL29 / Aft Lifts
    (277.0, 675.8, 281.3, 692.4),
    (290.6, 675.8, 294.9, 692.4),
]
for idx, (rx0, ry0, rx1, ry1) in enumerate(elevator_rects_pdf, start=1):
    r_poly = [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]
    create_extruded_polygon_mesh(
        f"Deck6_ElevatorBank_{idx}", r_poly,
        z_bot=0.16, z_top=0.38,
        mat_top=MAT_PLAN_ZONE_TOP, mat_side=MAT_WALL_CHARCOAL,
        mat_bevel=MAT_WALL_SILVER_CAP, bevel_top_w=0.025, bevel_top_h=0.02,
        apply_plan_uv=True
    )


# ==============================================================================
# 5. BUILD LAYER 3: 3D PERIMETER HULL BULWARK, INTERIOR WALLS & 16 LIFEBOATS
# ==============================================================================
# 5A. Outer Hull Perimeter Bulwark Wall (Z = +0.16m .. +0.42m)
hull_closed_polyline = hull_loop + [hull_loop[0]]
create_polyline_wall_mesh(
    "Deck6_Outer_Hull_Bulwark_Wall",
    [hull_closed_polyline],
    z_bot=0.16, z_top=0.42,
    thickness=0.12,
    mat_side=MAT_WALL_WHITE_EXT,
    mat_cap=MAT_WALL_BLACK_CAP
)

# 5B. Colosseo Panoramic Smoked Glass Bay Walls (Port & Starboard Midship Bulges)
create_polyline_wall_mesh(
    "Deck6_Colosseo_Panoramic_Glass_Wall",
    [vdata["colosseo_port_outer"], vdata["colosseo_stbd_outer"]],
    z_bot=0.16, z_top=0.52,
    thickness=0.09,
    mat_side=MAT_COLOSSEO_GLASS,
    mat_cap=MAT_WALL_SILVER_CAP
)

# 5C. 750 Interior Monochrome Structural Walls & Partition Linework (Z = +0.16m .. +0.34m)
create_polyline_wall_mesh(
    "Deck6_Interior_Walls_Monochrome",
    vdata["wall_polylines"],
    z_bot=0.16, z_top=0.34,
    thickness=0.055,
    mat_side=MAT_WALL_CHARCOAL,
    mat_cap=MAT_WALL_SILVER_CAP
)

# 5D. 16 3D Monochrome Lifeboats (8 Port + 8 Starboard in the Forward & Aft Lifeboat Galleries)
for lb_idx, lb_poly in enumerate(vdata["lifeboats"], start=1):
    # Main slate-grey lifeboat hull
    create_extruded_polygon_mesh(
        f"Deck6_Lifeboat_{lb_idx:02d}_Hull", lb_poly,
        z_bot=0.02, z_top=0.28,
        mat_top=MAT_LIFEBOAT_GREY, mat_side=MAT_LIFEBOAT_GREY,
        mat_bevel=MAT_LIFEBOAT_CABIN, bevel_top_w=0.08, bevel_top_h=0.06
    )
    # Raised pearl-white canopy cabin in the center of each lifeboat
    xs = [p[0] for p in lb_poly]
    ys = [p[1] for p in lb_poly]
    cx, cy = 0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys))
    hw = 0.28 * (max(xs) - min(xs))
    hh = 0.30 * (max(ys) - min(ys))
    cabin_poly = [
        (cx - hw, cy - hh), (cx + hw, cy - hh),
        (cx + hw, cy + hh), (cx - hw, cy + hh)
    ]
    create_extruded_polygon_mesh(
        f"Deck6_Lifeboat_{lb_idx:02d}_Cabin", cabin_poly,
        z_bot=0.28, z_top=0.38,
        mat_top=MAT_LIFEBOAT_CABIN, mat_side=MAT_WALL_CHARCOAL
    )
    # Two 3D steel davit arms connecting each lifeboat to the Deck 6 hull wall
    hull_x = 244.0 if cx < X_CENTER else 328.6
    for dy_off in (-0.28 * (max(ys) - min(ys)), +0.28 * (max(ys) - min(ys))):
        davit_line = [(cx, cy + dy_off), (hull_x, cy + dy_off)]
        create_polyline_wall_mesh(
            f"Deck6_Lifeboat_{lb_idx:02d}_Davit_{dy_off:+.1f}",
            [davit_line],
            z_bot=0.20, z_top=0.40,
            thickness=0.08,
            mat_side=MAT_DAVIT_GRAPHITE,
            mat_cap=MAT_WALL_SILVER_CAP
        )


# ==============================================================================
# 6. BUILD LAYER 4 (HERO): RISTORANTE ARLECCHINO EMBOSSED SOLID 3D BLOCK (#308)
#    "d emboss atau d tonjolkan secara polos (hanya bidang polos mengikuti
#     outline restoran) dan d highlight hijau"
# ==============================================================================
arl_poly = vdata["arlecchino_poly"]

# 6A. Crisp White/Emerald Architectural Collar Bezel at Base (Z = +0.16m .. +0.23m)
create_extruded_polygon_mesh(
    "Deck6_Arlecchino_Base_Collar", arl_poly,
    z_bot=0.16, z_top=0.23,
    mat_top=MAT_ARL_BASE_COLLAR, mat_side=MAT_ARL_BASE_COLLAR
)

# 6B. Main Prominent Embossed Solid 3D Block of Ristorante Arlecchino (Z = +0.20m .. +0.94m)
#     - 100% Plain, Smooth Top Surface ("bidang polos mengikuti outline restoran")
#     - Precision 45-degree beveled top rim highlighted in luminous emerald green
create_extruded_polygon_mesh(
    "Deck6_Arlecchino_Embossed_Highlight_Block", arl_poly,
    z_bot=0.20, z_top=0.94,
    mat_top=MAT_ARL_TOP_GREEN,
    mat_side=MAT_ARL_SIDE_GREEN,
    mat_bevel=MAT_ARL_RIM_GLOW,
    bevel_top_w=0.065,
    bevel_top_h=0.055,
    apply_plan_uv=False
)


# ==============================================================================
# 7. STUDIO BACKDROP PLANE, LIGHTING & AGX COLOR MANAGEMENT
# ==============================================================================
# Architectural dark-slate studio ground plane beneath the hull plinth (Z = -0.52m)
bpy.ops.mesh.primitive_plane_add(size=160.0, location=(0.0, 0.0, -0.525))
studio_plane = bpy.context.active_object
studio_plane.name = "Studio_Backdrop_Floor"
link_obj(studio_plane, MAT_STUDIO_FLOOR, parent=None)

# World Illumination (Bright, Clean Studio Lighting per Rule 1C)
world = bpy.data.worlds.new("Deck6_Isometric_Studio_World")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs["Color"].default_value = (0.12, 0.13, 0.15, 1.0)
bg_node.inputs["Strength"].default_value = 0.92

# AgX Medium High Contrast Color Management
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0.22
scene.view_settings.gamma = 1.0

# Render Engine Setup
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene.eevee, "taa_render_samples"):
    scene.eevee.taa_render_samples = 64
if hasattr(scene.eevee, "use_raytracing"):
    scene.eevee.use_raytracing = True

# Key Sun Light (Crisp 3D Isometric Shadows & Bevel Highlights)
sun_data = bpy.data.lights.new(name="Iso_Key_Sun", type='SUN')
sun_data.energy = 3.2
sun_data.color = (1.0, 0.99, 0.97)
sun_data.angle = math.radians(3.5)
sun_obj = bpy.data.objects.new("Iso_Key_Sun", sun_data)
sun_obj.rotation_euler = Euler((math.radians(48.0), math.radians(-22.0), math.radians(35.0)), 'XYZ')
scene.collection.objects.link(sun_obj)

# Warm Rim Sun Light (Separates dark hull & walls from studio floor)
rim_data = bpy.data.lights.new(name="Iso_Rim_Sun", type='SUN')
rim_data.energy = 1.35
rim_data.color = (0.90, 0.95, 1.0)
rim_data.angle = math.radians(8.0)
rim_obj = bpy.data.objects.new("Iso_Rim_Sun", rim_data)
rim_obj.rotation_euler = Euler((math.radians(55.0), math.radians(30.0), math.radians(-145.0)), 'XYZ')
scene.collection.objects.link(rim_obj)

# Shadowless Overhead Studio Fill Area Lights (Even illumination across entire 67m ship deck)
for fx in (-22.0, 0.0, 22.0):
    fill_data = bpy.data.lights.new(name=f"Studio_Fill_{fx:+.0f}", type='AREA')
    fill_data.energy = 450.0
    fill_data.shape = 'RECTANGLE'
    fill_data.size = 26.0
    fill_data.size_y = 14.0
    fill_data.color = (0.98, 0.99, 1.0)
    fill_data.use_shadow = False
    if hasattr(fill_data, "specular_factor"):
        fill_data.specular_factor = 0.0
    fill_obj = bpy.data.objects.new(f"Studio_Fill_{fx:+.0f}", fill_data)
    fill_obj.location = (fx, 0.0, 18.0)
    scene.collection.objects.link(fill_obj)


# ==============================================================================
# 8. SAVE .BLEND & EXPORT .GLB (EXCLUDING STUDIO BACKDROP PLANE FROM GLB)
# ==============================================================================
blend_out = os.path.join(PROJ_DIR, "deck6_arlecchino_highlight.blend")
glb_out = os.path.join(PROJ_DIR, "deck6_arlecchino_highlight.glb")

bpy.ops.wm.save_as_mainfile(filepath=blend_out)
print("Saved Blender file:", blend_out)

# Hide studio floor during GLB export so GLB is pure Deck 6 model
studio_plane.hide_render = True
studio_plane.hide_viewport = True
bpy.ops.object.select_all(action='DESELECT')
for o in root_col.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=glb_out,
    use_selection=True,
    export_format='GLB',
    export_apply=True
)
studio_plane.hide_render = False
studio_plane.hide_viewport = False
print("Exported GLB file:", glb_out)


# ==============================================================================
# 9. RENDER REALISTIC ISOMETRIC POV SCREENSHOTS
# ==============================================================================
def look_at(cam_obj, target_pt):
    direction = Vector(target_pt) - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()


cam_data = bpy.data.cameras.new("Iso_Camera")
cam_data.type = 'ORTHO'
cam_data.clip_start = 0.1
cam_data.clip_end = 400.0
cam_obj = bpy.data.objects.new("Iso_Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Configure viewport 3D shading to Rendered / Material Preview as well
for win in bpy.context.window_manager.windows:
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'
                    space.shading.use_scene_lights = True
                    space.shading.use_scene_world = True

# SHOT 1: Full-Ship Isometric POV (Shows entire Deck 6 from Stern to Bow with Arlecchino embossed in Green)
# True Isometric angle looking from Starboard-Aft-Above toward Midship so the entire ship length
# fits diagonally across the widescreen frame at large scale!
scene.render.resolution_x = 2560
scene.render.resolution_y = 1600
scene.render.resolution_percentage = 100

cam_obj.location = (-36.0, -34.0, 38.0)
look_at(cam_obj, (-1.5, 0.0, 0.2))
cam_data.ortho_scale = 52.0

render1_path = os.path.join(SCRATCH_DIR, "render_deck6_isometric_full.png")
scene.render.filepath = render1_path
bpy.ops.render.render(write_still=True)
print("Rendered Shot 1 (Full Isometric):", render1_path)

# SHOT 2: Mid-Ship Isometric Hero POV (Focused on Embossed Green Ristorante Arlecchino + Colosseo + Jazz Club + Photo Store)
# Notice how in blender coords:
# Arlecchino y_pdf = 509.55..647.48 -> X_bl = (464.885 - 578.5) * 0.10 = -11.36m
cam_obj.location = (-28.0, -22.0, 22.0)
look_at(cam_obj, (-10.5, 0.2, 0.35))
cam_data.ortho_scale = 23.5

render2_path = os.path.join(SCRATCH_DIR, "render_deck6_isometric_arlecchino_closeup.png")
scene.render.filepath = render2_path
bpy.ops.render.render(write_still=True)
print("Rendered Shot 2 (Arlecchino Isometric Closeup):", render2_path)

# SHOT 3: Portside-Forward Isometric POV (Viewing from Port-Bow Quarter down the length of Deck 6)
cam_obj.location = (34.0, 34.0, 38.0)
look_at(cam_obj, (-2.5, 0.0, 0.2))
cam_data.ortho_scale = 52.0

render3_path = os.path.join(SCRATCH_DIR, "render_deck6_isometric_bow_quarter.png")
scene.render.filepath = render3_path
bpy.ops.render.render(write_still=True)
print("Rendered Shot 3 (Port-Bow Isometric):", render3_path)

# Save final blend file with camera positioned on the Hero Isometric view
cam_obj.location = (-36.0, -34.0, 38.0)
look_at(cam_obj, (-1.5, 0.0, 0.2))
cam_data.ortho_scale = 52.0
bpy.ops.wm.save_as_mainfile(filepath=blend_out)
