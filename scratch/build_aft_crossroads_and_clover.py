import bpy
import bmesh
import math
import struct
import zlib
import os
from mathutils import Vector

BLEND_PATH = "/Users/dianjulie/Documents/Map Project/arlecchino_block1.blend"
GLB_PATH = "/Users/dianjulie/Documents/Map Project/arlecchino_block1.glb"
TILE_PNG_PATH = "/Users/dianjulie/Documents/Map Project/scratch/corridor_crossroads_tile_2d.png"

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

# ==============================================================================
# 0. GENERATE TRUE 2D-TILEABLE GEOMETRIC MEDALLION + 45° DIAMOND TEXTURE
#    (Matches Photo 14.23.51 across both Central Corridor and Aft Crossroads!)
# ==============================================================================
def generate_crossroads_tile_png(filepath, size=512):
    raw_rows = []
    for py in range(size):
        y = (py + 0.5) / size - 0.5  # [-0.5, +0.5]
        row = bytearray([0])  # PNG filter type 0
        for px in range(size):
            x = (px + 0.5) / size - 0.5  # [-0.5, +0.5]
            ax = abs(x)
            ay = abs(y)
            m = max(ax, ay)

            # Subtle marble/ceramic grain
            grain = int(4.0 * math.sin(px * 0.19) * math.cos(py * 0.23))

            # 1. Center Nested Square Medallion (m <= 0.305)
            if m <= 0.305:
                if m <= 0.088:
                    # Inner black square
                    base = (22, 24, 28)
                elif m <= 0.142:
                    # Inner white square ring
                    base = (242, 239, 232)
                elif m <= 0.242:
                    # Thick black square ring
                    base = (22, 24, 28)
                elif m <= 0.286:
                    # Outer white framing border
                    base = (242, 239, 232)
                else:
                    # Crisp black outer hairline
                    base = (24, 26, 30)
            else:
                # 2. Outer 45-degree Diagonal Diamond Checkerboard Lattice
                # 4 diamond periods per unit ensures 100% seamless wrap at x,y = +-0.5
                u_d = (x + y) * 4.0
                v_d = (x - y) * 4.0
                fu = u_d - math.floor(u_d)
                fv = v_d - math.floor(v_d)
                iu = int(math.floor(u_d))
                iv = int(math.floor(v_d))

                # Grout line between diagonal tiles
                if fu < 0.035 or fu > 0.965 or fv < 0.035 or fv > 0.965:
                    base = (165, 162, 156)
                elif (iu + iv) % 2 == 0:
                    base = (22, 24, 28)
                else:
                    base = (242, 239, 232)

            r = max(0, min(255, base[0] + grain))
            g = max(0, min(255, base[1] + grain))
            b = max(0, min(255, base[2] + grain))
            row.extend((r, g, b))
        raw_rows.append(bytes(row))

    raw_data = b"".join(raw_rows)

    def make_chunk(chunk_type, data):
        return (
            struct.pack(">I", len(data))
            + chunk_type
            + data
            + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw_data, level=6)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + make_chunk(b"IHDR", ihdr)
        + make_chunk(b"IDAT", idat)
        + make_chunk(b"IEND", b"")
    )
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(png_bytes)

generate_crossroads_tile_png(TILE_PNG_PATH, size=512)

# ==============================================================================
# 1. REMOVE PREVIOUS ROTUNDA / CROSSROADS / CLOVER / CHANDELIER MESHES
# ==============================================================================
prefixes_to_remove = (
    "Rotunda_",
    "Floor_Rotunda_Aft_Tile",
    "Ceiling_Rotunda_Aft_Flat",
    "Crossroads_",
    "Clover_",
    "Chandelier_",
    "Ceiling_Crossroads_",
    "Ceiling_Dome_",
    "Ceiling_Chandelier_",
)

for obj in list(bpy.data.objects):
    if obj.name.startswith(prefixes_to_remove):
        bpy.data.objects.remove(obj, do_unlink=True)

# Remove redundant Floor_Dining_Carpet_Alcove that caused Z-fighting in Block 1
alcove_b1 = bpy.data.objects.get("Floor_Dining_Carpet_Alcove")
if alcove_b1:
    bpy.data.objects.remove(alcove_b1, do_unlink=True)

# Lower Block 2 alcove carpets by 4mm in Z so they never Z-fight with Floor_Block2_Dining_Carpet
for b2_alc_name in ("Floor_Block2_Carpet_Alcove_WS1", "Floor_Block2_Carpet_Alcove_WS2"):
    obj = bpy.data.objects.get(b2_alc_name)
    if obj:
        for v in obj.data.vertices:
            if v.co.z > -0.01:
                v.co.z = -0.004
        obj.data.update()

# Trim Ceiling_Recessed_Slab and longitudinal CeilBeam_Y_* so they stop at X=10.15m
# (the Aft pillar line of Block 1 & Block 2) and do NOT poke into the white Crossroads ceiling!
for obj in bpy.data.objects:
    if obj.type == 'MESH' and (
        obj.name == "Ceiling_Recessed_Slab"
        or obj.name.startswith("CeilBeam_Y_")
        or obj.name.startswith("B2_CeilBeam_Y_")
    ):
        changed = False
        for v in obj.data.vertices:
            wco = obj.matrix_world @ v.co
            if wco.x > 10.150:
                v.co.x -= (wco.x - 10.150)
                changed = True
        if changed:
            obj.data.update()

# Update Mat_Corridor_Geometric_Tile with our 2D-tileable medallion + diamond texture
TILE_PERIOD = 1.280
CLOVER_CX = 12.900
CLOVER_CY = 8.730

def compute_tile_uv(vx, vy):
    # Centered at (CLOVER_CX, CLOVER_CY = 8.730) so a full square medallion sits along Y=8.730
    u = 0.5 + (vy - CLOVER_CY) / TILE_PERIOD
    v = 0.5 + (vx - (CLOVER_CX - 0.44)) / TILE_PERIOD
    return (u, v)

mat_tile = bpy.data.materials.get("Mat_Corridor_Geometric_Tile")
if mat_tile and mat_tile.use_nodes:
    img = bpy.data.images.load(TILE_PNG_PATH, check_existing=True)
    img.pack()
    for n in mat_tile.node_tree.nodes:
        if n.type == 'TEX_IMAGE':
            n.image = img
            n.extension = 'REPEAT'
        elif n.type == 'BSDF_PRINCIPLED':
            n.inputs["Roughness"].default_value = 0.28
            if "Sheen Weight" in n.inputs:
                n.inputs["Sheen Weight"].default_value = 0.0
        elif n.type == 'BUMP':
            n.inputs["Strength"].default_value = 0.06

# Update Floor_Corridor_Tile max X to 10.400 and sync its UVs to the seamless 2D grid
corr_tile = bpy.data.objects.get("Floor_Corridor_Tile")
if corr_tile:
    uv_layer = corr_tile.data.uv_layers.active.data if corr_tile.data.uv_layers.active else None
    for v in corr_tile.data.vertices:
        wco = corr_tile.matrix_world @ v.co
        if wco.x > 10.401:
            v.co.x -= (wco.x - 10.400)
    if uv_layer:
        for poly in corr_tile.data.polygons:
            for li in poly.loop_indices:
                vi = corr_tile.data.loops[li].vertex_index
                wco = corr_tile.matrix_world @ corr_tile.data.vertices[vi].co
                uv_layer[li].uv = compute_tile_uv(wco.x, wco.y)
    corr_tile.data.update()

# ==============================================================================
# 2. MATERIALS RETRIEVAL & CREATION
# ==============================================================================
def get_or_create_mat(name, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.4, metallic=0.0,
                      emission_color=None, emission_strength=0.0, coat_weight=0.0):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Sheen Weight" in bsdf.inputs:
            bsdf.inputs["Sheen Weight"].default_value = 0.0
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = coat_weight
        if emission_color and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

mat_carpet = bpy.data.materials.get("Mat_Arlecchino_Carpet")
if mat_carpet and mat_carpet.use_nodes:
    bsdf_c = mat_carpet.node_tree.nodes.get("Principled BSDF")
    if bsdf_c and "Sheen Weight" in bsdf_c.inputs:
        bsdf_c.inputs["Sheen Weight"].default_value = 0.0
        bsdf_c.inputs["Roughness"].default_value = 0.90

mat_wall_white = bpy.data.materials.get("Mat_Classical_Wall_White") or get_or_create_mat(
    "Mat_Classical_Wall_White", (0.95, 0.94, 0.91, 1.0), roughness=0.55
)
mat_wainscot_red = bpy.data.materials.get("Mat_Wainscot_Venetian_Red") or get_or_create_mat(
    "Mat_Wainscot_Venetian_Red", (0.48, 0.04, 0.06, 1.0), roughness=0.42
)
mat_black_steel = bpy.data.materials.get("Mat_Black_Powder_Steel") or get_or_create_mat(
    "Mat_Black_Powder_Steel", (0.06, 0.06, 0.07, 1.0), roughness=0.35, metallic=0.65
)
mat_dark_walnut = bpy.data.materials.get("Mat_Dark_Walnut_Wood") or get_or_create_mat(
    "Mat_Dark_Walnut_Wood", (0.14, 0.08, 0.05, 1.0), roughness=0.38
)
mat_clover_cream = get_or_create_mat(
    "Mat_Clover_Cream_Stone", (0.93, 0.90, 0.83, 1.0), roughness=0.20, metallic=0.0, coat_weight=0.25
)
mat_led_warm = bpy.data.materials.get("Mat_LED_Warm_2700K") or get_or_create_mat(
    "Mat_LED_Warm_2700K", (1.0, 0.93, 0.78, 1.0), roughness=0.15,
    emission_color=(1.0, 0.88, 0.64, 1.0), emission_strength=5.0
)
mat_cove_glow = get_or_create_mat(
    "Mat_Dome_Cove_Glow", (1.0, 0.93, 0.78, 1.0), roughness=0.2,
    emission_color=(1.0, 0.87, 0.62, 1.0), emission_strength=3.2
)
mat_murano_turquoise = get_or_create_mat(
    "Mat_Murano_Turquoise_Glass", (0.08, 0.66, 0.60, 1.0), roughness=0.05, metallic=0.15,
    emission_color=(0.06, 0.52, 0.46, 1.0), emission_strength=0.42, coat_weight=1.0
)
mat_murano_smoked = get_or_create_mat(
    "Mat_Murano_Smoked_Glass", (0.60, 0.54, 0.43, 1.0), roughness=0.05, metallic=0.22,
    emission_color=(0.42, 0.36, 0.25, 1.0), emission_strength=0.22, coat_weight=1.0
)
mat_murano_gold_globe = get_or_create_mat(
    "Mat_Murano_Gold_Globe", (0.56, 0.44, 0.24, 1.0), roughness=0.10, metallic=0.72,
    emission_color=(0.35, 0.26, 0.12, 1.0), emission_strength=0.18, coat_weight=1.0
)
mat_frosted_cup = get_or_create_mat(
    "Mat_Murano_Frosted_Cup", (0.98, 0.96, 0.91, 1.0), roughness=0.18,
    emission_color=(1.0, 0.93, 0.78, 1.0), emission_strength=1.4, coat_weight=0.6
)
mat_brass = get_or_create_mat(
    "Mat_Polished_Brass", (0.82, 0.65, 0.28, 1.0), roughness=0.18, metallic=0.92
)
mat_exit_green = get_or_create_mat(
    "Mat_Exit_Sign_Green", (0.05, 0.62, 0.32, 1.0), roughness=0.2,
    emission_color=(0.08, 0.78, 0.42, 1.0), emission_strength=1.8
)
mat_portrait_art = get_or_create_mat(
    "Mat_Portrait_Art_BW", (0.28, 0.26, 0.25, 1.0), roughness=0.35
)

scene_col = bpy.context.scene.collection

def link_obj(obj):
    if obj.name not in scene_col.objects:
        scene_col.objects.link(obj)
    return obj

def make_box(name, x0, x1, y0, y1, z0, z1, mat):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5), verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj)

def make_cylinder(name, radius, height, location, mat, segments=28):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=height)
    bmesh.ops.translate(bm, vec=location, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj)

# ==============================================================================
# 3. BUILD AFT CROSSROADS FLOOR ("PEREMPATAN KORIDOR") WITH 2D-TILED MEDALLIONS
# ==============================================================================
def make_tiled_floor_slab(name, x0, x1, y0, y1, z0, z1, mat):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5), verts=bm.verts)
    uv_lay = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            vx, vy = loop.vert.co.x, loop.vert.co.y
            loop[uv_lay].uv = compute_tile_uv(vx, vy)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj)

make_tiled_floor_slab("Crossroads_Floor_Main",     10.400, 15.600, 0.000,  13.080, -0.040, 0.000, mat_tile)
make_tiled_floor_slab("Crossroads_Floor_StbdWing", 11.080, 15.600, 13.080, 17.460, -0.040, 0.000, mat_tile)

# ==============================================================================
# 4. CROSSROADS WALLS, ENTRANCE ARCHITRAVES, ARTWORK, SANITIZER & FOREGROUND RAILS
# ==============================================================================
# 4A. Classical White Architrave / Header Soffit across X=10.12..10.46 at Z=2.56..2.79
# (Separates the coffered dining ceilings of Block 1 & Block 2 from the crisp white Crossroads ceiling, per Photo 14.23.51)
make_box("Crossroads_Header_Beam_Port", 10.12, 10.46, 0.00, 7.62,  2.56, 2.79, mat_wall_white)
make_box("Crossroads_Header_Crown_Port", 10.09, 10.49, 0.00, 7.64, 2.71, 2.79, mat_wall_white)
make_box("Crossroads_Header_Beam_Stbd", 10.12, 10.46, 9.84, 13.12, 2.56, 2.79, mat_wall_white)
make_box("Crossroads_Header_Crown_Stbd", 10.09, 10.49, 9.82, 13.14, 2.71, 2.79, mat_wall_white)

# 4B. Portside Aft Wall (Y=0.00..4.25): Step out pier face to X=10.85 so it frames the left of Photo 14.23.51
# with the corner pilaster at Y=4.25 and the large framed B&W portrait + brass picture lamp!
make_box("Crossroads_Port_FwdWall_Plinth", 10.40, 10.89, 0.00, 4.28, 0.00, 0.16, mat_wall_white)
make_box("Crossroads_Port_FwdWall_Red",    10.41, 10.88, 0.00, 4.26, 0.16, 0.84, mat_wainscot_red)
make_box("Crossroads_Port_FwdWall_Rail",   10.40, 10.895, 0.00, 4.29, 0.84, 0.91, mat_wall_white)
make_box("Crossroads_Port_FwdWall_Upper",  10.41, 10.87, 0.00, 4.27, 0.91, 2.79, mat_wall_white)
make_box("Crossroads_Port_FwdWall_Crown",  10.39, 10.90, 0.00, 4.30, 2.70, 2.79, mat_wall_white)

# Framed B&W Portrait on the Portside wall (Y=2.85..3.95, X=10.87..10.91, visible on left of Photo 14.23.51)
make_box("Crossroads_Port_Art_Frame",     10.865, 10.905, 2.85, 3.95, 1.02, 2.12, mat_black_steel)
make_box("Crossroads_Port_Art_Matting",   10.900, 10.910, 2.92, 3.88, 1.09, 2.05, mat_wall_white)
make_box("Crossroads_Port_Art_Canvas",    10.906, 10.914, 3.04, 3.76, 1.19, 1.95, mat_portrait_art)
make_box("Crossroads_Port_Art_LampArm",   10.87,  11.03,  3.37, 3.43, 2.22, 2.26, mat_brass)
make_box("Crossroads_Port_Art_LampShade", 10.98,  11.07,  3.20, 3.60, 2.18, 2.24, mat_brass)

# 4C. Starboardside Aft Wall Cladding (Facing Crossroads +X at X=10.80..11.08, Y=13.05..17.46, right of Photo 14.23.51)
make_box("Crossroads_Stbd_FwdWall_Plinth", 10.80, 11.09, 13.05, 17.46, 0.00, 0.16, mat_wall_white)
make_box("Crossroads_Stbd_FwdWall_Red",    10.81, 11.08, 13.07, 17.44, 0.16, 0.84, mat_wainscot_red)
make_box("Crossroads_Stbd_FwdWall_Rail",   10.80, 11.095, 13.04, 17.46, 0.84, 0.91, mat_wall_white)
make_box("Crossroads_Stbd_FwdWall_Upper",  10.81, 11.07, 13.06, 17.46, 0.91, 2.79, mat_wall_white)
make_box("Crossroads_Stbd_FwdWall_Crown",  10.79, 11.10, 13.03, 17.46, 2.70, 2.79, mat_wall_white)

make_box("Crossroads_Stbd_Return_Plinth",  10.30, 11.09, 13.02, 13.12, 0.00, 0.16, mat_wall_white)
make_box("Crossroads_Stbd_Return_Red",     10.31, 11.08, 13.03, 13.11, 0.16, 0.84, mat_wainscot_red)
make_box("Crossroads_Stbd_Return_Rail",    10.30, 11.095, 13.01, 13.13, 0.84, 0.91, mat_wall_white)
make_box("Crossroads_Stbd_Return_Upper",   10.31, 11.07, 13.03, 13.12, 0.91, 2.79, mat_wall_white)

# 4D. Corridor Ceiling Green EXIT Sign (Centered at Y=8.73, X=10.38, Z=2.63..2.75 per Photos 14.23.51 & 14.23.52)
make_box("Crossroads_ExitSign_Frame", 10.34, 10.40, 8.53, 8.93, 2.63, 2.76, mat_wall_white)
make_box("Crossroads_ExitSign_Panel", 10.335, 10.405, 8.55, 8.91, 2.64, 2.74, mat_exit_green)

# 4E. Portside Outer Wall & Starboard Inboard Wall Extensions (X=10.40..15.60)
make_box("Crossroads_PortHull_Plinth", 10.40, 15.60, -0.19, 0.03, 0.00, 0.15, mat_wall_white)
make_box("Crossroads_PortHull_Red",    10.40, 15.60, -0.17, 0.01, 0.15, 0.83, mat_wainscot_red)
make_box("Crossroads_PortHull_Rail",   10.40, 15.60, -0.19, 0.05, 0.83, 0.89, mat_wall_white)
make_box("Crossroads_PortHull_Upper",  10.40, 15.60, -0.18, 0.02, 0.89, 2.79, mat_wall_white)

make_box("Crossroads_StbdInboard_Plinth", 10.12, 15.60, 17.43, 17.65, 0.00, 0.16, mat_wall_white)
make_box("Crossroads_StbdInboard_Red",    10.12, 15.60, 17.44, 17.64, 0.16, 0.84, mat_wainscot_red)
make_box("Crossroads_StbdInboard_Rail",   10.12, 15.60, 17.42, 17.65, 0.84, 0.91, mat_wall_white)
make_box("Crossroads_StbdInboard_Upper",  10.12, 15.60, 17.45, 17.66, 0.91, 2.79, mat_wall_white)

# 4F. Symmetrical Aft Threshold Railings (visible in bottom-left & bottom-right corners of Photo 14.23.51)
# + Clean Aft Backdrop Wall at X=15.60m (~2m behind Clover Table)
make_box("Crossroads_AftSiku_TopWood_Port_Y", 14.65, 14.74, 6.20, 7.65, 0.858, 0.902, mat_dark_walnut)
make_box("Crossroads_AftSiku_TopWood_Port_X", 14.65, 15.58, 7.588, 7.673, 0.858, 0.902, mat_dark_walnut)
make_box("Crossroads_AftSiku_Post_Port_0",    14.67, 14.71, 7.61, 7.65, 0.00, 0.88, mat_black_steel)
make_box("Crossroads_AftSiku_Post_Port_1",    14.67, 14.71, 6.21, 6.25, 0.00, 0.88, mat_black_steel)

make_box("Crossroads_AftSiku_TopWood_Stbd_Y", 14.65, 14.74, 9.81, 11.26, 0.858, 0.902, mat_dark_walnut)
make_box("Crossroads_AftSiku_TopWood_Stbd_X", 14.65, 15.58, 9.788, 9.872, 0.858, 0.902, mat_dark_walnut)
make_box("Crossroads_AftSiku_Post_Stbd_0",    14.67, 14.71, 9.81, 9.85, 0.00, 0.88, mat_black_steel)
make_box("Crossroads_AftSiku_Post_Stbd_1",    14.67, 14.71, 11.21, 11.25, 0.00, 0.88, mat_black_steel)

make_box("Crossroads_AftBackdrop_Plinth", 15.54, 15.76, 0.00, 17.46, 0.00, 0.16, mat_wall_white)
make_box("Crossroads_AftBackdrop_Red",    15.56, 15.75, 0.00, 17.46, 0.16, 0.84, mat_wainscot_red)
make_box("Crossroads_AftBackdrop_Rail",   15.53, 15.76, 0.00, 17.46, 0.84, 0.91, mat_wall_white)
make_box("Crossroads_AftBackdrop_Upper",  15.57, 15.78, 0.00, 17.46, 0.91, 2.79, mat_wall_white)

# ==============================================================================
# 5. BUILD THE 4-LEAF CLOVER TABLE ("MEJA BENTUK CLOVER")
#    - Exact Corridor Centerline: Y = 8.730m
#    - Center X = 12.900m (~2.0m gap from Block 1 & Block 2 Aft railings/pillars)
#    - 4 circular discs (Ø = 0.75m / 75 cm each):
#      * Portside (Y = 8.29m) & Starboardside (Y = 9.17m) HIGHER (Z_top = 0.90m)
#      * Forward (X = 12.46m) & Aft (X = 13.34m) LOWER (Z_top = 0.76m)
# ==============================================================================
LEAF_RADIUS = 0.375  # 75 cm diameter
LEAF_OFFSET = 0.440

clover_leaves = [
    ("Forward",       CLOVER_CX - LEAF_OFFSET, CLOVER_CY,               0.760, "low"),
    ("Aft",           CLOVER_CX + LEAF_OFFSET, CLOVER_CY,               0.760, "low"),
    ("Portside",      CLOVER_CX,               CLOVER_CY - LEAF_OFFSET, 0.900, "high"),
    ("Starboardside", CLOVER_CX,               CLOVER_CY + LEAF_OFFSET, 0.900, "high"),
]

make_cylinder("Clover_Center_HubPlate", 0.32, 0.032, (CLOVER_CX, CLOVER_CY, 0.738), mat_clover_cream, segments=40)
make_cylinder("Clover_Center_HubRim",   0.326, 0.026, (CLOVER_CX, CLOVER_CY, 0.734), mat_dark_walnut, segments=40)

def make_curved_spider_strut(name, cx, cy, z_start, z_end, r_start, r_end, angle_rad, mat):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    steps = 12
    tube_r = 0.013
    ring_Count = 10
    rings = []

    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    for i in range(steps + 1):
        t = i / steps
        r = r_start + (r_end - r_start) * (t ** 1.35)
        z = z_start + (z_end - z_start) * (1.0 - (1.0 - t) ** 1.45)

        dr = (r_end - r_start) * 1.35 * (max(t, 0.01) ** 0.35)
        dz = (z_end - z_start) * 1.45 * ((1.0 - min(t, 0.99)) ** 0.45)
        tangent = Vector((dr * cos_a, dr * sin_a, dz)).normalized()
        side = Vector((-sin_a, cos_a, 0.0))
        norm = tangent.cross(side).normalized()

        center = Vector((cx + r * cos_a, cy + r * sin_a, z))
        ring_verts = []
        for j in range(ring_Count):
            phi = 2.0 * math.pi * j / ring_Count
            pt = center + tube_r * (math.cos(phi) * side + math.sin(phi) * norm)
            ring_verts.append(bm.verts.new(pt))
        rings.append(ring_verts)

    for i in range(steps):
        for j in range(ring_Count):
            jn = (j + 1) % ring_Count
            bm.faces.new((rings[i][j], rings[i][jn], rings[i + 1][jn], rings[i + 1][j]))

    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj)

for suffix, lx, ly, z_top, tier in clover_leaves:
    top_thick = 0.022
    rim_thick = 0.044
    make_cylinder(
        f"Clover_TopDisc_{suffix}",
        LEAF_RADIUS - 0.004,
        top_thick,
        (lx, ly, z_top - top_thick * 0.5),
        mat_clover_cream,
        segments=48,
    )
    make_cylinder(
        f"Clover_RimBand_{suffix}",
        LEAF_RADIUS,
        rim_thick,
        (lx, ly, z_top - rim_thick * 0.5 - 0.002),
        mat_dark_walnut,
        segments=48,
    )
    make_cylinder(
        f"Clover_SubPlate_{suffix}",
        LEAF_RADIUS * 0.78,
        0.014,
        (lx, ly, z_top - rim_thick - 0.007),
        mat_black_steel,
        segments=36,
    )
    make_cylinder(
        f"Clover_PedBase_{suffix}",
        0.145,
        0.016,
        (lx, ly, 0.008),
        mat_black_steel,
        segments=32,
    )
    col_h = z_top - rim_thick - 0.016
    make_cylinder(
        f"Clover_PedCol_{suffix}",
        0.034,
        col_h,
        (lx, ly, 0.016 + col_h * 0.5),
        mat_black_steel,
        segments=24,
    )
    for k in range(4):
        ang = (math.pi * 0.25) + k * (math.pi * 0.5)
        make_curved_spider_strut(
            f"Clover_Strut_{suffix}_{k}",
            lx,
            ly,
            0.22,
            z_top - rim_thick - 0.005,
            0.032,
            LEAF_RADIUS * 0.76,
            ang,
            mat_black_steel,
        )

# ==============================================================================
# 6. BUILD CROSSROADS CEILING, STEPPED CIRCULAR DOME & GRAND MURANO CHANDELIER
# ==============================================================================
DOME_R_INNER = 1.68
DOME_R_OUTER = 1.94

def make_annulus_ring(name, cx, cy, r_in, r_out, z0, z1, mat, segments=64):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings_in_bot = []
    rings_in_top = []
    rings_out_bot = []
    rings_out_top = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        ca, sa = math.cos(a), math.sin(a)
        rings_in_bot.append(bm.verts.new((cx + r_in * ca, cy + r_in * sa, z0)))
        rings_in_top.append(bm.verts.new((cx + r_in * ca, cy + r_in * sa, z1)))
        rings_out_bot.append(bm.verts.new((cx + r_out * ca, cy + r_out * sa, z0)))
        rings_out_top.append(bm.verts.new((cx + r_out * ca, cy + r_out * sa, z1)))
    for i in range(segments):
        inext = (i + 1) % segments
        bm.faces.new((rings_in_bot[i], rings_out_bot[i], rings_out_bot[inext], rings_in_bot[inext]))
        bm.faces.new((rings_in_top[i], rings_in_top[inext], rings_out_top[inext], rings_out_top[i]))
        bm.faces.new((rings_in_bot[i], rings_in_bot[inext], rings_in_top[inext], rings_in_top[i]))
        bm.faces.new((rings_out_bot[i], rings_out_top[i], rings_out_top[inext], rings_out_bot[inext]))
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj)

# Start flat white ceiling right at X=10.15m (the Aft pillar line of Block 1 & Block 2!)
make_box("Ceiling_Crossroads_Port",     10.15, 15.60, 0.00, CLOVER_CY - DOME_R_OUTER, 2.79, 2.98, mat_wall_white)
make_box("Ceiling_Crossroads_Stbd",     10.15, 15.60, CLOVER_CY + DOME_R_OUTER, 17.46, 2.79, 2.98, mat_wall_white)
make_box("Ceiling_Crossroads_FwdStrip", 10.15, CLOVER_CX - DOME_R_OUTER, CLOVER_CY - DOME_R_OUTER, CLOVER_CY + DOME_R_OUTER, 2.79, 2.98, mat_wall_white)
make_box("Ceiling_Crossroads_AftStrip", CLOVER_CX + DOME_R_OUTER, 15.60, CLOVER_CY - DOME_R_OUTER, CLOVER_CY + DOME_R_OUTER, 2.79, 2.98, mat_wall_white)

make_annulus_ring("Ceiling_Dome_OuterCollar", CLOVER_CX, CLOVER_CY, DOME_R_OUTER - 0.02, DOME_R_OUTER * 1.42, 2.79, 2.98, mat_wall_white, segments=64)

# 3 Stepped Classical Moulding Rings around the circular dome
make_annulus_ring("Ceiling_Dome_StepRing_1", CLOVER_CX, CLOVER_CY, 1.84, 1.96, 2.74, 2.80, mat_wall_white, segments=64)
make_annulus_ring("Ceiling_Dome_StepRing_2", CLOVER_CX, CLOVER_CY, 1.75, 1.86, 2.77, 2.84, mat_wall_white, segments=64)
make_annulus_ring("Ceiling_Dome_StepRing_3", CLOVER_CX, CLOVER_CY, 1.66, 1.77, 2.81, 2.89, mat_wall_white, segments=64)

# Warm 2700K Cove Lighting Ring inside the dome recess
make_annulus_ring("Ceiling_Dome_CoveLED", CLOVER_CX, CLOVER_CY, 1.64, 1.72, 2.88, 2.96, mat_cove_glow, segments=64)

# Upper Recessed Circular Dome Ceiling Slab at Z=[2.96, 3.04]
make_cylinder("Ceiling_Dome_UpperDisk", 2.05, 0.08, (CLOVER_CX, CLOVER_CY, 3.00), mat_wall_white, segments=64)

downlight_coords = [
    (11.15, 6.20), (11.15, 11.26),
    (12.90, 5.40), (12.90, 12.06),
    (14.65, 6.20), (14.65, 11.26),
]
for idx, (dx, dy) in enumerate(downlight_coords):
    make_cylinder(f"Ceiling_Crossroads_Downlight_{idx}", 0.055, 0.015, (dx, dy, 2.785), mat_led_warm, segments=20)

# ==============================================================================
# 7. GRAND 12-ARM VENETIAN MURANO GLASS CHANDELIER (PER PHOTO 14.23.52)
#    With vertically-aligned horn tips, inner metal sockets & ruffled flower cups!
# ==============================================================================
make_cylinder("Ceiling_Chandelier_Rose", 0.11, 0.04, (CLOVER_CX, CLOVER_CY, 2.94), mat_brass, segments=32)
make_cylinder("Ceiling_Chandelier_Rod",  0.018, 0.62, (CLOVER_CX, CLOVER_CY, 2.63), mat_brass, segments=20)
make_cylinder("Ceiling_Chandelier_UpperCrown", 0.095, 0.05, (CLOVER_CX, CLOVER_CY, 2.52), mat_frosted_cup, segments=28)

def make_oblate_sphere(name, cx, cy, cz, rx, ry, rz, mat, u_seg=36, v_seg=24):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u_seg, v_segments=v_seg, radius=1.0)
    bmesh.ops.scale(bm, vec=(rx, ry, rz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj)

make_oblate_sphere("Ceiling_Chandelier_UpperVase",   CLOVER_CX, CLOVER_CY, 2.41, 0.105, 0.105, 0.11, mat_murano_smoked)
make_annulus_ring("Ceiling_Chandelier_MidCollar",    CLOVER_CX, CLOVER_CY, 0.08, 0.165, 2.31, 2.345, mat_frosted_cup, segments=36)
make_oblate_sphere("Ceiling_Chandelier_MainGlobe",   CLOVER_CX, CLOVER_CY, 2.19, 0.245, 0.245, 0.145, mat_murano_gold_globe, u_seg=42, v_seg=28)
make_oblate_sphere("Ceiling_Chandelier_BottomFinial", CLOVER_CX, CLOVER_CY, 2.02, 0.055, 0.055, 0.045, mat_frosted_cup, u_seg=24, v_seg=16)

def make_murano_horn_arm(name, cx, cy, angle_rad, r_end, z_end, mat):
    """Builds a cubic Bezier S-curved Venetian glass horn arm whose tip is strictly vertical at (r_end, z_end)."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    steps = 18
    ring_cnt = 14
    rings = []

    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Control points in (r, z): P2 and P3 share r = r_end so tangent at t=1 is strictly vertical (dr=0, dz>0)!
    p0_r, p0_z = 0.16, 2.27
    p1_r, p1_z = 0.30, 1.96
    p2_r, p2_z = r_end, 2.02
    p3_r, p3_z = r_end, z_end

    def eval_rz(t):
        u = 1.0 - t
        r = (u**3)*p0_r + 3*(u**2)*t*p1_r + 3*u*(t**2)*p2_r + (t**3)*p3_r
        z = (u**3)*p0_z + 3*(u**2)*t*p1_z + 3*u*(t**2)*p2_z + (t**3)*p3_z
        return r, z

    for i in range(steps + 1):
        t = i / steps
        r, z = eval_rz(t)
        # Horn radius flares smoothly from 1.6cm at the globe to 4.0cm at the flower cup
        tube_r = 0.015 + 0.025 * (t ** 1.5)

        t_a = max(0.0, t - 0.01)
        t_b = min(1.0, t + 0.01)
        ra, za = eval_rz(t_a)
        rb, zb = eval_rz(t_b)
        tang = Vector(((rb - ra) * cos_a, (rb - ra) * sin_a, zb - za)).normalized()
        side = Vector((-sin_a, cos_a, 0.0))
        norm = tang.cross(side).normalized()

        center = Vector((cx + r * cos_a, cy + r * sin_a, z))
        ring_verts = []
        for j in range(ring_cnt):
            phi = 2.0 * math.pi * j / ring_cnt
            flute = 1.0 + 0.05 * math.sin(6.0 * phi)
            pt = center + (tube_r * flute) * (math.cos(phi) * side + math.sin(phi) * norm)
            ring_verts.append(bm.verts.new(pt))
        rings.append(ring_verts)

    for i in range(steps):
        for j in range(ring_cnt):
            jn = (j + 1) % ring_cnt
            bm.faces.new((rings[i][j], rings[i][jn], rings[i + 1][jn], rings[i + 1][j]))

    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj)

def make_ruffled_bobeche(name, cx, cy, z_base, mat):
    """Creates a scalloped Venetian flower-cup bobèche at the top of each glass horn."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    segs = 24
    r_bot = 0.038
    r_top = 0.072
    h = 0.042
    bot_ring = []
    top_ring = []
    for j in range(segs):
        phi = 2.0 * math.pi * j / segs
        scallop = 1.0 + 0.12 * math.sin(8.0 * phi)
        wave_z = 0.005 * math.cos(8.0 * phi)
        bot_ring.append(bm.verts.new((cx + r_bot * math.cos(phi), cy + r_bot * math.sin(phi), z_base)))
        top_ring.append(bm.verts.new((cx + (r_top * scallop) * math.cos(phi), cy + (r_top * scallop) * math.sin(phi), z_base + h + wave_z)))
    for j in range(segs):
        jn = (j + 1) % segs
        bm.faces.new((bot_ring[j], bot_ring[jn], top_ring[jn], top_ring[j]))
    bm.faces.new(bot_ring)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj)

NUM_ARMS = 12
for i in range(NUM_ARMS):
    ang = i * (2.0 * math.pi / NUM_ARMS)
    is_turquoise = (i % 2 == 0)
    arm_mat = mat_murano_turquoise if is_turquoise else mat_murano_smoked
    r_tip = 0.62 if is_turquoise else 0.54
    z_tip = 2.50 if is_turquoise else 2.44

    make_murano_horn_arm(
        f"Ceiling_Chandelier_Arm_{i:02d}",
        CLOVER_CX,
        CLOVER_CY,
        ang,
        r_tip,
        z_tip,
        arm_mat,
    )

    bx = CLOVER_CX + r_tip * math.cos(ang)
    by = CLOVER_CY + r_tip * math.sin(ang)

    # Dark metal bulb socket inside top of glass horn (visible in Photo 14.23.52)
    make_cylinder(
        f"Ceiling_Chandelier_Socket_{i:02d}",
        0.022,
        0.065,
        (bx, by, z_tip - 0.022),
        mat_black_steel,
        segments=18,
    )
    # Ruffled frosted flower-cup bobèche
    make_ruffled_bobeche(
        f"Ceiling_Chandelier_Bobeche_{i:02d}",
        bx,
        by,
        z_tip - 0.004,
        mat_frosted_cup,
    )
    # Warm glowing globe bulb inside the bobèche cup
    make_oblate_sphere(
        f"Ceiling_Chandelier_Bulb_{i:02d}",
        bx,
        by,
        z_tip + 0.052,
        0.036,
        0.036,
        0.044,
        mat_led_warm,
        u_seg=18,
        v_seg=14,
    )

# ==============================================================================
# 8. SAVE .BLEND AND EXPORT .GLB
# ==============================================================================
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format='GLB',
    export_apply=True,
    export_materials='EXPORT',
)
print("SUCCESS: Refined Aft Crossroads 2D-Tiled Floor, Clover Table, Dome & 12-Arm Murano Chandelier!")
