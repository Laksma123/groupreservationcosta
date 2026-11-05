import bpy
import math
from mathutils import Vector, Euler

scene = bpy.context.scene
scene.render.film_transparent = True
scene.render.filter_size = 0.85
scene.render.resolution_x = 7680
scene.render.resolution_y = 4320
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

view_rot = Euler((0.8243613, 0.0, 0.0), 'XYZ')
view_loc = Vector((0.0, 0.0, 0.20))

def _align_viewport():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'RENDERED'
                        space.shading.use_scene_lights = True
                        space.shading.use_scene_world = True
                        space.clip_start = 0.2
                        space.clip_end = 400.0
                        r3d = space.region_3d
                        if r3d:
                            r3d.view_perspective = 'ORTHO'
                            r3d.view_location = view_loc
                            r3d.view_rotation = view_rot.to_quaternion()
                            r3d.view_distance = 65.0
    return None

bpy.app.timers.register(_align_viewport, first_interval=0.5)
