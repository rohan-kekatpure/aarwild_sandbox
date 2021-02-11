import shutil
import time
from pathlib import Path

import numpy as np
import bpy
import aarwild_bpy.funcs as F
import aarwild_bpy.ops as O
from mathutils import Vector as V
import cv2

F.delete_default_objects()
img = cv2.imread('candle_holder.png')
O.spinbz('_test', img, steps=256)
obj = bpy.data.objects['_test']
F.add_camera(loc=V((0.65, 0, .65)), look_at=V((0, 0, .15)))
cam = bpy.data.objects['cam']
cam.rotation_euler = np.pi / 180. * V((54.4, 0, 90.8))
bpy.context.scene.camera = cam

F.make_active(obj)
modifier = obj.modifiers['screw']
modifier.render_steps = 256

bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
render = bpy.data.scenes['Scene'].render
render.image_settings.file_format = 'JPEG'
frames_dir = Path('images')/'frames'
if frames_dir.exists():
    shutil.rmtree(frames_dir)
frames_dir.mkdir(parents=True)

source_image = cv2.resize(img, None, fx=0.5, fy=0.5)
hs, ws = source_image.shape[:2]
for i, deg in enumerate(np.arange(0, 370, 10)):
    modifier.angle = np.deg2rad(deg)
    fname = render.filepath = (frames_dir/f'frame_{i:03d}.jpg').as_posix()
    bpy.ops.render.render(write_still=True)
    print(fname)
    fimg = cv2.imread(fname)
    fimg[:hs, :ws, :] = source_image
    cv2.imwrite(render.filepath, fimg)

