import pickle

try:
    import bpy
    import aarwild_bpy.funcs as F
except:
    print('cannot import `bpy`')
    pass

import numpy as np

def make_quad_mesh_ex1():
    verts = [(1.0, 1.0, -1.0),
             (1.0, -1.0, -1.0),
             (-1.0, -1.0, -1.0),
             (-1.0, 1.0, -1.0),
             (1.0, 1.0, 1.0),
             (1.0, -1.0, 1.0),
             (-1.0, -1.0, 1.0),
             (-1.0, 1.0, 1.0)]

    faces = [(0, 1, 2, 3),
             (4, 7, 6, 5),
             (0, 4, 5, 1),
             (1, 5, 6, 2),
             (2, 6, 7, 3),
             (4, 0, 3, 7)]

    mesh_data = bpy.data.meshes.new("cube_mesh_data")
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()  # (calc_edges=True) not needed here

    cube_object = bpy.data.objects.new("Cube_Object", mesh_data)

    scene = bpy.context.scene
    scene.objects.link(cube_object)
    cube_object.select = True

def make_tri_mesh():

    verts = [
        (-0.285437, -0.744976, -0.471429),
        (-0.285437, -0.744976, -2.471429),
        (1.714563, -0.744976, -2.471429),
        (1.714563, -0.744976, -0.471429),
        (-0.285437, 1.255024, -0.471429),
        (-0.285437, 1.255024, -2.471429),
        (1.714563, 1.255024, -2.471429),
        (1.714563, 1.255024, -0.471429)]

    faces = [
        (4, 5, 1),
        (5, 6, 2),
        (6, 7, 3),
        (4, 0, 7),
        (0, 1, 2),
        (7, 6, 5),
        (0, 4, 1),
        (1, 5, 2),
        (2, 6, 3),
        (7, 0, 3),
        (3, 0, 2),
        (4, 7, 5)]

    mesh_data = bpy.data.meshes.new("cube_mesh_data")
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()  # (calc_edges=True) not needed here

    cube_object = bpy.data.objects.new("Cube_Object", mesh_data)

    scene = bpy.context.scene
    scene.objects.link(cube_object)
    cube_object.select = True

def _make_quad_faces_from_verts(nx, ny):
    faces = []
    for i in range(ny - 1):
        f_v1 = i * nx
        for j in range(nx - 1):
            f_v2 = f_v1 + 1
            f_v3 = f_v2 + nx
            f_v4 = f_v1 + nx
            face = (f_v1, f_v2, f_v3, f_v4)
            faces.append(face)
            f_v1 += 1
            print(face)
        f_v1 += nx
    return faces

def make_quad_mesh_ex2():
    x = np.linspace(0, 10, 100)
    y = np.linspace(0, 10, 80)
    xg, yg = np.meshgrid(x, y)
    zg = np.sin((xg - 5.) * (yg - 5.))/((xg - 5.) * (yg - 5.))
    verts_2d = np.column_stack((xg.ravel(), yg.ravel(), zg.ravel()))
    verts = [tuple(v) for v in verts_2d.tolist()]
    edges = []
    nx = x.shape[0]
    ny = y.shape[0]
    faces = _make_quad_faces_from_verts(nx, ny)

    # Create new object from vertices, edges and faces
    F.delete_default_objects()
    _ = F.create_object_from_mesh_data(
        verts, edges, faces,
        obj_name='surf', mesh_name='surf_mesh'
    )

def import_step_mesh():
    with open('_meshes.pkl', 'rb') as f:
        meshes = pickle.load(f)

    # Create new object from vertices, edges and faces
    F.delete_default_objects()
    for verts, faces in meshes:
        _ = F.create_object_from_mesh_data(verts, [], faces,
                                           obj_name='surf',
                                           mesh_name='surf_mesh')
    F.write_blendfile('_dazuiniao_tessellation.blend', relative_paths=False)

if __name__ == '__main__':
    import_step_mesh()
