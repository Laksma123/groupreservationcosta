import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

# ==============================================================================
# COSTA SMERALDA (EXCELLENCE CLASS) — 80%+ ACCURATE OUTER 3D MODEL
# WITH 4-LAYER CUTAWAY ARCHITECTURE (DECK 5, DECK 6, DECK 7, DECK 8–MUFFLER)
# ==============================================================================
# Real Ship Dimensions (Meyer Turku NB-1394):
# - LOA (Length Overall): 337.0 m
# - Beam (Moulded Width): 42.0 m
# - Height: ~64.0 m
#
# Model Scale: 1 : 5 horizontal (1 Blender unit = 5 meters)
# - Length X: -33.70m (Stern/Aft) to +33.70m (Bow/Forward) -> Total 67.40m
# - Width Y : -4.20m (Starboard, +Z in Three.js) to +4.20m (Port, -Z in Three.js) -> Total 8.40m
# - Vertical Z: Slight 1.25x vertical emphasis so cutaway restaurant interiors are rich & clear
#
# 5 Structural Root Hierarchies (Exported as named nodes in costa_smeralda_ship.glb):
# 0. Ship_Layer0_Base_Deck4Down   (Z = -1.60 .. +1.85m) — Fixed Hull, Bulbous Bow, Tricolore Livery
# 1. Ship_Layer1_Deck5            (Z = +1.85 .. +2.70m) — Deck 5 "Taormina" (Aft: La Colombina Placeholder)
# 2. Ship_Layer2_Deck6            (Z = +2.70 .. +3.60m) — Deck 6 "Roma" (Aft: Il Meneghino, Mid: Arlecchino 2-Block + Placeholders, 16 Lifeboats)
# 3. Ship_Layer3_Deck7            (Z = +3.60 .. +4.45m) — Deck 7 "Positano" (Aft: Il Rugantino Placeholder, Mid: Colosseo Atrium)
# 4. Ship_Layer4_Top_Deck8ToMuffler (Z = +4.45 .. +14.20m) — Unified Top Superstructure (Decks 8–20, Bridge Wings, Piazza di Spagna, Magrodome, Aqua Park, Volare Arch, Costa Yellow Funnel)
# ==============================================================================

PROJ_DIR = "/Users/dianjulie/Documents/Map Project"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0


# ------------------------------------------------------------------------------
# 2. PBR MATERIALS
# ------------------------------------------------------------------------------
def make_mat(name, rgba, rough=0.35, metal=0.05, emit_rgba=None, emit_strength=0.0, alpha=1.0, tex_path=None):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal

    if tex_path and os.path.exists(tex_path):
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.image = bpy.data.images.load(tex_path)
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

    if emit_rgba and emit_strength > 0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emit_rgba
            bsdf.inputs["Emission Strength"].default_value = emit_strength
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = emit_rgba

    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(mat, "blend_method"):
            mat.blend_method = 'BLEND'

    return mat


MAT_HULL_WHITE      = make_mat("Costa_Hull_White", (0.97, 0.98, 0.99, 1.0), rough=0.26, metal=0.08)
MAT_SUPER_WHITE     = make_mat("Costa_Super_White", (0.99, 0.99, 1.00, 1.0), rough=0.30, metal=0.05)
MAT_BOOT_NAVY       = make_mat("Costa_Boot_Navy", (0.03, 0.07, 0.15, 1.0), rough=0.35, metal=0.12)
MAT_KEEL_RED        = make_mat("Costa_Keel_Antifouling", (0.38, 0.08, 0.09, 1.0), rough=0.55, metal=0.05)
MAT_TRICOLORE_GREEN = make_mat("Costa_Tricolore_Green", (0.00, 0.55, 0.27, 1.0), rough=0.28, metal=0.08)
MAT_TRICOLORE_RED   = make_mat("Costa_Tricolore_Red", (0.82, 0.12, 0.16, 1.0), rough=0.28, metal=0.08)
MAT_COSTA_BLUE      = make_mat("Costa_Brand_Blue", (0.05, 0.20, 0.52, 1.0), rough=0.28, metal=0.12)
MAT_COSTA_YELLOW    = make_mat("Costa_Funnel_Yellow", (0.96, 0.76, 0.02, 1.0), rough=0.24, metal=0.08)
MAT_GLASS_DARK      = make_mat("Costa_Glass_Dark", (0.06, 0.18, 0.32, 1.0), rough=0.12, metal=0.45, emit_rgba=(0.08, 0.28, 0.48, 1.0), emit_strength=0.15)
MAT_GLASS_BALCONY   = make_mat("Costa_Glass_Balcony", (0.16, 0.55, 0.82, 1.0), rough=0.15, metal=0.25, emit_rgba=(0.12, 0.48, 0.78, 1.0), emit_strength=0.22, alpha=0.82)
MAT_GLASS_ATRIUM    = make_mat("Costa_Glass_Atrium", (0.32, 0.72, 0.95, 1.0), rough=0.10, metal=0.20, emit_rgba=(0.45, 0.80, 0.98, 1.0), emit_strength=0.35, alpha=0.68)
MAT_TEAK_DECK       = make_mat("Costa_Teak_Promenade", (0.76, 0.58, 0.38, 1.0), rough=0.55, metal=0.02)
MAT_POOL_WATER      = make_mat("Costa_Pool_Aqua", (0.08, 0.78, 0.92, 1.0), rough=0.10, metal=0.10, emit_rgba=(0.08, 0.78, 0.92, 1.0), emit_strength=0.40)
MAT_LIFEBOAT_ORANGE = make_mat("Costa_Lifeboat_Orange", (0.96, 0.36, 0.05, 1.0), rough=0.28, metal=0.08)
MAT_STEEL_SILVER    = make_mat("Costa_Steel_Silver", (0.78, 0.81, 0.85, 1.0), rough=0.25, metal=0.80)
MAT_SLIDE_CORAL     = make_mat("Costa_Slide_Coral", (0.95, 0.32, 0.18, 1.0), rough=0.22, metal=0.05)
MAT_SLIDE_CYAN      = make_mat("Costa_Slide_Cyan", (0.06, 0.68, 0.90, 1.0), rough=0.22, metal=0.05)

# Interior Cutaway Deck Floor & Placeholder Materials
MAT_DECK_SLAB_FLOOR = make_mat("Cutaway_Deck_Floor", (0.13, 0.18, 0.26, 1.0), rough=0.60, metal=0.05)
MAT_PLACEHOLDER_CABIN = make_mat("Placeholder_Cabin_Grey", (0.28, 0.35, 0.45, 1.0), rough=0.50, metal=0.05)
MAT_PLACEHOLDER_GALLEY = make_mat("Placeholder_Galley_Steel", (0.38, 0.44, 0.52, 1.0), rough=0.40, metal=0.35)
MAT_COLOMBINA_ZONE  = make_mat("Placeholder_Colombina_Deck5", (0.85, 0.42, 0.14, 1.0), rough=0.32, metal=0.08, emit_rgba=(0.95, 0.50, 0.15, 1.0), emit_strength=0.28)
MAT_MENEGHINO_ZONE  = make_mat("Placeholder_Meneghino_Deck6", (0.78, 0.18, 0.35, 1.0), rough=0.32, metal=0.08, emit_rgba=(0.88, 0.22, 0.42, 1.0), emit_strength=0.28)
MAT_ARLECCHINO_PH   = make_mat("Placeholder_Arlecchino_Unbuilt", (0.65, 0.52, 0.25, 1.0), rough=0.38, metal=0.10, emit_rgba=(0.75, 0.60, 0.28, 1.0), emit_strength=0.18)
MAT_ARLECCHINO_GOLD = make_mat("Active_Arlecchino_2Block_Rim", (0.98, 0.78, 0.18, 1.0), rough=0.20, metal=0.30, emit_rgba=(0.98, 0.80, 0.22, 1.0), emit_strength=0.65)
MAT_RUGANTINO_ZONE  = make_mat("Placeholder_Rugantino_Deck7", (0.08, 0.68, 0.55, 1.0), rough=0.32, metal=0.08, emit_rgba=(0.10, 0.78, 0.62, 1.0), emit_strength=0.28)
MAT_COLOSSEO_ZONE   = make_mat("Placeholder_Colosseo_Atrium", (0.22, 0.52, 0.88, 1.0), rough=0.28, metal=0.15, emit_rgba=(0.25, 0.58, 0.95, 1.0), emit_strength=0.25)
MAT_THEATRE_ZONE    = make_mat("Placeholder_Sanremo_Theatre", (0.48, 0.25, 0.72, 1.0), rough=0.35, metal=0.10, emit_rgba=(0.52, 0.28, 0.78, 1.0), emit_strength=0.20)


# ------------------------------------------------------------------------------
# 3. CREATE THE 5 STRUCTURAL ROOT EMPTIES FOR 4-LAYER CUTAWAY
# ------------------------------------------------------------------------------
def make_root(name):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    scene.collection.objects.link(empty)
    return empty


ROOT_L0 = make_root("Ship_Layer0_Base_Deck4Down")
ROOT_L1 = make_root("Ship_Layer1_Deck5")
ROOT_L2 = make_root("Ship_Layer2_Deck6")
ROOT_L3 = make_root("Ship_Layer3_Deck7")
ROOT_L4 = make_root("Ship_Layer4_Top_Deck8ToMuffler")


def link_obj(obj, parent_root, mat=None):
    if obj.name not in scene.collection.objects:
        scene.collection.objects.link(obj)
    obj.parent = parent_root
    if mat:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    return obj


# ------------------------------------------------------------------------------
# 4. PARAMETRIC SHIP HULL & SUPERSTRUCTURE PROFILE GENERATOR
# ------------------------------------------------------------------------------
def ship_half_beam_at(x_norm, stern_round=0.88, bow_start=0.42, mid_recess=0.0, mid_recess_range=(-0.18, 0.24)):
    """
    Computes the normalized half-width [0..1] at longitudinal coordinate x_norm in [-1.0 (Stern) .. +1.0 (Bow)].
    Captures:
    - Rounded cruiser stern & transom at x_norm -> -1.0
    - Parallel midbody with optional Meyer Turku midship recess
    - Sleek parabolic clipper bow tapering to 0 at x_norm -> +1.0
    """
    if x_norm > bow_start:
        # Forward bow taper
        t = (x_norm - bow_start) / max(1e-5, (1.0 - bow_start))
        w = math.pow(max(0.0, 1.0 - t * t), 0.62)
    elif x_norm < -0.72:
        # Stern quarter taper
        t = (-0.72 - x_norm) / 0.28
        w = 1.0 - (1.0 - stern_round) * (t * t)
        if x_norm < -0.94:
            t2 = (-0.94 - x_norm) / 0.06
            w *= max(0.35, 1.0 - 0.45 * (t2 * t2))
    else:
        w = 1.0

    # Optional midship recessed bay (for balcony decks or lifeboat deck)
    if mid_recess > 0.0 and mid_recess_range[0] <= x_norm <= mid_recess_range[1]:
        # Smooth cosine transition at recess ends
        r_len = mid_recess_range[1] - mid_recess_range[0]
        rel = (x_norm - mid_recess_range[0]) / r_len
        edge_factor = min(1.0, min(rel / 0.08, (1.0 - rel) / 0.08))
        w -= mid_recess * edge_factor

    return max(0.0, w)


def create_ship_deck_solid(
    name, parent_root, mat,
    x_aft, x_fwd, half_beam, z_bot, z_top,
    bow_flare=0.0, stern_rake=0.0,
    mid_recess=0.0, mid_recess_range=(-0.18, 0.24),
    bow_start=0.42, n_x=56
):
    """
    Creates a smooth, manifold 3D ship deck/hull block between z_bot and z_top
    with optional bow flare and stern rake.
    """
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    ring_bot = []
    ring_top = []

    length = x_fwd - x_aft
    x_mid = 0.5 * (x_aft + x_fwd)

    # Sample points from stern (-1) to bow (+1)
    xs_norm = [(-1.0 + 2.0 * i / n_x) for i in range(n_x + 1)]

    # Build Starboard side (-Y) from Stern to Bow, then Port side (+Y) from Bow to Stern
    pts_bot = []
    pts_top = []

    for side in (-1.0, 1.0):
        seq = xs_norm if side < 0 else list(reversed(xs_norm))[1:-1]
        for xn in seq:
            hb_norm = ship_half_beam_at(xn, bow_start=bow_start, mid_recess=mid_recess, mid_recess_range=mid_recess_range)
            # Bow flare & stern rake longitudinal shift at top vs bottom
            x_base = x_mid + 0.5 * length * xn
            dx_top = 0.0
            dy_flare = 1.0
            if xn > bow_start:
                tb = (xn - bow_start) / (1.0 - bow_start)
                dx_top = bow_flare * (tb ** 1.4)
                dy_flare = 1.0 + 0.08 * bow_flare * tb
            elif xn < -0.78:
                ts = (-0.78 - xn) / 0.22
                dx_top = stern_rake * (ts ** 1.3)

            y_bot = side * half_beam * hb_norm
            y_top = side * half_beam * hb_norm * dy_flare

            pts_bot.append(bm.verts.new((x_base, y_bot, z_bot)))
            pts_top.append(bm.verts.new((x_base + dx_top, y_top, z_top)))

    bm.verts.ensure_lookup_table()
    n_pts = len(pts_bot)

    for i in range(n_pts):
        j = (i + 1) % n_pts
        bm.faces.new([pts_bot[i], pts_bot[j], pts_top[j], pts_top[i]])

    bm.faces.new(list(reversed(pts_bot)))
    bm.faces.new(pts_top)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    for poly in mesh.polygons:
        poly.use_smooth = True

    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj, parent_root, mat)


def create_ship_hollow_shell(
    name, parent_root, mat_wall, mat_floor,
    x_aft, x_fwd, half_beam, z_bot, z_top, wall_thick=0.22, floor_thick=0.10,
    bow_flare=0.15, mid_recess=0.0, mid_recess_range=(-0.18, 0.24), bow_start=0.42, n_x=52
):
    """
    Creates an open-top ship deck tray (floor slab + outer perimeter hull walls)
    so when the upper layer lifts up in the 4-layer cutaway, the interior deck plan
    and restaurants are visible inside!
    """
    # 1. Floor Slab
    create_ship_deck_solid(
        f"{name}_FloorSlab", parent_root, mat_floor,
        x_aft, x_fwd, half_beam - 0.02, z_bot, z_bot + floor_thick,
        bow_flare=0.0, mid_recess=mid_recess, mid_recess_range=mid_recess_range, bow_start=bow_start, n_x=n_x
    )

    # 2. Outer Perimeter Wall Ring (between z_bot + floor_thick and z_top)
    mesh = bpy.data.meshes.new(f"{name}_HullWall")
    bm = bmesh.new()

    length = x_fwd - x_aft
    x_mid = 0.5 * (x_aft + x_fwd)
    xs_norm = [(-1.0 + 2.0 * i / n_x) for i in range(n_x + 1)]

    outer_bot, outer_top = [], []
    inner_bot, inner_top = [], []

    for side in (-1.0, 1.0):
        seq = xs_norm if side < 0 else list(reversed(xs_norm))[1:-1]
        for xn in seq:
            hb_norm = ship_half_beam_at(xn, bow_start=bow_start, mid_recess=mid_recess, mid_recess_range=mid_recess_range)
            x_base = x_mid + 0.5 * length * xn
            dx_top = 0.0
            if xn > bow_start:
                tb = (xn - bow_start) / (1.0 - bow_start)
                dx_top = bow_flare * (tb ** 1.4)

            yo = side * half_beam * hb_norm
            # Keep inner wall inset by wall_thick
            yi = side * max(0.0, (half_beam * hb_norm - wall_thick))
            xi_shift = -wall_thick * (1.2 if xn > 0.85 else (-1.2 if xn < -0.85 else 0.0))

            outer_bot.append(bm.verts.new((x_base, yo, z_bot + floor_thick)))
            outer_top.append(bm.verts.new((x_base + dx_top, yo, z_top)))
            inner_bot.append(bm.verts.new((x_base + xi_shift, yi, z_bot + floor_thick)))
            inner_top.append(bm.verts.new((x_base + dx_top + xi_shift, yi, z_top)))

    n_pts = len(outer_bot)
    for i in range(n_pts):
        j = (i + 1) % n_pts
        # Outer wall
        bm.faces.new([outer_bot[i], outer_bot[j], outer_top[j], outer_top[i]])
        # Inner wall
        bm.faces.new([inner_bot[j], inner_bot[i], inner_top[i], inner_top[j]])
        # Top rim
        bm.faces.new([outer_top[i], outer_top[j], inner_top[j], inner_top[i]])
        # Bottom rim
        bm.faces.new([inner_bot[i], inner_bot[j], outer_bot[j], outer_bot[i]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(f"{name}_HullWall", mesh)
    return link_obj(obj, parent_root, mat_wall)


def add_box(name, parent_root, mat, center, size, rot_z=0.0):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    if abs(rot_z) > 1e-5:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rot_z, 3, 'Z'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj, parent_root, mat)


def add_cyl(name, parent_root, mat, center, radius, height, segs=28, rot_euler=(0, 0, 0), scale_xy=(1.0, 1.0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=radius, radius2=radius, depth=height)
    for v in bm.verts:
        v.co.x *= scale_xy[0]
        v.co.y *= scale_xy[1]
    if any(abs(a) > 1e-5 for a in rot_euler):
        rot_mat = Euler(rot_euler, 'XYZ').to_matrix()
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_mat, verts=bm.verts)
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj, parent_root, mat)


# ==============================================================================
# 5. BUILD LAYER 0: BASE HULL (DECK 4 & BELOW — NOT CUTAWAY)
# ==============================================================================
# 5A. Underwater Keel & Antifouling Hull (Z = -1.55 .. -0.30)
create_ship_deck_solid(
    "L0_Keel_Antifouling", ROOT_L0, MAT_KEEL_RED,
    x_aft=-31.8, x_fwd=32.8, half_beam=4.05, z_bot=-1.55, z_top=-0.30,
    bow_flare=0.25, stern_rake=-0.6, bow_start=0.38
)

# 5B. Bulbous Bow (Protruding torpedo bulb at X = +31.5 .. +34.8, Z = -1.05)
add_cyl(
    "L0_Bulbous_Bow", ROOT_L0, MAT_KEEL_RED,
    center=(33.0, 0.0, -0.95), radius=0.62, height=3.8, segs=24,
    rot_euler=(0.0, math.pi / 2, 0.0), scale_xy=(0.95, 0.78)
)
add_cyl(
    "L0_Bulbous_Bow_Tip", ROOT_L0, MAT_KEEL_RED,
    center=(34.7, 0.0, -0.92), radius=0.58, height=1.1, segs=24,
    rot_euler=(0.0, math.pi / 2, 0.0), scale_xy=(0.85, 0.75)
)

# 5C. Twin Stern Azipod Thrusters & Rudder Skegs
for sy, sname in [(-1.45, "Stbd"), (1.45, "Port")]:
    add_box(f"L0_Azipod_Strut_{sname}", ROOT_L0, MAT_BOOT_NAVY, (-30.2, sy, -0.95), (1.3, 0.22, 1.1))
    add_cyl(f"L0_Azipod_Pod_{sname}", ROOT_L0, MAT_KEEL_RED, (-30.4, sy, -1.45), 0.32, 2.1, rot_euler=(0, math.pi / 2, 0))

# 5D. Dark Navy Boot-Topping Waterline Belt (Z = -0.30 .. +0.22)
create_ship_deck_solid(
    "L0_Waterline_BootTopping", ROOT_L0, MAT_BOOT_NAVY,
    x_aft=-32.4, x_fwd=33.0, half_beam=4.14, z_bot=-0.30, z_top=0.22,
    bow_flare=0.22, stern_rake=-0.25, bow_start=0.40
)

# 5E. Main White Lower Hull — Decks 1 to 4 (Z = +0.22 .. +1.85)
create_ship_deck_solid(
    "L0_Main_White_Hull_Decks1to4", ROOT_L0, MAT_HULL_WHITE,
    x_aft=-33.1, x_fwd=33.7, half_beam=4.20, z_bot=0.22, z_top=1.85,
    bow_flare=0.65, stern_rake=-0.45, bow_start=0.40
)

# 5F. Iconic Costa Smeralda Italian Tricolore Bow Ribbon (Green, White, Red swooshes wrapping the bow)
create_ship_deck_solid(
    "L0_Bow_Tricolore_Green", ROOT_L0, MAT_TRICOLORE_GREEN,
    x_aft=17.5, x_fwd=33.82, half_beam=4.23, z_bot=1.18, z_top=1.42,
    bow_flare=0.48, bow_start=-0.85, n_x=32
)
create_ship_deck_solid(
    "L0_Bow_Tricolore_Red", ROOT_L0, MAT_TRICOLORE_RED,
    x_aft=15.0, x_fwd=33.65, half_beam=4.23, z_bot=0.72, z_top=0.96,
    bow_flare=0.45, bow_start=-0.85, n_x=32
)
create_ship_deck_solid(
    "L0_Bow_Costa_Blue_Swoosh", ROOT_L0, MAT_COSTA_BLUE,
    x_aft=21.0, x_fwd=33.90, half_beam=4.24, z_bot=1.52, z_top=1.70,
    bow_flare=0.35, bow_start=-0.85, n_x=28
)

# 5G. Bow Thruster Marks & Lower Hull Porthole Strips (Decks 3 & 4)
for tx in (27.8, 28.9, 30.0, 31.1):
    add_cyl(f"L0_BowThruster_{tx:.1f}", ROOT_L0, MAT_BOOT_NAVY, (tx, 0.0, -0.65), 0.28, 3.6, rot_euler=(math.pi / 2, 0, 0))

# Top floor finish of Deck 4
create_ship_deck_solid(
    "L0_Deck4_Ceiling_Slab", ROOT_L0, MAT_DECK_SLAB_FLOOR,
    x_aft=-32.9, x_fwd=33.4, half_beam=4.12, z_bot=1.80, z_top=1.86,
    bow_flare=0.0, bow_start=0.40
)


# ==============================================================================
# 6. BUILD LAYER 1: CUTAWAY DECK 5 "TAORMINA" (Z = 1.85 .. 2.70)
#    Aft = Placeholder Ristorante La Colombina (978 seats)
# ==============================================================================
create_ship_hollow_shell(
    "L1_Deck5_Shell", ROOT_L1, MAT_HULL_WHITE, MAT_DECK_SLAB_FLOOR,
    x_aft=-33.3, x_fwd=34.0, half_beam=4.20, z_bot=1.85, z_top=2.70,
    wall_thick=0.20, floor_thick=0.08, bow_flare=0.32, bow_start=0.40
)

# Deck 5 Exterior Window Strip
create_ship_deck_solid(
    "L1_Deck5_Window_Band", ROOT_L1, MAT_GLASS_DARK,
    x_aft=-33.35, x_fwd=28.0, half_beam=4.215, z_bot=2.12, z_top=2.48,
    bow_flare=0.10, bow_start=0.40
)

# --- DECK 5 AFT: RISTORANTE LA COLOMBINA PLACEHOLDER (X = -31.8 .. -18.5) ---
create_ship_deck_solid(
    "L1_Colombina_Floor_Zone", ROOT_L1, MAT_COLOMBINA_ZONE,
    x_aft=-31.8, x_fwd=-18.5, half_beam=3.45, z_bot=1.93, z_top=2.02,
    bow_flare=0.0, bow_start=0.98, n_x=28
)

# Simplified architectural table rows & service islands inside La Colombina Placeholder
for rx in (-30.6, -28.4, -26.2, -23.8, -21.4, -19.4):
    max_y = 2.6 if rx > -29.0 else 1.8
    for ry in (-max_y, -max_y * 0.5, 0.0, max_y * 0.5, max_y):
        add_box(f"L1_Colombina_TablePH_{rx:.1f}_{ry:.1f}", ROOT_L1, MAT_SUPER_WHITE, (rx, ry, 2.18), (1.35, 0.72, 0.28))

# --- DECK 5 MID & FWD: GALLEY & TAORMINA CABIN PLACEHOLDERS ---
add_box("L1_Deck5_Galley_Placeholder", ROOT_L1, MAT_PLACEHOLDER_GALLEY, (-12.5, 0.0, 2.20), (10.5, 6.8, 0.42))
for cx in (-4.0, 3.0, 10.0, 17.0, 23.5):
    w_cab = 2.5 if cx < 20.0 else 1.65
    y_cab = 2.0 if cx < 20.0 else 1.25
    add_box(f"L1_Deck5_CabinBlock_Stbd_{cx:.0f}", ROOT_L1, MAT_PLACEHOLDER_CABIN, (cx, -y_cab, 2.20), (5.6, w_cab, 0.42))
    add_box(f"L1_Deck5_CabinBlock_Port_{cx:.0f}", ROOT_L1, MAT_PLACEHOLDER_CABIN, (cx, +y_cab, 2.20), (5.6, w_cab, 0.42))


# ==============================================================================
# 7. BUILD LAYER 2: CUTAWAY DECK 6 "ROMA" (Z = 2.70 .. 3.60)
#    - Aft: Placeholder Ristorante Il Meneghino (886 seats)
#    - Mid-Ship: Ristorante Arlecchino (2 FINISHED BLOCKS + Unbuilt Block Placeholders)
#    - Mid-Fwd: Colosseo Lower Atrium + Mastroianni Bar + Sanremo Theatre Placeholders
#    - Exterior: 16 Orange/Yellow Lifeboats (8 per side: 4 Fwd + 4 Aft of Midship Bay)
# ==============================================================================
create_ship_hollow_shell(
    "L2_Deck6_Shell", ROOT_L2, MAT_HULL_WHITE, MAT_DECK_SLAB_FLOOR,
    x_aft=-33.5, x_fwd=34.3, half_beam=4.20, z_bot=2.70, z_top=3.60,
    wall_thick=0.18, floor_thick=0.08, bow_flare=0.32,
    mid_recess=0.32, mid_recess_range=(-0.56, 0.64), bow_start=0.40
)

# --- 7A. DECK 6 AFT: RISTORANTE IL MENEGHINO PLACEHOLDER (X = -31.8 .. -19.0) ---
create_ship_deck_solid(
    "L2_Meneghino_Floor_Zone", ROOT_L2, MAT_MENEGHINO_ZONE,
    x_aft=-31.8, x_fwd=-19.0, half_beam=3.45, z_bot=2.78, z_top=2.87,
    bow_flare=0.0, bow_start=0.98, n_x=28
)
for rx in (-30.8, -28.6, -26.4, -24.0, -21.6, -19.6):
    max_y = 2.6 if rx > -29.0 else 1.8
    for ry in (-max_y, -max_y * 0.5, 0.0, max_y * 0.5, max_y):
        add_box(f"L2_Meneghino_TablePH_{rx:.1f}_{ry:.1f}", ROOT_L2, MAT_SUPER_WHITE, (rx, ry, 3.04), (1.35, 0.72, 0.28))

# --- 7B. DECK 6 AFT-MID: MAIN GALLEY PLACEHOLDER (X = -18.5 .. -8.2) ---
add_box("L2_Deck6_MainGalley_PH", ROOT_L2, MAT_PLACEHOLDER_GALLEY, (-13.3, 0.0, 3.06), (9.6, 6.4, 0.42))

# --- 7C. DECK 6 MID-SHIP: RISTORANTE ARLECCHINO (X = -7.8 .. +3.8) ---
# 1) Unbuilt Arlecchino Blocks (Aft, Port-Inboard & Fwd sections of Arlecchino) -> Placeholders!
add_box("L2_Arlecchino_Unbuilt_AftBlock_PH", ROOT_L2, MAT_ARLECCHINO_PH, (-6.2, 0.0, 2.83), (2.8, 6.8, 0.08))
for rx in (-6.9, -5.4):
    for ry in (-2.2, 0.0, 2.2):
        add_box(f"L2_Arlecchino_UnbuiltTable_Aft_{rx:.1f}_{ry:.1f}", ROOT_L2, MAT_SUPER_WHITE, (rx, ry, 3.02), (1.05, 0.65, 0.24))

add_box("L2_Arlecchino_Unbuilt_FwdBlock_PH", ROOT_L2, MAT_ARLECCHINO_PH, (+2.7, 0.0, 2.83), (2.0, 6.8, 0.08))
for ry in (-2.2, 0.0, 2.2):
    add_box(f"L2_Arlecchino_UnbuiltTable_Fwd_{ry:.1f}", ROOT_L2, MAT_SUPER_WHITE, (+2.7, ry, 3.02), (1.05, 0.65, 0.24))

# Port-side opposite unbuilt Arlecchino wing placeholder (Y = +0.8 .. +3.4, X = -4.5 .. +1.5)
add_box("L2_Arlecchino_Unbuilt_PortWing_PH", ROOT_L2, MAT_ARLECCHINO_PH, (-1.5, 2.15, 2.83), (5.8, 2.4, 0.08))
for rx in (-3.6, -1.5, +0.6):
    for ry in (1.45, 2.75):
        add_box(f"L2_Arlecchino_UnbuiltTable_Port_{rx:.1f}_{ry:.1f}", ROOT_L2, MAT_SUPER_WHITE, (rx, ry, 3.02), (1.15, 0.65, 0.24))

# 2) THE 2 FINISHED BLOCKS OF ARLECCHINO (X = -4.5 .. +1.5, Y = -3.75 .. +0.75)
# Glowing golden base frame & interactive click hitbox for the 2 finished blocks:
add_box("L2_Arlecchino_2Block_Active_Hitbox", ROOT_L2, MAT_ARLECCHINO_GOLD, (-1.50, -1.55, 2.80), (6.15, 4.55, 0.05))

# Import the actual 2-Block Arlecchino GLB into Deck 6 so both Blender and the exported GLB
# contain the real 2-block Arlecchino geometry right inside Deck 6 Mid-Ship!
ARLECCHINO_GLB = os.path.join(PROJ_DIR, "arlecchino_block1.glb")
if os.path.exists(ARLECCHINO_GLB):
    before_objs = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=ARLECCHINO_GLB)
    imported_objs = [o for o in bpy.data.objects if o not in before_objs]

    arl_holder = bpy.data.objects.new("L2_Arlecchino_2Block_RealModel", None)
    scene.collection.objects.link(arl_holder)
    arl_holder.parent = ROOT_L2

    # Parent top-level imported objects to arl_holder and remove ceiling meshes so inside is visible in cutaway!
    for o in imported_objs:
        if o.parent is None:
            o.parent = arl_holder
        if o.type == 'MESH':
            nm = o.name
            if nm.startswith((
                "Ceiling_", "CeilBeam_", "B2_CeilBeam_", "B3_CeilBeam_", "B4_CeilBeam_", "B3B4_Ceiling_",
                "RedSpot_", "B2_RedSpot_", "B3_RedSpot_", "B4_RedSpot_",
                "Corr_Downlight_", "B3B4_Corr_Downlight_", "Crossroads_Header_Beam_", "Crossroads_ExitSign_"
            )):
                bpy.data.objects.remove(o, do_unlink=True)

    # Transform arl_holder so the 4 blocks (Y_arl = 0..17.46m -> X_ship = -4.45..+1.48m,
    # X_arl = -2.35..28.15m -> Y_ship = +0.55..-3.75m Starboard window wall) fit inside Deck 6!
    arl_holder.scale = (0.15, 0.34, 0.22)
    arl_holder.rotation_euler = (0.0, 0.0, -math.pi / 2.0)
    arl_holder.location = (-4.45, -0.22, 2.83)

# --- 7D. DECK 6 MID-FWD: COLOSSEO LOWER ATRIUM & SANREMO THEATRE PLACEHOLDERS ---
add_cyl("L2_Colosseo_Lower_Stage", ROOT_L2, MAT_COLOSSEO_ZONE, (7.8, 0.0, 2.95), 2.75, 0.25, segs=36)
add_cyl("L2_Colosseo_Center_Core", ROOT_L2, MAT_SUPER_WHITE, (7.8, 0.0, 3.08), 1.35, 0.30, segs=32)

# Panoramic Midship Colosseo / Arlecchino Glass Bay Windows (X = -5.6 .. +10.2)
for sy, sname in [(-4.12, "Stbd"), (4.12, "Port")]:
    add_box(f"L2_Midship_PanoramicGlass_{sname}", ROOT_L2, MAT_GLASS_ATRIUM, (2.3, sy, 3.18), (15.8, 0.10, 0.78))

# Forward Sanremo Theatre Lower Level Placeholder (X = +15.0 .. +28.5)
add_box("L2_Sanremo_Theatre_Lower_PH", ROOT_L2, MAT_THEATRE_ZONE, (21.5, 0.0, 3.02), (11.5, 5.4, 0.35))

# --- 7E. EXTERIOR LIFEBOAT GALLERY: 8 ORANGE LIFEBOATS PER SIDE (4 AFT + 4 FWD OF MIDSHIP BAY) ---
lifeboat_x_positions = [-16.8, -13.7, -10.6, -7.5, +11.6, +14.7, +17.8, +20.9]
for side_sign, side_lbl in [(-1.0, "Stbd"), (+1.0, "Port")]:
    y_lb = side_sign * 4.02
    for idx, lx in enumerate(lifeboat_x_positions, start=1):
        # Orange lower hull + canopy of each Excellence-class lifeboat
        add_cyl(
            f"L2_Lifeboat_{side_lbl}_{idx}_Hull", ROOT_L2, MAT_LIFEBOAT_ORANGE,
            center=(lx, y_lb, 3.18), radius=0.34, height=2.55, segs=18,
            rot_euler=(0.0, math.pi / 2.0, 0.0), scale_xy=(0.75, 1.0)
        )
        add_box(
            f"L2_Lifeboat_{side_lbl}_{idx}_Cabin", ROOT_L2, MAT_COSTA_YELLOW,
            center=(lx, y_lb, 3.34), size=(1.65, 0.56, 0.22)
        )
        # Steel Davit Arms
        for dx in (-0.85, +0.85):
            add_box(
                f"L2_Davit_{side_lbl}_{idx}_{dx:+.1f}", ROOT_L2, MAT_STEEL_SILVER,
                center=(lx + dx, y_lb - side_sign * 0.15, 3.45), size=(0.10, 0.45, 0.48)
            )


# ==============================================================================
# 8. BUILD LAYER 3: CUTAWAY DECK 7 "POSITANO" (Z = 3.60 .. 4.45)
#    Aft = Placeholder Ristorante Il Rugantino (546 seats) & Superba Bar
# ==============================================================================
create_ship_hollow_shell(
    "L3_Deck7_Shell", ROOT_L3, MAT_HULL_WHITE, MAT_DECK_SLAB_FLOOR,
    x_aft=-33.6, x_fwd=34.5, half_beam=4.20, z_bot=3.60, z_top=4.45,
    wall_thick=0.18, floor_thick=0.08, bow_flare=0.28,
    mid_recess=0.32, mid_recess_range=(-0.56, 0.64), bow_start=0.40
)

# --- 8A. DECK 7 AFT: RISTORANTE IL RUGANTINO PLACEHOLDER (X = -31.8 .. -18.5) ---
create_ship_deck_solid(
    "L3_Rugantino_Floor_Zone", ROOT_L3, MAT_RUGANTINO_ZONE,
    x_aft=-31.8, x_fwd=-18.5, half_beam=3.45, z_bot=3.68, z_top=3.77,
    bow_flare=0.0, bow_start=0.98, n_x=28
)
for rx in (-30.6, -28.2, -25.8, -23.2, -20.6):
    max_y = 2.5 if rx > -29.0 else 1.75
    for ry in (-max_y, -max_y * 0.5, 0.0, max_y * 0.5, max_y):
        add_box(f"L3_Rugantino_TablePH_{rx:.1f}_{ry:.1f}", ROOT_L3, MAT_SUPER_WHITE, (rx, ry, 3.94), (1.30, 0.72, 0.28))

# --- 8B. DECK 7 MID: CODE DESIGN MUSEUM, SHOPS & COLOSSEO MID-LEVEL ATRIUM ---
add_box("L3_CoDe_Museum_Shops_PH", ROOT_L3, MAT_PLACEHOLDER_CABIN, (-11.2, 0.0, 3.96), (12.5, 6.4, 0.40))
add_cyl("L3_Colosseo_Mid_Ring", ROOT_L3, MAT_COLOSSEO_ZONE, (7.8, 0.0, 3.92), 2.95, 0.30, segs=36)
for sy, sname in [(-4.16, "Stbd"), (4.16, "Port")]:
    add_box(f"L3_Midship_PanoramicGlass_{sname}", ROOT_L3, MAT_GLASS_ATRIUM, (3.0, sy, 4.05), (14.2, 0.10, 0.78))

# --- 8C. DECK 7 FWD: LAGUNA CASINO & SANREMO THEATRE UPPER LEVEL ---
add_box("L3_Laguna_Casino_PH", ROOT_L3, MAT_PLACEHOLDER_CABIN, (15.2, 0.0, 3.96), (6.5, 6.2, 0.40))
add_box("L3_Sanremo_Theatre_Upper_PH", ROOT_L3, MAT_THEATRE_ZONE, (23.5, 0.0, 3.96), (8.5, 5.2, 0.40))


# ==============================================================================
# 9. BUILD LAYER 4: UNIFIED TOP SUPERSTRUCTURE (DECK 8 TO UPPER MUFFLER)
#    Moves as ONE unified top block (Z = 4.45 .. 14.20)
# ==============================================================================
# 9A. Deck 8 "Capri" — Lungomare Riviera Wide Wrap-Around Promenade (Z = 4.45 .. 5.15)
create_ship_deck_solid(
    "L4_Deck8_Lungomare_TeakPromenade", ROOT_L4, MAT_TEAK_DECK,
    x_aft=-33.7, x_fwd=34.6, half_beam=4.42, z_bot=4.45, z_top=4.62,
    bow_flare=0.18, bow_start=0.40
)
create_ship_deck_solid(
    "L4_Deck8_Superstructure_Core", ROOT_L4, MAT_SUPER_WHITE,
    x_aft=-32.6, x_fwd=28.2, half_beam=3.98, z_bot=4.62, z_top=5.12,
    bow_flare=0.0, mid_recess=0.18, mid_recess_range=(-0.15, 0.25), bow_start=0.35
)
create_ship_deck_solid(
    "L4_Deck8_Promenade_GlassRailing", ROOT_L4, MAT_GLASS_BALCONY,
    x_aft=-33.65, x_fwd=34.55, half_beam=4.43, z_bot=4.62, z_top=4.84,
    bow_flare=0.15, bow_start=0.40
)

# Bow Mooring Foredeck Details on Deck 8/9 (X = +28.2 .. +34.4)
add_box("L4_Bow_Breakwater_WaveShield", ROOT_L4, MAT_SUPER_WHITE, (29.5, 0.0, 4.82), (0.35, 4.6, 0.42))
for wx, wy in [(30.8, -1.2), (30.8, 1.2), (32.2, -0.7), (32.2, 0.7)]:
    add_cyl(f"L4_Bow_Winch_{wx:.1f}_{wy:.1f}", ROOT_L4, MAT_STEEL_SILVER, (wx, wy, 4.75), 0.28, 0.25, segs=16)

# 9B. Decks 9 to 17 Multi-Tier Passenger Balcony Superstructure (8 Tiered Decks: 9,10,11,12,14,15,16,17)
deck_tiers = [
    ("Deck09_Napoli",    5.12, 5.72, -32.2, 27.2, 4.12, 0.22),
    ("Deck10_Palermo",   5.72, 6.32, -31.7, 26.2, 4.10, 0.22),
    ("Deck11_Venezia",   6.32, 6.92, -31.1, 25.1, 4.08, 0.22),
    ("Deck12_Firenze",   6.92, 7.52, -30.5, 24.0, 4.06, 0.22),
    ("Deck14_Milano",    7.52, 8.12, -29.8, 22.9, 4.04, 0.22),
    ("Deck15_Torino",    8.12, 8.72, -28.9, 21.8, 4.02, 0.20),
    ("Deck16_Como",      8.72, 9.32, -26.8, 20.4, 3.98, 0.18),
    ("Deck17_Bellagio",  9.32, 9.92, -24.6, 18.8, 3.92, 0.16),
]

for dname, zb, zt, x_a, x_f, h_beam, m_rec in deck_tiers:
    # White horizontal slab & cabin setback
    create_ship_deck_solid(
        f"L4_{dname}_Slab", ROOT_L4, MAT_SUPER_WHITE,
        x_aft=x_a, x_fwd=x_f, half_beam=h_beam, z_bot=zb, z_top=zb + 0.22,
        mid_recess=m_rec, mid_recess_range=(-0.16, 0.24), bow_start=0.32
    )
    create_ship_deck_solid(
        f"L4_{dname}_CabinWall", ROOT_L4, MAT_HULL_WHITE,
        x_aft=x_a + 0.35, x_fwd=x_f - 0.35, half_beam=h_beam - 0.18, z_bot=zb + 0.22, z_top=zt,
        mid_recess=m_rec, mid_recess_range=(-0.16, 0.24), bow_start=0.32
    )
    # Tinted blue glass balcony strip
    create_ship_deck_solid(
        f"L4_{dname}_BalconyGlass", ROOT_L4, MAT_GLASS_BALCONY,
        x_aft=x_a + 0.05, x_fwd=x_f - 0.05, half_beam=h_beam + 0.02, z_bot=zb + 0.22, z_top=zb + 0.48,
        mid_recess=m_rec, mid_recess_range=(-0.16, 0.24), bow_start=0.32
    )

# Vertical white balcony privacy dividers along the hull sides for crisp realism
for vx in range(-26, 20, 3):
    hb_v = 4.06 * ship_half_beam_at(vx / 30.0, bow_start=0.32, mid_recess=0.20, mid_recess_range=(-0.16, 0.24))
    for side in (-1.0, 1.0):
        add_box(
            f"L4_BalconyPillar_{vx}_{'S' if side < 0 else 'P'}", ROOT_L4, MAT_SUPER_WHITE,
            center=(vx, side * hb_v, 7.22), size=(0.14, 0.18, 4.20)
        )

# 9C. Deck 15 Navigation Bridge & Protruding Port/Starboard Bridge Wings (X = +21.4, Z = 8.42)
add_box("L4_NavBridge_CenterHouse", ROOT_L4, MAT_SUPER_WHITE, (21.6, 0.0, 8.45), (2.4, 8.4, 0.68))
add_box("L4_NavBridge_Windshield", ROOT_L4, MAT_GLASS_DARK, (22.2, 0.0, 8.52), (1.45, 8.5, 0.38))
for side_s, s_lbl in [(-1.0, "Stbd"), (+1.0, "Port")]:
    # Protruding Bridge Wings extending 1.45m past the ship beam!
    add_box(f"L4_BridgeWing_{s_lbl}", ROOT_L4, MAT_SUPER_WHITE, (21.5, side_s * 4.85, 8.45), (1.55, 2.25, 0.58))
    add_box(f"L4_BridgeWing_Glass_{s_lbl}", ROOT_L4, MAT_GLASS_DARK, (21.5, side_s * 4.92, 8.52), (1.62, 2.15, 0.32))
    add_cyl(f"L4_BridgeWing_Support_{s_lbl}", ROOT_L4, MAT_SUPER_WHITE, (21.5, side_s * 4.65, 7.95), 0.22, 0.75, segs=16)

# 9D. Aft Decks 15–18 Cascading "Piazza di Spagna" (Spanish Steps Amphitheater) & Deck 18 "Orizzonte" Canopy
# Tiered grand staircase descending along the actual stern cascade from X = -23.5 (Deck 18) to X = -29.2 (Deck 15)
for step_i in range(9):
    sx = -23.6 - step_i * 0.66
    sz = 9.88 - step_i * 0.21
    sw = 4.6 + step_i * 0.18
    add_box(f"L4_PiazzaDiSpagna_Step_{step_i}", ROOT_L4, MAT_TEAK_DECK, (sx, 0.0, sz), (0.72, sw, 0.22))

# Curved white architectural side wings framing Piazza di Spagna at the stern
for side_s, s_lbl in [(-1.0, "Stbd"), (+1.0, "Port")]:
    for wi in range(8):
        wx = -23.4 - wi * 0.72
        wz = 10.05 - wi * 0.22
        wy = side_s * (2.45 + wi * 0.10)
        add_box(f"L4_PiazzaWing_{s_lbl}_{wi}", ROOT_L4, MAT_SUPER_WHITE, (wx, wy, wz), (0.95, 0.34, 0.55))

# Cantilevered Deck 18 "Passeggiata Orizzonte" Glass-Floor Overhang Balcony at Stern
add_cyl(
    "L4_Orizzonte_Cantilever_Arch", ROOT_L4, MAT_SUPER_WHITE,
    center=(-24.2, 0.0, 10.22), radius=3.15, height=0.22, segs=32, scale_xy=(0.85, 1.0)
)
add_cyl(
    "L4_Orizzonte_GlassWalkway", ROOT_L4, MAT_GLASS_ATRIUM,
    center=(-24.4, 0.0, 10.36), radius=3.22, height=0.18, segs=32, scale_xy=(0.85, 1.0)
)

# 9E. Midship Decks 16–18 "La Spiaggia" Arched Glass Magrodome Conservatory Roof (X = +1.5 .. +12.2)
add_box("L4_LaSpiaggia_PoolBase", ROOT_L4, MAT_POOL_WATER, (6.8, 0.0, 9.96), (7.8, 4.2, 0.10))
add_cyl(
    "L4_LaSpiaggia_Magrodome_Glass", ROOT_L4, MAT_GLASS_ATRIUM,
    center=(6.8, 0.0, 9.95), radius=3.45, height=10.6, segs=32,
    rot_euler=(0.0, math.pi / 2.0, 0.0), scale_xy=(0.38, 1.0)
)
# White arched structural steel ribs over the Magrodome
for rib_x in (2.0, 3.6, 5.2, 6.8, 8.4, 10.0, 11.6):
    add_cyl(
        f"L4_Magrodome_Rib_{rib_x:.1f}", ROOT_L4, MAT_SUPER_WHITE,
        center=(rib_x, 0.0, 9.96), radius=3.52, height=0.16, segs=28,
        rot_euler=(0.0, math.pi / 2.0, 0.0), scale_xy=(0.39, 1.0)
    )

# 9F. Twin Architectural White Fin Towers (Forward & Aft of Magrodome)
for fx, fname in [(12.8, "Fwd"), (0.6, "Mid")]:
    for side_s, s_lbl in [(-1.0, "Stbd"), (+1.0, "Port")]:
        add_box(
            f"L4_ArchFin_{fname}_{s_lbl}", ROOT_L4, MAT_SUPER_WHITE,
            center=(fx, side_s * 3.35, 10.65), size=(1.85, 0.28, 1.55)
        )

# 9G. Forward Decks 18–19 "Settimo Cielo" Sun Deck, Radomes & Forward Radar Mast (X = +13.2 .. +21.5)
create_ship_deck_solid(
    "L4_Deck18_SettimoCielo", ROOT_L4, MAT_SUPER_WHITE,
    x_aft=12.5, x_fwd=19.8, half_beam=3.45, z_bot=9.92, z_top=10.45, bow_start=0.20, n_x=24
)
create_ship_deck_solid(
    "L4_Deck19_Solarium", ROOT_L4, MAT_SUPER_WHITE,
    x_aft=13.5, x_fwd=18.2, half_beam=2.75, z_bot=10.45, z_top=10.90, bow_start=0.20, n_x=20
)

# Satellite Communication Radomes (White Spheres on Pedestals)
for rx, ry, rz, rad in [
    (19.2, -1.6, 10.35, 0.42), (19.2, 1.6, 10.35, 0.42),
    (14.2, -2.2, 10.85, 0.48), (14.2, 2.2, 10.85, 0.48),
    (-15.5, -2.0, 10.25, 0.40), (-15.5, 2.0, 10.25, 0.40),
]:
    add_cyl(f"L4_Radome_Ped_{rx:.1f}_{ry:.1f}", ROOT_L4, MAT_SUPER_WHITE, (rx, ry, rz - 0.22), 0.14, 0.35, segs=16)
    mesh_sp = bpy.data.meshes.new(f"L4_Radome_{rx:.1f}_{ry:.1f}")
    bm_sp = bmesh.new()
    bmesh.ops.create_uvsphere(bm_sp, u_segments=20, v_segments=14, radius=rad)
    bmesh.ops.translate(bm_sp, vec=(rx, ry, rz + rad * 0.55), verts=bm_sp.verts)
    bm_sp.to_mesh(mesh_sp)
    bm_sp.free()
    for p in mesh_sp.polygons:
        p.use_smooth = True
    link_obj(bpy.data.objects.new(mesh_sp.name, mesh_sp), ROOT_L4, MAT_SUPER_WHITE)

# Forward Raked Radar Mast (X = +16.8, Z = 10.85 .. 13.95)
add_cyl(
    "L4_Forward_Radar_Mast", ROOT_L4, MAT_SUPER_WHITE,
    center=(16.5, 0.0, 12.35), radius=0.22, height=3.3, segs=20,
    rot_euler=(0.0, -0.24, 0.0), scale_xy=(1.5, 0.8)
)
add_box("L4_Radar_Crossbar_1", ROOT_L4, MAT_SUPER_WHITE, (16.4, 0.0, 12.65), (0.28, 2.65, 0.12))
add_box("L4_Radar_Scanner_1", ROOT_L4, MAT_COSTA_BLUE, (16.55, 0.0, 12.82), (0.22, 1.45, 0.14))
add_box("L4_Radar_Crossbar_2", ROOT_L4, MAT_SUPER_WHITE, (16.2, 0.0, 13.45), (0.22, 1.85, 0.10))

# 9H. "Aqua Park Smeralda" Colorful Waterslides (X = -3.8 .. -0.2, Z = 9.95 .. 12.05)
add_cyl("L4_AquaPark_Tower", ROOT_L4, MAT_SUPER_WHITE, (-1.8, 0.0, 11.05), 0.35, 2.3, segs=18)
for sl_i in range(14):
    ang = sl_i * 0.48
    sx1 = -1.6 + 1.15 * math.cos(ang)
    sy1 = -1.1 + 0.95 * math.sin(ang)
    sz1 = 11.85 - sl_i * 0.13
    add_cyl(f"L4_Waterslide_Coral_{sl_i}", ROOT_L4, MAT_SLIDE_CORAL, (sx1, sy1, sz1), 0.22, 0.48, segs=14, rot_euler=(0.3, 0.4, ang))

    sx2 = -2.2 + 1.05 * math.cos(-ang + 1.2)
    sy2 = +1.1 + 0.90 * math.sin(-ang + 1.2)
    sz2 = 11.75 - sl_i * 0.125
    add_cyl(f"L4_Waterslide_Cyan_{sl_i}", ROOT_L4, MAT_SLIDE_CYAN, (sx2, sy2, sz2), 0.22, 0.48, segs=14, rot_euler=(-0.3, 0.4, -ang))

# 9I. ICONIC COSTA YELLOW FUNNEL / MUFFLER WITH BLUE "C" LOGO (X = -8.5, Z = 9.90 .. 14.15)
# Funnel base casing
add_box("L4_Funnel_BaseCasing", ROOT_L4, MAT_SUPER_WHITE, (-8.5, 0.0, 10.22), (6.2, 3.6, 0.68))

# Main streamlined aerodynamic yellow funnel body
add_cyl(
    "L4_Costa_Yellow_Funnel", ROOT_L4, MAT_COSTA_YELLOW,
    center=(-8.6, 0.0, 12.15), radius=1.52, height=3.65, segs=36,
    rot_euler=(0.0, -0.16, 0.0), scale_xy=(1.75, 0.88)
)

# Dark Navy Funnel Top Cap Shroud
add_cyl(
    "L4_Costa_Funnel_NavyCap", ROOT_L4, MAT_BOOT_NAVY,
    center=(-8.92, 0.0, 13.88), radius=1.48, height=0.52, segs=36,
    rot_euler=(0.0, -0.16, 0.0), scale_xy=(1.72, 0.86)
)

# 3 Silver Exhaust Muffler Pipes protruding from the top of the funnel
for mx in (-9.65, -8.95, -8.25):
    add_cyl(
        f"L4_Muffler_ExhaustPipe_{mx:.2f}", ROOT_L4, MAT_STEEL_SILVER,
        center=(mx, 0.0, 14.22), radius=0.26, height=0.55, segs=20,
        rot_euler=(0.0, -0.16, 0.0)
    )

# Air-intake louvre grilles on the funnel sides
for side_s, s_lbl in [(-1.0, "Stbd"), (+1.0, "Port")]:
    add_box(
        f"L4_Funnel_Grille_{s_lbl}", ROOT_L4, MAT_BOOT_NAVY,
        center=(-9.85, side_s * 1.18, 12.65), size=(1.35, 0.12, 1.45)
    )

# Costa Blue 'C' Logo Plaques on both Starboard (-Y) and Port (+Y) sides of the Yellow Funnel!
for side_s, s_lbl in [(-1.0, "Stbd"), (+1.0, "Port")]:
    # Build a curved 3D 'C' emblem on both sides of the funnel so it looks ultra-sharp at any zoom!
    c_cx, c_cy, c_cz = -8.15, side_s * 1.34, 12.15
    for seg_i in range(14):
        # Angle from 40 deg to 320 deg forms a bold 'C'
        theta = math.radians(42 + seg_i * (276 / 13.0))
        px = c_cx - side_s * 0.72 * math.cos(theta)
        pz = c_cz + 0.72 * math.sin(theta)
        add_box(
            f"L4_Funnel_C_Logo_{s_lbl}_{seg_i}", ROOT_L4, MAT_COSTA_BLUE,
            center=(px, c_cy, pz), size=(0.30, 0.08, 0.30)
        )

# 9J. Deck 20 "Passeggiata Volare" High White Parabolic Skywalk Arch (X = -15.8 .. -11.2, Z = 9.95 .. 13.55)
for arch_i in range(25):
    t = -1.0 + 2.0 * arch_i / 24.0  # -1 (Stbd) to +1 (Port)
    ay = t * 2.85
    az = 10.05 + 3.40 * (1.0 - t * t)
    ax = -13.6 - 0.85 * (1.0 - t * t)
    roll = math.atan2(-6.80 * t, 2.85)
    add_cyl(
        f"L4_Passeggiata_Volare_Arch_{arch_i}", ROOT_L4, MAT_SUPER_WHITE,
        center=(ax, ay, az), radius=0.22, height=0.52, segs=16,
        rot_euler=(roll + math.pi / 2.0, 0.0, 0.0), scale_xy=(1.35, 0.85)
    )


# ==============================================================================
# 10. SAVE .BLEND AND EXPORT .GLB FOR WEB PORTAL
# ==============================================================================
BLEND_PATH = os.path.join(PROJ_DIR, "costa_smeralda_ship.blend")
GLB_PATH = os.path.join(PROJ_DIR, "costa_smeralda_ship.glb")

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print(f"Saved Blender file: {BLEND_PATH}")

bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format='GLB',
    export_apply=False,
    export_yup=True,
    export_materials='EXPORT'
)
print(f"Exported GLB file: {GLB_PATH}")


# ==============================================================================
# 11. RENDER VERIFICATION IMAGES (EXTERIOR PROFILE & 4-LAYER CUTAWAY)
# ==============================================================================
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 900

world = bpy.data.worlds.new("ShipWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.04, 0.10, 0.20, 1.0)
bg_node.inputs[1].default_value = 1.2

# Sun & Fill Lights
sun_data = bpy.data.lights.new("SunLight", type='SUN')
sun_data.energy = 3.8
sun_data.color = (1.0, 0.97, 0.90)
sun_obj = bpy.data.objects.new("SunLight", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(48), math.radians(15), math.radians(-35))

fill_data = bpy.data.lights.new("FillLight", type='SUN')
fill_data.energy = 1.6
fill_data.color = (0.75, 0.88, 1.0)
fill_obj = bpy.data.objects.new("FillLight", fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.rotation_euler = (math.radians(65), math.radians(-20), math.radians(145))

cam_data = bpy.data.cameras.new("VerifyCam")
cam_data.lens = 35
cam_obj = bpy.data.objects.new("VerifyCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj


def point_cam(pos, target):
    cam_obj.location = Vector(pos)
    direction = Vector(target) - Vector(pos)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()


# 1) Render Full Ship Starboard Bow 3/4 View
point_cam((42.0, -44.0, 18.0), (0.0, 0.0, 5.5))
scene.render.filepath = os.path.join(PROJ_DIR, "scratch", "render_ship_full_bow34.png")
bpy.ops.render.render(write_still=True)

# 2) Render Full Ship Starboard Stern 3/4 View (Piazza di Spagna, Volare Arch & Yellow Funnel)
point_cam((-46.0, -38.0, 19.0), (-6.0, 0.0, 6.0))
scene.render.filepath = os.path.join(PROJ_DIR, "scratch", "render_ship_full_stern34.png")
bpy.ops.render.render(write_still=True)

# 3) Render Cutaway Deck 6 (Lifting Layer 3 & Layer 4 to expose Deck 6 Arlecchino 2-Block & Meneghino)
ROOT_L3.location.z = 5.5
ROOT_L4.location.z = 9.5
point_cam((12.0, -32.0, 16.5), (-4.0, 0.0, 4.5))
scene.render.filepath = os.path.join(PROJ_DIR, "scratch", "render_ship_cutaway_deck6.png")
bpy.ops.render.render(write_still=True)

# Restore zero offsets and re-save clean .blend
ROOT_L3.location.z = 0.0
ROOT_L4.location.z = 0.0
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("All verification renders complete.")
