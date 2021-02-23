import json
import pickle
from pathlib import Path

try:
    import bpy
    import aarwild_bpy.funcs as F
except:
    print('cannot import `bpy`')
    pass

def import_step_mesh():
    with Path('_meshes.json').open() as f:
        meshes = json.load(f)

    F.delete_default_objects()
    # Create new object from vertices, edges and faces
    for i, mesh in enumerate(meshes):
        mesh_type = mesh['type']
        obj_name = f'{mesh_type}_{i:04d}'
        mesh_name = f'mesh_{mesh_type}_{i:04d}'

        _ = F.create_object_from_mesh_data(
            mesh['vertices'], mesh['edges'], mesh['faces'],
            obj_name=obj_name, mesh_name=mesh_name
        )
    F.write_blendfile('_dazuiniao_tessellation.blend', relative_paths=False)
    
if __name__ == '__main__':
    import_step_mesh()
