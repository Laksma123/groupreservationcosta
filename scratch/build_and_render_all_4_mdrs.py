import bpy
import bmesh
import json
import math
import os
import shutil
from mathutils import Vector, Matrix, Euler
from mathutils.geometry import tessellate_polygon

PROJ_DIR = "/Users/dianjulie/Documents/Map Project"
SCRATCH_DIR = os.path.join(PROJ_DIR, "scratch")
OUT_FOLDER = os.path.join(PROJ_DIR, "MDR_3D_Deck_Plans")
os.makedirs(OUT_FOLDER, exist_ok=True)

SCALE = 0.10  # 1 PDF pt = 0.10 Blender meters (Full ship length = 67.33m)


def build_and_render_mdr_deck(json_filename, png_filename, blend_filename, glb_filename):
    vec_json_path = os.path.join(SCRATCH_DIR, json_filename)
    with open(vec_json_path, "r") as f:
        vdata = json.load(f)

    CLIP = vdata["clip"]
    X_CENTER = vdata["x_center"]
    Y_MID = vdata["y_mid"]
    TEX_PLAN = vdata["tex_plan"]
    TEX_BUMP = vdata["tex_bump"]
    MODEL_NAME = vdata["name"]

    def pdf_to_bl(x_pdf, y_pdf):
        return ((Y_MID - y_pdf) * SCALE, (X_CENTER - x_pdf) * SCALE)

    def bl_to_uv(x_bl, y_bl):
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

    root_col = bpy.data.collections.new(f"{MODEL_NAME}_Collection")
    scene.collection.children.link(root_col)

    ROOT_EMPTY = bpy.data.objects.new(f"{MODEL_NAME}_Root", None)
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
        tex_color.interpolation = 'Cubic'

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

    # Architectural Monochrome + Emerald Green Highlight Materials
    MAT_HULL_OBSIDIAN   = make_pbr_mat("Hull_Plinth_Obsidian_Black", (0.045, 0.050, 0.060, 1.0), rough=0.28, metal=0.20)
    MAT_HULL_TITANIUM   = make_pbr_mat("Hull_Waterline_Titanium_Grey", (0.28, 0.31, 0.36, 1.0), rough=0.32, metal=0.45)
    MAT_HULL_WHITE      = make_pbr_mat("Hull_Sheer_Pure_White", (0.94, 0.95, 0.97, 1.0), rough=0.25, metal=0.06)

    MAT_PLAN_FLOOR      = make_plan_textured_mat(f"{MODEL_NAME}_Plan_Floor", rough=0.36, bump_dist=0.012)
    MAT_PLAN_ZONE_TOP   = make_plan_textured_mat(f"{MODEL_NAME}_Zone_Relief_Top", tint_rgba=(0.98, 0.99, 1.0, 1.0), rough=0.32, bump_dist=0.015)

    MAT_WALL_WHITE_EXT  = make_pbr_mat("Wall_Exterior_White", (0.95, 0.96, 0.98, 1.0), rough=0.26, metal=0.05)
    MAT_WALL_BLACK_CAP  = make_pbr_mat("Wall_TopCap_JetBlack", (0.035, 0.040, 0.048, 1.0), rough=0.22, metal=0.18)
    MAT_WALL_CHARCOAL   = make_pbr_mat("Wall_Interior_Charcoal", (0.12, 0.135, 0.16, 1.0), rough=0.32, metal=0.15)
    MAT_WALL_SILVER_CAP = make_pbr_mat("Wall_Interior_DarkGraphite_Cap", (0.055, 0.062, 0.075, 1.0), rough=0.24, metal=0.22)
    MAT_ZONE_SIDE_GREY  = make_pbr_mat("Zone_Relief_Side_Slate", (0.22, 0.25, 0.30, 1.0), rough=0.35, metal=0.12)

    MAT_LIFEBOAT_GREY   = make_pbr_mat("Lifeboat_Monochrome_SlateGrey", (0.30, 0.34, 0.40, 1.0), rough=0.28, metal=0.25)
    MAT_LIFEBOAT_CABIN  = make_pbr_mat("Lifeboat_Monochrome_PearlWhite", (0.90, 0.92, 0.95, 1.0), rough=0.24, metal=0.08)
    MAT_DAVIT_GRAPHITE  = make_pbr_mat("Lifeboat_Davit_Graphite", (0.10, 0.11, 0.13, 1.0), rough=0.28, metal=0.65)
    MAT_COLOSSEO_GLASS  = make_pbr_mat("Colosseo_Smoked_Glass", (0.14, 0.17, 0.22, 1.0), rough=0.10, metal=0.40, alpha=0.76)

    MAT_MDR_TOP_GREEN   = make_pbr_mat(
        "MDR_Emboss_Top_Green",
        (0.038, 0.65, 0.26, 1.0),
        rough=0.20,
        metal=0.06,
        emit_rgba=(0.05, 0.76, 0.32, 1.0),
        emit_strength=0.16,
    )
    MAT_MDR_SIDE_GREEN  = make_pbr_mat(
        "MDR_Emboss_Side_DeepGreen",
        (0.018, 0.38, 0.14, 1.0),
        rough=0.26,
        metal=0.08,
        emit_rgba=(0.025, 0.45, 0.18, 1.0),
        emit_strength=0.06,
    )
    MAT_MDR_RIM_GLOW    = make_pbr_mat(
        "MDR_Emboss_Bevel_Rim_BrightGreen",
        (0.32, 0.96, 0.56, 1.0),
        rough=0.14,
        metal=0.12,
        emit_rgba=(0.35, 0.98, 0.60, 1.0),
        emit_strength=0.42,
    )
    MAT_MDR_BASE_COLLAR = make_pbr_mat(
        "MDR_Base_Collar_White",
        (0.96, 0.98, 0.97, 1.0),
        rough=0.20,
        metal=0.10,
    )

    def create_extruded_polygon_mesh(
        name, poly_pdf, z_bot, z_top,
        mat_top, mat_side=None, mat_bevel=None,
        bevel_top_w=0.0, bevel_top_h=0.0,
        apply_plan_uv=False
    ):
        pts_2d = [Vector(pdf_to_bl(px, py)) for px, py in poly_pdf]
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

        for i in range(n):
            j = (i + 1) % n
            f_side = bm.faces.new([v_bot[i], v_bot[j], v_mid[j], v_mid[i]])
            f_side.material_index = side_idx

        if bevel_top_w > 0.0 and bevel_top_h > 0.0:
            for i in range(n):
                j = (i + 1) % n
                f_bev = bm.faces.new([v_mid[i], v_mid[j], v_top[j], v_top[i]])
                f_bev.material_index = bev_idx

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

                for vs in ([c0, c1, t1, t0], [c1, c2, t2, t1], [c2, c3, t3, t2], [c3, c0, t0, t3]):
                    f = bm.faces.new(vs)
                    f.material_index = 0
                ft = bm.faces.new([t0, t1, t2, t3])
                ft.material_index = 1

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(name, mesh)
        obj.data.materials.append(mat_side)
        obj.data.materials.append(mat_cap)
        return link_obj(obj)

    # 1. Sculpted Ship Hull Plinth & Main Floor Slab
    hull_loop = vdata["hull_outer_loop"]
    create_extruded_polygon_mesh(
        f"{MODEL_NAME}_Hull_Plinth_Obsidian", hull_loop,
        z_bot=-0.52, z_top=-0.16,
        mat_top=MAT_HULL_OBSIDIAN, mat_side=MAT_HULL_OBSIDIAN
    )
    create_extruded_polygon_mesh(
        f"{MODEL_NAME}_Hull_Waterline_Titanium", hull_loop,
        z_bot=-0.16, z_top=-0.04,
        mat_top=MAT_HULL_TITANIUM, mat_side=MAT_HULL_TITANIUM
    )
    create_extruded_polygon_mesh(
        f"{MODEL_NAME}_Main_Floor_Slab", hull_loop,
        z_bot=-0.04, z_top=0.16,
        mat_top=MAT_PLAN_FLOOR, mat_side=MAT_HULL_WHITE,
        apply_plan_uv=True
    )

    # 2. Stepped Monochrome Zone Reliefs & Architectural Cores
    for z_name, z_poly in vdata["zone_polys"].items():
        create_extruded_polygon_mesh(
            f"{MODEL_NAME}_ZoneRelief_{z_name}", z_poly,
            z_bot=0.155, z_top=0.205,
            mat_top=MAT_PLAN_ZONE_TOP, mat_side=MAT_ZONE_SIDE_GREY,
            apply_plan_uv=True
        )

    if vdata.get("engine_casing"):
        create_extruded_polygon_mesh(
            f"{MODEL_NAME}_Engine_Casing_3D_Core", vdata["engine_casing"],
            z_bot=0.16, z_top=0.28,
            mat_top=MAT_PLAN_ZONE_TOP, mat_side=MAT_WALL_CHARCOAL,
            apply_plan_uv=True
        )

    for idx, (rx0, ry0, rx1, ry1) in enumerate(vdata.get("elevators", []), start=1):
        r_poly = [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]
        create_extruded_polygon_mesh(
            f"{MODEL_NAME}_ElevatorBank_{idx}", r_poly,
            z_bot=0.16, z_top=0.38,
            mat_top=MAT_PLAN_ZONE_TOP, mat_side=MAT_WALL_CHARCOAL,
            mat_bevel=MAT_WALL_SILVER_CAP, bevel_top_w=0.025, bevel_top_h=0.02,
            apply_plan_uv=True
        )

    # 3. Outer Hull Perimeter Bulwark, Colosseo Glass Bays, Interior Walls & Lifeboats
    hull_closed_polyline = hull_loop + [hull_loop[0]]
    create_polyline_wall_mesh(
        f"{MODEL_NAME}_Outer_Hull_Bulwark_Wall",
        [hull_closed_polyline],
        z_bot=0.16, z_top=0.42,
        thickness=0.12,
        mat_side=MAT_WALL_WHITE_EXT,
        mat_cap=MAT_WALL_BLACK_CAP
    )

    if vdata.get("colosseo_port_outer") and vdata.get("colosseo_stbd_outer"):
        create_polyline_wall_mesh(
            f"{MODEL_NAME}_Colosseo_Panoramic_Glass_Wall",
            [vdata["colosseo_port_outer"], vdata["colosseo_stbd_outer"]],
            z_bot=0.16, z_top=0.52,
            thickness=0.09,
            mat_side=MAT_COLOSSEO_GLASS,
            mat_cap=MAT_WALL_SILVER_CAP
        )

    if vdata.get("wall_polylines"):
        create_polyline_wall_mesh(
            f"{MODEL_NAME}_Interior_Walls_Monochrome",
            vdata["wall_polylines"],
            z_bot=0.16, z_top=0.34,
            thickness=0.055,
            mat_side=MAT_WALL_CHARCOAL,
            mat_cap=MAT_WALL_SILVER_CAP
        )

    for lb_idx, lb_poly in enumerate(vdata.get("lifeboats", []), start=1):
        create_extruded_polygon_mesh(
            f"{MODEL_NAME}_Lifeboat_{lb_idx:02d}_Hull", lb_poly,
            z_bot=0.02, z_top=0.28,
            mat_top=MAT_LIFEBOAT_GREY, mat_side=MAT_LIFEBOAT_GREY,
            mat_bevel=MAT_LIFEBOAT_CABIN, bevel_top_w=0.08, bevel_top_h=0.06
        )
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
            f"{MODEL_NAME}_Lifeboat_{lb_idx:02d}_Cabin", cabin_poly,
            z_bot=0.28, z_top=0.38,
            mat_top=MAT_LIFEBOAT_CABIN, mat_side=MAT_WALL_CHARCOAL
        )
        hull_x = (X_CENTER - 42.3) if cx < X_CENTER else (X_CENTER + 42.3)
        for dy_off in (-0.28 * (max(ys) - min(ys)), +0.28 * (max(ys) - min(ys))):
            davit_line = [(cx, cy + dy_off), (hull_x, cy + dy_off)]
            create_polyline_wall_mesh(
                f"{MODEL_NAME}_Lifeboat_{lb_idx:02d}_Davit_{dy_off:+.1f}",
                [davit_line],
                z_bot=0.20, z_top=0.40,
                thickness=0.08,
                mat_side=MAT_DAVIT_GRAPHITE,
                mat_cap=MAT_WALL_SILVER_CAP
            )

    # 4. HERO EMBOSSED SOLID 3D GREEN MDR BLOCK ("hanya bidang polos mengikuti outline restoran")
    mdr_poly = vdata["mdr_poly"]
    create_extruded_polygon_mesh(
        f"{MODEL_NAME}_MDR_Base_Collar", mdr_poly,
        z_bot=0.16, z_top=0.23,
        mat_top=MAT_MDR_BASE_COLLAR, mat_side=MAT_MDR_BASE_COLLAR
    )
    create_extruded_polygon_mesh(
        f"{MODEL_NAME}_MDR_Embossed_Highlight_Block", mdr_poly,
        z_bot=0.20, z_top=0.94,
        mat_top=MAT_MDR_TOP_GREEN,
        mat_side=MAT_MDR_SIDE_GREEN,
        mat_bevel=MAT_MDR_RIM_GLOW,
        bevel_top_w=0.065,
        bevel_top_h=0.055,
        apply_plan_uv=False
    )

    # 5. Lighting, Transparent Background (No Backdrop Floor!) & AgX Color Management
    world = bpy.data.worlds.new(f"{MODEL_NAME}_Studio_World")
    scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    bg_node.inputs["Color"].default_value = (0.12, 0.13, 0.15, 1.0)
    bg_node.inputs["Strength"].default_value = 0.92

    # 100% Transparent Background in Render & Viewport + Sharp Subpixel Filter
    scene.render.film_transparent = True
    scene.render.filter_size = 0.85
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.compression = 15

    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.22
    scene.view_settings.gamma = 1.0

    scene.render.engine = 'BLENDER_EEVEE'
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 128
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = True

    sun_data = bpy.data.lights.new(name="Iso_Key_Sun", type='SUN')
    sun_data.energy = 3.2
    sun_data.color = (1.0, 0.99, 0.97)
    sun_data.angle = math.radians(3.5)
    sun_obj = bpy.data.objects.new("Iso_Key_Sun", sun_data)
    sun_obj.rotation_euler = Euler((math.radians(48.0), math.radians(-22.0), math.radians(35.0)), 'XYZ')
    scene.collection.objects.link(sun_obj)

    rim_data = bpy.data.lights.new(name="Iso_Rim_Sun", type='SUN')
    rim_data.energy = 1.35
    rim_data.color = (0.90, 0.95, 1.0)
    rim_data.angle = math.radians(8.0)
    rim_obj = bpy.data.objects.new("Iso_Rim_Sun", rim_data)
    rim_obj.rotation_euler = Euler((math.radians(55.0), math.radians(30.0), math.radians(-145.0)), 'XYZ')
    scene.collection.objects.link(rim_obj)

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

    # 6. Exact User-Preferred Camera Angle with Tight Ultra-HD 8K Framing
    #    - Same exact 47.23-deg tilt: Euler((0.8243613, 0.0, 0.0), 'XYZ')
    #    - Centered at X=0.0 with ortho_scale=70.5 so the 67.33m ship fills ~96% of the 7680px width!
    cam_data = bpy.data.cameras.new("Iso_Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 70.5
    cam_data.clip_start = 0.1
    cam_data.clip_end = 400.0
    cam_obj = bpy.data.objects.new("Iso_Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    view_rot = Euler((0.8243613, 0.0, 0.0), 'XYZ')
    view_loc = Vector((0.0, 0.0, 0.20))
    forward = view_rot.to_matrix() @ Vector((0.0, 0.0, -1.0))
    cam_obj.location = view_loc - forward * 44.0
    cam_obj.rotation_euler = view_rot

    # Render Transparent RGBA PNG at Ultra-HD 8K Width (7680 x 1600 px -> ~7,350 x 850 px ship pixels!)
    scene.render.resolution_x = 7680
    scene.render.resolution_y = 1600
    scene.render.resolution_percentage = 100

    png_out = os.path.join(OUT_FOLDER, png_filename)
    scene.render.filepath = png_out
    bpy.ops.render.render(write_still=True)
    print(f"Rendered 8K Ultra-HD transparent PNG: {png_out}")

    # Save .blend with 8K 16:9 (7680 x 4320) resolution so Viewport Render Image in GUI is also 8K!
    scene.render.resolution_x = 7680
    scene.render.resolution_y = 4320
    blend_out = os.path.join(OUT_FOLDER, blend_filename)
    glb_out = os.path.join(OUT_FOLDER, glb_filename)
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)

    bpy.ops.object.select_all(action='DESELECT')
    for o in root_col.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=glb_out,
        use_selection=True,
        export_format='GLB',
        export_apply=True
    )

    # If this is Arlecchino Deck 6, also update the root-level .blend and .glb
    if "Arlecchino" in png_filename:
        shutil.copy2(blend_out, os.path.join(PROJ_DIR, "deck6_arlecchino_highlight.blend"))
        shutil.copy2(glb_out, os.path.join(PROJ_DIR, "deck6_arlecchino_highlight.glb"))


if __name__ == "__main__":
    configs = [
        (
            "deck5_colombina_vector_data.json",
            "Colombina_Deck_5_Plan.png",
            "Deck5_La_Colombina_Highlight.blend",
            "Deck5_La_Colombina_Highlight.glb",
        ),
        (
            "deck6_meneghino_vector_data.json",
            "Meneghino_Deck_6_Plan.png",
            "Deck6_Il_Meneghino_Highlight.blend",
            "Deck6_Il_Meneghino_Highlight.glb",
        ),
        (
            "deck6_arlecchino_vector_data.json",
            "Arlecchino_Deck_6_Plan.png",
            "Deck6_Arlecchino_Highlight.blend",
            "Deck6_Arlecchino_Highlight.glb",
        ),
        (
            "deck7_rugantino_vector_data.json",
            "Rugantino_Deck_7_Plan.png",
            "Deck7_Il_Rugantino_Highlight.blend",
            "Deck7_Il_Rugantino_Highlight.glb",
        ),
    ]
    for json_fn, png_fn, blend_fn, glb_fn in configs:
        build_and_render_mdr_deck(json_fn, png_fn, blend_fn, glb_fn)
    print("ALL 4 MDR TRANSPARENT PNGS & BLEND MODELS COMPLETED!")
