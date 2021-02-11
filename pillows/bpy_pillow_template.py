import argparse
import sys
from pathlib import Path
import bpy
import aarwild_bpy.funcs as F
from mathutils import Vector

def _process_args() -> argparse.Namespace:
    script_name = Path(__file__).name
    help_msg = 'blender -b -P {} -- [options]'.format(script_name)
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument('--texture-image', dest='texture_image', action='store',
                        help='texture image', required=True)
    parser.add_argument('--width', dest='width', action='store',
                        help='model width', required=True)
    parser.add_argument('--height', dest='height', action='store',
                        help='model height', required=True)
    parser.add_argument('--depth', dest='depth', action='store',
                        help='model depth', required=True)
    parser.add_argument('--output-file', dest='output_file_path', action='store',
                        help='output file path', required=True)
    parser.add_argument('--material-dir', dest='material_dir', action='store',
                        help='material dir')
    parser.add_argument('--use-material', dest='use_material', action='store_true',
                        help='If true, use supplied material instead of default')

    argv = sys.argv
    if '--' not in argv:
        parser.print_help()
        exit(1)
    else:
        argv = argv[argv.index('--') + 1:]  # get all args after '--'

    args = parser.parse_args(argv)
    return args

def apply_texture(texture_image_path: str) -> None:
    texture_image = bpy.data.images.load(texture_image_path)
    texture_image.name = '_pillow_texture'

    mat = bpy.data.materials['pillow_material']
    tex_node = mat.node_tree.nodes['Image Texture']
    tex_node.image = bpy.data.images['_pillow_texture']
    bpy.ops.file.pack_all()

def apply_material(material_dir: Path) -> None:
    # Append material from material blend file
    material_code = material_dir.name
    material_path = material_dir/'material.blend'/'Material'
    bpy.ops.wm.append(filename=material_code, directory=material_path.as_posix())

    # Apply material to texture
    mat = bpy.data.materials.get(material_code)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            F.apply_material(obj, mat)
    bpy.ops.file.pack_all()

def resize_to_dims(width: float, height: float) -> None:
    """
    Resizes the pillow template according to provided width
    and height. Since we're using tempaltes, independent
    scaling in two or three dimensions is oging to distort the
    texture. Therefore we can apply only one global scale.
    That scale is computed from the width value. It can
    equivalently be computed from the height. But we cannot use
    depth since the pillow depth numbers are least reliable.

    :height: Not used presently
    """
    obj = bpy.data.objects[0]
    template_dims_inches = obj.dimensions / F.METERS_IN_INCHES
    scale_factor = width / template_dims_inches.x

    # Cap the scaling at 2.0
    scale_factor = min(scale_factor, 2.0)
    F.scale(obj, scale_factor, apply_to_mesh=True)

def main() -> None:
    args = _process_args()
    texture_img_path = args.texture_image
    output_file_path = args.output_file_path
    material_dir = Path(args.material_dir)

    if args.use_material:
        apply_material(material_dir)
    else:
        apply_texture(texture_img_path)

    resize_to_dims(float(args.width), float(args.height))
    F.write_blendfile(output_file_path, relative_paths=True)

if __name__ == '__main__':
    main()
