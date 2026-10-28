import bpy
import math
import os
from mathutils import Vector

ROOT = "/Users/dianjulie/Documents/Map Project"
BLEND_PATH = os.path.join(ROOT, "arlecchino_block1.blend")
OUT_DIR = os.path.join(ROOT, "scratch", "renders")
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
scene = bpy.context.scene

# Add 6 subtle warm filament point lights inside the 6 Murano Chandelier globes (Z = 2.02m)
light_col = bpy.data.collections.get("04_Lighting") or scene.collection
for obj in list(bpy.data.objects):
    if obj.name.startswith("B5_Light_Pendant_"):
        bpy.data.objects.remove(obj, do_unlink=True)

pendant_light_specs = [
    ("B5_Light_Pendant_419_1", (34.10, 7.35, 2.08),  18.0, (1.0, 0.86, 0.65), 0.16),
    ("B5_Light_Pendant_419_2", (35.55, 7.35, 1.78),  18.0, (1.0, 0.82, 0.58), 0.16),
    ("B5_Light_Pendant_419_3", (37.00, 7.35, 2.08),  18.0, (1.0, 0.86, 0.65), 0.16),
    ("B5_Light_Pendant_484_1", (34.10, 10.11, 2.08), 18.0, (1.0, 0.86, 0.65), 0.16),
    ("B5_Light_Pendant_484_2", (35.55, 10.11, 1.78), 18.0, (1.0, 0.82, 0.58), 0.16),
    ("B5_Light_Pendant_484_3", (37.00, 10.11, 2.08), 18.0, (1.0, 0.86, 0.65), 0.16),
]
for l_name, l_loc, l_energy, l_col, l_rad in pendant_light_specs:
    ldata = bpy.data.lights.new(name=l_name, type='POINT')
    ldata.energy = l_energy
    ldata.color = l_col
    ldata.shadow_soft_size = l_rad
    ldata.use_shadow = False
    ldata.use_custom_distance = True
    ldata.cutoff_distance = 3.2
    if hasattr(ldata, "specular_factor"):
        ldata.specular_factor = 0.08
    lobj = bpy.data.objects.new(name=l_name, object_data=ldata)
    lobj.location = l_loc
    light_col.objects.link(lobj)

if hasattr(scene.eevee, "shadow_pool_size"):
    scene.eevee.shadow_pool_size = '1024'

scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 64
if hasattr(scene.eevee, "use_shadows"):
    scene.eevee.use_shadows = True
if hasattr(scene.eevee, "use_raytracing"):
    scene.eevee.use_raytracing = True

try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.22
except Exception:
    pass

# Save the updated .blend with AAA Block 5 lighting & exposure!
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

scene.render.resolution_x = 1600
scene.render.resolution_y = 960

cam_data = bpy.data.cameras.new("CheckCamB5_AAA")
cam_data.lens = 24.0
cam_obj = bpy.data.objects.new("CheckCamB5_AAA", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def look_at(obj, target):
    direction = Vector(target) - obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()

# Render 1: Exact perspective of the 6 Murano Pendants over Tables 419 & 484 (matching user screenshot!)
cam_data.type = 'PERSP'
cam_data.lens = 26.0
cam_obj.location = Vector((30.40, 8.73, 1.52))
look_at(cam_obj, (36.50, 8.73, 1.72))
scene.render.filepath = os.path.join(OUT_DIR, "b5_aaa_1_chandeliers_perspective.png")
bpy.ops.render.render(write_still=True)

# Render 2: Diagonal Close-Up of the 6 Ribbed Murano Glass Chandeliers & Brass Collars (matching Photo 14.31.14.jpeg!)
cam_data.lens = 28.0
cam_obj.location = Vector((32.85, 6.15, 1.68))
look_at(cam_obj, (36.20, 9.20, 2.05))
scene.render.filepath = os.path.join(OUT_DIR, "b5_aaa_2_chandeliers_diagonal_closeup.png")
bpy.ops.render.render(write_still=True)

# Render 3: Close-Up of Continuous Seamless Curved Teal & Ivory Tub Chairs (matching Photo 14.30.44 (2).jpeg!)
cam_data.lens = 28.0
cam_obj.location = Vector((33.15, 2.55, 1.42))
look_at(cam_obj, (31.85, 1.25, 0.68))
scene.render.filepath = os.path.join(OUT_DIR, "b5_aaa_3_smooth_tub_chairs_closeup.png")
bpy.ops.render.render(write_still=True)

# Render 4: Close-Up of 10-Pax Light-Oak Table (419) & Continuous Steam-Bent Oak Armchairs (matching Photo 14.30.53 (1).jpeg!)
cam_data.lens = 28.0
cam_obj.location = Vector((33.35, 8.73, 1.35))
look_at(cam_obj, (35.80, 7.15, 0.68))
scene.render.filepath = os.path.join(OUT_DIR, "b5_aaa_4_smooth_oak_chairs_and_10x_table.png")
bpy.ops.render.render(write_still=True)

# Render 5: Portside Forward Sofa Row (319..415), See-Through Vase Niche & 9 Fornasetti Plates
cam_data.lens = 21.0
cam_obj.location = Vector((32.40, 4.85, 1.48))
look_at(cam_obj, (28.15, 2.85, 1.32))
scene.render.filepath = os.path.join(OUT_DIR, "b5_aaa_5_portside_niche_and_fornasetti.png")
bpy.ops.render.render(write_still=True)

# Render 6: Starboardside Forward Sofa Row (480..398), See-Through Vase Niche & Block 6 Access Portal
cam_data.lens = 21.0
cam_obj.location = Vector((32.40, 12.61, 1.48))
look_at(cam_obj, (28.15, 14.61, 1.32))
scene.render.filepath = os.path.join(OUT_DIR, "b5_aaa_6_starboard_niche_and_block6_portal.png")
bpy.ops.render.render(write_still=True)

# Render 7: Portside Window Row (329/331), Patterned Metal Grille Partition & L-Shaped Waiter Stations
cam_data.lens = 22.0
cam_obj.location = Vector((34.30, 4.10, 1.50))
look_at(cam_obj, (38.80, 1.55, 1.22))
scene.render.filepath = os.path.join(OUT_DIR, "b5_aaa_7_aft_metal_grille_and_waiter_stations.png")
bpy.ops.render.render(write_still=True)

# Render 8: Top-down Bird's-Eye Orthographic View of Block 3, Block 4 & Block 5 (Ceilings hidden)
ceil_prefixes = (
    "Ceiling_", "CeilBeam_", "B2_CeilBeam_", "B3_CeilBeam_", "B4_CeilBeam_",
    "B3B4_Ceiling_", "RedSpot_", "B2_RedSpot_", "B3_RedSpot_", "B4_RedSpot_",
    "Corr_Downlight_", "B3B4_Corr_Downlight_", "Crossroads_Header_",
    "B5_Ceiling_", "B5_Ceil_", "B5_Cove_", "B5_Spot_"
)
for o in bpy.data.objects:
    if o.name.startswith(ceil_prefixes):
        o.hide_render = True

cam_data.type = 'ORTHO'
cam_data.ortho_scale = 33.0
cam_obj.location = Vector((28.20, 8.73, 18.0))
cam_obj.rotation_euler = (0.0, 0.0, math.pi)
scene.render.filepath = os.path.join(OUT_DIR, "b5_aaa_8_topdown_ortho_map.png")
bpy.ops.render.render(write_still=True)

print("Rendered all 8 AAA Block 5 showcase views successfully!")
