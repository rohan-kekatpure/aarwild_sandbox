import argparse
import json
import pickle
import sys
from pathlib import Path

try:
    import bpy
    import aarwild_bpy.funcs as F
except:
    print('cannot import `bpy`')
    pass

def _process_args() -> argparse.Namespace:
    script_name = Path(__file__).name
    help_msg = 'blender -b -P {} -- [options]'.format(script_name)
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument('--meshes-file', dest='meshes_file', action='store',
                        help='path to mesh file', required=True)
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

def import_step_mesh():
    args = _process_args()
    with Path(args.meshes_file).open() as f:
        meshes = json.load(f)

    F.delete_default_objects()
    # Create new object from vertices, edges and faces
    for i, mesh in enumerate(meshes):
        mesh_type = mesh['type']
        mesh_name = mesh['name']
        obj_name = mesh_name = f'{mesh_name}_{mesh_type}'
        _ = F.create_object_from_mesh_data(
            mesh['vertices'], mesh['edges'], mesh['faces'],
            obj_name=obj_name, mesh_name=mesh_name
        )
    F.write_blendfile(args.output_file, relative_paths=False)
    
if __name__ == '__main__':
    import_step_mesh()
