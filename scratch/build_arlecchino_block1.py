import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler

# ==============================================================================
# COSTA SMERALDA - RISTORANTE ARLECCHINO (DECK 6 ROMA, STARBOARD BLOCK 1)
# High-Precision 3D Interior Builder forBlender 5.2 LTS
# ==============================================================================

TEX_DIR = "/Users/dianjulie/Documents/Map Project/scratch/textures"
OUT_DIR = "/Users/dianjulie/Documents/Map Project"
RENDER_DIR = "/Users/dianjulie/Documents/Map Project/scratch/renders"
os.makedirs(RENDER_DIR, exist_ok=True)

# Room Physical Dimensions (Block 1 Portside: Y=0..7.58m | Corridor: Y=7.58..9.88m | Block 2 Starboardside: Y=9.88..17.46m)
ROOM_LEN_X = 10.40   # X: 0.0 (Forward/Service wall) to 10.40m (Aft/Rotunda wall)
ROOM_WID_Y = 7.58    # Y: 0.0 (Portside Hull Window wall) to 7.58m (Block 1 Pillar/Railing line)
CORR_WID_Y = 2.30    # Y: 7.58m to 9.88m (Black & White Geometric Tiled Corridor between Block 1 and Block 2)
B2_PILLAR_Y = ROOM_WID_Y + CORR_WID_Y  # 9.88m (Block 2 Starboardside Pillar/Railing line)
B2_WALL_Y = B2_PILLAR_Y + ROOM_WID_Y   # 17.46m (Block 2 Inboard Banquette Sofa Wall)
CEIL_H = 2.78        # Z: Main ceiling soffit height
COFFER_H = 2.96      # Z: Recessed coffer height


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def get_or_create_collection(name, parent=None):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def link_to_collection(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def set_bsdf(bsdf, **kwargs):
    """Safely set Principled BSDF sockets across Blender 4.x / 5.x."""
    socket_aliases = {
        "Base Color": ["Base Color"],
        "Roughness": ["Roughness"],
        "Metallic": ["Metallic"],
        "IOR": ["IOR"],
        "Specular": ["Specular IOR Level", "Specular"],
        "Coat Weight": ["Coat Weight", "Clearcoat"],
        "Coat Roughness": ["Coat Roughness", "Clearcoat Roughness"],
        "Sheen Weight": ["Sheen Weight", "Sheen"],
        "Sheen Roughness": ["Sheen Roughness"],
        "Sheen Tint": ["Sheen Tint"],
        "Transmission Weight": ["Transmission Weight", "Transmission"],
        "Emission Color": ["Emission Color", "Emission"],
        "Emission Strength": ["Emission Strength"],
    }
    for k, val in kwargs.items():
        targets = socket_aliases.get(k, [k])
        for t in targets:
            if t in bsdf.inputs:
                bsdf.inputs[t].default_value = val
                break


def make_material(name, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.0,
                  coat=0.0, coat_rough=0.1, sheen=0.0, sheen_rough=0.5,
                  transmission=0.0, emission=None, emission_strength=0.0,
                  tex_path=None, uv_scale=(1.0, 1.0), bump_strength=0.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    set_bsdf(
        bsdf,
        **{
            "Base Color": base_color,
            "Roughness": roughness,
            "Metallic": metallic,
            "Coat Weight": coat,
            "Coat Roughness": coat_rough,
            "Sheen Weight": sheen,
            "Sheen Roughness": sheen_rough,
            "Transmission Weight": transmission,
        }
    )
    if emission is not None and emission_strength > 0.0:
        set_bsdf(bsdf, **{"Emission Color": emission, "Emission Strength": emission_strength})

    if tex_path and os.path.exists(tex_path):
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-700, 0)
        mapping = nodes.new("ShaderNodeMapping")
        mapping.location = (-500, 0)
        mapping.inputs["Scale"].default_value = (uv_scale[0], uv_scale[1], 1.0)
        links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

        tex_img = nodes.new("ShaderNodeTexImage")
        tex_img.location = (-250, 0)
        tex_img.image = bpy.data.images.load(tex_path, check_existing=True)
        links.new(mapping.outputs["Vector"], tex_img.inputs["Vector"])
        links.new(tex_img.outputs["Color"], bsdf.inputs["Base Color"])

        if bump_strength > 0.0:
            bump = nodes.new("ShaderNodeBump")
            bump.location = (-50, -220)
            bump.inputs["Strength"].default_value = bump_strength
            bump.inputs["Distance"].default_value = 0.005
            links.new(tex_img.outputs["Color"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def apply_box_uv(obj, scale_per_meter=1.0):
    """Assigns clean metric planar/box UVs to a mesh object so textures tile accurately."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv_layer = me.uv_layers.active.data
    verts = me.vertices
    for poly in me.polygons:
        nx, ny, nz = abs(poly.normal.x), abs(poly.normal.y), abs(poly.normal.z)
        for loop_idx in poly.loop_indices:
            v = verts[me.loops[loop_idx].vertex_index].co
            if nz >= nx and nz >= ny:
                u, w = v.x * scale_per_meter, v.y * scale_per_meter
            elif ny >= nx and ny >= nz:
                u, w = v.x * scale_per_meter, v.z * scale_per_meter
            else:
                u, w = v.y * scale_per_meter, v.z * scale_per_meter
            uv_layer[loop_idx].uv = (u, w)


def apply_normalized_face_uv(obj):
    """Maps a single quad/box front face 0..1 for artwork/paintings."""
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


def apply_corridor_runner_uv(obj, y_center=7.96, uv_width_y=2.04, pitch_x=1.02, x_offset=0.20):
    """
    Maps the 2048x1024 corridor_tile.png symmetrically along the corridor:
    - Computes world coordinates directly from obj.location + v.co (avoiding stale matrix_world before scene update).
    - U = 0.5 is locked to y_center (7.96m, exact midpoint between Pillar corridor face Y=7.10m and Corridor Wall Y=8.82m).
    - U spans width uv_width_y (2.04m), so the central medallion + triangles (U=0.25..0.75) spans 1.02m (Y=7.45..8.47m),
      flanked symmetrically by 0.35m of plain dark charcoal ceramic tiles on both the pillar side and wall side.
    - V tiles along world X with period pitch_x = 1.02m (1:1 square aspect ratio for every medallion).
    """
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
# MATERIAL PALETTE (Matched to 8 On-Site Photos of Ristorante Arlecchino)
# ==============================================================================
def build_materials():
    mats = {}
    mats["carpet"] = make_material(
        "Mat_Arlecchino_Carpet",
        roughness=0.88,
        sheen=0.35,
        sheen_rough=0.8,
        tex_path=os.path.join(TEX_DIR, "arlecchino_carpet.png"),
        uv_scale=(1.0, 1.0),
        bump_strength=0.18,
    )
    mats["corridor_tile"] = make_material(
        "Mat_Corridor_Geometric_Tile",
        roughness=0.22,
        coat=0.35,
        coat_rough=0.12,
        tex_path=os.path.join(TEX_DIR, "corridor_tile.png"),
        uv_scale=(1.0, 1.0),
        bump_strength=0.05,
    )
    mats["marble_top"] = make_material(
        "Mat_Carrara_Marble_Top",
        roughness=0.14,
        coat=0.85,
        coat_rough=0.06,
        tex_path=os.path.join(TEX_DIR, "carrara_marble.png"),
        uv_scale=(1.0, 1.0),
    )
    mats["dark_marble"] = make_material(
        "Mat_Emperador_Dark_Marble",
        base_color=(0.11, 0.06, 0.05, 1.0),
        roughness=0.16,
        coat=0.8,
        coat_rough=0.08,
    )
    mats["velvet_maroon"] = make_material(
        "Mat_Velvet_Burgundy_Maroon",
        base_color=(0.115, 0.004, 0.012, 1.0),
        roughness=0.62,
        sheen=0.35,
        sheen_rough=0.45,
    )
    mats["leather_ivory"] = make_material(
        "Mat_Leatherette_Ivory_Cream",
        base_color=(0.76, 0.71, 0.62, 1.0),
        roughness=0.36,
        coat=0.18,
        coat_rough=0.32,
    )
    mats["wall_white"] = make_material(
        "Mat_Classical_Wall_White",
        base_color=(0.88, 0.85, 0.79, 1.0),
        roughness=0.34,
        coat=0.12,
    )
    mats["wall_red"] = make_material(
        "Mat_Wainscot_Venetian_Red",
        base_color=(0.20, 0.008, 0.016, 1.0),
        roughness=0.26,
        coat=0.45,
        coat_rough=0.15,
    )
    mats["ceiling_dark"] = make_material(
        "Mat_Coffer_Charcoal_Slate",
        base_color=(0.14, 0.16, 0.18, 1.0),
        roughness=0.45,
    )
    mats["black_metal"] = make_material(
        "Mat_Black_Powder_Steel",
        base_color=(0.04, 0.04, 0.045, 1.0),
        roughness=0.32,
        metallic=0.85,
    )
    mats["wood_walnut"] = make_material(
        "Mat_Dark_Walnut_Wood",
        base_color=(0.12, 0.065, 0.04, 1.0),
        roughness=0.28,
        coat=0.5,
        coat_rough=0.15,
    )
    mats["chair_leg"] = make_material(
        "Mat_Espresso_Chair_Leg",
        base_color=(0.05, 0.035, 0.03, 1.0),
        roughness=0.30,
    )
    mats["brass"] = make_material(
        "Mat_Polished_Brass",
        base_color=(0.85, 0.66, 0.28, 1.0),
        roughness=0.18,
        metallic=0.95,
    )
    mats["chrome"] = make_material(
        "Mat_Polished_Chrome",
        base_color=(0.88, 0.89, 0.91, 1.0),
        roughness=0.10,
        metallic=0.98,
    )
    mats["murano_glass"] = make_material(
        "Mat_Murano_Green_Glass",
        base_color=(0.35, 0.78, 0.64, 1.0),
        roughness=0.08,
        transmission=0.85,
        coat=0.8,
    )
    mats["blind_cream"] = make_material(
        "Mat_Roman_Blind_Cream",
        base_color=(0.84, 0.80, 0.73, 1.0),
        roughness=0.65,
        sheen=0.3,
    )
    mats["led_warm"] = make_material(
        "Mat_LED_Warm_2700K",
        base_color=(1.0, 0.92, 0.78, 1.0),
        emission=(1.0, 0.86, 0.64, 1.0),
        emission_strength=14.0,
    )
    mats["led_red"] = make_material(
        "Mat_LED_Accent_Red",
        base_color=(1.0, 0.15, 0.12, 1.0),
        emission=(1.0, 0.12, 0.08, 1.0),
        emission_strength=18.0,
    )
    mats["window_daylight"] = make_material(
        "Mat_Window_Sea_Daylight",
        base_color=(0.88, 0.95, 1.0, 1.0),
        roughness=0.9,
        emission=(0.85, 0.93, 1.0, 1.0),
        emission_strength=1.4,
        tex_path=os.path.join(TEX_DIR, "ocean_view.png"),
    )
    mats["window_glass"] = make_material(
        "Mat_Marine_Window_Glass",
        base_color=(0.92, 0.97, 1.0, 1.0),
        roughness=0.04,
        transmission=0.92,
        coat=0.9,
    )
    mats["art_1"] = make_material(
        "Mat_Framed_Art_1",
        roughness=0.2,
        coat=0.6,
        tex_path=os.path.join(TEX_DIR, "framed_art_1.png"),
    )
    mats["art_2"] = make_material(
        "Mat_Framed_Art_2",
        roughness=0.2,
        coat=0.6,
        tex_path=os.path.join(TEX_DIR, "framed_art_2.png"),
    )
    mats["art_3"] = make_material(
        "Mat_Framed_Art_3",
        roughness=0.2,
        coat=0.6,
        tex_path=os.path.join(TEX_DIR, "framed_art_3.png"),
    )
    mats["plates_wall"] = make_material(
        "Mat_Plates_Wall",
        roughness=0.15,
        coat=0.8,
        tex_path=os.path.join(TEX_DIR, "plates_wall.png"),
    )
    mats["fire_sticker"] = make_material(
        "Mat_Fire_Safety_Sign",
        roughness=0.3,
        tex_path=os.path.join(TEX_DIR, "fire_sticker.png"),
    )
    mats["plant_green"] = make_material(
        "Mat_Succulent_Green",
        base_color=(0.16, 0.38, 0.18, 1.0),
        roughness=0.55,
    )
    mats["menu_card"] = make_material(
        "Mat_Costa_Menu_Stand",
        base_color=(0.94, 0.91, 0.87, 1.0),
        roughness=0.25,
        coat=0.7,
    )
    return mats


# ==============================================================================
# MODULAR FURNITURE ASSETS (CHAIRS, CARRARA MARBLE TABLES, ACCESSORIES)
# ==============================================================================
def create_chair_template(name, upholstery_mat, leg_mat, col):
    """
    Creates a detailed Italian dining chair matching the Arlecchino photos:
    - 4 tapered dark espresso legs
    - Thick upholstered seat cushion with rounded bevel
    - Curved channel-tufted backrest (5 vertical flutes)
    - Signature winged/rolled top ear-rail crest (seen in all 8 photos)
    Returns root parent Empty/Mesh or joined mesh for fast instancing.
    """
    bm = bmesh.new()
    # We'll create two meshes (upholstery and legs) and join them into one multi-material mesh!
    # Wait: multi-material single mesh makes instancing 100+ chairs effortless and super clean!
    me = bpy.data.meshes.new(name + "_mesh")
    me.materials.append(upholstery_mat)  # slot 0
    me.materials.append(leg_mat)         # slot 1

    def add_bm_part(bmesh_target, size, center, rot_euler=(0, 0, 0), bevel_amt=0.015, mat_idx=0, taper_top=1.0, taper_bot=1.0):
        temp = bmesh.new()
        bmesh.ops.create_cube(temp, size=1.0)
        for v in temp.verts:
            if v.co.z > 0:
                v.co.x *= taper_top
                v.co.y *= taper_top
            else:
                v.co.x *= taper_bot
                v.co.y *= taper_bot
        bmesh.ops.scale(temp, vec=size, verts=temp.verts)
        if bevel_amt > 0:
            bmesh.ops.bevel(temp, geom=temp.edges, offset=bevel_amt, segments=3, profile=0.5, affect='EDGES')
        rot_mat = Euler(rot_euler, 'XYZ').to_matrix().to_4x4()
        bmesh.ops.transform(temp, matrix=rot_mat, verts=temp.verts)
        bmesh.ops.translate(temp, vec=center, verts=temp.verts)
        for f in temp.faces:
            f.material_index = mat_idx
            f.smooth = True
        # Merge into main bm
        vert_map = {}
        for v in temp.verts:
            vert_map[v] = bmesh_target.verts.new(v.co)
        for f in temp.faces:
            try:
                nf = bmesh_target.faces.new([vert_map[v] for v in f.verts])
                nf.material_index = f.material_index
                nf.smooth = True
            except ValueError:
                pass
        temp.free()

    # Chair local coordinates:
    # Center at (0, 0, 0) on the floor; chair faces +Y (front of seat is +Y, backrest is -Y)
    # 1. Four tapered legs (mat_idx=1)
    leg_positions = [
        (-0.20,  0.19, 0.215, ( 0.04, -0.03, 0)),
        ( 0.20,  0.19, 0.215, ( 0.04,  0.03, 0)),
        (-0.19, -0.20, 0.215, (-0.07, -0.03, 0)),
        ( 0.19, -0.20, 0.215, (-0.07,  0.03, 0)),
    ]
    for lx, ly, lz, lrot in leg_positions:
        add_bm_part(bm, (0.042, 0.042, 0.43), (lx, ly, lz), rot_euler=lrot, bevel_amt=0.006, mat_idx=1, taper_top=1.0, taper_bot=0.62)

    # Under-seat frame rails (mat_idx=1)
    add_bm_part(bm, (0.42, 0.41, 0.035), (0.0, -0.005, 0.41), bevel_amt=0.005, mat_idx=1)

    # 2. Upholstered Seat Cushion (mat_idx=0)
    add_bm_part(bm, (0.48, 0.46, 0.085), (0.0, 0.01, 0.455), bevel_amt=0.024, mat_idx=0, taper_top=1.02, taper_bot=0.95)

    # 3. Channel-Tufted Backrest (5 vertical fluted panels curved slightly around the sitter)
    flute_xs = [-0.17, -0.085, 0.0, 0.085, 0.17]
    for fx in flute_xs:
        curve_y = -0.205 + abs(fx) * 0.12
        yaw = -fx * 0.45
        add_bm_part(
            bm,
            (0.088, 0.068, 0.39),
            (fx, curve_y, 0.67),
            rot_euler=(-0.11, 0.0, yaw),
            bevel_amt=0.020,
            mat_idx=0,
        )

    # Back outer support shell (smooth curved back panel)
    add_bm_part(
        bm,
        (0.47, 0.045, 0.40),
        (0.0, -0.222, 0.675),
        rot_euler=(-0.11, 0.0, 0.0),
        bevel_amt=0.018,
        mat_idx=0,
        taper_top=1.05,
        taper_bot=0.94,
    )

    # 4. Signature Rolled Top Crest & Winged Side Ears (seen clearly in 14.14.04(3) & 14.14.06)
    add_bm_part(
        bm,
        (0.51, 0.095, 0.095),
        (0.0, -0.235, 0.875),
        rot_euler=(-0.12, 0.0, 0.0),
        bevel_amt=0.032,
        mat_idx=0,
    )
    # Left & Right wrapped ear bolsters at top of backrest
    for side in (-1.0, 1.0):
        add_bm_part(
            bm,
            (0.065, 0.115, 0.105),
            (side * 0.235, -0.195, 0.865),
            rot_euler=(-0.08, 0.0, side * 0.25),
            bevel_amt=0.025,
            mat_idx=0,
        )

    bm.to_mesh(me)
    bm.free()
    return me


def spawn_chair(name, chair_mesh, location, yaw_rad, col):
    obj = bpy.data.objects.new(name, chair_mesh)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, yaw_rad)
    link_to_collection(obj, col)
    return obj


def build_table_assembly(table_id, center_xy, length_x, width_y, yaw_rad, chair_variant_mesh, pax_count, mats, col, skip_side_b=False):
    """
    Builds a complete dining table group (named `Table_<ID>`) with:
    - White Carrara marble tabletop (beveled glossy slab, Z = 0.75m)
    - Black steel cylindrical pedestal column(s) + cast-iron circular base plate(s)
    - Tabletop accessories (Costa Menu Stand, mini succulent planter, salt & pepper shakers)
    - Surrounding dining chairs (4-pax or 6-pax)
    """
    t_col = get_or_create_collection(f"Table_{table_id}", parent=col)
    cx, cy = center_xy
    cos_a = math.cos(yaw_rad)
    sin_a = math.sin(yaw_rad)

    def to_world(lx, ly, lz):
        wx = cx + lx * cos_a - ly * sin_a
        wy = cy + lx * sin_a + ly * cos_a
        return (wx, wy, lz)

    # 1. Carrara Marble Tabletop (thickness 0.032m, top at Z=0.755m)
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
    # Dark under-table sub-apron
    add_box(
        f"TableSubTop_{table_id}",
        (length_x - 0.08, width_y - 0.08, 0.022),
        to_world(0.0, 0.0, 0.715),
        mats["black_metal"],
        t_col,
        rot=(0.0, 0.0, yaw_rad),
    )

    # 2. Pedestal Column(s) & Round Cast-Iron Base Plate(s)
    if length_x <= 1.0:
        ped_xs = [0.0]
    elif length_x <= 1.65:
        ped_xs = [-length_x * 0.28, length_x * 0.28]
    else:
        ped_xs = [-length_x * 0.32, 0.0, length_x * 0.32]

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

    # 3. Tabletop Accessories removed per user request (clean, empty marble tabletops)

    # 4. Chairs along both long sides (+Y and -Y in local table coords)
    chairs_per_side = max(1, pax_count // 2)
    if chairs_per_side == 1:
        chair_xs = [0.0]
    elif chairs_per_side == 2:
        chair_xs = [-length_x * 0.27, length_x * 0.27]
    else:
        chair_xs = [-length_x * 0.33, 0.0, length_x * 0.33]

    chair_offset_y = width_y * 0.5 + 0.19
    for c_i, ch_x in enumerate(chair_xs):
        # -Y side chair facing +Y (into the table)
        spawn_chair(
            f"Chair_{table_id}_A{c_i+1}",
            chair_variant_mesh,
            to_world(ch_x, -chair_offset_y, 0.0),
            yaw_rad,
            t_col,
        )
        if not skip_side_b:
            # +Y side chair facing -Y (into the table)
            spawn_chair(
                f"Chair_{table_id}_B{c_i+1}",
                chair_variant_mesh,
                to_world(ch_x, chair_offset_y, 0.0),
                yaw_rad + math.pi,
                t_col,
            )

    return top_obj


# ==============================================================================
# ARCHITECTURAL STRUCTURE: FLOOR, WINDOWS, PILLARS, X-RAILING, COFFERED CEILING
# ==============================================================================
def build_architecture(mats, arch_col):
    # Pintu Masuk Kedua width remains 1.25m (X = -0.10m .. 1.15m), while the recessed walls in Block 1 & Block 2 step deeper in -X
    FWD_WALL_X = -1.55
    EXT_LEN_X = ROOM_LEN_X - FWD_WALL_X  # 11.95m
    EXT_MID_X = (FWD_WALL_X + ROOM_LEN_X) * 0.5  # 4.425m

    # 1. Floors
    # Block 1 (Portside) Dining Room Carpet Floor (X: -1.55..10.4, Y: 0..7.58)
    add_box(
        "Floor_Dining_Carpet",
        (EXT_LEN_X, ROOM_WID_Y, 0.04),
        (EXT_MID_X, ROOM_WID_Y * 0.5, -0.02),
        mats["carpet"],
        arch_col,
        uv_metric=0.58,
    )
    # Block 2 (Starboardside) Dining Room Carpet Floor (X: -1.95..10.40, Y: 9.88..17.46)
    B2_FWD_WALL_X = -1.95
    B2_EXT_LEN_X = ROOM_LEN_X - B2_FWD_WALL_X  # 12.35m
    B2_EXT_MID_X = (B2_FWD_WALL_X + ROOM_LEN_X) * 0.5  # 4.225m
    add_box(
        "Floor_Block2_Dining_Carpet",
        (B2_EXT_LEN_X, ROOM_WID_Y, 0.04),
        (B2_EXT_MID_X, (B2_PILLAR_Y + B2_WALL_Y) * 0.5, -0.02),
        mats["carpet"],
        arch_col,
        uv_metric=0.58,
    )
    # Extra carpet strips covering the recessed Waiter Station alcoves in Block 2
    add_box(
        "Floor_Block2_Carpet_Alcove_WS1",
        (2.60, 0.80, 0.04),
        (-0.70, B2_WALL_Y + 0.33, -0.02),
        mats["carpet"],
        arch_col,
        uv_metric=0.58,
    )
    add_box(
        "Floor_Block2_Carpet_Alcove_WS2",
        (0.75, 2.80, 0.04),
        (ROOM_LEN_X + 0.30, 14.50, -0.02),
        mats["carpet"],
        arch_col,
        uv_metric=0.58,
    )

    # Central Corridor Geometric Black-and-White Tile Floor (X: -2.35..10.50, Y: 7.58..9.88)
    corr_y_min = ROOM_WID_Y      # 7.58m (Block 1 Pillar centerline)
    corr_y_max = B2_PILLAR_Y     # 9.88m (Block 2 Pillar centerline)
    corr_y_mid = (corr_y_min + corr_y_max) * 0.5  # 8.73m (Exact midpoint of corridor)
    corr_x_min = -2.35
    corr_x_max = ROOM_LEN_X + 0.10
    corr_floor_obj = add_box(
        "Floor_Corridor_Tile",
        (corr_x_max - corr_x_min, corr_y_max - corr_y_min, 0.04),
        ((corr_x_min + corr_x_max) * 0.5, corr_y_mid, -0.02),
        mats["corridor_tile"],
        arch_col,
    )
    apply_corridor_runner_uv(corr_floor_obj, y_center=corr_y_mid, uv_width_y=2.04, pitch_x=1.02, x_offset=0.20)

    # 2. Outer Hull Window Wall (Y = 0.0, X = -0.85 to 10.4)
    # Continuous lower wainscoting along hull (Z = 0..0.86m)
    add_box("Hull_Plinth", (EXT_LEN_X, 0.22, 0.15), (EXT_MID_X, -0.08, 0.075), mats["wall_white"], arch_col)
    add_box("Hull_Red_Wainscot", (EXT_LEN_X, 0.18, 0.68), (EXT_MID_X, -0.08, 0.49), mats["wall_red"], arch_col)
    add_box("Hull_Chair_Rail", (EXT_LEN_X, 0.24, 0.06), (EXT_MID_X, -0.07, 0.86), mats["wall_white"], arch_col, bevel=0.008)
    # Continuous header above windows (Z = 2.50..2.78m)
    add_box("Hull_Window_Header", (EXT_LEN_X, 0.22, 0.30), (EXT_MID_X, -0.08, 2.64), mats["wall_white"], arch_col)

    # Structural Wall Piers between the 3 Panoramic Ocean Windows
    # Window 1: X = 0.85..3.15 | Pier 1: X = 3.15..4.15 | Window 2: X = 4.15..6.45 | Pier 2: X = 6.45..7.45 | Window 3: X = 7.45..9.75
    pier_ranges = [
        (FWD_WALL_X, 0.85, False, None),
        (3.15, 4.15, True, mats["art_2"]),
        (6.45, 7.45, True, mats["art_3"]),
        (9.75, ROOM_LEN_X, False, None),
    ]
    for p_idx, (x0, x1, has_art, art_mat) in enumerate(pier_ranges):
        pw = x1 - x0
        px = (x0 + x1) * 0.5
        # Upper white paneled pier
        add_box(f"Hull_Pier_{p_idx}", (pw, 0.24, 1.65), (px, -0.04, 1.70), mats["wall_white"], arch_col, bevel=0.005)
        # Decorative red border strip on window jambs (offset cleanly to avoid coplanar overlap)
        if x0 > 0.1:
            add_box(f"Hull_JambRed_L_{p_idx}", (0.055, 0.18, 1.60), (x0 - 0.028, -0.05, 1.69), mats["wall_red"], arch_col)
        if x1 < ROOM_LEN_X - 0.1:
            add_box(f"Hull_JambRed_R_{p_idx}", (0.055, 0.18, 1.60), (x1 + 0.028, -0.05, 1.69), mats["wall_red"], arch_col)

        if has_art and art_mat:
            # Black Picture Frame + Cropped Real B&W Art + Brass Picture Light (as in 14.14.03 & 14.14.05)
            add_box(f"Pier_Frame_{p_idx}", (0.58, 0.03, 0.72), (px, 0.09, 1.66), mats["black_metal"], arch_col, bevel=0.004)
            add_box(f"Pier_MatBoard_{p_idx}", (0.52, 0.034, 0.66), (px, 0.092, 1.66), mats["wall_white"], arch_col)
            art_obj = add_box(f"Pier_Art_{p_idx}", (0.38, 0.038, 0.52), (px, 0.095, 1.66), art_mat, arch_col)
            apply_normalized_face_uv(art_obj)
            # Brass picture lamp above frame
            add_cylinder(f"Pier_LampBar_{p_idx}", 0.012, 0.42, (px, 0.16, 2.08), mats["brass"], arch_col, rot=(0, math.pi * 0.5, 0))
            add_box(f"Pier_LampGlow_{p_idx}", (0.38, 0.02, 0.015), (px, 0.16, 2.065), mats["led_warm"], arch_col)

    # 3 Panoramic Ocean Windows + Roman Blinds (Tirai Lipat Romawi)
    win_ranges = [(0.85, 3.15), (4.15, 6.45), (7.45, 9.75)]
    for w_idx, (wx0, wx1) in enumerate(win_ranges):
        ww = wx1 - wx0
        wcx = (wx0 + wx1) * 0.5
        # Glass pane
        add_box(f"Win_Glass_{w_idx}", (ww, 0.015, 1.60), (wcx, -0.12, 1.68), mats["window_glass"], arch_col)
        # 2 vertical white window mullions dividing each window into 3 panes
        for m_i in (1, 2):
            mx = wx0 + ww * (m_i / 3.0)
            add_box(f"Win_Mullion_{w_idx}_{m_i}", (0.048, 0.065, 1.60), (mx, -0.09, 1.68), mats["wall_white"], arch_col)
        # Exterior ocean & sky horizon panel outside the ship hull
        sea_obj = add_box(f"Win_Daylight_{w_idx}", (ww + 0.5, 0.02, 1.85), (wcx, -0.55, 1.68), mats["window_daylight"], arch_col)
        apply_normalized_face_uv(sea_obj)

        # Roman Blind (Tirai Lipat Romawi) at top of window (Z = 2.08..2.52m)
        # 4 soft horizontal pleated folds + 2 vertical maroon ribbon straps + 1 horizontal maroon band
        fold_zs = [2.46, 2.34, 2.22, 2.11]
        for f_i, fz in enumerate(fold_zs):
            add_box(
                f"RomanBlind_Fold_{w_idx}_{f_i}",
                (ww + 0.08, 0.065, 0.13),
                (wcx, 0.02 + (f_i % 2) * 0.012, fz),
                mats["blind_cream"],
                arch_col,
                bevel=0.018,
            )
        # Horizontal burgundy ribbon band across Roman blind
        add_box(f"RomanBlind_HBand_{w_idx}", (ww + 0.09, 0.072, 0.032), (wcx, 0.028, 2.26), mats["wall_red"], arch_col)
        # Vertical burgundy ribbon bands near left & right edges of Roman blind
        for side_x in (wx0 + 0.16, wx1 - 0.16):
            add_box(f"RomanBlind_VBand_{w_idx}_{side_x:.1f}", (0.038, 0.075, 0.46), (side_x, 0.03, 2.29), mats["wall_red"], arch_col)

    # 3. Waiter Station, Sofa Wall & 2-Step Recessed Wall at 2nd Entrance (advanced +1.25m so Pintu Masuk Kedua is half of 2.50m = 1.25m!)
    # Looking from inside the room toward the Waiter Station wall:
    # - Pintu Masuk Kedua: X = -0.10m .. 1.15m (width 1.25m = exact half of 2.50m!)
    # - LEFT corner (Y = 0.00..2.25m, anchored at Window corner): 9 Decorative Plates + Red Banquette Sofa (wall face at X = -1.55m)
    # - RIGHT corner from Pintu Masuk Kedua (Y = 7.58m going inward in -Y):
    #     1) Wall Segment 1 (sejajar pintu masuk kedua, length 1.50m: Y = 6.08..7.58m) at X = -0.10m (with red wainscoting & table chart)
    #     2) Lekukan 1 + Wall Segment 2 (steps inward -1.45m to X = -1.55m, length 0.75m: Y = 5.33..6.08m, with white service door)
    #     3) Lekukan 2 + Waiter Station Niche (steps inward -0.65m = exact station width to X = -2.20m, remaining length = 3.08m: Y = 2.25..5.33m)
    #        so the Waiter Station front (X = -1.55m) sits completely flush inside the recessed niche!
    SOFA_WALL_X = -1.55
    SEG1_WALL_X = -0.10
    SEG2_WALL_X = -1.55
    STATION_BACK_X = -2.20  # Recessed by exact station depth (0.65m) behind SEG2_WALL_X (-1.55m)

    # Extra carpet strip covering the recessed Waiter Station floor & entrance alcove (X: -2.25..-0.05, Y: 0..7.58)
    add_box(
        "Floor_Dining_Carpet_Alcove",
        (2.20, ROOM_WID_Y, 0.04),
        (-1.15, ROOM_WID_Y * 0.5, -0.02),
        mats["carpet"],
        arch_col,
        uv_metric=0.58,
    )

    plate_offsets = [
        (-0.36,  0.34, 0.13), (0.0,  0.40, 0.15), (0.36,  0.34, 0.13),
        (-0.38,  0.00, 0.15), (0.0,  0.00, 0.17), (0.38,  0.00, 0.15),
        (-0.34, -0.35, 0.13), (0.0, -0.39, 0.14), (0.34, -0.35, 0.13),
    ]
    add_box("FwdWall_Upper_A", (0.18, 2.25, CEIL_H), (SOFA_WALL_X - 0.09, 1.125, CEIL_H * 0.5), mats["wall_white"], arch_col)
    add_box("FwdWall_Red_A", (0.20, 2.25, 0.75), (SOFA_WALL_X - 0.07, 1.125, 0.45), mats["wall_red"], arch_col)
    add_box("FwdWall_ChairRail_A", (0.045, 2.25, 0.065), (SOFA_WALL_X + 0.012, 1.125, 0.88), mats["wall_white"], arch_col, bevel=0.006)
    add_box("FwdWall_Crown_A", (0.05, 2.25, 0.08), (SOFA_WALL_X + 0.015, 1.125, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)
    for p_i, (dy, dz, prad) in enumerate(plate_offsets):
        p_obj = add_cylinder(
            f"Fwd_Plate_{p_i}",
            radius=prad,
            depth=0.025,
            location=(SOFA_WALL_X + 0.02, 1.15 + dy, 1.78 + dz),
            mat=mats["plates_wall"],
            col=arch_col,
            rot=(0, math.pi * 0.5, 0),
        )
        apply_normalized_face_uv(p_obj)
    # Red Banquette Sofa Booth anchored at Window Corner (Y = 0.12..2.18m, X = -1.55..-0.91m)
    add_box("Fwd_Banquette_Base", (0.62, 2.06, 0.44), (SOFA_WALL_X + 0.31, 1.15, 0.22), mats["wood_walnut"], arch_col, bevel=0.01)
    add_box("Fwd_Banquette_Seat", (0.64, 2.06, 0.10), (SOFA_WALL_X + 0.32, 1.15, 0.46), mats["velvet_maroon"], arch_col, bevel=0.025)
    add_box("Fwd_Banquette_Back", (0.18, 2.06, 0.58), (SOFA_WALL_X + 0.09, 1.15, 0.78), mats["velvet_maroon"], arch_col, bevel=0.025)

    # --- 2-STEP RECESSED WALL FROM PINTU MASUK KEDUA (Y = 7.58m -> 5.33m) ---
    # Step 1: Wall Segment 1 aligned with Pintu Masuk Kedua (Y = 6.08..7.58m, length = 1.50m, front face at X = -0.10m)
    seg1_y0, seg1_y1 = ROOM_WID_Y - 1.50, ROOM_WID_Y  # 6.08..7.58m (1.50m)
    seg1_len = seg1_y1 - seg1_y0
    seg1_cy = (seg1_y0 + seg1_y1) * 0.5
    add_box("FwdStep1_Wall_White", (0.38, seg1_len, CEIL_H), (SEG1_WALL_X - 0.19, seg1_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("FwdStep1_Wall_Red", (0.02, seg1_len - 0.14, 0.68), (SEG1_WALL_X + 0.005, seg1_cy, 0.50), mats["wall_red"], arch_col)
    add_box("FwdStep1_Wall_Plinth", (0.04, seg1_len, 0.16), (SEG1_WALL_X + 0.01, seg1_cy, 0.08), mats["wall_white"], arch_col, bevel=0.004)
    add_box("FwdStep1_Wall_ChairRail", (0.045, seg1_len + 0.02, 0.065), (SEG1_WALL_X + 0.012, seg1_cy, 0.88), mats["wall_white"], arch_col, bevel=0.006)
    add_box("FwdStep1_Wall_Crown", (0.05, seg1_len + 0.02, 0.08), (SEG1_WALL_X + 0.015, seg1_cy, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)
    # Costa Smeralda Table Layout Chart plaque on Wall Segment 1 (seen in 14.14.06.jpeg)
    add_box("FwdStep1_ChartPlaque", (0.015, 0.42, 0.68), (SEG1_WALL_X + 0.01, seg1_cy, 1.68), mats["art_2"], arch_col)

    # Lekukan 1 Return (at Y = 6.08m, stepping inward from X = -0.10m to X = -1.55m)
    ret1_dx = SEG1_WALL_X - SEG2_WALL_X  # 1.45m
    ret1_cx = (SEG1_WALL_X + SEG2_WALL_X) * 0.5  # -0.825m
    add_box("FwdStep1_Return_White", (ret1_dx + 0.06, 0.24, CEIL_H), (ret1_cx, seg1_y0 + 0.12, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("FwdStep1_Return_Red", (ret1_dx - 0.08, 0.02, 0.68), (ret1_cx, seg1_y0 - 0.005, 0.50), mats["wall_red"], arch_col)
    add_box("FwdStep1_Return_Plinth", (ret1_dx + 0.02, 0.04, 0.16), (ret1_cx, seg1_y0 - 0.01, 0.08), mats["wall_white"], arch_col, bevel=0.004)
    add_box("FwdStep1_Return_ChairRail", (ret1_dx + 0.04, 0.045, 0.065), (ret1_cx, seg1_y0 - 0.012, 0.88), mats["wall_white"], arch_col, bevel=0.006)
    add_box("FwdStep1_Return_Crown", (ret1_dx + 0.04, 0.05, 0.08), (ret1_cx, seg1_y0 - 0.015, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)

    # Step 2: Wall Segment 2 (recessed to X = -1.55m, Y = 5.33..6.08m, width = 0.75m, with white service door as in 14.14.06.jpeg)
    seg2_y0, seg2_y1 = seg1_y0 - 0.75, seg1_y0
    seg2_len = seg2_y1 - seg2_y0
    seg2_cy = (seg2_y0 + seg2_y1) * 0.5
    add_box("FwdStep2_Wall_White", (0.68, seg2_len, CEIL_H), (SEG2_WALL_X - 0.34, seg2_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("FwdStep2_Door_Frame", (0.025, 0.60, 2.08), (SEG2_WALL_X + 0.006, seg2_cy, 1.04), mats["wall_white"], arch_col, bevel=0.003)
    add_box("FwdStep2_Door_Leaf", (0.015, 0.54, 2.02), (SEG2_WALL_X + 0.012, seg2_cy, 1.01), mats["wall_white"], arch_col)
    # Narrow red wainscot strips flanking the white service door (seen in 14.14.06.jpeg)
    for jamb_y in (seg2_y0 + 0.04, seg2_y1 - 0.04):
        add_box(f"FwdStep2_JambRed_{jamb_y:.2f}", (0.02, 0.06, 0.68), (SEG2_WALL_X + 0.005, jamb_y, 0.50), mats["wall_red"], arch_col)
    add_box("FwdStep2_Wall_ChairRail", (0.04, seg2_len, 0.055), (SEG2_WALL_X + 0.01, seg2_cy, 0.88), mats["wall_white"], arch_col)

    # Step 3 (Lekukan 2): Double Waiter Service Sideboard Station recessed by its exact depth (0.65m) into X = -2.35..-1.70m
    # Spanning the remaining space Y = 2.25m to seg2_y0 (5.33m, total length = 3.08m)
    sb_y_start = 2.25
    sb_y_end = seg2_y0
    part_thick = 0.035
    avail_sec_sum = (sb_y_end - sb_y_start) - 4 * part_thick  # 2.94m divided in 1:3:1:3 ratio
    w_short = round(avail_sec_sum * (0.5 / 4.0), 4)
    w_long = round(avail_sec_sum * (1.5 / 4.0), 4)
    section_widths = [w_short, w_long, w_short, w_long]
    total_sb_len = sum(section_widths) + 4 * part_thick
    sb_y_center = sb_y_start + total_sb_len * 0.5

    # Backing wall & side return walls of the recessed Waiter Station alcove (X = -1.10m)
    add_box("FwdWall_ServiceBack", (0.18, total_sb_len + 0.10, CEIL_H), (STATION_BACK_X - 0.09, sb_y_center, CEIL_H * 0.5), mats["wall_white"], arch_col)
    add_box("FwdWall_AlcoveReturn_Left", (0.65, 0.04, CEIL_H), (STATION_BACK_X + 0.325, sb_y_start, CEIL_H * 0.5), mats["wall_white"], arch_col)
    add_box("FwdWall_AlcoveReturn_Right", (0.65, 0.04, CEIL_H), (STATION_BACK_X + 0.325, sb_y_end, CEIL_H * 0.5), mats["wall_white"], arch_col)

    # Main carcass & plinth (recessed at X = STATION_BACK_X .. SEG2_WALL_X, i.e., -1.10m .. -0.45m)
    add_box("Sideboard_Plinth", (0.62, total_sb_len, 0.04), (STATION_BACK_X + 0.31, sb_y_center, 0.02), mats["black_metal"], arch_col)
    add_box("Sideboard_Carcass", (0.62, total_sb_len, 0.84), (STATION_BACK_X + 0.31, sb_y_center, 0.46), mats["black_metal"], arch_col)
    # Continuous Countertop (Z = 0.88..0.92m) & Back Backsplash (height 25cm: Z = 0.92..1.17m)
    add_box("Sideboard_MarbleTop", (0.65, total_sb_len + 0.02, 0.04), (STATION_BACK_X + 0.325, sb_y_center, 0.90), mats["dark_marble"], arch_col, bevel=0.005)
    add_box("Sideboard_Backsplash", (0.04, total_sb_len + 0.02, 0.25), (STATION_BACK_X + 0.02, sb_y_center, 1.045), mats["dark_marble"], arch_col, bevel=0.004)

    curr_y = sb_y_start
    for sec_i, sec_w in enumerate(section_widths):
        sec_cy = curr_y + sec_w * 0.5
        face_w = sec_w - 0.025

        # 1. Bottom Half (Z = 0.05..0.45m, height 0.40m): 1 Lower Cabinet per section (Total = 4 Lower Cabinets)
        add_box(
            f"Sideboard_LowerCab_{sec_i+1}",
            (0.025, face_w, 0.39),
            (STATION_BACK_X + 0.625, sec_cy, 0.25),
            mats["wall_white"],
            arch_col,
            bevel=0.004,
        )
        add_box(
            f"Sideboard_LowerCab_Handle_{sec_i+1}",
            (0.018, min(0.16, face_w * 0.45), 0.015),
            (STATION_BACK_X + 0.645, sec_cy, 0.40),
            mats["chrome"],
            arch_col,
        )

        # 2. Top Half Split into 2 Drawers (Middle Drawer Z = 0.465..0.665m & Top Drawer Z = 0.675..0.875m; Total = 8 Drawers)
        # Middle Drawer (White Front)
        add_box(
            f"Sideboard_MidDrawer_{sec_i+1}",
            (0.025, face_w, 0.195),
            (STATION_BACK_X + 0.625, sec_cy, 0.565),
            mats["wall_white"],
            arch_col,
            bevel=0.004,
        )
        add_box(
            f"Sideboard_MidDrawer_Handle_{sec_i+1}",
            (0.018, min(0.16, face_w * 0.45), 0.015),
            (STATION_BACK_X + 0.645, sec_cy, 0.565),
            mats["chrome"],
            arch_col,
        )
        # Top Drawer (Dark Front with White Trim)
        add_box(
            f"Sideboard_TopDrawer_{sec_i+1}",
            (0.025, face_w, 0.195),
            (STATION_BACK_X + 0.625, sec_cy, 0.775),
            mats["black_metal"],
            arch_col,
            bevel=0.004,
        )
        add_box(
            f"Sideboard_TopDrawer_Handle_{sec_i+1}",
            (0.018, min(0.16, face_w * 0.45), 0.015),
            (STATION_BACK_X + 0.645, sec_cy, 0.775),
            mats["chrome"],
            arch_col,
        )

        # Move to partition at the right side of this section
        part_cy = curr_y + sec_w + part_thick * 0.5
        # Vertical partition stile in cabinet body
        add_box(
            f"Sideboard_BodyPartition_{sec_i+1}",
            (0.64, part_thick, 0.86),
            (STATION_BACK_X + 0.32, part_cy, 0.45),
            mats["black_metal"],
            arch_col,
            bevel=0.003,
        )
        # Short physical partition (~25 cm high above counter top, Z = 0.92..1.17m)
        add_box(
            f"Sideboard_TopPartition25cm_{sec_i+1}",
            (0.65, part_thick, 0.25),
            (STATION_BACK_X + 0.325, part_cy, 1.045),
            mats["dark_marble"],
            arch_col,
            bevel=0.004,
        )
        curr_y += sec_w + part_thick

    # 4. Entrance End Wall at X = 10.40m (tembok pintu masuk pertama)
    # Spans Y = 0.0..4.25m so Lubang Pintu Masuk Pertama (Y = 4.25..5.56m) opens cleanly beside Pillar_Entrance (at Y = 5.85m)!
    add_box("AftWall_Plinth_A", (0.28, 4.25, 0.15), (ROOM_LEN_X - 0.10, 2.125, 0.075), mats["wall_white"], arch_col)
    add_box("AftWall_Red_A", (0.26, 4.25, 0.68), (ROOM_LEN_X - 0.10, 2.125, 0.49), mats["wall_red"], arch_col)
    add_box("AftWall_Rail_A", (0.30, 4.25, 0.06), (ROOM_LEN_X - 0.10, 2.125, 0.86), mats["wall_white"], arch_col, bevel=0.008)
    add_box("AftWall_Upper_A", (0.26, 4.25, 1.92), (ROOM_LEN_X - 0.10, 2.125, 1.85), mats["wall_white"], arch_col)
    for p_i, (dy, dz, prad) in enumerate(plate_offsets):
        p_obj = add_cylinder(
            f"Aft_Plate_{p_i}",
            radius=prad,
            depth=0.025,
            location=(ROOM_LEN_X - 0.24, 1.35 + dy, 1.76 + dz),
            mat=mats["plates_wall"],
            col=arch_col,
            rot=(0, math.pi * 0.5, 0),
        )
        apply_normalized_face_uv(p_obj)

    # 5. Pillars & X-Cross Balustrade Railings for BOTH Block 1 (Portside, Y=7.58m) & Block 2 (Starboardside, Y=9.88m)
    # corr_dir: +1.0 if corridor face is +Y (Block 1), -1.0 if corridor face is -Y (Block 2)
    pillar_specs = [
        # (name_tag, px, py, pw_x, pw_y, has_corr_art, has_sconce, art_mat, corr_dir)
        # --- BLOCK 1 (PORTSIDE) ---
        ("WideCorr_3", 1.975, ROOM_WID_Y, 1.65, 0.58, True, True, mats["art_1"], 1.0),
        ("WideCorr_2", 4.975, ROOM_WID_Y, 1.65, 0.58, True, True, mats["art_3"], 1.0),
        ("WideCorr_1", 7.975, ROOM_WID_Y, 1.65, 0.58, True, True, mats["art_1"], 1.0),
        ("Entrance_Sq", 10.15, ROOM_WID_Y - 1.65, 0.58, 0.58, False, False, None, 1.0),
        ("RoofSupport_403_405", 3.475, ROOM_WID_Y - 1.65, 0.54, 0.54, False, False, None, 1.0),
        # --- BLOCK 2 (STARBOARDSIDE - EXACT MIRROR ACROSS CORRIDOR) ---
        ("B2_WideCorr_3", 1.975, B2_PILLAR_Y, 1.65, 0.58, True, True, mats["art_1"], -1.0),
        ("B2_WideCorr_2", 4.975, B2_PILLAR_Y, 1.65, 0.58, True, True, mats["art_3"], -1.0),
        ("B2_WideCorr_1", 7.975, B2_PILLAR_Y, 1.65, 0.58, True, True, mats["art_1"], -1.0),
        ("B2_Entrance_Sq", 10.15, B2_PILLAR_Y + 1.65, 0.58, 0.58, False, False, None, -1.0),
        ("B2_RoofSupport_468_470", 3.475, B2_PILLAR_Y + 1.65, 0.54, 0.54, False, False, None, -1.0),
    ]
    for p_idx, (p_tag, px, py, pw_x, pw_y, has_corr_art, has_sconce, art_m, corr_dir) in enumerate(pillar_specs):
        # White base plinth
        add_box(f"Pillar_Plinth_{p_tag}", (pw_x + 0.06, pw_y + 0.06, 0.16), (px, py, 0.08), mats["wall_white"], arch_col, bevel=0.005)
        # White lower frame + Red recessed wainscoting panels on all 4 sides
        add_box(f"Pillar_LowerWhite_{p_tag}", (pw_x, pw_y, 0.76), (px, py, 0.54), mats["wall_white"], arch_col, bevel=0.005)
        add_box(f"Pillar_RedInset_X_{p_tag}", (pw_x + 0.015, pw_y - 0.12, 0.62), (px, py, 0.54), mats["wall_red"], arch_col)
        add_box(f"Pillar_RedInset_Y_{p_tag}", (pw_x - 0.12, pw_y + 0.015, 0.62), (px, py, 0.54), mats["wall_red"], arch_col)
        # Chair rail molding
        add_box(f"Pillar_ChairRail_{p_tag}", (pw_x + 0.07, pw_y + 0.07, 0.065), (px, py, 0.94), mats["wall_white"], arch_col, bevel=0.008)
        # Upper white classical shaft + subtle classical panel trim
        add_box(f"Pillar_UpperShaft_{p_tag}", (pw_x, pw_y, CEIL_H - 0.96), (px, py, 0.96 + (CEIL_H - 0.96) * 0.5), mats["wall_white"], arch_col, bevel=0.006)
        add_box(f"Pillar_UpperCollar_{p_tag}", (pw_x + 0.03, pw_y + 0.03, 0.22), (px, py, CEIL_H - 0.15), mats["wall_white"], arch_col, bevel=0.005)
        # Crown molding
        add_box(f"Pillar_Crown_{p_tag}", (pw_x + 0.08, pw_y + 0.08, 0.08), (px, py, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.008)

        # Framed Artwork on Corridor Face of Wide Corridor Pillars
        if has_corr_art and art_m is not None:
            ay_frame = py + corr_dir * (pw_y * 0.5 + 0.012)
            ay_mat   = py + corr_dir * (pw_y * 0.5 + 0.016)
            ay_pic   = py + corr_dir * (pw_y * 0.5 + 0.020)
            add_box(f"Pillar_ArtFrame_Y_{p_tag}", (0.52, 0.024, 0.92), (px, ay_frame, 1.64), mats["black_metal"], arch_col, bevel=0.003)
            add_box(f"Pillar_ArtMat_Y_{p_tag}", (0.46, 0.024, 0.86), (px, ay_mat, 1.64), mats["wall_white"], arch_col)
            ao = add_box(f"Pillar_ArtPic_Y_{p_tag}", (0.36, 0.024, 0.72), (px, ay_pic, 1.64), art_m, arch_col)
            apply_normalized_face_uv(ao)

        # Murano Green & Gold 2-Arm Glass Wall Sconce on Dining Room Face (-corr_dir) of Pillar
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

    # 6. X-Cross Balustrade Railings (Dark Walnut Handrail + Black Metal X-Lattice Bars)
    def add_x_railing_segment(seg_name, p_start, p_end, n_bays=1):
        p0 = Vector(p_start)
        p1 = Vector(p_end)
        vec = p1 - p0
        seg_len = vec.length
        yaw = math.atan2(vec.y, vec.x)
        mid = (p0 + p1) * 0.5
        rail_h = 0.88

        # Top dark walnut wooden handrail
        add_box(f"Rail_TopWood_{seg_name}", (seg_len + 0.04, 0.085, 0.045), (mid.x, mid.y, rail_h), mats["wood_walnut"], arch_col, bevel=0.008, rot=(0, 0, yaw))
        # Bottom black steel bar
        add_box(f"Rail_BotBar_{seg_name}", (seg_len, 0.035, 0.025), (mid.x, mid.y, 0.08), mats["black_metal"], arch_col, rot=(0, 0, yaw))
        # End & intermediate vertical posts
        for b in range(n_bays + 1):
            t = b / n_bays
            pt = p0.lerp(p1, t)
            add_box(f"Rail_Post_{seg_name}_{b}", (0.035, 0.035, rail_h), (pt.x, pt.y, rail_h * 0.5), mats["black_metal"], arch_col, rot=(0, 0, yaw))
            add_box(f"Rail_Foot_{seg_name}_{b}", (0.08, 0.08, 0.015), (pt.x, pt.y, 0.008), mats["black_metal"], arch_col, rot=(0, 0, yaw))

        for b in range(n_bays):
            b0 = p0.lerp(p1, b / n_bays)
            b1 = p0.lerp(p1, (b + 1) / n_bays)
            # Inset vertical side bars framing the single 'X' (as seen in 14.14.03.jpeg)
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
            # Two crossing diagonal bars forming the 'X'
            for sign in (-1.0, 1.0):
                obj = add_box(
                    f"Rail_XBar_{seg_name}_{b}_{sign}",
                    (diag_len * 0.98, 0.024, 0.024),
                    (bm_mid.x, bm_mid.y, 0.08 + diag_h * 0.5),
                    mats["black_metal"],
                    arch_col,
                )
                obj.rotation_euler = Euler((0.0, sign * pitch, yaw), 'XYZ')
            # Center ring at X intersection
            add_cylinder(
                f"Rail_CenterRing_{seg_name}_{b}",
                0.045,
                0.026,
                (bm_mid.x, bm_mid.y, 0.08 + diag_h * 0.5),
                mats["black_metal"],
                arch_col,
                rot=(math.pi * 0.5, 0, yaw),
            )

    # --- Block 1 Railings (Portside, Y = 7.63m) ---
    rail_y = ROOM_WID_Y + 0.05  # 7.63m
    add_x_railing_segment("Corridor_Bay2_1X", (2.80, rail_y, 0.0), (4.15, rail_y, 0.0), n_bays=1)
    add_x_railing_segment("Corridor_Bay1_1X", (5.80, rail_y, 0.0), (7.15, rail_y, 0.0), n_bays=1)
    add_x_railing_segment("Siku_Corridor_1X", (8.80, rail_y, 0.0), (10.15, rail_y, 0.0), n_bays=1)
    add_x_railing_segment("Siku_Inward_1X", (10.15, rail_y, 0.0), (10.15, ROOM_WID_Y - 1.36, 0.0), n_bays=1)

    # --- Block 2 Railings (Starboardside, Y = 9.83m - exact mirror of Block 1) ---
    b2_rail_y = B2_PILLAR_Y - 0.05  # 9.83m
    add_x_railing_segment("B2_Corridor_Bay2_1X", (2.80, b2_rail_y, 0.0), (4.15, b2_rail_y, 0.0), n_bays=1)
    add_x_railing_segment("B2_Corridor_Bay1_1X", (5.80, b2_rail_y, 0.0), (7.15, b2_rail_y, 0.0), n_bays=1)
    add_x_railing_segment("B2_Siku_Corridor_1X", (8.80, b2_rail_y, 0.0), (10.15, b2_rail_y, 0.0), n_bays=1)
    add_x_railing_segment("B2_Siku_Inward_1X", (10.15, b2_rail_y, 0.0), (10.15, B2_PILLAR_Y + 1.36, 0.0), n_bays=1)

    # ==========================================================================
    # 7. BLOCK 2 (STARBOARDSIDE) WALLS, BANQUETTE SOFAS & 2 WAITER STATIONS
    # ==========================================================================
    def build_double_waiter_station(tag, f0_xy, f1_xy, front_normal_xy):
        """
        Builds a precision Double Waiter Station (0.5m > Partition > 1.5m > Partition > 0.5m > Partition > 1.5m > Partition)
        recessed by 0.65m behind the front line f0_xy -> f1_xy, facing `front_normal_xy`.
        Includes 4 short 25cm top partitions, 4 white lower cabinets, 4 white middle drawers, and 4 black top drawers.
        """
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

        # Recessed alcove backing wall & side returns
        add_box(f"{tag}_AlcoveBackWall", (0.16, total_len + 0.12, CEIL_H), st_pos(-0.08, s_mid, CEIL_H * 0.5), mats["wall_white"], arch_col, rot=(0, 0, normal_yaw))
        add_box(f"{tag}_AlcoveReturn_0", (station_depth, 0.04, CEIL_H), st_pos(station_depth * 0.5, 0.0, CEIL_H * 0.5), mats["wall_white"], arch_col, rot=(0, 0, normal_yaw))
        add_box(f"{tag}_AlcoveReturn_1", (station_depth, 0.04, CEIL_H), st_pos(station_depth * 0.5, total_len, CEIL_H * 0.5), mats["wall_white"], arch_col, rot=(0, 0, normal_yaw))
        # Upper wall header above Waiter Station alcove (Z = 2.15..2.78m)
        add_box(f"{tag}_AlcoveHeader", (0.14, total_len + 0.04, 0.45), st_pos(station_depth - 0.05, s_mid, CEIL_H - 0.225), mats["wall_white"], arch_col, rot=(0, 0, normal_yaw))

        # Main carcass & plinth
        add_box(f"{tag}_Plinth", (0.62, total_len, 0.04), st_pos(0.31, s_mid, 0.02), mats["black_metal"], arch_col, rot=(0, 0, normal_yaw))
        add_box(f"{tag}_Carcass", (0.62, total_len, 0.84), st_pos(0.31, s_mid, 0.46), mats["black_metal"], arch_col, rot=(0, 0, normal_yaw))
        # Dark Emperador Marble Countertop (Z = 0.88..0.92m) & 25cm Backsplash (Z = 0.92..1.17m)
        add_box(f"{tag}_MarbleTop", (0.65, total_len + 0.02, 0.04), st_pos(0.325, s_mid, 0.90), mats["dark_marble"], arch_col, bevel=0.005, rot=(0, 0, normal_yaw))
        add_box(f"{tag}_Backsplash", (0.04, total_len + 0.02, 0.25), st_pos(0.02, s_mid, 1.045), mats["dark_marble"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))

        curr_s = 0.0
        for sec_i, sec_w in enumerate(sec_widths):
            sec_cs = curr_s + sec_w * 0.5
            face_w = sec_w - 0.025
            handle_w = min(0.16, face_w * 0.45)

            # 1. Lower Cabinet (Bottom Half Z = 0.05..0.45m)
            add_box(f"{tag}_LowerCab_{sec_i+1}", (0.025, face_w, 0.39), st_pos(0.625, sec_cs, 0.25), mats["wall_white"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
            add_box(f"{tag}_LowerCab_Handle_{sec_i+1}", (0.018, handle_w, 0.015), st_pos(0.645, sec_cs, 0.40), mats["chrome"], arch_col, rot=(0, 0, normal_yaw))

            # 2. Middle Drawer (White Front, Z = 0.465..0.665m)
            add_box(f"{tag}_MidDrawer_{sec_i+1}", (0.025, face_w, 0.195), st_pos(0.625, sec_cs, 0.565), mats["wall_white"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
            add_box(f"{tag}_MidDrawer_Handle_{sec_i+1}", (0.018, handle_w, 0.015), st_pos(0.645, sec_cs, 0.565), mats["chrome"], arch_col, rot=(0, 0, normal_yaw))

            # 3. Top Drawer (Black Front, Z = 0.675..0.875m)
            add_box(f"{tag}_TopDrawer_{sec_i+1}", (0.025, face_w, 0.195), st_pos(0.625, sec_cs, 0.775), mats["black_metal"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
            add_box(f"{tag}_TopDrawer_Handle_{sec_i+1}", (0.018, handle_w, 0.015), st_pos(0.645, sec_cs, 0.775), mats["chrome"], arch_col, rot=(0, 0, normal_yaw))

            # 4. Vertical Body Stile + Short 25cm Countertop Partition
            part_cs = curr_s + sec_w + part_thick * 0.5
            add_box(f"{tag}_BodyPart_{sec_i+1}", (0.64, part_thick, 0.86), st_pos(0.32, part_cs, 0.45), mats["black_metal"], arch_col, bevel=0.003, rot=(0, 0, normal_yaw))
            add_box(f"{tag}_TopPart25cm_{sec_i+1}", (0.65, part_thick, 0.25), st_pos(0.325, part_cs, 1.045), mats["dark_marble"], arch_col, bevel=0.004, rot=(0, 0, normal_yaw))
            curr_s += sec_w + part_thick

    # --- A. Block 2 Pintu Masuk Kedua Wall & 2-Table Sofa Banquette (X = -0.10m stepping to X = -1.95m) ---
    # Step 1: Wall Segment 1 aligned with Pintu Masuk Kedua (X = -0.10m, Y = 9.88m .. 11.20m)
    b2_seg1_y0, b2_seg1_y1 = B2_PILLAR_Y, 11.20
    b2_seg1_len = b2_seg1_y1 - b2_seg1_y0
    b2_seg1_cy = (b2_seg1_y0 + b2_seg1_y1) * 0.5
    add_box("B2_FwdStep1_Wall_White", (0.38, b2_seg1_len, CEIL_H), (-0.10 - 0.19, b2_seg1_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("B2_FwdStep1_Wall_Red", (0.02, b2_seg1_len - 0.12, 0.68), (-0.10 + 0.005, b2_seg1_cy, 0.50), mats["wall_red"], arch_col)
    add_box("B2_FwdStep1_Wall_Plinth", (0.04, b2_seg1_len, 0.16), (-0.10 + 0.01, b2_seg1_cy, 0.08), mats["wall_white"], arch_col, bevel=0.004)
    add_box("B2_FwdStep1_Wall_ChairRail", (0.045, b2_seg1_len + 0.02, 0.065), (-0.10 + 0.012, b2_seg1_cy, 0.88), mats["wall_white"], arch_col, bevel=0.006)
    add_box("B2_FwdStep1_Wall_Crown", (0.05, b2_seg1_len + 0.02, 0.08), (-0.10 + 0.015, b2_seg1_cy, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)

    # Return wall at Y = 11.20m stepping deeply back from X = -0.10m to B2_FWD_WALL_X = -1.95m (as in 14.24.12.jpeg)
    b2_ret_dx = -0.10 - B2_FWD_WALL_X  # 1.85m
    b2_ret_cx = (-0.10 + B2_FWD_WALL_X) * 0.5  # -1.025m
    add_box("B2_FwdReturn_Wall_White", (b2_ret_dx + 0.06, 0.24, CEIL_H), (b2_ret_cx, 11.08, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("B2_FwdReturn_Wall_Red", (b2_ret_dx - 0.08, 0.02, 0.68), (b2_ret_cx, 11.205, 0.50), mats["wall_red"], arch_col)
    add_box("B2_FwdReturn_Plinth", (b2_ret_dx + 0.02, 0.04, 0.16), (b2_ret_cx, 11.21, 0.08), mats["wall_white"], arch_col, bevel=0.004)
    add_box("B2_FwdReturn_ChairRail", (b2_ret_dx + 0.04, 0.045, 0.065), (b2_ret_cx, 11.212, 0.88), mats["wall_white"], arch_col, bevel=0.006)
    add_box("B2_FwdReturn_Crown", (b2_ret_dx + 0.04, 0.05, 0.08), (b2_ret_cx, 11.215, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)
    # Wall-mounted black ship telephone on B2_FwdReturn_Wall near the corner (seen in 14.24.12.jpeg)
    add_box("B2_FwdReturn_WallPhone_Base", (0.15, 0.035, 0.22), (-0.34, 11.218, 1.15), mats["black_metal"], arch_col, bevel=0.004)
    add_box("B2_FwdReturn_WallPhone_Handset", (0.045, 0.045, 0.20), (-0.38, 11.235, 1.15), mats["black_metal"], arch_col, bevel=0.006)

    # Step 2: Back Wall behind the 2 Sofa Tables 466 & 464 (X = -1.95m, Y = 11.20m .. 17.46m)
    b2_fwd_y0, b2_fwd_y1 = 11.20, B2_WALL_Y
    b2_fwd_len = b2_fwd_y1 - b2_fwd_y0
    b2_fwd_cy = (b2_fwd_y0 + b2_fwd_y1) * 0.5
    add_box("B2_FwdWall_Upper", (0.20, b2_fwd_len, CEIL_H), (B2_FWD_WALL_X - 0.10, b2_fwd_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("B2_FwdWall_Red", (0.02, b2_fwd_len - 0.10, 0.68), (B2_FWD_WALL_X + 0.005, b2_fwd_cy, 0.50), mats["wall_red"], arch_col)
    add_box("B2_FwdWall_Plinth", (0.04, b2_fwd_len, 0.16), (B2_FWD_WALL_X + 0.01, b2_fwd_cy, 0.08), mats["wall_white"], arch_col)
    add_box("B2_FwdWall_ChairRail", (0.045, b2_fwd_len, 0.065), (B2_FWD_WALL_X + 0.012, b2_fwd_cy, 0.88), mats["wall_white"], arch_col)
    add_box("B2_FwdWall_Crown", (0.05, b2_fwd_len, 0.08), (B2_FWD_WALL_X + 0.015, b2_fwd_cy, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)

    # Red Velvet Banquette Sofa for Tables 466 & 464 (along X = -1.95m, Y = 11.30m .. 15.00m, length = 3.70m)
    b2_sofa2_len = 3.70
    b2_sofa2_cy = 13.15
    add_box("B2_Entrance2_Sofa_Base", (0.62, b2_sofa2_len, 0.44), (B2_FWD_WALL_X + 0.31, b2_sofa2_cy, 0.22), mats["wood_walnut"], arch_col, bevel=0.01)
    add_box("B2_Entrance2_Sofa_Seat", (0.64, b2_sofa2_len, 0.10), (B2_FWD_WALL_X + 0.32, b2_sofa2_cy, 0.46), mats["velvet_maroon"], arch_col, bevel=0.025)
    add_box("B2_Entrance2_Sofa_Back", (0.18, b2_sofa2_len, 0.58), (B2_FWD_WALL_X + 0.09, b2_sofa2_cy, 0.78), mats["velvet_maroon"], arch_col, bevel=0.025)

    # Low Partition Wall at the end of Sofa 464 (Y = 15.08m, height = 1.15m, seen in 14.24.12(1).jpeg)
    add_box("B2_LowPartition_White", (0.88, 0.12, 1.15), (B2_FWD_WALL_X + 0.44, 15.08, 0.575), mats["wall_white"], arch_col, bevel=0.005)
    add_box("B2_LowPartition_Red", (0.82, 0.13, 0.68), (B2_FWD_WALL_X + 0.44, 15.08, 0.50), mats["wall_red"], arch_col)
    add_box("B2_LowPartition_Cap", (0.92, 0.15, 0.05), (B2_FWD_WALL_X + 0.45, 15.08, 1.15), mats["wall_white"], arch_col, bevel=0.006)

    # --- B. Waiter Station #1 (Rectangle 2 in Normal Map: facing -Y toward Pintu Masuk Kedua!) ---
    # Recessed along Y = 15.85m (flush with the front of the structural pier at Y = 15.85m..17.46m, as in 14.24.12(1).jpeg),
    # shifted back with B2_FWD_WALL_X to span X = -1.90m .. 0.45m (length 2.35m), facing -Y (0, -1) straight toward Pintu Masuk Kedua!
    build_double_waiter_station("B2_WaiterStation_1_Rect2", (-1.90, 15.85), (0.45, 15.85), (0.0, -1.0))

    # Structural Wall Pier separating Waiter Station #1 from the 6-Table Sofa Row (X = 0.45m .. 1.95m, Y = 15.85..17.46m)
    pier1_w_x = 1.95 - 0.45  # 1.50m
    pier1_cx = (0.45 + 1.95) * 0.5  # 1.20m
    pier1_len_y = B2_WALL_Y - 15.85  # 1.61m
    pier1_cy = (15.85 + B2_WALL_Y) * 0.5  # 16.655m
    add_box("B2_WS1_Pier_White", (pier1_w_x, pier1_len_y, CEIL_H), (pier1_cx, pier1_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("B2_WS1_Pier_Red", (pier1_w_x + 0.01, pier1_len_y + 0.01, 0.68), (pier1_cx, pier1_cy, 0.50), mats["wall_red"], arch_col)
    add_box("B2_WS1_Pier_Plinth", (pier1_w_x + 0.03, pier1_len_y + 0.03, 0.16), (pier1_cx, pier1_cy, 0.08), mats["wall_white"], arch_col, bevel=0.004)
    add_box("B2_WS1_Pier_Rail", (pier1_w_x + 0.03, pier1_len_y + 0.03, 0.065), (pier1_cx, pier1_cy, 0.88), mats["wall_white"], arch_col, bevel=0.006)
    add_box("B2_WS1_Pier_Crown", (pier1_w_x + 0.04, pier1_len_y + 0.04, 0.08), (pier1_cx, pier1_cy, CEIL_H - 0.04), mats["wall_white"], arch_col, bevel=0.006)

    # --- C. Block 2 Inboard Back Wall & 6-Table Banquette Sofa (Y = 17.46m, X = 1.95m .. 10.02m) ---
    b2_inboard_x0, b2_inboard_x1 = 1.95, 10.02
    b2_inboard_len = b2_inboard_x1 - b2_inboard_x0  # 8.07m
    b2_inboard_cx = (b2_inboard_x0 + b2_inboard_x1) * 0.5
    add_box("B2_InboardWall_Upper", (b2_inboard_len + 0.20, 0.22, CEIL_H), (b2_inboard_cx, B2_WALL_Y + 0.11, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("B2_InboardWall_Red", (b2_inboard_len, 0.02, 0.68), (b2_inboard_cx, B2_WALL_Y - 0.005, 0.50), mats["wall_red"], arch_col)
    add_box("B2_InboardWall_ChairRail", (b2_inboard_len, 0.045, 0.065), (b2_inboard_cx, B2_WALL_Y - 0.012, 0.88), mats["wall_white"], arch_col, bevel=0.006)

    # Continuous Red Velvet Banquette Sofa for the 6 Sofa Tables (384, 382, 380, 378, 376, 374)
    add_box("B2_Inboard_Sofa_Base", (b2_inboard_len, 0.62, 0.44), (b2_inboard_cx, B2_WALL_Y - 0.31, 0.22), mats["wood_walnut"], arch_col, bevel=0.01)
    add_box("B2_Inboard_Sofa_Seat", (b2_inboard_len, 0.64, 0.10), (b2_inboard_cx, B2_WALL_Y - 0.32, 0.46), mats["velvet_maroon"], arch_col, bevel=0.025)
    add_box("B2_Inboard_Sofa_Back", (b2_inboard_len, 0.18, 0.58), (b2_inboard_cx, B2_WALL_Y - 0.09, 0.78), mats["velvet_maroon"], arch_col, bevel=0.025)

    # 4 Black-Framed Artworks + Brass Picture Lamps along the Inboard Sofa Wall (as seen in 14.24.13.jpeg)
    inboard_art_specs = [
        (2.85, mats["art_2"]),
        (4.90, mats["art_3"]),
        (6.95, mats["art_2"]),
        (9.00, mats["art_3"]),
    ]
    for a_idx, (ax, amat) in enumerate(inboard_art_specs):
        add_box(f"B2_Inboard_Frame_{a_idx}", (0.64, 0.024, 0.78), (ax, B2_WALL_Y - 0.012, 1.70), mats["black_metal"], arch_col, bevel=0.004)
        add_box(f"B2_Inboard_Mat_{a_idx}", (0.56, 0.024, 0.70), (ax, B2_WALL_Y - 0.016, 1.70), mats["wall_white"], arch_col)
        ao = add_box(f"B2_Inboard_Art_{a_idx}", (0.44, 0.024, 0.56), (ax, B2_WALL_Y - 0.020, 1.70), amat, arch_col)
        apply_normalized_face_uv(ao)
        add_cylinder(f"B2_Inboard_LampBar_{a_idx}", 0.012, 0.46, (ax, B2_WALL_Y - 0.09, 2.15), mats["brass"], arch_col, rot=(0, math.pi * 0.5, 0))
        add_box(f"B2_Inboard_LampGlow_{a_idx}", (0.42, 0.02, 0.015), (ax, B2_WALL_Y - 0.09, 2.135), mats["led_warm"], arch_col)

    # --- D. Block 2 Pintu Masuk Pertama Wall: Waiter Station #2 (Rectangle 4) + 9 Decorative Plates Wall ---
    # Lubang Pintu Masuk Pertama is open at Y = 11.82m .. 13.15m beside B2_Entrance_Sq (Y = 11.53m)
    # 1) Waiter Station #2 (Rectangle 4 in Normal Map: opposite to Block 1's Waiter Station, facing -X into Block 2!)
    # Spans Y = 13.15m .. 15.85m (length 2.70m) with front flush at X = 10.02m, recessed into +X (10.02..10.67m)
    build_double_waiter_station("B2_WaiterStation_2_Rect4", (10.02, 13.15), (10.02, 15.85), (-1.0, 0.0))
    # Classical Pilaster Jamb framing the Pintu Masuk Pertama side of Waiter Station #2 (at Y = 13.08m, X = 10.15m, seen in 14.24.13(2).jpeg)
    add_box("B2_WS2_EntranceJamb_White", (0.32, 0.18, CEIL_H), (10.16, 13.08, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("B2_WS2_EntranceJamb_Red", (0.33, 0.19, 0.68), (10.16, 13.08, 0.50), mats["wall_red"], arch_col)
    add_box("B2_WS2_EntranceJamb_Plinth", (0.35, 0.21, 0.16), (10.16, 13.08, 0.08), mats["wall_white"], arch_col)
    add_box("B2_WS2_EntranceJamb_Rail", (0.35, 0.21, 0.065), (10.16, 13.08, 0.88), mats["wall_white"], arch_col)

    # 2) Corner Wall Segment with 9 Decorative Fornasetti Plates (Y = 15.85m .. 17.46m at X = 10.02m, seen in 14.24.13(2).jpeg)
    b2_aft_y0, b2_aft_y1 = 15.85, B2_WALL_Y
    b2_aft_len = b2_aft_y1 - b2_aft_y0  # 1.61m
    b2_aft_cy = (b2_aft_y0 + b2_aft_y1) * 0.5  # 16.655m
    add_box("B2_AftPlates_Wall_White", (0.28, b2_aft_len, CEIL_H), (10.02 + 0.14, b2_aft_cy, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
    add_box("B2_AftPlates_Wall_Red", (0.02, b2_aft_len - 0.08, 0.68), (10.02 - 0.005, b2_aft_cy, 0.50), mats["wall_red"], arch_col)
    add_box("B2_AftPlates_Wall_Plinth", (0.04, b2_aft_len, 0.16), (10.02 - 0.01, b2_aft_cy, 0.08), mats["wall_white"], arch_col)
    add_box("B2_AftPlates_Wall_Rail", (0.045, b2_aft_len + 0.02, 0.065), (10.02 - 0.012, b2_aft_cy, 0.88), mats["wall_white"], arch_col, bevel=0.006)
    for p_i, (dy, dz, prad) in enumerate(plate_offsets):
        p_obj = add_cylinder(
            f"B2_Aft_Plate_{p_i}",
            radius=prad,
            depth=0.025,
            location=(10.02 - 0.018, b2_aft_cy + dy * 0.85, 1.76 + dz),
            mat=mats["plates_wall"],
            col=arch_col,
            rot=(0, math.pi * 0.5, 0),
        )
        apply_normalized_face_uv(p_obj)

    # 8. Coffered Ceiling Grid (Z = 2.78m to 2.96m) across Block 1, Corridor & Block 2
    total_scene_y = B2_WALL_Y + 0.80
    add_box(
        "Ceiling_Recessed_Slab",
        (B2_EXT_LEN_X + 2.2, total_scene_y, 0.08),
        (B2_EXT_MID_X, total_scene_y * 0.5 - 0.2, COFFER_H + 0.04),
        mats["ceiling_dark"],
        arch_col,
    )
    # Block 1 Coffered Ceiling Beams
    beam_xs = [-1.85, -0.10, 1.15, 3.475, 6.48, 10.15]
    beam_ys_b1 = [0.25, 2.95, ROOM_WID_Y - 1.65, ROOM_WID_Y]
    for bx in beam_xs:
        add_box(f"CeilBeam_X_White_{bx:.1f}", (0.42, ROOM_WID_Y + 0.2, 0.18), (bx, ROOM_WID_Y * 0.5, CEIL_H + 0.09), mats["wall_white"], arch_col, bevel=0.006)
        add_box(f"CeilBeam_X_Red_{bx:.1f}", (0.22, ROOM_WID_Y + 0.1, 0.012), (bx, ROOM_WID_Y * 0.5, CEIL_H - 0.008), mats["wall_red"], arch_col)
    for by in beam_ys_b1:
        add_box(f"CeilBeam_Y_White_{by:.1f}", (EXT_LEN_X + 0.6, 0.42, 0.174), (EXT_MID_X - 0.2, by, CEIL_H + 0.093), mats["wall_white"], arch_col, bevel=0.006)
        add_box(f"CeilBeam_Y_Red_{by:.1f}", (EXT_LEN_X + 0.5, 0.22, 0.012), (EXT_MID_X - 0.2, by, CEIL_H - 0.004), mats["wall_red"], arch_col)

    for bx in beam_xs[:-1]:
        for by in [1.5, 4.35, 6.65]:
            add_cylinder(f"RedSpot_X_{bx:.1f}_{by:.1f}", 0.038, 0.010, (bx, by, CEIL_H - 0.016), mats["led_red"], arch_col)
    for by in beam_ys_b1:
        for bx in [-1.0, 2.3, 5.0, 8.3]:
            add_cylinder(f"RedSpot_Y_{bx:.1f}_{by:.1f}", 0.038, 0.010, (bx, by, CEIL_H - 0.012), mats["led_red"], arch_col)

    # Block 2 Coffered Ceiling Beams (mirrored in Y across the corridor, with 4mm Z-offset between X and Y beams to avoid Z-fighting)
    beam_ys_b2 = [B2_PILLAR_Y, B2_PILLAR_Y + 1.65, 14.51, 17.21]
    b2_center_y = (B2_PILLAR_Y + B2_WALL_Y) * 0.5
    for bx in beam_xs:
        add_box(f"B2_CeilBeam_X_White_{bx:.1f}", (0.42, ROOM_WID_Y + 0.2, 0.18), (bx, b2_center_y, CEIL_H + 0.09), mats["wall_white"], arch_col, bevel=0.006)
        add_box(f"B2_CeilBeam_X_Red_{bx:.1f}", (0.22, ROOM_WID_Y + 0.1, 0.012), (bx, b2_center_y, CEIL_H - 0.008), mats["wall_red"], arch_col)
    for by in beam_ys_b2:
        add_box(f"B2_CeilBeam_Y_White_{by:.1f}", (B2_EXT_LEN_X + 0.4, 0.42, 0.174), (B2_EXT_MID_X, by, CEIL_H + 0.093), mats["wall_white"], arch_col, bevel=0.006)
        add_box(f"B2_CeilBeam_Y_Red_{by:.1f}", (B2_EXT_LEN_X + 0.3, 0.22, 0.012), (B2_EXT_MID_X, by, CEIL_H - 0.004), mats["wall_red"], arch_col)

    for bx in beam_xs[:-1]:
        for by in [10.80, 13.10, 15.90]:
            add_cylinder(f"B2_RedSpot_X_{bx:.1f}_{by:.1f}", 0.038, 0.010, (bx, by, CEIL_H - 0.016), mats["led_red"], arch_col)
    for by in beam_ys_b2:
        for bx in [-1.0, 2.3, 5.0, 8.3]:
            add_cylinder(f"B2_RedSpot_Y_{bx:.1f}_{by:.1f}", 0.038, 0.010, (bx, by, CEIL_H - 0.012), mats["led_red"], arch_col)

    # Central Corridor flat ceiling (Y = 7.58..9.88m) + Warm Cove Downlights
    add_box(
        "Ceiling_Corridor_Flat",
        (corr_x_max - corr_x_min, CORR_WID_Y - 0.04, 0.17),
        ((corr_x_min + corr_x_max) * 0.5, corr_y_mid, CEIL_H + 0.095),
        mats["wall_white"],
        arch_col,
    )
    for cx_light in [-1.2, 1.2, 3.6, 6.0, 8.4, 10.0]:
        add_cylinder(f"Corr_Downlight_{cx_light:.1f}", 0.05, 0.01, (cx_light, corr_y_mid, CEIL_H - 0.005), mats["led_warm"], arch_col)

    # Corridor End Wall at X = -2.35m, Side Corridor Extensions (X = -2.35..-0.10m) & Aft Rotunda Backdrop Wall at X = 11.40m
    upper_corr_h = CEIL_H - 0.88
    upper_corr_z = 0.88 + upper_corr_h * 0.5
    add_box("Rotunda_EndWall_Upper", (0.20, CORR_WID_Y + 1.20, upper_corr_h), (corr_x_min, corr_y_mid, upper_corr_z), mats["wall_white"], arch_col)
    add_box("Rotunda_EndWall_Red", (0.22, CORR_WID_Y + 1.20, 0.72), (corr_x_min + 0.02, corr_y_mid, 0.48), mats["wall_red"], arch_col)
    # Corridor Side Walls between Pintu Masuk Kedua (X = -0.10m) and Rotunda_EndWall (X = -2.35m) on both Block 1 & Block 2 sides
    corr_ext_len = -0.10 - corr_x_min  # 2.25m
    corr_ext_cx = (-0.10 + corr_x_min) * 0.5  # -1.225m
    for side_tag, side_y, in_dir in [("B1", ROOM_WID_Y - 0.14, 1.0), ("B2", B2_PILLAR_Y + 0.14, -1.0)]:
        add_box(f"CorrExt_SideWall_White_{side_tag}", (corr_ext_len, 0.24, CEIL_H), (corr_ext_cx, side_y, CEIL_H * 0.5), mats["wall_white"], arch_col, bevel=0.005)
        add_box(f"CorrExt_SideWall_Red_{side_tag}", (corr_ext_len - 0.08, 0.02, 0.68), (corr_ext_cx, side_y + in_dir * 0.125, 0.50), mats["wall_red"], arch_col)
        add_box(f"CorrExt_SideWall_Plinth_{side_tag}", (corr_ext_len, 0.04, 0.16), (corr_ext_cx, side_y + in_dir * 0.13, 0.08), mats["wall_white"], arch_col)
        add_box(f"CorrExt_SideWall_Rail_{side_tag}", (corr_ext_len, 0.045, 0.065), (corr_ext_cx, side_y + in_dir * 0.132, 0.88), mats["wall_white"], arch_col)

    # Aft Rotunda Continuation Floor & Classical Wall at X = 11.40m (visible through Pintu Masuk Pertama of Block 1 & Block 2)
    rot_floor_obj = add_box(
        "Floor_Rotunda_Aft_Tile",
        (1.10, 10.60, 0.04),
        (10.90, corr_y_mid, -0.02),
        mats["corridor_tile"],
        arch_col,
    )
    apply_corridor_runner_uv(rot_floor_obj, y_center=corr_y_mid, uv_width_y=2.04, pitch_x=1.02, x_offset=0.20)
    add_box("Ceiling_Rotunda_Aft_Flat", (1.20, 10.80, 0.17), (10.90, corr_y_mid, CEIL_H + 0.095), mats["wall_white"], arch_col)
    add_box("Rotunda_AftBackdrop_Upper", (0.20, 10.80, upper_corr_h), (11.40, corr_y_mid, upper_corr_z), mats["wall_white"], arch_col)
    add_box("Rotunda_AftBackdrop_Red", (0.22, 10.80, 0.72), (11.38, corr_y_mid, 0.48), mats["wall_red"], arch_col)
    add_box("Rotunda_AftBackdrop_Plinth", (0.24, 10.80, 0.15), (11.37, corr_y_mid, 0.075), mats["wall_white"], arch_col)
    add_box("Rotunda_AftBackdrop_Rail", (0.24, 10.80, 0.06), (11.37, corr_y_mid, 0.88), mats["wall_white"], arch_col)


# ==============================================================================
# LAYOUT OF BLOCK 1 (PORTSIDE) & BLOCK 2 (STARBOARDSIDE) TABLES
# ==============================================================================
def populate_all_tables(mats, furn_col_b1, furn_col_b2):
    chair_ivory = create_chair_template("Template_Chair_Ivory", mats["leather_ivory"], mats["chair_leg"], furn_col_b1)
    chair_maroon = create_chair_template("Template_Chair_Maroon", mats["velvet_maroon"], mats["chair_leg"], furn_col_b1)

    # --------------------------------------------------------------------------
    # BLOCK 1 (PORTSIDE: Y = 0.0 .. 7.58m)
    # --------------------------------------------------------------------------
    # 1. ROW A: WINDOW SIDE (Ivory Chairs - Table 301 shifted back in -X with recessed sofa wall to X = -0.42m)
    build_table_assembly("301_Window_Booth", (-0.42, 1.15), 1.45, 0.88, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b1, skip_side_b=True)
    build_table_assembly("303_Window_Bay1", (3.45, 1.35), 2.10, 0.90, math.pi * 0.5, chair_ivory, 6, mats, furn_col_b1)
    build_table_assembly("305_Window_Bay2", (6.22, 1.35), 2.10, 0.90, math.pi * 0.5, chair_ivory, 6, mats, furn_col_b1)
    build_table_assembly("307_Window_Bay3", (9.00, 1.35), 2.10, 0.90, math.pi * 0.5, chair_ivory, 6, mats, furn_col_b1)

    # 2. ROW B: MIDDLE / CENTER ROW (Maroon Velvet Chairs, yaw = 0.0)
    build_table_assembly("399_Center_Fwd", (2.30, 4.14), 2.05, 0.90, 0.0, chair_maroon, 6, mats, furn_col_b1)
    build_table_assembly("397_Center_Mid", (5.00, 4.14), 2.05, 0.90, 0.0, chair_maroon, 6, mats, furn_col_b1)
    build_table_assembly("393_Center_Aft", (7.70, 4.14), 2.05, 0.90, 0.0, chair_maroon, 6, mats, furn_col_b1)

    # 3. ROW C: CORRIDOR PILLAR & X-RAILING ROW (Ivory Chairs, 1 pillar 1 table flush at Y = 6.58m)
    build_table_assembly("403_Railing_FwdBay", (1.975, 6.58), 1.40, 0.88, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b1)
    build_table_assembly("405_Railing_MidBay", (4.975, 6.58), 1.40, 0.88, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b1)
    build_table_assembly("407_Railing_AftBay", (7.975, 6.58), 1.40, 0.88, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b1)

    # --------------------------------------------------------------------------
    # BLOCK 2 (STARBOARDSIDE: Y = 9.88 .. 17.46m)
    # --------------------------------------------------------------------------
    # 1. ROW C: CORRIDOR PILLAR & X-RAILING ROW (Ivory Chairs - 1 pillar 1 table centered at X=1.975, 4.975, 7.975, flush at Y=10.88m!)
    # Tabletop -Y edge at 10.88 - 0.70 = 10.18m, flush outside pillar inner face at 10.17m without penetration!
    build_table_assembly("468_B2_Railing_Fwd", (1.975, 10.88), 1.40, 0.88, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b2)
    build_table_assembly("470_B2_Railing_Mid", (4.975, 10.88), 1.40, 0.88, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b2)
    build_table_assembly("472_B2_Railing_Aft", (7.975, 10.88), 1.40, 0.88, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b2)

    # 2. ROW B: MIDDLE / CENTER ROW (Maroon Velvet Chairs - ROTATED 90 DEGREES from Block 1 -> yaw = math.pi * 0.5, aligned with 468, 470, 472!)
    build_table_assembly("462_B2_Center_Fwd", (1.975, 13.68), 1.95, 0.90, math.pi * 0.5, chair_maroon, 6, mats, furn_col_b2)
    build_table_assembly("460_B2_Center_Mid", (4.975, 13.68), 1.95, 0.90, math.pi * 0.5, chair_maroon, 6, mats, furn_col_b2)
    build_table_assembly("458_B2_Center_Aft", (7.975, 13.68), 1.95, 0.90, math.pi * 0.5, chair_maroon, 6, mats, furn_col_b2)

    # 3. 2 SOFA TABLES NEAR PINTU MASUK KEDUA (Tables 466 & 464 along X = -1.95m Banquette Sofa, centered at X = -0.90m)
    # Ivory chair backs sit at X = -0.05m (aligned flush with X = -0.10m entrance wall edge, with 1.15m clear gap to Table 462 maroon chairs at X = 1.10m!)
    build_table_assembly("466_B2_Entrance2_Sofa1", (-0.90, 12.20), 1.40, 0.85, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b2, skip_side_b=True)
    build_table_assembly("464_B2_Entrance2_Sofa2", (-0.90, 14.05), 1.40, 0.85, math.pi * 0.5, chair_ivory, 4, mats, furn_col_b2, skip_side_b=True)

    # 4. 6 SOFA TABLES ALONG INBOARD WALL (From Pintu Masuk Pertama to Waiter Station #1: 4 pax -> 2 pax -> 4 pax -> 2 pax -> 2 pax -> 4 pax)
    build_table_assembly("384_B2_Sofa_4Pax_1", (9.18, 16.32), 1.35, 0.85, 0.0, chair_ivory, 4, mats, furn_col_b2, skip_side_b=True)
    build_table_assembly("382_B2_Sofa_2Pax_1", (7.82, 16.32), 0.80, 0.85, 0.0, chair_ivory, 2, mats, furn_col_b2, skip_side_b=True)
    build_table_assembly("380_B2_Sofa_4Pax_2", (6.46, 16.32), 1.35, 0.85, 0.0, chair_ivory, 4, mats, furn_col_b2, skip_side_b=True)
    build_table_assembly("378_B2_Sofa_2Pax_2", (5.10, 16.32), 0.80, 0.85, 0.0, chair_ivory, 2, mats, furn_col_b2, skip_side_b=True)
    build_table_assembly("376_B2_Sofa_2Pax_3", (4.02, 16.32), 0.80, 0.85, 0.0, chair_ivory, 2, mats, furn_col_b2, skip_side_b=True)
    build_table_assembly("374_B2_Sofa_4Pax_3", (2.68, 16.32), 1.35, 0.85, 0.0, chair_ivory, 4, mats, furn_col_b2, skip_side_b=True)


# ==============================================================================
# LIGHTING & CAMERAS (MATCHED TO PHOTO PERSPECTIVES + 3D OVERVIEW)
# ==============================================================================
def setup_lighting_and_cameras():
    scene = bpy.context.scene
    light_col = get_or_create_collection("Lighting_And_Cameras")

    # World background (Warm Mediterranean Daylight)
    world = bpy.data.worlds.new("Arlecchino_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.85, 0.91, 0.98, 1.0)
        bg.inputs["Strength"].default_value = 1.2

    # 1. Area Light Portals at the 3 Panoramic Ocean Windows in Block 1 (Portside)
    for w_idx, wcx in enumerate([2.0, 5.3, 8.6]):
        ldata = bpy.data.lights.new(name=f"WindowPortalLight_{w_idx}", type='AREA')
        ldata.energy = 180.0
        ldata.color = (0.94, 0.97, 1.0)
        ldata.shape = 'RECTANGLE'
        ldata.size = 2.1
        ldata.size_y = 1.45
        lobj = bpy.data.objects.new(name=f"WindowPortalLight_{w_idx}", object_data=ldata)
        lobj.location = (wcx, 0.12, 1.68)
        lobj.rotation_euler = Euler((-math.pi * 0.46, 0.0, 0.0), 'XYZ')
        link_to_collection(lobj, light_col)

    # 2. Warm Interior Coffered Ceiling Fill Lights across Block 1, Corridor & Block 2
    ceil_grid = [
        # Block 1
        (-0.6, 1.5), (1.6, 1.5), (4.2, 1.5), (6.8, 1.5), (9.0, 1.5),
        (-0.6, 3.8), (1.6, 3.8), (4.2, 3.8), (6.8, 3.8), (9.0, 3.8),
        (2.0, 6.2), (5.2, 6.2), (8.2, 6.2),
        # Corridor
        (-0.8, 8.73), (2.0, 8.73), (6.0, 8.73), (9.5, 8.73),
        # Block 2
        (2.0, 11.2), (5.2, 11.2), (8.2, 11.2),
        (-0.8, 12.8), (2.5, 13.6), (5.2, 13.6), (8.2, 13.6),
        (-0.8, 15.2), (3.0, 16.0), (6.0, 16.0), (9.0, 16.0),
    ]
    for idx, (lx, ly) in enumerate(ceil_grid):
        ldata = bpy.data.lights.new(name=f"CeilingWarmFill_{idx}", type='AREA')
        ldata.energy = 45.0
        ldata.color = (1.0, 0.89, 0.74)
        ldata.shape = 'DISK'
        ldata.size = 0.85
        lobj = bpy.data.objects.new(name=f"CeilingWarmFill_{idx}", object_data=ldata)
        lobj.location = (lx, ly, CEIL_H - 0.05)
        lobj.rotation_euler = (0.0, 0.0, 0.0)
        link_to_collection(lobj, light_col)

    # Helper to create a camera looking from `eye` to `target`
    def make_cam(name, eye, target, lens_mm=24.0):
        cdata = bpy.data.cameras.new(name)
        cdata.lens = lens_mm
        cdata.clip_start = 0.05
        cdata.clip_end = 100.0
        cobj = bpy.data.objects.new(name, cdata)
        cobj.location = Vector(eye)
        direction = Vector(target) - Vector(eye)
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cobj.rotation_euler = rot_quat.to_euler()
        link_to_collection(cobj, light_col)
        return cobj

    # Camera 1: Central Corridor View Looking Between Block 1 (Left) & Block 2 (Right) (Matches 14.24.10.jpeg)
    cam1 = make_cam(
        "Cam_1_Corridor_Symmetry_View",
        eye=(9.60, 8.73, 1.52),
        target=(1.50, 8.73, 1.35),
        lens_mm=20.0,
    )
    # Camera 2: Block 2 Interior Looking from Entrance 1 Toward 90-Deg Maroon Tables, 2 Entrance Sofas & Waiter Station #1 (Matches 14.23.52(1).jpeg & 14.24.12(1).jpeg)
    cam2 = make_cam(
        "Cam_2_Block2_MaroonRows_And_WS1",
        eye=(8.85, 13.75, 1.52),
        target=(-0.40, 14.10, 1.18),
        lens_mm=20.0,
    )
    # Camera 3: Block 2 Panorama of the 6 Sofa Tables (4-2-4-2-2-4) & Waiter Station #2 + 9 Plates Wall (Matches 14.24.13.jpeg & 14.24.13(2).jpeg)
    cam3 = make_cam(
        "Cam_3_Block2_6Sofas_And_WS2",
        eye=(2.40, 12.10, 1.52),
        target=(8.20, 15.65, 1.25),
        lens_mm=19.0,
    )
    # Camera 4: Block 2 Entrance 2 Recessed Sofa Tables (466 & 464), 1.15m Chair Gap & Alignment with Entrance 2 Wall (Matches 14.24.12.jpeg)
    cam4 = make_cam(
        "Cam_4_Block2_Entrance2_SofaGap_And_Wall",
        eye=(2.10, 13.80, 1.55),
        target=(-0.85, 11.40, 1.10),
        lens_mm=20.0,
    )

    scene.camera = cam2
    return [cam1, cam2, cam3, cam4]


def configure_cycles_and_render(cameras):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'

    # Configure Apple Silicon Metal GPU acceleration if available
    try:
        prefs = bpy.context.preferences
        cprefs = prefs.addons['cycles'].preferences
        cprefs.compute_device_type = 'METAL'
        cprefs.get_devices()
        for dev in cprefs.devices:
            dev.use = True
        scene.cycles.device = 'GPU'
        print("Enabled Cycles METAL GPU rendering!")
    except Exception as e:
        print("Using Cycles CPU fallback:", e)
        scene.cycles.device = 'CPU'

    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 3

    # Color management for crisp hospitality interior contrast
    scene.view_settings.view_transform = 'AgX' if 'AgX' in [ 'Standard', 'AgX', 'Filmic' ] else 'Filmic'
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    scene.view_settings.exposure = -0.12

    scene.render.resolution_x = 1440
    scene.render.resolution_y = 810
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'

    # Configure 3D Viewport in saved .blend file so user opens directly in colored Material Preview looking across Corridor & Block 2
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        space.shading.use_scene_lights = False
                        space.shading.use_scene_world = False
                        space.lock_camera = False
                        space.region_3d.view_perspective = 'PERSP'
                        space.region_3d.view_location = Vector((5.0, 12.8, 1.15))
                        space.region_3d.view_distance = 6.2
                        space.region_3d.view_rotation = Euler((math.radians(72.0), 0.0, math.radians(125.0)), 'XYZ').to_quaternion()
                        space.clip_start = 0.05
                        space.clip_end = 100.0

    # Save .blend and .glb files first
    blend_path = os.path.join(OUT_DIR, "arlecchino_block1.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("Saved Blender project:", blend_path)

    glb_path = os.path.join(OUT_DIR, "arlecchino_block1.glb")
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB')
    print("Exported GLB model:", glb_path)

    import sys
    if "--no-render" not in sys.argv:
        # Render all 4 camera views
        for idx, cam in enumerate(cameras, start=1):
            scene.camera = cam
            out_png = os.path.join(RENDER_DIR, f"render_b2_{idx}_{cam.name}.png")
            scene.render.filepath = out_png
            bpy.ops.render.render(write_still=True)
            print(f"Rendered View {idx}: {out_png}")


def main():
    clear_scene()
    arch_col = get_or_create_collection("01_Architecture_Deck6_Arlecchino")
    furn_col_b1 = get_or_create_collection("02_Furniture_Block1_Portside")
    furn_col_b2 = get_or_create_collection("03_Furniture_Block2_Starboardside")

    mats = build_materials()
    build_architecture(mats, arch_col)
    populate_all_tables(mats, furn_col_b1, furn_col_b2)
    cameras = setup_lighting_and_cameras()
    configure_cycles_and_render(cameras)


if __name__ == "__main__":
    main()
