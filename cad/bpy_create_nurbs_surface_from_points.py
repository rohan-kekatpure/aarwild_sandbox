'''
Working code in Blender 2.90 for creating parametric
NURBS from points. This file is coded purely using
blender's concepts of NURBS, it does not have any concept
of Knots etc.
'''
import json

try:
    import bpy
    from mathutils import Vector
    import aarwild_bpy.funcs as F
except:
    pass

def make_surf_example():
    surface_data = bpy.data.curves.new('wook', 'SURFACE')
    surface_data.dimensions = '3D'

    # 16 coordinates
    points = [
        Vector((-1.5, -1.5, 0.0, 1.0)), Vector((-1.5, -0.5, 0.0, 1.0)),
        Vector((-1.5, 0.5, 0.0, 1.0)), Vector((-1.5, 1.5, 0.0, 1.0)),
        Vector((-0.5, -1.5, 0.0, 1.0)), Vector((-0.5, -0.5, 1.0, 1.0)),
        Vector((-0.5, 0.5, 1.0, 1.0)), Vector((-0.5, 1.5, 0.0, 1.0)),
        Vector((0.5, -1.5, 0.0, 1.0)), Vector((0.5, -0.5, 1.0, 1.0)),
        Vector((0.5, 0.5, 1.0, 1.0)), Vector((0.5, 1.5, 0.0, 1.0)),
        Vector((1.5, -1.5, 0.0, 1.0)), Vector((1.5, -0.5, 0.0, 1.0)),
        Vector((1.5, 0.5, 0.0, 1.0)), Vector((1.5, 1.5, 0.0, 1.0))
    ]

    # set points per segments (U * V)
    for i in range(0, 16, 4):
        spline = surface_data.splines.new(type='NURBS')
        spline.points.add(3)  # already has a default vector

        for p, new_co in zip(spline.points, points[i:i+4]):
            p.co = new_co

    surface_object = bpy.data.objects.new('NURBS_OBJ', surface_data)
    coll = bpy.data.collections['Collection']
    coll.objects.link(surface_object)

    F.make_active(surface_object)
    bpy.ops.object.mode_set(mode='EDIT')

    splines = surface_object.data.splines
    for s in splines:
        for p in s.points:
            p.select = True

    bpy.ops.curve.make_segment()

def make_curve_example():
    curve_data = bpy.data.curves.new('spl', type='CURVE')
    curve_data.dimensions = '2D'
    curve_data.resolution_u = 32
    spline = curve_data.splines.new('NURBS')
    spline.points.add(3)
    spline.points[0].co = (0, 0, 0, 1)
    spline.points[1].co = (1, 0, 0, 1)
    spline.points[2].co = (2, 0, 0, 1)
    spline.points[3].co = (3, 0.5, 0, 1)
    obj = bpy.data.objects.new('nurbs', curve_data)
    coll = bpy.data.collections['Collection']
    coll.objects.link(obj)

def _make_surf(name, num_u_poles, num_v_poles, poles_coords):
    Nu = num_u_poles
    Nv = num_v_poles
    P = poles_coords

    surface_data = bpy.data.curves.new(name, 'SURFACE')
    surface_data.dimensions = '3D'
    num_points = Nu * Nv
    for i in range(0, num_points, Nv):
        spline = surface_data.splines.new(type='NURBS')
        spline.points.add(Nv - 1)  # already has a default vector

        for p, new_co in zip(spline.points, P[i: i + Nv]):
            p.co = new_co

    surface_object = bpy.data.objects.new(name, surface_data)
    coll = bpy.data.collections['Collection']
    coll.objects.link(surface_object)

    F.make_active(surface_object)
    bpy.ops.object.mode_set(mode='EDIT')

    splines = surface_object.data.splines
    for s in splines:
        for p in s.points:
            p.select = True

    bpy.ops.curve.make_segment()
    bpy.ops.object.mode_set(mode='OBJECT')

def import_cad():
    F.delete_default_objects()

    with open('pyocc/_nurbs_surfaces.json') as f:
        nurbs_surfaces = json.load(f)

    for i, ns in enumerate(nurbs_surfaces):
        name = f'nurbs_surface_{i:06d}'
        Nu = ns['num_Upoles']
        Nv = ns['num_Vpoles']
        poles_coords = ns['poles_coords']
        _make_surf(name, Nu, Nv, poles_coords)

if __name__ == '__main__':
    import_cad()
