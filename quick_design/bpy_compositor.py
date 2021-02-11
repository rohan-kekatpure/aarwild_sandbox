import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import cv2
from mathutils import Vector as V, Matrix
import bpy
import aarwild_bpy.funcs as F
from aarwild_quick_design.scene import Scene
import numpy as np

def _process_args():
    script_name = Path(__file__).name
    help_msg = 'blender -b -P {} -- [options]'.format(script_name)
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument('-l', '--layout', dest='layout', action='store',
                        help='Layout image', required=True)
    parser.add_argument('-i', '--image', dest='image', action='store',
                        help='Input image', required=True)
    argv = sys.argv
    if '--' not in argv:
        parser.print_help()
        exit(1)
    else:
        argv = argv[argv.index('--') + 1:]  # get all args after '--'

    args = parser.parse_args(argv)
    return args


def _add_planes(scene):
    size = 2.
    walls = scene.walls
    for wall_type, wall_data in walls.items():
        if wall_data is None:
            continue
        loc = V(wall_data.plane.origin)
        x90 = V((np.pi / 2., 0, 0))
        y90 = V((0, np.pi / 2., 0))
        z90 = V((0, 0, np.pi / 2.))
        r0 = V((0, 0, 0))
        if wall_type == 'LEFT':
            rot = x90
        elif wall_type == 'RIGHT':
            rot = x90 if walls['FRONT'] else y90
        elif wall_type in ['CEIL', 'FLOOR']:
            rot = r0
        elif wall_type in 'FRONT':
            rot = y90
        else:
            rot = r0

        bpy.ops.mesh.primitive_plane_add(
            size=size,
            location=loc,
            rotation=rot
        )
        obj = bpy.context.active_object
        obj.name = wall_type
        obj.data.name = wall_type

def main():
    args = _process_args()

    # Construct scene
    layout_path = Path(args.layout)
    image_path = Path(args.image)
    layout = cv2.imread(layout_path.as_posix())
    image = cv2.imread(image_path.as_posix())

    scene = Scene(image, layout)
    scene.build()

    F.delete_default_objects()
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.name = 'cam'
    cam.data.name = 'cam'

    # Set field of view
    cam.data.type = 'PERSP'
    cam.data.lens_unit = 'FOV'
    cam.data.angle = scene.horizontal_fov
    print('fov -> {}'.format(scene.horizontal_fov * 180. / np.pi))

    # Set camera transform
    cam.matrix_world = Matrix(scene.camera_matrix)

    # Set background image
    cam.data.show_background_images = True
    bg = cam.data.background_images.new()
    bg.alpha = 1.0
    bg.frame_method = 'FIT'

    tmp_dir = bpy.app.tempdir
    tmp_filename = 'qdimage_{}'.format(uuid.uuid4().hex)
    tmp_path = os.path.join(tmp_dir, tmp_filename)
    tmp_file = open(tmp_path, 'wb')
    # with open(args.input_image, 'rb') as f:
    with image_path.open('rb') as f:
        tmp_file.write(f.read())
    tmp_file.close()
    img = bpy.data.images.load(tmp_path)
    img.name = tmp_filename
    img.pack()
    bg.image = img
    os.remove(tmp_path)

    # Set render resolution
    render_settings = bpy.context.scene.render
    render_settings.resolution_x = scene.image_data.width
    render_settings.resolution_y = scene.image_data.height

    # Add planes for the detected walls
    _add_planes(scene)

    # Export scene and babylon manifest
    bjs_filepath = Path('_scene.babylon').resolve()
    bpy.ops.export.bjs(filepath=bjs_filepath.as_posix())

    json_filepath = Path('_scene.json')
    with json_filepath.open('w') as f:
        json.dump(scene.to_dict(), f, indent=2)


if __name__ == '__main__':
    main()
