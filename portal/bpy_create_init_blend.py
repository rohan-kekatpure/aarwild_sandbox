import sys
import argparse
from pathlib import Path

import bpy
import aarwild_bpy.funcs as F

def _process_args() -> argparse.Namespace:
    script_name = Path(__file__).name
    help_msg = 'blender -b -P {} -- [options]'.format(script_name)
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument('--images-dir', dest='images_dir', action='store',
                        help='images dir', required=True)
    parser.add_argument('--width', dest='width', type=float, action='store',
                        help='model width', required=True)
    parser.add_argument('--height', dest='height', type=float, action='store',
                        help='model height', required=True)
    parser.add_argument('--depth', dest='depth', type=float, action='store',
                        help='model depth', required=True)

    argv = sys.argv
    if '--' not in argv:
        parser.print_help()
        exit(1)
    else:
        argv = argv[argv.index('--') + 1:]  # get all args after '--'

    args = parser.parse_args(argv)
    return args

def _create_bbox(width_inches: float, height_inches: float, depth_inches: float) -> None:
    width = width_inches * F.METERS_IN_INCHES
    height = height_inches * F.METERS_IN_INCHES
    depth = depth_inches * F.METERS_IN_INCHES
    bpy.ops.mesh.primitive_cube_add(
        calc_uvs=False,
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, height / 2.),
        scale=(width, depth, height)
    )
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj = bpy.data.objects['Cube']
    obj.name = '_bounds'
    obj.display_type = 'BOUNDS'
    obj.hide_select = True

def _load_images(images_dir: Path) -> None:
    for imagefile in images_dir.glob('*.jpg'):
        bpy.data.images.load(imagefile.as_posix())

    for img in bpy.data.images:
        img.use_fake_user = True
    bpy.ops.file.pack_all()

def _toggle_image_viewer() -> None:
    for a in bpy.context.screen.areas:
        if a.type == 'DOPESHEET_EDITOR':
            a.ui_type = 'VIEW'

def main() -> None:
    args = _process_args()
    F.delete_default_objects()
    F.change_units_to_inches()
    _create_bbox(args.width, args.height, args.depth)
    _load_images(Path(args.images_dir))
    _toggle_image_viewer()
    bpy.ops.wm.save_mainfile(filepath='_init.blend')

if __name__ == '__main__':
    main()
