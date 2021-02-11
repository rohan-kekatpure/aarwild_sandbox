import numpy as np
import math
import pickle
import bpy
from aarwild_utils.transforms import Mapping
import aarwild_bpy.funcs as F
from pathlib import Path

def _height(x: float) -> float:
    BETA_1 = 1.65262087
    BETA_2 = 5.18870584
    return np.log(1. + BETA_1 * x) / (1. + BETA_2 * x)

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

def make_grid() -> None:
    F.delete_default_objects()

    N = 20
    if N % 2 != 0:
        raise ValueError(f'N must be even, found {N}')

    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=N,
        y_subdivisions=N,
        size=1,
        enter_editmode=False,
        align='WORLD',
        location=(0.5, 0, .5),
        rotation=(math.radians(90), 0, 0),
        scale=(1, 1, 1)
    )

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    grid = bpy.data.objects['Grid']
    grid.name = 'mygrid'

    # open transformation file
    with open('_front_image_transform.pkl', 'rb+') as f:
        T: Mapping = pickle.load(f)

    # Allow 1 pixel buffer to prevent out-of-simplex errors
    px_min = T.bounds.x_min + 1
    py_min = T.bounds.y_min + 1
    px_max = T.bounds.x_max - 1
    py_max = T.bounds.y_max - 1

    D = np.array([[px_max - px_min, py_max - py_min]])
    P0 = np.array([[px_min, py_min]])
    points = np.array([[v.co.x, v.co.z] for v in grid.data.vertices])
    pixels = D * points + P0  # [0, 1] x [0, 1] -> [0, px_max] x [0, py_max]
    new_pixels = T.transform.inverse(pixels)  # Transform
    new_points = (new_pixels - P0) / D  # [0, px_max] x [0, py_max] -> [0, 1] x [0, 1]

    heights = np.zeros((N * N,))
    for i in range(1, N // 2):
        mask = np.zeros((N, N), dtype=bool)
        mask[i: -i, i: -i] = True
        idx = np.row_stack(np.where(mask))
        idx = np.ravel_multi_index(idx, dims=(N, N))
        heights[idx] = _height(float(i) / float(N))

    coords = np.column_stack((new_points[:, 0], heights, new_points[:, 1]))

    # Assign planar coordinates
    for i, v in enumerate(grid.data.vertices):
        v.co = coords[i]

    # Apply mirror modifier
    F.applymod_mirror(grid, '_mod_mirror', mirror_axis=(False, True, False),
                      mirror_u=True, mirror_v=True, offset_u=1.0, offset_v=0)

    # Scale uv to match standard image
    F.scale_uv(grid, factor=(0.5, 1.), pivot=(0., 0.))

    # Subdivision surface
    F.applymod_subdivision(grid, '_mod_subdiv', levels=1)

    # Apply material
    apply_material(Path('m_f03a35'))

    # Shade smooth
    F.make_active(grid)
    bpy.ops.object.shade_smooth()

    # Rotate and center
    bpy.ops.transform.rotate(value=math.radians(180.), orient_axis='X')
    F.move(grid, (0., 0., 0.))
    bpy.ops.object.transform_apply(location=True, rotation=True)

if __name__ == '__main__':
    make_grid()


