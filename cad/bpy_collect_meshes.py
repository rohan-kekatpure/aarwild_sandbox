import argparse
import sys
from pathlib import Path
import bpy
import aarwild_bpy.funcs as F

def _process_args() -> argparse.Namespace:
    script_name = Path(__file__).name
    help_msg = 'blender -b -P {} -- [options]'.format(script_name)
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument('--object-dir', dest='object_dir', action='store',
                        help='path to dir containing .obj files', required=True)
    parser.add_argument('--output-file', dest='output_file', action='store',
                        help='path to output blend file', required=True)

    argv = sys.argv
    if '--' not in argv:
        parser.print_help()
        exit(1)
    else:
        argv = argv[argv.index('--') + 1:]  # get all args after '--'

    args = parser.parse_args(argv)
    return args

def _load_meshes(obj_dir: Path) -> None:
    for obj_file in obj_dir.glob('*.obj'):
        F.load_obj(obj_file.as_posix())

def _scale_all() -> None:
    coll = bpy.data.collections['Collection']
    max_dim = max(F.collection_get_dims(coll))
    factor = 1. / max_dim if max_dim > 0. else 1.
    F.collection_scale(coll, factor)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def _remesh_all() -> None:
    for o in bpy.data.objects:
        F.make_active(o)
        bpy.ops.object.modifier_add(type='REMESH')
        mod = bpy.context.object.modifiers['Remesh']
        mod.mode = 'SHARP'
        mod.octree_depth = 6
        mod.sharpness = 100
        mod.use_remove_disconnected = False
        bpy.ops.object.modifier_apply(modifier=mod.name)

def main() -> None:
    args = _process_args()
    obj_dir = Path(args.object_dir)
    F.delete_default_objects()

    # Load all meshes of split from the input CAD file
    _load_meshes(obj_dir)

    # Scale the collection such that the largest dimension
    # of the collection is 1.0 meter
    _scale_all()

    # Remesh all objects
    # _remesh_all()

    # Save BLEND file
    F.write_blendfile(args.output_file, relative_paths=False)

if __name__ == '__main__':
    main()
