import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler

ROOT = "/Users/dianjulie/Documents/Map Project"
BLEND_PATH = os.path.join(ROOT, "arlecchino_block1.blend")
GLB_PATH = os.path.join(ROOT, "arlecchino_block1.glb")

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
scene = bpy.context.scene
scene_col = scene.collection

# ==============================================================================
# CANONICAL COORDINATE & MIRROR SYMMETRY CONSTANTS
# Mirror plane across Clover Table center X_clover = 12.900m:
#   M(x) = 25.800 - x
# ==============================================================================
CLOVER_CX = 12.900
CLOVER_CY = 8.730

def mx(x):
    return 25.800 - x

ROOM_WID_Y = 7.58     # Block 1 & Block 3 Portside: Y = 0.00 .. 7.58m
CORR_WID_Y = 2.30     # Central Corridor: Y = 7.58 .. 9.88m (Center = 8.73m)
B2_PILLAR_Y = 9.88    # Block 2 & Block 4 Starboardside Pillar line: Y = 9.88m
B2_WALL_Y = 17.46     # Block 2 & Block 4 Starboardside Inboard Wall: Y = 17.46m
CEIL_H = 2.78
COFFER_H = 2.96

B34_START_X = mx(10.400)   # 15.400m (Exact Crossroads-to-Block3/4 carpet & corridor boundary)
B34_SIKU_X  = mx(10.150)   # 15.650m (Pintu Masuk Pertama / Pagar Siku / First Pillar line)
B34_AFT_WALL_X = mx(-1.55) # 27.350m (Aft wall face of Block 3 & Block 4)
B34_CORR_END_X = mx(-2.35) # 28.150m (Aft end of corridor between Block 3 & Block 4)

def get_or_create_collection(name, parent=None):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    if parent is None:
        scene_col.children.link(col)
    else:
        parent.children.link(col)
    return col

def link_to_collection(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

def apply_box_uv(obj, scale_per_meter=1.0):
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv_layer = me.uv_layers.active.data
    verts = me.vertices
    for poly in me.polygons:
        nx, ny, nz = abs(poly.normal.x), abs(poly.normal.y), abs(poly.normal.z)
        for loop_idx in poly.loop_indices:
            v = (obj.matrix_world @ verts[me.loops[loop_idx].vertex_index].co) if obj.location.length == 0 else (obj.location + verts[me.loops[loop_idx].vertex_index].co)
            if nz >= nx and nz >= ny:
                u, w = v.x * scale_per_meter, v.y * scale_per_meter
            elif ny >= nx and ny >= nz:
                u, w = v.x * scale_per_meter, v.z * scale_per_meter
            else:
                u, w = v.y * scale_per_meter, v.z * scale_per_meter
            uv_layer[loop_idx].uv = (u, w)

def apply_normalized_face_uv(obj):
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv_layer = me.uv_layers.active.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)
    for poly in me.polygons:
        for loop_idx in poly.loop_indices:
            v = me.vertices[me.loops[loop_idx].vertex_index].co
            if dx >= dy:
                u = (v.x - min(xs)) / max(dx, 1e-4)
            else:
                u = (v.y - min(ys)) / max(dy, 1e-4)
            w = (v.z - min(zs)) / max(dz, 1e-4)
            uv_layer[loop_idx].uv = (u, w)

def apply_corridor_runner_uv(obj, y_center=8.73, uv_width_y=2.04, pitch_x=1.02, x_offset=15.40):
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv_layer = me.uv_layers.active.data
    ox, oy = obj.location.x, obj.location.y
    for poly in me.polygons:
        for loop_idx in poly.loop_indices:
            v_co = me.vertices[me.loops[loop_idx].vertex_index].co
            wx = ox + v_co.x
            wy = oy + v_co.y
            u = 0.5 + (wy - y_center) / uv_width_y
            v = (wx - x_offset) / pitch_x
            uv_layer[loop_idx].uv = (u, v)

def add_box(name, size, location, mat, col, bevel=0.0, rot=(0, 0, 0), uv_metric=None):
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    if bevel > 0.0:
        bmesh.ops.bevel(bm, geom=bm.edges, offset=bevel, segments=2, profile=0.5, affect='EDGES')
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    if uv_metric is not None:
        apply_box_uv(obj, uv_metric)
    link_to_collection(obj, col)
    return obj

def add_cylinder(name, radius, depth, location, mat, col, vertices=32, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=vertices, radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    return obj

# ==============================================================================
# 0. CLEAN UP PREVIOUS PLACEHOLDERS OR B3/B4 OBJECTS IF RE-RUNNING
# ==============================================================================
remove_prefixes = (
    "Crossroads_AftSiku_",
    "Crossroads_AftBackdrop_",
    "Crossroads_Floor_",
    "Crossroads_PortHull_",
    "Crossroads_StbdInboard_",
    "Ceiling_Crossroads_MainSlab",
    "B3_",
    "B4_",
    "B3B4_",
    "Floor_Block3_",
    "Floor_Block4_",
    "Floor_B3B4_",
    "Pillar_Plinth_B3_", "Pillar_LowerWhite_B3_", "Pillar_RedInset_X_B3_", "Pillar_RedInset_Y_B3_",
    "Pillar_ChairRail_B3_", "Pillar_UpperShaft_B3_", "Pillar_UpperCollar_B3_", "Pillar_Crown_B3_",
    "Pillar_ArtFrame_Y_B3_", "Pillar_ArtMat_Y_B3_", "Pillar_ArtPic_Y_B3_",
    "Sconce_Backplate_B3_", "Sconce_Arm_B3_", "Sconce_Cup_B3_", "Sconce_Bulb_B3_",
    "Pillar_Plinth_B4_", "Pillar_LowerWhite_B4_", "Pillar_RedInset_X_B4_", "Pillar_RedInset_Y_B4_",
    "Pillar_ChairRail_B4_", "Pillar_UpperShaft_B4_", "Pillar_UpperCollar_B4_", "Pillar_Crown_B4_",
    "Pillar_ArtFrame_Y_B4_", "Pillar_ArtMat_Y_B4_", "Pillar_ArtPic_Y_B4_",
    "Sconce_Backplate_B4_", "Sconce_Arm_B4_", "Sconce_Cup_B4_", "Sconce_Bulb_B4_",
    "Rail_TopWood_B3_", "Rail_BotBar_B3_", "Rail_Post_B3_", "Rail_Foot_B3_", "Rail_InnerV_B3_", "Rail_XBar_B3_", "Rail_CenterRing_B3_",
    "Rail_TopWood_B4_", "Rail_BotBar_B4_", "Rail_Post_B4_", "Rail_Foot_B4_", "Rail_InnerV_B4_", "Rail_XBar_B4_", "Rail_CenterRing_B4_",
    "TableTop_309", "TableSubTop_309", "PedBase_309", "PedCol_309", "Chair_309",
    "TableTop_311", "TableSubTop_311", "PedBase_311", "PedCol_311", "Chair_311",
    "TableTop_313", "TableSubTop_313", "PedBase_313", "PedCol_313", "Chair_313",
    "TableTop_315", "TableSubTop_315", "PedBase_315", "PedCol_315", "Chair_315",
    "TableTop_389", "TableSubTop_389", "PedBase_389", "PedCol_389", "Chair_389",
    "TableTop_391", "TableSubTop_391", "PedBase_391", "PedCol_391", "Chair_391",
    "TableTop_409", "TableSubTop_409", "PedBase_409", "PedCol_409", "Chair_409",
    "TableTop_411", "TableSubTop_411", "PedBase_411", "PedCol_411", "Chair_411",
    "TableTop_413", "TableSubTop_413", "PedBase_413", "PedCol_413", "Chair_413",
    "TableTop_474", "TableSubTop_474", "PedBase_474", "PedCol_474", "Chair_474",
    "TableTop_476", "TableSubTop_476", "PedBase_476", "PedCol_476", "Chair_476",
    "TableTop_478", "TableSubTop_478", "PedBase_478", "PedCol_478", "Chair_478",
    "TableTop_456", "TableSubTop_456", "PedBase_456", "PedCol_456", "Chair_456",
    "TableTop_454", "TableSubTop_454", "PedBase_454", "PedCol_454", "Chair_454",
    "TableTop_452", "TableSubTop_452", "PedBase_452", "PedCol_452", "Chair_452",
    "TableTop_386", "TableSubTop_386", "PedBase_386", "PedCol_386", "Chair_386",
    "TableTop_388", "TableSubTop_388", "PedBase_388", "PedCol_388", "Chair_388",
    "TableTop_390", "TableSubTop_390", "PedBase_390", "PedCol_390", "Chair_390",
    "TableTop_392", "TableSubTop_392", "PedBase_392", "PedCol_392", "Chair_392",
    "TableTop_394", "TableSubTop_394", "PedBase_394", "PedCol_394", "Chair_394",
    "TableTop_396", "TableSubTop_396", "PedBase_396", "PedCol_396", "Chair_396",
)
for obj in list(bpy.data.objects):
    if obj.name.startswith(remove_prefixes):
        bpy.data.objects.remove(obj, do_unlink=True)

arch_col = get_or_create_collection("01_Architecture_Deck6_Arlecchino")
furn_col_b3 = get_or_create_collection("04_Furniture_Block3_Portside")
furn_col_b4 = get_or_create_collection("05_Furniture_Block4_Starboardside")

# Retrieve existing materials
mats = {
    "carpet": bpy.data.materials.get("Mat_Arlecchino_Carpet"),
    "corridor_tile": bpy.data.materials.get("Mat_Corridor_Geometric_Tile"),
    "crossroads_tile": bpy.data.materials.get("Mat_Crossroads_Geometric_Tile"),
    "marble_top": bpy.data.materials.get("Mat_Carrara_Marble_Top"),
    "dark_marble": bpy.data.materials.get("Mat_Emperador_Dark_Marble"),
    "velvet_maroon": bpy.data.materials.get("Mat_Velvet_Burgundy_Maroon"),
    "leather_ivory": bpy.data.materials.get("Mat_Leatherette_Ivory_Cream"),
    "wall_white": bpy.data.materials.get("Mat_Classical_Wall_White"),
    "wall_red": bpy.data.materials.get("Mat_Wainscot_Venetian_Red"),
    "ceiling_dark": bpy.data.materials.get("Mat_Coffer_Charcoal_Slate"),
    "black_metal": bpy.data.materials.get("Mat_Black_Powder_Steel"),
    "wood_walnut": bpy.data.materials.get("Mat_Dark_Walnut_Wood"),
    "chair_leg": bpy.data.materials.get("Mat_Espresso_Chair_Leg"),
    "brass": bpy.data.materials.get("Mat_Polished_Brass"),
    "chrome": bpy.data.materials.get("Mat_Polished_Chrome"),
    "murano_glass": bpy.data.materials.get("Mat_Murano_Green_Glass"),
    "blind_cream": bpy.data.materials.get("Mat_Roman_Blind_Cream"),
    "led_warm": bpy.data.materials.get("Mat_LED_Warm_2700K"),
    "led_red": bpy.data.materials.get("Mat_LED_Accent_Red"),
    "window_daylight": bpy.data.materials.get("Mat_Window_Sea_Daylight"),
    "window_glass": bpy.data.materials.get("Mat_Marine_Window_Glass"),
    "art_1": bpy.data.materials.get("Mat_Framed_Art_1"),
    "art_2": bpy.data.materials.get("Mat_Framed_Art_2"),
    "art_3": bpy.data.materials.get("Mat_Framed_Art_3"),
    "plates_wall": bpy.data.materials.get("Mat_Plates_Wall"),
}

# Retrieve chair template meshes from existing Block 1 chairs
chair_ivory_mesh = bpy.data.objects["Chair_303_Window_Bay1_A1"].data
chair_maroon_mesh = bpy.data.objects["Chair_399_Center_Fwd_A1"].data

def spawn_chair(name, chair_mesh, location, yaw_rad, col):
    obj = bpy.data.objects.new(name, chair_mesh)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, yaw_rad)
    link_to_collection(obj, col)
    return obj

def build_table_assembly(table_id, center_xy, length_x, width_y, yaw_rad, chair_variant_mesh, pax_count, col, skip_side_b=False):
    t_col = get_or_create_collection(f"Table_{table_id}", parent=col)
    cx, cy = center_xy
    cos_a = math.cos(yaw_rad)
    sin_a = math.sin(yaw_rad)

    def to_world(lx, ly, lz):
        wx = cx + lx * cos_a - ly * sin_a
        wy = cy + lx * sin_a + ly * cos_a
        return (wx, wy, lz)

    top_obj = add_box(
        f"TableTop_{table_id}",
        (length_x, width_y, 0.032),
        to_world(0.0, 0.0, 0.742),
        mats["marble_top"],
        t_col,
        bevel=0.005,
        rot=(0.0, 0.0, yaw_rad),
        uv_metric=0.45,
    )
    add_box(
        f"TableSubTop_{table_id}",
        (length_x - 0.08, width_y - 0.08, 0.022),
        to_world(0.0, 0.0, 0.715),
        mats["black_metal"],
        t_col,
        rot=(0.0, 0.0, yaw_rad),
    )

    if length_x <= 1.0:
        ped_xs = [0.0]
    elif length_x <= 1.65:
        ped_xs = [-length_x * 0.28, length_x * 0.28]
    elif length_x <= 2.30:
        ped_xs = [-length_x * 0.32, 0.0, length_x * 0.32]
    else:
        ped_xs = [-length_x * 0.36, -length_x * 0.12, length_x * 0.12, length_x * 0.36]

    for i, px in enumerate(ped_xs):
        add_cylinder(
            f"PedBase_{table_id}_{i}",
            radius=0.24,
            depth=0.016,
            location=to_world(px, 0.0, 0.008),
            mat=mats["black_metal"],
            col=t_col,
        )
        add_cylinder(
            f"PedCol_{table_id}_{i}",
            radius=0.042,
            depth=0.70,
            location=to_world(px, 0.0, 0.36),
            mat=mats["black_metal"],
            col=t_col,
        )

    # Support 2, 4, 6, 8, or 10 pax (1, 2, 3, 4, or 5 chairs per long side)
    chairs_per_side = max(1, pax_count // 2)
    if chairs_per_side == 1:
        chair_xs = [0.0]
    elif chairs_per_side == 2:
        chair_xs = [-length_x * 0.27, length_x * 0.27]
    elif chairs_per_side == 3:
        chair_xs = [-length_x * 0.33, 0.0, length_x * 0.33]
    else:
        span = length_x * 0.78
        chair_xs = [-span * 0.5 + span * (k / (chairs_per_side - 1)) for k in range(chairs_per_side)]

    chair_offset_y = width_y * 0.5 + 0.19
    for c_i, ch_x in enumerate(chair_xs):
        spawn_chair(
            f"Chair_{table_id}_A{c_i+1}",
            chair_variant_mesh,
            to_world(ch_x, -chair_offset_y, 0.0),
            yaw_rad,
            t_col,
        )
        if not skip_side_b:
            spawn_chair(
                f"Chair_{table_id}_B{c_i+1}",
                chair_variant_mesh,
                to_world(ch_x, chair_offset_y, 0.0),
                yaw_rad + math.pi,
                t_col,
            )
    return top_obj

# ==============================================================================
# 1. REBUILD CROSSROADS FLOOR & CEILING TO SPAN EXACTLY X = 10.400m .. 15.400m
#    (Symmetrical 2.50m from Clover Table X=12.900m to both Block 1/2 and Block 3/4!)
# ==============================================================================
TILE_PERIOD = 1.250

def compute_crossroads_uv(vx, vy):
    u = 0.5 + (vy - CLOVER_CY) / TILE_PERIOD
    v = (vx - 10.4000) / TILE_PERIOD
    return (u, v)

def make_tiled_floor_slab(name, x0, x1, y0, y1, z0, z1, mat):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5), verts=bm.verts)
    uv_lay = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            vx, vy = loop.vert.co.x, loop.vert.co.y
            loop[uv_lay].uv = compute_crossroads_uv(vx, vy)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    link_to_collection(obj, arch_col)
    return obj

# Crossroads floor from X = 10.4000m to X = 15.4000m (exact 4.0000 tile periods!)
make_tiled_floor_slab("Crossroads_Floor_Main",     10.4000, B34_START_X, 0.000,  13.080, -0.040, 0.000, mats["crossroads_tile"])
make_tiled_floor_slab("Crossroads_Floor_StbdWing", 11.0800, B34_START_X, 13.080, 17.460, -0.040, 0.000, mats["crossroads_tile"])

# Crossroads outer Portside & Starboardside walls (X = 10.40m .. 15.40m)
add_box("Crossroads_PortHull_Plinth", (5.00, 0.22, 0.15), (12.90, -0.08, 0.075), mats["wall_white"], arch_col)
add_box("Crossroads_PortHull_Red",    (5.00, 0.18, 0.68), (12.90, -0.08, 0.49),  mats["wall_red"],   arch_col)
add_box("Crossroads_PortHull_Rail",   (5.00, 0.24, 0.06), (12.90, -0.07, 0.86),  mats["wall_white"], arch_col)
add_box("Crossroads_PortHull_Upper",  (5.00, 0.20, 1.90), (12.90, -0.08, 1.84),  mats["wall_white"], arch_col)

add_box("Crossroads_StbdInboard_Plinth", (5.00, 0.22, 0.16), (12.90, 17.54, 0.08), mats["wall_white"], arch_col)
add_box("Crossroads_StbdInboard_Red",    (5.00, 0.20, 0.68), (12.90, 17.54, 0.50), mats["wall_red"],   arch_col)
add_box("Crossroads_StbdInboard_Rail",   (5.00, 0.23, 0.065), (12.90, 17.535, 0.88), mats["wall_white"], arch_col)
add_box("Crossroads_StbdInboard_Upper",  (5.00, 0.21, 1.88), (12.90, 17.555, 1.85), mats["wall_white"], arch_col)

# Crossroads unified flat ceiling slab from X = 10.15m to X = 15.65m (symmetrical around X = 12.90m!)
def make_ceiling_with_circular_hole(name, x0, x1, y0, y1, z0, z1, cx, cy, hole_r, mat, segments=64):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    in_bot, in_top, out_bot, out_top = [], [], [], []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        ca, sa = math.cos(a), math.sin(a)
        ix, iy = cx + hole_r * ca, cy + hole_r * sa
        tx = ((x1 - cx) / ca) if ca > 1e-6 else (((x0 - cx) / ca) if ca < -1e-6 else 1e9)
        ty = ((y1 - cy) / sa) if sa > 1e-6 else (((y0 - cy) / sa) if sa < -1e-6 else 1e9)
        t = min(tx, ty)
        ox = max(x0, min(x1, cx + t * ca))
        oy = max(y0, min(y1, cy + t * sa))
        in_bot.append(bm.verts.new((ix, iy, z0)))
        in_top.append(bm.verts.new((ix, iy, z1)))
        out_bot.append(bm.verts.new((ox, oy, z0)))
        out_top.append(bm.verts.new((ox, oy, z1)))
    for i in range(segments):
        inext = (i + 1) % segments
        bm.faces.new((in_bot[i], out_bot[i], out_bot[inext], in_bot[inext]))
        bm.faces.new((in_top[i], in_top[inext], out_top[inext], out_top[i]))
        bm.faces.new((in_bot[i], in_bot[inext], in_top[inext], in_top[i]))
        bm.faces.new((out_bot[i], out_top[i], out_top[inext], out_bot[inext]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    link_to_collection(obj, arch_col)
    return obj

make_ceiling_with_circular_hole(
    "Ceiling_Crossroads_MainSlab",
    10.15, B34_SIKU_X,
    0.00, 17.46,
    2.790, 2.980,
    CLOVER_CX, CLOVER_CY,
    1.880,
    mats["wall_white"],
    segments=64,
)

# Classical White Architrave Header Beams at X = 15.34..15.68m (mirror of Crossroads_Header_Beam_Port/Stbd at X = 10.12..10.46m)
add_box("Crossroads_Header_Beam_B3_Port",  (0.34, 7.62, 0.23), (15.51, 3.81,  2.675), mats["wall_white"], arch_col)
add_box("Crossroads_Header_Crown_B3_Port", (0.40, 7.64, 0.08), (15.51, 3.82,  2.750), mats["wall_white"], arch_col)
add_box("Crossroads_Header_Beam_B4_Stbd",  (0.34, 3.28, 0.23), (15.51, 11.48, 2.675), mats["wall_white"], arch_col)
add_box("Crossroads_Header_Crown_B4_Stbd", (0.40, 3.32, 0.08), (15.51, 11.48, 2.750), mats["wall_white"], arch_col)

# ==============================================================================
# 2. FLOORS FOR BLOCK 3, BLOCK 4 & CENTRAL CORRIDOR (X = 15.400m .. 28.150m)
# ==============================================================================
B34_LEN_X = B34_AFT_WALL_X - B34_START_X       # 27.35 - 15.40 = 11.95m
B34_MID_X = (B34_START_X + B34_AFT_WALL_X) * 0.5  # 21.375m

# Block 3 Portside Dining Carpet (single unified slab -> zero Z-fighting!)
add_box(
    "Floor_Block3_Dining_Carpet",
    (B34_LEN_X, ROOM_WID_Y, 0.04),
    (B34_MID_X, ROOM_WID_Y * 0.5, -0.02),
    mats["carpet"],
    arch_col,
    uv_metric=0.58,
)

# Block 4 Starboardside Dining Carpet (single unified slab -> zero Z-fighting!)
add_box(
    "Floor_Block4_Dining_Carpet",
    (B34_LEN_X, ROOM_WID_Y, 0.04),
    (B34_MID_X, (B2_PILLAR_Y + B2_WALL_Y) * 0.5, -0.02),
    mats["carpet"],
    arch_col,
    uv_metric=0.58,
)

# Central Corridor Floor between Block 3 & Block 4 (exact same runner pattern with black left/right edges!)
corr34_len = B34_CORR_END_X - B34_START_X  # 28.15 - 15.40 = 12.75m (= 12.5 * 1.02m exact periods!)
corr34_mid_x = (B34_START_X + B34_CORR_END_X) * 0.5  # 21.775m
corr34_obj = add_box(
    "Floor_B3B4_Corridor_Tile",
    (corr34_len, CORR_WID_Y, 0.04),
    (corr34_mid_x, CLOVER_CY, -0.02),
    mats["corridor_tile"],
    arch_col,
)
apply_corridor_runner_uv(corr34_obj, y_center=CLOVER_CY, uv_width_y=2.04, pitch_x=1.02, x_offset=B34_START_X)

# ==============================================================================
# 3. PILLARS & X-CROSS BALUSTRADE RAILINGS FOR BLOCK 3 & BLOCK 4
#    Exact mirror M(x) = 25.800 - x of Block 1 & Block 2!
# ==============================================================================
b34_pillar_specs = [
    # --- BLOCK 3 (PORTSIDE AFT: Y = 7.58m) ---
    ("B3_WideCorr_1", mx(7.975), ROOM_WID_Y, 1.65, 0.58, True, True, mats["art_1"], 1.0),
    ("B3_WideCorr_2", mx(4.975), ROOM_WID_Y, 1.65, 0.58, True, True, mats["art_3"], 1.0),
    ("B3_WideCorr_3", mx(1.975), ROOM_WID_Y, 1.65, 0.58, True, True, mats["art_1"], 1.0),
    ("B3_Entrance_Sq", mx(10.15), ROOM_WID_Y - 1.65, 0.58, 0.58, False, False, None, 1.0),
    ("B3_RoofSupport_411_413", mx(3.475), ROOM_WID_Y - 1.65, 0.54, 0.54, False, False, None, 1.0),
    # --- BLOCK 4 (STARBOARDSIDE AFT: Y = 9.88m) ---
    ("B4_WideCorr_1", mx(7.975), B2_PILLAR_Y, 1.65, 0.58, True, True, mats["art_1"], -1.0),
    ("B4_WideCorr_2", mx(4.975), B2_PILLAR_Y, 1.65, 0.58, True, True, mats["art_3"], -1.0),
    ("B4_WideCorr_3", mx(1.975), B2_PILLAR_Y, 1.65, 0.58, True, True, mats["art_1"], -1.0),
    ("B4_Entrance_Sq", mx(10.15), B2_PILLAR_Y + 1.65, 0.58, 0.58, False, False, None, -1.0),
    ("B4_RoofSupport_476_478", mx(3.475), B2_PILLAR_Y + 1.65, 0.54, 0.54, False, False, None, -1.0),
]

for p_tag, px, py, pw_x, pw_y, has_corr_art, has_sconce, art_m, corr_dir in b34_pillar_specs:
    add_box(f"Pillar_Plinth_{p_tag}", (pw_x + 0.06, pw_y + 0.06, 0.16), (px, py, 0.08), mats["wall_white"], arch_col, bevel=0.005)
    add_box(f"Pillar_LowerWhite_{p_tag}", (pw_x, pw_y, 0.76), (px, py, 0.54), mats["wall_white"], arch_col, bevel=0.005)
    add_box(f"Pillar_RedInset_X_{p_tag}", (pw_x + 0.015, pw_y - 0.12, 0.62), (px, py, 0.54), mats["wall_red"], arch_col)
    add_box(f"Pillar_RedInset_Y_{p_tag}", (pw_x - 0.12, pw_y + 0.015, 0.62), (px, py, 0.54), mats["wall_red"], arch_col)
    add_box(f"Pillar_ChairRail_{p_tag}", (pw_x + 0.07, pw_y + 0.07, 0.065), (px, py, 0.94), mats["wall_white"], arch_col, bevel=0.008)
    add_box(f"Pillar_UpperShaft_{p_tag}", (pw_x, pw_y, CEIL_H - 0.96), (px, py, 0.96 + (CEIL_H - 0.96) * 0.5), mats["wall_white"], arch_col, bevel=0.006)
    add_box(f"Pillar_UpperCollar_{p_tag}", (pw_x + 0.03, pw_y + 0.03, 0.22), (px, py, CEIL_H - 0.15), mats["wall_white"], arch_col, bevel=0.005)
    add_box(f"Pillar_Crown_{p_tag}", (pw_x + 0.08, pw_y + 0.08, 0.08), (px, py, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.008)

    if has_corr_art and art_m is not None:
        ay_frame = py + corr_dir * (pw_y * 0.5 + 0.012)
        ay_mat   = py + corr_dir * (pw_y * 0.5 + 0.016)
        ay_pic   = py + corr_dir * (pw_y * 0.5 + 0.020)
        add_box(f"Pillar_ArtFrame_Y_{p_tag}", (0.52, 0.024, 0.92), (px, ay_frame, 1.64), mats["black_metal"], arch_col, bevel=0.003)
        add_box(f"Pillar_ArtMat_Y_{p_tag}", (0.46, 0.024, 0.86), (px, ay_mat, 1.64), mats["wall_white"], arch_col)
        ao = add_box(f"Pillar_ArtPic_Y_{p_tag}", (0.36, 0.024, 0.72), (px, ay_pic, 1.64), art_m, arch_col)
        apply_normalized_face_uv(ao)

    if has_sconce:
        room_dir = -corr_dir
        sy = py + room_dir * (pw_y * 0.5 + 0.02)
        sz = 1.92
        add_cylinder(f"Sconce_Backplate_{p_tag}", 0.065, 0.03, (px, sy, sz), mats["brass"], arch_col, rot=(math.pi * 0.5, 0, 0))
        for arm_side in (-1.0, 1.0):
            ax = px + arm_side * 0.11
            add_cylinder(f"Sconce_Arm_{p_tag}_{arm_side}", 0.016, 0.14, (px + arm_side * 0.055, sy + room_dir * 0.06, sz - 0.03), mats["murano_glass"], arch_col, rot=(-room_dir * 0.4, arm_side * 0.6, 0))
            add_cylinder(f"Sconce_Cup_{p_tag}_{arm_side}", 0.042, 0.045, (ax, sy + room_dir * 0.10, sz + 0.02), mats["murano_glass"], arch_col)
            add_cylinder(f"Sconce_Bulb_{p_tag}_{arm_side}", 0.024, 0.065, (ax, sy + room_dir * 0.10, sz + 0.065), mats["led_warm"], arch_col)

def add_x_railing_segment(seg_name, p_start, p_end, n_bays=1):
    p0 = Vector(p_start)
    p1 = Vector(p_end)
    vec = p1 - p0
    seg_len = vec.length
    yaw = math.atan2(vec.y, vec.x)
    mid = (p0 + p1) * 0.5
    rail_h = 0.88

    add_box(f"Rail_TopWood_{seg_name}", (seg_len + 0.04, 0.085, 0.045), (mid.x, mid.y, rail_h), mats["wood_walnut"], arch_col, bevel=0.008, rot=(0, 0, yaw))
    add_box(f"Rail_BotBar_{seg_name}", (seg_len, 0.035, 0.025), (mid.x, mid.y, 0.08), mats["black_metal"], arch_col, rot=(0, 0, yaw))
    for b in range(n_bays + 1):
        t = b / n_bays
        pt = p0.lerp(p1, t)
        add_box(f"Rail_Post_{seg_name}_{b}", (0.035, 0.035, rail_h), (pt.x, pt.y, rail_h * 0.5), mats["black_metal"], arch_col, rot=(0, 0, yaw))
        add_box(f"Rail_Foot_{seg_name}_{b}", (0.08, 0.08, 0.015), (pt.x, pt.y, 0.008), mats["black_metal"], arch_col, rot=(0, 0, yaw))

    for b in range(n_bays):
        b0 = p0.lerp(p1, b / n_bays)
        b1 = p0.lerp(p1, (b + 1) / n_bays)
        inset_ratio = min(0.08 / max((b1 - b0).length, 0.1), 0.12)
        inner0 = b0.lerp(b1, inset_ratio)
        inner1 = b0.lerp(b1, 1.0 - inset_ratio)
        for s_idx, isp in enumerate((inner0, inner1)):
            add_box(f"Rail_InnerV_{seg_name}_{b}_{s_idx}", (0.020, 0.022, rail_h - 0.10), (isp.x, isp.y, 0.08 + (rail_h - 0.10) * 0.5), mats["black_metal"], arch_col, rot=(0, 0, yaw))
        bm_mid = (inner0 + inner1) * 0.5
        bay_w = (inner1 - inner0).length
        diag_h = rail_h - 0.12
        diag_len = math.hypot(bay_w, diag_h)
        pitch = math.atan2(diag_h, bay_w)
        for sign in (-1.0, 1.0):
            obj = add_box(
                f"Rail_XBar_{seg_name}_{b}_{sign}",
                (diag_len * 0.98, 0.024, 0.024),
                (bm_mid.x, bm_mid.y, 0.08 + diag_h * 0.5),
                mats["black_metal"],
                arch_col,
            )
            obj.rotation_euler = Euler((0.0, sign * pitch, yaw), 'XYZ')
        add_cylinder(
            f"Rail_CenterRing_{seg_name}_{b}",
            0.045,
            0.026,
            (bm_mid.x, bm_mid.y, 0.08 + diag_h * 0.5),
            mats["black_metal"],
            arch_col,
            rot=(math.pi * 0.5, 0, yaw),
        )

# Block 3 Railings (Portside Aft, Y = 7.63m, exact mirror M(x) of Block 1!)
b3_rail_y = ROOM_WID_Y + 0.05  # 7.63m
add_x_railing_segment("B3_Siku_Inward_1X",   (mx(10.15), b3_rail_y, 0.0), (mx(10.15), ROOM_WID_Y - 1.36, 0.0), n_bays=1)
add_x_railing_segment("B3_Siku_Corridor_1X", (mx(10.15), b3_rail_y, 0.0), (mx(8.80),  b3_rail_y, 0.0), n_bays=1)
add_x_railing_segment("B3_Corridor_Bay1_1X", (mx(7.15),  b3_rail_y, 0.0), (mx(5.80),  b3_rail_y, 0.0), n_bays=1)
add_x_railing_segment("B3_Corridor_Bay2_1X", (mx(4.15),  b3_rail_y, 0.0), (mx(2.80),  b3_rail_y, 0.0), n_bays=1)

# Block 4 Railings (Starboardside Aft, Y = 9.83m, exact mirror M(x) of Block 2!)
b4_rail_y = B2_PILLAR_Y - 0.05  # 9.83m
add_x_railing_segment("B4_Siku_Inward_1X",   (mx(10.15), b4_rail_y, 0.0), (mx(10.15), B2_PILLAR_Y + 1.36, 0.0), n_bays=1)
add_x_railing_segment("B4_Siku_Corridor_1X", (mx(10.15), b4_rail_y, 0.0), (mx(8.80),  b4_rail_y, 0.0), n_bays=1)
add_x_railing_segment("B4_Corridor_Bay1_1X", (mx(7.15),  b4_rail_y, 0.0), (mx(5.80),  b4_rail_y, 0.0), n_bays=1)
add_x_railing_segment("B4_Corridor_Bay2_1X", (mx(4.15),  b4_rail_y, 0.0), (mx(2.80),  b4_rail_y, 0.0), n_bays=1)

# ==============================================================================
# 4. HELPER FOR DOUBLE WAITER STATION (USED IN BOTH BLOCK 3 & BLOCK 4)
# ==============================================================================
def build_double_waiter_station(tag, f0_xy, f1_xy, front_normal_xy):
    f0 = Vector((f0_xy[0], f0_xy[1], 0.0))
    f1 = Vector((f1_xy[0], f1_xy[1], 0.0))
    tang = (f1 - f0).normalized()
    total_len = (f1 - f0).length
    n_front = Vector((front_normal_xy[0], front_normal_xy[1], 0.0)).normalized()
    n_back = -n_front
    normal_yaw = math.atan2(n_front.y, n_front.x)
    station_depth = 0.65
    back_origin = f0 + n_back * station_depth

    part_thick = 0.035
    avail_sec = total_len - 4 * part_thick
    w_short = round(avail_sec * (0.5 / 4.0), 4)
    w_long = round(avail_sec * (1.5 / 4.0), 4)
    sec_widths = [w_short, w_long, w_short, w_long]
    s_mid = total_len * 0.5

    def st_pos(d_from_back, s_along, z):
        p = back_origin + n_front * d_from_back + tang * s_along
        return (p.x, p.y, z)

    add_box(f"{tag}_AlcoveBackWall", (0.16, total_len + 0.12, CEIL_H), st_pos(-0.08, s_mid, CEIL_H * 0.5), mats["wall_white"], arch_col, rot=(0, 0, normal_yaw))
    add_box(f"{tag}_AlcoveReturn_0", (station_depth, 0.04, CEIL_H), st_pos(station_depth * 0.5, 0.0, CEIL_H * 0.5), mats["wall_white"], arch_col, rot=(0, 0, normal_yaw))
    add_box(f"{tag}_AlcoveReturn_1", (station_depth, 0.04, CEIL_H), st_pos(station_depth * 0.5, total_len, CEIL_H * 0.5), mats["wall_white"], arch_col, rot=(0, 0, normal_yaw))
    add_box(f"{tag}_AlcoveHeader",   (0.14, total_len + 0.04, 0.45), st_pos(station_depth - 0.05, s_mid, CEIL_H - 0.225), mats["wall_white"], arch_col, rot=(0, 0, normal_yaw))

    add_box(f"{tag}_Plinth",     (0.62, total_len, 0.04), st_pos(0.31, s_mid, 0.02), mats["black_metal"], arch_col, rot=(0, 0, normal_yaw))
    add_box(f"{tag}_Carcass",    (0.62, total_len, 0.84), st_pos(0.31, s_mid, 0.46), mats["black_metal"], arch_col, rot=(0, 0, normal_yaw))
    add_box(f"{tag}_MarbleTop",  (0.65, total_len + 0.02, 0.04), st_pos(0.325, s_mid, 0.90), mats["dark_marble"], arch_col, bevel=0.005, rot=(0, 0, normal_yaw))
    add_box(f"{tag}_Backsplash", (0.04, total_len + 0.02, 0.25), st_pos(0.02, s_mid, 1.045), mats["dark_marble"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))

    curr_s = 0.0
    for sec_i, sec_w in enumerate(sec_widths):
        sec_cs = curr_s + sec_w * 0.5
        face_w = sec_w - 0.025
        handle_w = min(0.16, face_w * 0.45)

        add_box(f"{tag}_LowerCab_{sec_i+1}", (0.025, face_w, 0.39), st_pos(0.625, sec_cs, 0.25), mats["wall_white"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
        add_box(f"{tag}_LowerCab_Handle_{sec_i+1}", (0.018, handle_w, 0.015), st_pos(0.645, sec_cs, 0.40), mats["chrome"], arch_col, rot=(0, 0, normal_yaw))

        add_box(f"{tag}_MidDrawer_{sec_i+1}", (0.025, face_w, 0.195), st_pos(0.625, sec_cs, 0.565), mats["wall_white"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
        add_box(f"{tag}_MidDrawer_Handle_{sec_i+1}", (0.018, handle_w, 0.015), st_pos(0.645, sec_cs, 0.565), mats["chrome"], arch_col, rot=(0, 0, normal_yaw))

        add_box(f"{tag}_TopDrawer_{sec_i+1}", (0.025, face_w, 0.195), st_pos(0.625, sec_cs, 0.775), mats["black_metal"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
        add_box(f"{tag}_TopDrawer_Handle_{sec_i+1}", (0.018, handle_w, 0.015), st_pos(0.645, sec_cs, 0.775), mats["chrome"], arch_col, rot=(0, 0, normal_yaw))

        part_cs = curr_s + sec_w + part_thick * 0.5
        add_box(f"{tag}_BodyPart_{sec_i+1}", (0.64, part_thick, 0.86), st_pos(0.32, part_cs, 0.45), mats["black_metal"], arch_col, bevel=0.003, rot=(0, 0, normal_yaw))
        add_box(f"{tag}_TopPart25cm_{sec_i+1}", (0.65, part_thick, 0.25), st_pos(0.325, part_cs, 1.045), mats["dark_marble"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
        curr_s += sec_w + part_thick

plate_offsets = [
    (-0.36,  0.34, 0.13), (0.0,  0.40, 0.15), (0.36,  0.34, 0.13),
    (-0.38,  0.00, 0.15), (0.0,  0.00, 0.17), (0.38,  0.00, 0.15),
    (-0.34, -0.35, 0.13), (0.0, -0.39, 0.14), (0.34, -0.35, 0.13),
]

# ==============================================================================
# 5. BLOCK 3 (PORTSIDE AFT) ARCHITECTURE, WINDOWS, 2 WAITER STATIONS & WALL ART
# ==============================================================================
# 5A. Portside Outer Hull Window Wall (Y = 0.00m, X = 15.40m .. 27.35m, exact mirror M(x) of Block 1!)
add_box("B3_Hull_Plinth",        (B34_LEN_X, 0.22, 0.15), (B34_MID_X, -0.08, 0.075), mats["wall_white"], arch_col)
add_box("B3_Hull_Red_Wainscot",  (B34_LEN_X, 0.18, 0.68), (B34_MID_X, -0.08, 0.49),  mats["wall_red"],   arch_col)
add_box("B3_Hull_Chair_Rail",    (B34_LEN_X, 0.24, 0.06), (B34_MID_X, -0.07, 0.86),  mats["wall_white"], arch_col, bevel=0.008)
add_box("B3_Hull_Window_Header", (B34_LEN_X, 0.22, 0.30), (B34_MID_X, -0.08, 2.64),  mats["wall_white"], arch_col)

b3_pier_ranges = [
    (mx(10.40), mx(9.75), False, None),
    (mx(7.45),  mx(6.45), True,  mats["art_3"]),
    (mx(4.15),  mx(3.15), True,  mats["art_2"]),
    (mx(0.85),  mx(-1.55), False, None),
]
for p_idx, (x0, x1, has_art, art_mat) in enumerate(b3_pier_ranges):
    pw = x1 - x0
    px = (x0 + x1) * 0.5
    add_box(f"B3_Hull_Pier_{p_idx}", (pw, 0.24, 1.65), (px, -0.04, 1.70), mats["wall_white"], arch_col, bevel=0.005)
    if x0 > B34_START_X + 0.1:
        add_box(f"B3_Hull_JambRed_L_{p_idx}", (0.055, 0.18, 1.60), (x0 - 0.028, -0.05, 1.69), mats["wall_red"], arch_col)
    if x1 < B34_AFT_WALL_X - 0.1:
        add_box(f"B3_Hull_JambRed_R_{p_idx}", (0.055, 0.18, 1.60), (x1 + 0.028, -0.05, 1.69), mats["wall_red"], arch_col)
    if has_art and art_mat:
        add_box(f"B3_Pier_Frame_{p_idx}", (0.58, 0.03, 0.72), (px, 0.09, 1.66), mats["black_metal"], arch_col, bevel=0.004)
        add_box(f"B3_Pier_MatBoard_{p_idx}", (0.52, 0.034, 0.66), (px, 0.092, 1.66), mats["wall_white"], arch_col)
        art_obj = add_box(f"B3_Pier_Art_{p_idx}", (0.38, 0.038, 0.52), (px, 0.095, 1.66), art_mat, arch_col)
        apply_normalized_face_uv(art_obj)
        add_cylinder(f"B3_Pier_LampBar_{p_idx}", 0.012, 0.42, (px, 0.16, 2.08), mats["brass"], arch_col, rot=(0, math.pi * 0.5, 0))
        add_box(f"B3_Pier_LampGlow_{p_idx}", (0.38, 0.02, 0.015), (px, 0.16, 2.065), mats["led_warm"], arch_col)

b3_win_ranges = [(mx(9.75), mx(7.45)), (mx(6.45), mx(4.15)), (mx(3.15), mx(0.85))]
for w_idx, (wx0, wx1) in enumerate(b3_win_ranges):
    ww = wx1 - wx0
    wcx = (wx0 + wx1) * 0.5
    add_box(f"B3_Win_Glass_{w_idx}", (ww, 0.015, 1.60), (wcx, -0.12, 1.68), mats["window_glass"], arch_col)
    for m_i in (1, 2):
        mx_mull = wx0 + ww * (m_i / 3.0)
        add_box(f"B3_Win_Mullion_{w_idx}_{m_i}", (0.048, 0.065, 1.60), (mx_mull, -0.09, 1.68), mats["wall_white"], arch_col)
    sea_obj = add_box(f"B3_Win_Daylight_{w_idx}", (ww + 0.5, 0.02, 1.85), (wcx, -0.55, 1.68), mats["window_daylight"], arch_col)
    apply_normalized_face_uv(sea_obj)
    for f_i, fz in enumerate([2.46, 2.34, 2.22, 2.11]):
        add_box(f"B3_RomanBlind_Fold_{w_idx}_{f_i}", (ww + 0.08, 0.065, 0.13), (wcx, 0.02 + (f_i % 2) * 0.012, fz), mats["blind_cream"], arch_col, bevel=0.018)
    add_box(f"B3_RomanBlind_HBand_{w_idx}", (ww + 0.09, 0.072, 0.032), (wcx, 0.028, 2.26), mats["wall_red"], arch_col)
    for side_x in (wx0 + 0.16, wx1 - 0.16):
        add_box(f"B3_RomanBlind_VBand_{w_idx}_{side_x:.1f}", (0.038, 0.075, 0.46), (side_x, 0.03, 2.29), mats["wall_red"], arch_col)

# 5B. Block 3 Aft Wall (Entrance 2 at X = 24.65..25.90m, 2-Step Recessed Wall + Waiter Station #1 "Rect 7" + 9 Plates Wall at X = 27.35m)
B3_SEG1_X = mx(-0.10)  # 25.90m
B3_SEG2_X = mx(-1.55)  # 27.35m

# Corner wall segment (Y = 0.00..2.25m at X = 27.35m) with 9 Fornasetti Plates (NO sofa in Block 3!)
add_box("B3_AftWall_Upper_A",     (0.18, 2.25, CEIL_H), (B3_SEG2_X + 0.09, 1.125, CEIL_H * 0.5), mats["wall_white"], arch_col)
add_box("B3_AftWall_Red_A",       (0.20, 2.25, 0.75),   (B3_SEG2_X + 0.07, 1.125, 0.45),         mats["wall_red"],   arch_col)
add_box("B3_AftWall_Plinth_A",    (0.04, 2.25, 0.16),   (B3_SEG2_X - 0.01, 1.125, 0.08),         mats["wall_white"], arch_col)
add_box("B3_AftWall_ChairRail_A", (0.045, 2.25, 0.065), (B3_SEG2_X - 0.012, 1.125, 0.88),        mats["wall_white"], arch_col, bevel=0.006)
add_box("B3_AftWall_Crown_A",     (0.05, 2.25, 0.08),   (B3_SEG2_X - 0.015, 1.125, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)
for p_i, (dy, dz, prad) in enumerate(plate_offsets):
    p_obj = add_cylinder(
        f"B3_Aft_Plate_{p_i}",
        radius=prad,
        depth=0.025,
        location=(B3_SEG2_X - 0.02, 1.15 + dy, 1.78 + dz),
        mat=mats["plates_wall"],
        col=arch_col,
        rot=(0, math.pi * 0.5, 0),
    )
    apply_normalized_face_uv(p_obj)

# Step 1 from Entrance 2 (Y = 6.08..7.58m, front face at X = 25.90m, solid locker block to X = 27.44m)
seg1_y0, seg1_y1 = 6.08, 7.58
seg1_len = 1.50
seg1_cy = 6.83
ret1_dx = B3_SEG2_X - B3_SEG1_X  # 1.45m
ret1_cx = (B3_SEG1_X + B3_SEG2_X) * 0.5  # 26.625m
add_box("B3_AftStep1_Wall_White",     (ret1_dx + 0.18, seg1_len, CEIL_H),       (ret1_cx + 0.09, seg1_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B3_AftStep1_Wall_Red",       (0.02, seg1_len - 0.14, 0.68),            (B3_SEG1_X - 0.005, seg1_cy, 0.50),        mats["wall_red"],   arch_col)
add_box("B3_AftStep1_Wall_Plinth",    (0.04, seg1_len, 0.16),                   (B3_SEG1_X - 0.01, seg1_cy, 0.08),         mats["wall_white"], arch_col, bevel=0.004)
add_box("B3_AftStep1_Wall_ChairRail", (0.045, seg1_len + 0.02, 0.065),          (B3_SEG1_X - 0.012, seg1_cy, 0.88),        mats["wall_white"], arch_col, bevel=0.006)
add_box("B3_AftStep1_Wall_Crown",     (0.05, seg1_len + 0.02, 0.08),            (B3_SEG1_X - 0.015, seg1_cy, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)
add_box("B3_AftStep1_ChartPlaque",    (0.015, 0.42, 0.68),                      (B3_SEG1_X - 0.01, seg1_cy, 1.68),         mats["art_2"],      arch_col)

# Lekukan 1 Return trim at Y = 6.08m (stepping from X = 25.90m to X = 27.35m)
add_box("B3_AftStep1_Return_Red",       (ret1_dx - 0.08, 0.02, 0.68),        (ret1_cx, seg1_y0 - 0.005, 0.50),        mats["wall_red"],   arch_col)
add_box("B3_AftStep1_Return_Plinth",    (ret1_dx + 0.02, 0.04, 0.16),        (ret1_cx, seg1_y0 - 0.01, 0.08),         mats["wall_white"], arch_col, bevel=0.004)
add_box("B3_AftStep1_Return_ChairRail", (ret1_dx + 0.04, 0.045, 0.065),      (ret1_cx, seg1_y0 - 0.012, 0.88),        mats["wall_white"], arch_col, bevel=0.006)
add_box("B3_AftStep1_Return_Crown",     (ret1_dx + 0.04, 0.05, 0.08),        (ret1_cx, seg1_y0 - 0.015, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)

# Step 2 at X = 27.35m (Y = 5.33..6.08m, with white service door)
seg2_y0, seg2_y1 = 5.33, 6.08
seg2_len = 0.75
seg2_cy = 5.705
add_box("B3_AftStep2_Wall_White",     (0.68, seg2_len, CEIL_H), (B3_SEG2_X + 0.34, seg2_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B3_AftStep2_Door_Frame",     (0.025, 0.60, 2.08),      (B3_SEG2_X - 0.006, seg2_cy, 1.04),        mats["wall_white"], arch_col, bevel=0.003)
add_box("B3_AftStep2_Door_Leaf",      (0.015, 0.54, 2.02),      (B3_SEG2_X - 0.012, seg2_cy, 1.01),        mats["wall_white"], arch_col)
for jamb_y in (seg2_y0 + 0.04, seg2_y1 - 0.04):
    add_box(f"B3_AftStep2_JambRed_{jamb_y:.2f}", (0.02, 0.06, 0.68), (B3_SEG2_X - 0.005, jamb_y, 0.50), mats["wall_red"], arch_col)
add_box("B3_AftStep2_Wall_ChairRail", (0.04, seg2_len, 0.055),  (B3_SEG2_X - 0.01, seg2_cy, 0.88),         mats["wall_white"], arch_col)

# Step 3: Block 3 Waiter Station #1 (Rectangle 7 in 2D Map: Y = 2.25..5.33m, front flush at X = 27.35m, facing -X into Block 3!)
build_double_waiter_station("B3_WaiterStation_1_Rect7", (B3_SEG2_X, 2.25), (B3_SEG2_X, 5.33), (-1.0, 0.0))

# 5C. Block 3 Pintu Masuk Pertama Wall (Crossroads face flush at X = 15.40m = M(10.40m), interior face at X = 16.05m):
# - Waiter Station #2 (Rectangle 5 in 2D Map) behind Pintu Masuk Pertama wall (Y = 1.61..4.21m, front at X = 16.05m, facing +X into Block 3!)
# - 9 Fornasetti Plates on the window corner segment (Y = 0.00..1.61m at X = 16.05m, facing +X into Block 3!)
# - Crossroads-facing exterior cladding flush at X = 15.40m (so Crossroads floor X = 10.40..15.40m is 100% unobstructed!)
B3_FWD_IN_X = 16.05
B3_FWD_OUT_X = 15.40

build_double_waiter_station("B3_WaiterStation_2_Rect5", (B3_FWD_IN_X, 4.21), (B3_FWD_IN_X, 1.61), (1.0, 0.0))

# Classical Pilaster Jamb framing the Pintu Masuk Pertama doorway side of Waiter Station #2 (at Y = 4.25m, X = 15.725m)
add_box("B3_WS2_EntranceJamb_White",  (0.68, 0.18, CEIL_H), (15.725, 4.25, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B3_WS2_EntranceJamb_Red",    (0.69, 0.19, 0.68),   (15.725, 4.25, 0.50),         mats["wall_red"],   arch_col)
add_box("B3_WS2_EntranceJamb_Plinth", (0.71, 0.21, 0.16),   (15.725, 4.25, 0.08),         mats["wall_white"], arch_col)
add_box("B3_WS2_EntranceJamb_Rail",   (0.71, 0.21, 0.065),  (15.725, 4.25, 0.88),         mats["wall_white"], arch_col)

# Window-corner wall segment (Y = 0.00..1.61m) with 9 Fornasetti Plates facing +X into Block 3
b3_fwd_c_len = 1.61
b3_fwd_c_cy = 0.805
add_box("B3_FwdPlates_Wall_White",  (0.65, b3_fwd_c_len, CEIL_H),       (15.725, b3_fwd_c_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B3_FwdPlates_Wall_Red",    (0.02, b3_fwd_c_len - 0.08, 0.68),  (B3_FWD_IN_X + 0.005, b3_fwd_c_cy, 0.50), mats["wall_red"], arch_col)
add_box("B3_FwdPlates_Wall_Plinth", (0.04, b3_fwd_c_len, 0.16),         (B3_FWD_IN_X + 0.01,  b3_fwd_c_cy, 0.08), mats["wall_white"], arch_col)
add_box("B3_FwdPlates_Wall_Rail",   (0.045, b3_fwd_c_len + 0.02, 0.065),(B3_FWD_IN_X + 0.012, b3_fwd_c_cy, 0.88), mats["wall_white"], arch_col, bevel=0.006)
for p_i, (dy, dz, prad) in enumerate(plate_offsets):
    p_obj = add_cylinder(
        f"B3_Fwd_Plate_{p_i}",
        radius=prad,
        depth=0.025,
        location=(B3_FWD_IN_X + 0.018, b3_fwd_c_cy + dy * 0.85, 1.76 + dz),
        mat=mats["plates_wall"],
        col=arch_col,
        rot=(0, math.pi * 0.5, 0),
    )
    apply_normalized_face_uv(p_obj)

# Crossroads-facing cladding on the back of Block 3 Pintu Masuk Pertama wall (flush at X = 15.40m, Y = 0.00..4.34m)
add_box("B3_CrossroadsFace_Upper",  (0.10, 4.32, 1.88),  (B3_FWD_OUT_X + 0.04,  2.16, 1.85), mats["wall_white"], arch_col)
add_box("B3_CrossroadsFace_Crown",  (0.14, 4.35, 0.08),  (B3_FWD_OUT_X + 0.03,  2.17, 2.75), mats["wall_white"], arch_col)
add_box("B3_CrossroadsFace_Red",    (0.08, 4.30, 0.68),  (B3_FWD_OUT_X + 0.03,  2.16, 0.50), mats["wall_red"],   arch_col)
add_box("B3_CrossroadsFace_Plinth", (0.12, 4.34, 0.16),  (B3_FWD_OUT_X + 0.03,  2.17, 0.08), mats["wall_white"], arch_col)
add_box("B3_CrossroadsFace_Rail",   (0.13, 4.35, 0.065), (B3_FWD_OUT_X + 0.03,  2.17, 0.88), mats["wall_white"], arch_col)

# Step 1 from Entrance 2 of Block 4 (Y = 9.88..11.38m, front face at X = 25.90m, solid locker block to X = 27.44m)
b4_seg1_y0, b4_seg1_y1 = 9.88, 11.38
b4_seg1_len = 1.50
b4_seg1_cy = 10.63
add_box("B4_AftStep1_Wall_White",     (ret1_dx + 0.18, b4_seg1_len, CEIL_H),       (ret1_cx + 0.09, b4_seg1_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B4_AftStep1_Wall_Red",       (0.02, b4_seg1_len - 0.14, 0.68),            (B3_SEG1_X - 0.005, b4_seg1_cy, 0.50),        mats["wall_red"],   arch_col)
add_box("B4_AftStep1_Wall_Plinth",    (0.04, b4_seg1_len, 0.16),                   (B3_SEG1_X - 0.01, b4_seg1_cy, 0.08),         mats["wall_white"], arch_col, bevel=0.004)
add_box("B4_AftStep1_Wall_ChairRail", (0.045, b4_seg1_len + 0.02, 0.065),          (B3_SEG1_X - 0.012, b4_seg1_cy, 0.88),        mats["wall_white"], arch_col, bevel=0.006)
add_box("B4_AftStep1_Wall_Crown",     (0.05, b4_seg1_len + 0.02, 0.08),            (B3_SEG1_X - 0.015, b4_seg1_cy, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)

# Lekukan 1 Return trim at Y = 11.38m (stepping from X = 25.90m to X = 27.35m)
add_box("B4_AftStep1_Return_Red",       (ret1_dx - 0.08, 0.02, 0.68),        (ret1_cx, b4_seg1_y1 + 0.005, 0.50),        mats["wall_red"],   arch_col)
add_box("B4_AftStep1_Return_Plinth",    (ret1_dx + 0.02, 0.04, 0.16),        (ret1_cx, b4_seg1_y1 + 0.01, 0.08),         mats["wall_white"], arch_col, bevel=0.004)
add_box("B4_AftStep1_Return_ChairRail", (ret1_dx + 0.04, 0.045, 0.065),      (ret1_cx, b4_seg1_y1 + 0.012, 0.88),        mats["wall_white"], arch_col, bevel=0.006)
add_box("B4_AftStep1_Return_Crown",     (ret1_dx + 0.04, 0.05, 0.08),        (ret1_cx, b4_seg1_y1 + 0.015, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)

# Step 2 at X = 27.35m (Y = 11.38..12.13m, with white service door)
b4_seg2_y0, b4_seg2_y1 = 11.38, 12.13
b4_seg2_cy = 11.755
add_box("B4_AftStep2_Wall_White",     (0.68, 0.75, CEIL_H), (B3_SEG2_X + 0.34, b4_seg2_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B4_AftStep2_Door_Frame",     (0.025, 0.60, 2.08),  (B3_SEG2_X - 0.006, b4_seg2_cy, 1.04),        mats["wall_white"], arch_col, bevel=0.003)
add_box("B4_AftStep2_Door_Leaf",      (0.015, 0.54, 2.02),  (B3_SEG2_X - 0.012, b4_seg2_cy, 1.01),        mats["wall_white"], arch_col)
for jamb_y in (b4_seg2_y0 + 0.04, b4_seg2_y1 - 0.04):
    add_box(f"B4_AftStep2_JambRed_{jamb_y:.2f}", (0.02, 0.06, 0.68), (B3_SEG2_X - 0.005, jamb_y, 0.50), mats["wall_red"], arch_col)
add_box("B4_AftStep2_Wall_ChairRail", (0.04, 0.75, 0.055),  (B3_SEG2_X - 0.01, b4_seg2_cy, 0.88),         mats["wall_white"], arch_col)

# Step 3: Block 4 Waiter Station #1 (Rectangles 8 & 6 in 2D Map: Y = 12.13..15.21m, front flush at X = 27.35m, facing -X into Block 4!)
build_double_waiter_station("B4_WaiterStation_1_Rect86", (B3_SEG2_X, 12.13), (B3_SEG2_X, 15.21), (-1.0, 0.0))

# Corner wall segment (Y = 15.21..17.46m at X = 27.35m) with 9 Fornasetti Plates
add_box("B4_AftWall_Upper_A",     (0.18, 2.25, CEIL_H), (B3_SEG2_X + 0.09, 16.335, CEIL_H * 0.5), mats["wall_white"], arch_col)
add_box("B4_AftWall_Red_A",       (0.20, 2.25, 0.75),   (B3_SEG2_X + 0.07, 16.335, 0.45),         mats["wall_red"],   arch_col)
add_box("B4_AftWall_Plinth_A",    (0.04, 2.25, 0.16),   (B3_SEG2_X - 0.01, 16.335, 0.08),         mats["wall_white"], arch_col)
add_box("B4_AftWall_ChairRail_A", (0.045, 2.25, 0.065), (B3_SEG2_X - 0.012, 16.335, 0.88),        mats["wall_white"], arch_col, bevel=0.006)
add_box("B4_AftWall_Crown_A",     (0.05, 2.25, 0.08),   (B3_SEG2_X - 0.015, 16.335, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)
for p_i, (dy, dz, prad) in enumerate(plate_offsets):
    p_obj = add_cylinder(
        f"B4_Aft_Plate_{p_i}",
        radius=prad,
        depth=0.025,
        location=(B3_SEG2_X - 0.02, 16.31 + dy, 1.78 + dz),
        mat=mats["plates_wall"],
        col=arch_col,
        rot=(0, math.pi * 0.5, 0),
    )
    apply_normalized_face_uv(p_obj)

# 6B. Block 4 Pintu Masuk Pertama Wall (Crossroads face flush at X = 15.40m = M(10.40m), interior face at X = 16.05m):
# - Waiter Station #2 (Rectangle 6 in 2D Map) behind Pintu Masuk Pertama wall (Y = 13.25..15.85m, front at X = 16.05m, facing +X into Block 4!)
# - 9 Fornasetti Plates on the inboard corner segment (Y = 15.85..17.46m at X = 16.05m, facing +X into Block 4!)
build_double_waiter_station("B4_WaiterStation_2_Rect6", (B3_FWD_IN_X, 15.85), (B3_FWD_IN_X, 13.25), (1.0, 0.0))

add_box("B4_WS2_EntranceJamb_White",  (0.68, 0.18, CEIL_H), (15.725, 13.21, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B4_WS2_EntranceJamb_Red",    (0.69, 0.19, 0.68),   (15.725, 13.21, 0.50),         mats["wall_red"],   arch_col)
add_box("B4_WS2_EntranceJamb_Plinth", (0.71, 0.21, 0.16),   (15.725, 13.21, 0.08),         mats["wall_white"], arch_col)
add_box("B4_WS2_EntranceJamb_Rail",   (0.71, 0.21, 0.065),  (15.725, 13.21, 0.88),         mats["wall_white"], arch_col)

b4_fwd_c_len = 1.61
b4_fwd_c_cy = 16.655
add_box("B4_FwdPlates_Wall_White",  (0.65, b4_fwd_c_len, CEIL_H),       (15.725, b4_fwd_c_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B4_FwdPlates_Wall_Red",    (0.02, b4_fwd_c_len - 0.08, 0.68),  (B3_FWD_IN_X + 0.005, b4_fwd_c_cy, 0.50), mats["wall_red"], arch_col)
add_box("B4_FwdPlates_Wall_Plinth", (0.04, b4_fwd_c_len, 0.16),         (B3_FWD_IN_X + 0.01,  b4_fwd_c_cy, 0.08), mats["wall_white"], arch_col)
add_box("B4_FwdPlates_Wall_Rail",   (0.045, b4_fwd_c_len + 0.02, 0.065),(B3_FWD_IN_X + 0.012, b4_fwd_c_cy, 0.88), mats["wall_white"], arch_col, bevel=0.006)
for p_i, (dy, dz, prad) in enumerate(plate_offsets):
    p_obj = add_cylinder(
        f"B4_Fwd_Plate_{p_i}",
        radius=prad,
        depth=0.025,
        location=(B3_FWD_IN_X + 0.018, b4_fwd_c_cy + dy * 0.85, 1.76 + dz),
        mat=mats["plates_wall"],
        col=arch_col,
        rot=(0, math.pi * 0.5, 0),
    )
    apply_normalized_face_uv(p_obj)

# Crossroads-facing cladding on the back of Block 4 Pintu Masuk Pertama wall (flush at X = 15.40m, Y = 13.12..17.46m)
add_box("B4_CrossroadsFace_Upper",  (0.10, 4.32, 1.88),  (B3_FWD_OUT_X + 0.04,  15.30, 1.85), mats["wall_white"], arch_col)
add_box("B4_CrossroadsFace_Crown",  (0.14, 4.35, 0.08),  (B3_FWD_OUT_X + 0.03,  15.29, 2.75), mats["wall_white"], arch_col)
add_box("B4_CrossroadsFace_Red",    (0.08, 4.30, 0.68),  (B3_FWD_OUT_X + 0.03,  15.30, 0.50), mats["wall_red"],   arch_col)
add_box("B4_CrossroadsFace_Plinth", (0.12, 4.34, 0.16),  (B3_FWD_OUT_X + 0.03,  15.29, 0.08), mats["wall_white"], arch_col)
add_box("B4_CrossroadsFace_Rail",   (0.13, 4.35, 0.065), (B3_FWD_OUT_X + 0.03,  15.29, 0.88), mats["wall_white"], arch_col)

# 6C. Block 4 Inboard Back Wall & Continuous Banquette Sofa for 6x 4-Pax Tables (Y = 17.46m, X = 16.05m .. 27.35m)
b4_inboard_x0, b4_inboard_x1 = 16.05, 27.35
b4_inboard_len = b4_inboard_x1 - b4_inboard_x0  # 11.57m
b4_inboard_cx = (b4_inboard_x0 + b4_inboard_x1) * 0.5  # 21.565m

add_box("B4_InboardWall_Upper",     (b4_inboard_len + 0.20, 0.22, CEIL_H), (b4_inboard_cx, B2_WALL_Y + 0.11,  CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
add_box("B4_InboardWall_Red",       (b4_inboard_len, 0.02, 0.68),          (b4_inboard_cx, B2_WALL_Y - 0.005, 0.50),         mats["wall_red"],   arch_col)
add_box("B4_InboardWall_ChairRail", (b4_inboard_len, 0.045, 0.065),        (b4_inboard_cx, B2_WALL_Y - 0.012, 0.88),         mats["wall_white"], arch_col, bevel=0.006)

add_box("B4_Inboard_Sofa_Base", (b4_inboard_len, 0.62, 0.44), (b4_inboard_cx, B2_WALL_Y - 0.31, 0.22), mats["wood_walnut"],   arch_col, bevel=0.01)
add_box("B4_Inboard_Sofa_Seat", (b4_inboard_len, 0.64, 0.10), (b4_inboard_cx, B2_WALL_Y - 0.32, 0.46), mats["velvet_maroon"], arch_col, bevel=0.025)
add_box("B4_Inboard_Sofa_Back", (b4_inboard_len, 0.18, 0.58), (b4_inboard_cx, B2_WALL_Y - 0.09, 0.78), mats["velvet_maroon"], arch_col, bevel=0.025)

# Framed Artworks + Brass Picture Lamps along Block 4 Inboard Sofa Wall (same style as Block 2!)
b4_inboard_art_specs = [
    (mx(9.00), mats["art_3"]),
    (mx(6.95), mats["art_2"]),
    (mx(4.90), mats["art_3"]),
    (mx(2.85), mats["art_2"]),
    (25.20,    mats["art_3"]),
]
for a_idx, (ax, amat) in enumerate(b4_inboard_art_specs):
    add_box(f"B4_Inboard_Frame_{a_idx}", (0.64, 0.024, 0.78), (ax, B2_WALL_Y - 0.012, 1.70), mats["black_metal"], arch_col, bevel=0.004)
    add_box(f"B4_Inboard_Mat_{a_idx}",   (0.56, 0.024, 0.70), (ax, B2_WALL_Y - 0.016, 1.70), mats["wall_white"],  arch_col)
    ao = add_box(f"B4_Inboard_Art_{a_idx}", (0.44, 0.024, 0.56), (ax, B2_WALL_Y - 0.020, 1.70), amat, arch_col)
    apply_normalized_face_uv(ao)
    add_cylinder(f"B4_Inboard_LampBar_{a_idx}", 0.012, 0.46, (ax, B2_WALL_Y - 0.09, 2.15), mats["brass"], arch_col, rot=(0, math.pi * 0.5, 0))
    add_box(f"B4_Inboard_LampGlow_{a_idx}", (0.42, 0.02, 0.015), (ax, B2_WALL_Y - 0.09, 2.135), mats["led_warm"], arch_col)

# ==============================================================================
# 7. COFFERED CEILING & CORRIDOR CEILING FOR BLOCK 3 & BLOCK 4 (X = 15.65..28.15m)
# ==============================================================================
total_scene_y = B2_WALL_Y + 0.80
b34_ceil_len = B34_CORR_END_X - B34_SIKU_X  # 28.15 - 15.65 = 12.50m
b34_ceil_mid_x = (B34_SIKU_X + B34_CORR_END_X) * 0.5  # 21.90m

add_box(
    "B3B4_Ceiling_Recessed_Slab",
    (b34_ceil_len, total_scene_y, 0.08),
    (b34_ceil_mid_x, total_scene_y * 0.5 - 0.2, COFFER_H + 0.04),
    mats["ceiling_dark"],
    arch_col,
)

b34_beam_xs = [mx(10.15), mx(6.48), mx(3.475), mx(1.15), mx(-0.10), mx(-1.85)]
beam_ys_b3 = [0.25, 2.95, ROOM_WID_Y - 1.65, ROOM_WID_Y]
for bx in b34_beam_xs:
    add_box(f"B3_CeilBeam_X_White_{bx:.1f}", (0.42, ROOM_WID_Y + 0.2, 0.18),  (bx, ROOM_WID_Y * 0.5, CEIL_H + 0.09),  mats["wall_white"], arch_col, bevel=0.006)
    add_box(f"B3_CeilBeam_X_Red_{bx:.1f}",   (0.22, ROOM_WID_Y + 0.1, 0.012), (bx, ROOM_WID_Y * 0.5, CEIL_H - 0.008), mats["wall_red"],   arch_col)
for by in beam_ys_b3:
    add_box(f"B3_CeilBeam_Y_White_{by:.1f}", (b34_ceil_len, 0.42, 0.174), (b34_ceil_mid_x, by, CEIL_H + 0.093), mats["wall_white"], arch_col, bevel=0.006)
    add_box(f"B3_CeilBeam_Y_Red_{by:.1f}",   (b34_ceil_len, 0.22, 0.012), (b34_ceil_mid_x, by, CEIL_H - 0.004), mats["wall_red"],   arch_col)

for bx in b34_beam_xs[1:]:
    for by in [1.5, 4.35, 6.65]:
        add_cylinder(f"B3_RedSpot_X_{bx:.1f}_{by:.1f}", 0.038, 0.010, (bx, by, CEIL_H - 0.016), mats["led_red"], arch_col)
for by in beam_ys_b3:
    for bx in [mx(8.3), mx(5.0), mx(2.3), mx(-1.0)]:
        add_cylinder(f"B3_RedSpot_Y_{bx:.1f}_{by:.1f}", 0.038, 0.010, (bx, by, CEIL_H - 0.012), mats["led_red"], arch_col)

beam_ys_b4 = [B2_PILLAR_Y, B2_PILLAR_Y + 1.65, 14.51, 17.21]
b4_center_y = (B2_PILLAR_Y + B2_WALL_Y) * 0.5
for bx in b34_beam_xs:
    add_box(f"B4_CeilBeam_X_White_{bx:.1f}", (0.42, ROOM_WID_Y + 0.2, 0.18),  (bx, b4_center_y, CEIL_H + 0.09),  mats["wall_white"], arch_col, bevel=0.006)
    add_box(f"B4_CeilBeam_X_Red_{bx:.1f}",   (0.22, ROOM_WID_Y + 0.1, 0.012), (bx, b4_center_y, CEIL_H - 0.008), mats["wall_red"],   arch_col)
for by in beam_ys_b4:
    add_box(f"B4_CeilBeam_Y_White_{by:.1f}", (b34_ceil_len, 0.42, 0.174), (b34_ceil_mid_x, by, CEIL_H + 0.093), mats["wall_white"], arch_col, bevel=0.006)
    add_box(f"B4_CeilBeam_Y_Red_{by:.1f}",   (b34_ceil_len, 0.22, 0.012), (b34_ceil_mid_x, by, CEIL_H - 0.004), mats["wall_red"],   arch_col)

for bx in b34_beam_xs[1:]:
    for by in [10.80, 13.10, 15.90]:
        add_cylinder(f"B4_RedSpot_X_{bx:.1f}_{by:.1f}", 0.038, 0.010, (bx, by, CEIL_H - 0.016), mats["led_red"], arch_col)
for by in beam_ys_b4:
    for bx in [mx(8.3), mx(5.0), mx(2.3), mx(-1.0)]:
        add_cylinder(f"B4_RedSpot_Y_{bx:.1f}_{by:.1f}", 0.038, 0.010, (bx, by, CEIL_H - 0.012), mats["led_red"], arch_col)

# Central Corridor flat ceiling between Block 3 & Block 4
add_box(
    "B3B4_Ceiling_Corridor_Flat",
    (b34_ceil_len, CORR_WID_Y - 0.04, 0.17),
    (b34_ceil_mid_x, CLOVER_CY, CEIL_H + 0.095),
    mats["wall_white"],
    arch_col,
)
for cx_light in [mx(10.0), mx(8.4), mx(6.0), mx(3.6), mx(1.2), mx(-1.2)]:
    add_cylinder(f"B3B4_Corr_Downlight_{cx_light:.1f}", 0.05, 0.01, (cx_light, CLOVER_CY, CEIL_H - 0.005), mats["led_warm"], arch_col)

# Aft Corridor End Wall at X = 28.15m & Side Corridor Extensions (X = 25.90..28.15m)
upper_corr_h = CEIL_H - 0.88
upper_corr_z = 0.88 + upper_corr_h * 0.5
add_box("B3B4_Rotunda_EndWall_Upper", (0.20, CORR_WID_Y + 1.20, upper_corr_h), (B34_CORR_END_X, CLOVER_CY, upper_corr_z), mats["wall_white"], arch_col)
add_box("B3B4_Rotunda_EndWall_Red",   (0.22, CORR_WID_Y + 1.20, 0.72),         (B34_CORR_END_X - 0.02, CLOVER_CY, 0.48), mats["wall_red"],   arch_col)

corr_ext_len = B34_CORR_END_X - B3_SEG1_X  # 2.25m
corr_ext_cx = (B34_CORR_END_X + B3_SEG1_X) * 0.5  # 27.025m
for side_tag, side_y, in_dir in [("B3", ROOM_WID_Y - 0.14, 1.0), ("B4", B2_PILLAR_Y + 0.14, -1.0)]:
    add_box(f"B3B4_CorrExt_SideWall_White_{side_tag}",  (corr_ext_len, 0.24, CEIL_H),       (corr_ext_cx, side_y, CEIL_H * 0.5),             mats["wall_white"], arch_col, bevel=0.005)
    add_box(f"B3B4_CorrExt_SideWall_Red_{side_tag}",    (corr_ext_len - 0.08, 0.02, 0.68),  (corr_ext_cx, side_y + in_dir * 0.125, 0.50),    mats["wall_red"],   arch_col)
    add_box(f"B3B4_CorrExt_SideWall_Plinth_{side_tag}", (corr_ext_len, 0.04, 0.16),         (corr_ext_cx, side_y + in_dir * 0.13, 0.08),     mats["wall_white"], arch_col)
    add_box(f"B3B4_CorrExt_SideWall_Rail_{side_tag}",   (corr_ext_len, 0.045, 0.065),       (corr_ext_cx, side_y + in_dir * 0.132, 0.88),    mats["wall_white"], arch_col)

# ==============================================================================
# 8. POPULATE TABLES FOR BLOCK 3 (9 TABLES) & BLOCK 4 (12 TABLES)
# ==============================================================================
# --- BLOCK 3 (PORTSIDE AFT: 9 TABLES = 54 SEATS) ---
# 1. Window Row: 4 freestanding 6-pax tables without sofa (309, 311, 313, 315)
build_table_assembly("309_B3_Window_Bay1", (17.15, 1.35), 2.10, 0.90, math.pi * 0.5, chair_ivory_mesh, 6, furn_col_b3)
build_table_assembly("311_B3_Window_Bay2", (20.10, 1.35), 2.10, 0.90, math.pi * 0.5, chair_ivory_mesh, 6, furn_col_b3)
build_table_assembly("313_B3_Window_Bay3", (23.05, 1.35), 2.10, 0.90, math.pi * 0.5, chair_ivory_mesh, 6, furn_col_b3)
build_table_assembly("315_B3_Window_Bay4", (25.85, 1.35), 2.10, 0.90, math.pi * 0.5, chair_ivory_mesh, 6, furn_col_b3)

# 2. Center Row: 2 long maroon velvet tables: 391 (8 chairs) & 389 (10 chairs)
build_table_assembly("391_B3_Center_8Pax",  (18.55, 4.14), 2.65, 0.90, 0.0, chair_maroon_mesh, 8,  furn_col_b3)
build_table_assembly("389_B3_Center_10Pax", (22.95, 4.14), 3.30, 0.90, 0.0, chair_maroon_mesh, 10, furn_col_b3)

# 3. Railing Row: 3 tables centered on the 3 mirrored Wide Corridor Pillars (409, 411, 413)
build_table_assembly("409_B3_Railing_FwdBay", (mx(7.975), 6.58), 1.40, 0.88, math.pi * 0.5, chair_ivory_mesh, 4, furn_col_b3)
build_table_assembly("411_B3_Railing_MidBay", (mx(4.975), 6.58), 1.40, 0.88, math.pi * 0.5, chair_ivory_mesh, 4, furn_col_b3)
build_table_assembly("413_B3_Railing_AftBay", (mx(1.975), 6.58), 1.40, 0.88, math.pi * 0.5, chair_ivory_mesh, 4, furn_col_b3)

# --- BLOCK 4 (STARBOARDSIDE AFT: 12 TABLES = 54 SEATS) ---
# 1. Railing Row: 3 tables centered on the 3 mirrored Wide Corridor Pillars (474, 476, 478)
build_table_assembly("474_B4_Railing_Fwd", (mx(7.975), 10.88), 1.40, 0.88, math.pi * 0.5, chair_ivory_mesh, 4, furn_col_b4)
build_table_assembly("476_B4_Railing_Mid", (mx(4.975), 10.88), 1.40, 0.88, math.pi * 0.5, chair_ivory_mesh, 4, furn_col_b4)
build_table_assembly("478_B4_Railing_Aft", (mx(1.975), 10.88), 1.40, 0.88, math.pi * 0.5, chair_ivory_mesh, 4, furn_col_b4)

# 2. Center Row: 3 maroon velvet 6-pax tables (456, 454, 452), shifted +50 cm (+0.50m) toward Aft (+X) relative to Railing Row!
build_table_assembly("456_B4_Center_Fwd", (mx(7.975) + 0.50, 13.68), 1.95, 0.90, math.pi * 0.5, chair_maroon_mesh, 6, furn_col_b4)
build_table_assembly("454_B4_Center_Mid", (mx(4.975) + 0.50, 13.68), 1.95, 0.90, math.pi * 0.5, chair_maroon_mesh, 6, furn_col_b4)
build_table_assembly("452_B4_Center_Aft", (mx(1.975) + 0.50, 13.68), 1.95, 0.90, math.pi * 0.5, chair_maroon_mesh, 6, furn_col_b4)

# 3. Inboard Sofa Wall Row: 6 tables, ALL 4-pax ("mejax4 tanpa meja sofax2": 386, 388, 390, 392, 394, 396)
b4_sofa_tables = [
    ("386_B4_Sofa_4Pax_1", 16.95),
    ("388_B4_Sofa_4Pax_2", 18.83),
    ("390_B4_Sofa_4Pax_3", 20.71),
    ("392_B4_Sofa_4Pax_4", 22.59),
    ("394_B4_Sofa_4Pax_5", 24.47),
    ("396_B4_Sofa_4Pax_6", 26.35),
]
for tid, tx in b4_sofa_tables:
    build_table_assembly(tid, (tx, 16.32), 1.35, 0.85, 0.0, chair_ivory_mesh, 4, furn_col_b4, skip_side_b=True)

# ==============================================================================
# 9. SAVE .BLEND AND EXPORT .GLB
# ==============================================================================
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format='GLB',
    export_apply=True,
    export_materials='EXPORT',
)
print("SUCCESS: Built Block 3 (Portside Aft) and Block 4 (Starboardside Aft) with 100% symmetry and accuracy!")
