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
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

cam_data = bpy.data.cameras.new("CheckCamB5")
cam_data.lens = 20.0
cam_obj = bpy.data.objects.new("CheckCamB5", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def look_at(obj, target):
    direction = Vector(target) - obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()

# View 1: From Central Corridor between Block 3 & 4 looking Aft (+X) into Block 5
cam_data.type = 'PERSP'
cam_data.lens = 20.0
cam_obj.location = Vector((25.20, 8.73, 1.55))
look_at(cam_obj, (35.50, 8.73, 1.35))
scene.render.filepath = os.path.join(OUT_DIR, "b5_view1_corridor_to_green_zone.png")
bpy.ops.render.render(write_still=True)

# View 2: Portside Forward Sofa (319, 317, 385, 387, 415), See-Through Vase Niche & 9 Fornasetti Plates
cam_obj.location = Vector((32.50, 4.80, 1.50))
look_at(cam_obj, (28.15, 2.80, 1.35))
scene.render.filepath = os.path.join(OUT_DIR, "b5_view2_portside_sofa_and_niche.png")
bpy.ops.render.render(write_still=True)

# View 3: Starboardside Forward Sofa (480, 450, 448, 400, 398), See-Through Vase Niche & 9 Fornasetti Plates
cam_obj.location = Vector((32.50, 12.66, 1.50))
look_at(cam_obj, (28.15, 14.66, 1.35))
scene.render.filepath = os.path.join(OUT_DIR, "b5_view3_starboard_sofa_and_niche.png")
bpy.ops.render.render(write_still=True)

# View 4: Central Green Carpet, 10x Oak Tables (419 & 484), 6 Murano Pendants & Patterned Glass Wall
cam_obj.location = Vector((30.20, 8.73, 1.60))
look_at(cam_obj, (37.80, 8.73, 1.35))
scene.render.filepath = os.path.join(OUT_DIR, "b5_view4_center_oak_tables_and_glass_wall.png")
bpy.ops.render.render(write_still=True)

# View 5: Portside Window Row (329/331), Patterned Metal Grille Partition & 3 L-Shaped Waiter Stations
cam_obj.location = Vector((34.20, 4.20, 1.55))
look_at(cam_obj, (38.80, 1.60, 1.25))
scene.render.filepath = os.path.join(OUT_DIR, "b5_view5_aft_metal_grille_and_waiter_stations.png")
bpy.ops.render.render(write_still=True)

# View 6: Top-down Bird's-Eye Orthographic View of Block 3, Block 4 & Block 5 (Ceilings hidden)
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
# Rotate 180 deg around Z so Portside (Y=0) is at TOP, Starboardside (Y=17.46) is at BOTTOM,
# Block 3/4 is on RIGHT, and Block 5 (Aft +X) is on LEFT — matching Block_5_3_4_2D_Map_Reference.png!
cam_obj.rotation_euler = (0.0, 0.0, math.pi)
scene.render.filepath = os.path.join(OUT_DIR, "b5_view6_topdown_ortho.png")
bpy.ops.render.render(write_still=True)

print("Rendered all 6 Block 5 verification views successfully!")
