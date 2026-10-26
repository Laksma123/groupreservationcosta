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

cam_data = bpy.data.cameras.new("CheckCamB34")
cam_data.lens = 20.0
cam_obj = bpy.data.objects.new("CheckCamB34", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def look_at(obj, target):
    direction = Vector(target) - obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()

# View 1: From Forward of Clover Table looking Aft (+X) into Block 3 (Left/Portside) & Block 4 (Right/Starboardside)
cam_obj.location = Vector((10.65, 8.73, 1.50))
look_at(cam_obj, (21.50, 8.73, 1.35))
scene.render.filepath = os.path.join(OUT_DIR, "b34_view1_from_crossroads.png")
bpy.ops.render.render(write_still=True)

# View 2: Top-down Bird's-Eye of Block 3 & Block 4 (hide ceilings for clear floor plan inspection)
ceil_prefixes = ("Ceiling_", "CeilBeam_", "B2_CeilBeam_", "B3_CeilBeam_", "B4_CeilBeam_", "B3B4_Ceiling_", "RedSpot_", "B2_RedSpot_", "B3_RedSpot_", "B4_RedSpot_", "Corr_Downlight_", "B3B4_Corr_Downlight_", "Crossroads_Header_")
for o in bpy.data.objects:
    if o.name.startswith(ceil_prefixes):
        o.hide_render = True

cam_data.type = 'ORTHO'
cam_data.ortho_scale = 25.0
cam_obj.location = Vector((20.20, 8.73, 18.0))
look_at(cam_obj, (20.20, 8.73, 0.0))
scene.render.filepath = os.path.join(OUT_DIR, "b34_view2_topdown.png")
bpy.ops.render.render(write_still=True)
print("Rendered b34_view1_from_crossroads.png and b34_view2_topdown.png")
