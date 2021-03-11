import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, NewType

import OCC.Core.GeomAbs as G
import numpy as np
from OCC.Core.BRep import BRep_Tool, BRep_Tool_Curve, BRep_Builder
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.BRepBuilderAPI import (BRepBuilderAPI_NurbsConvert,
                                     BRepBuilderAPI_MakeEdge,
                                     BRepBuilderAPI_MakeFace,
                                     BRepBuilderAPI_MakeWire)
from OCC.Core.BRepTools import breptools_OuterWire
from OCC.Core.GeomConvert import GeomConvert_CompCurveToBSplineCurve, geomconvert_CurveToBSplineCurve
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import topods_Face, TopoDS_Wire, topods_Edge
from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnCurve
from OCC.Core.TopAbs import TopAbs_Orientation
from OCC.Core.BOPTools import BOPTools_AlgoTools2D_BuildPCurveForEdgeOnFace
from OCC.Core.TopTools import TopTools_ListOfShape

NURBSObject = NewType('NURBSObject', Any)

@dataclass
class NurbsParams:
    num_Upoles: int
    num_Vpoles: int
    U_degree: int
    V_degree: int
    poles_coords: List[np.ndarray]

    def to_dict(self):
        return {
            'num_Upoles': self.num_Upoles,
            'num_Vpoles': self.num_Vpoles,
            'poles_coords': [list(a) for a in self.poles_coords]
        }

@dataclass
class Mesh:
    name: str
    type_: str
    edges: List[List]
    faces: List[Tuple]
    vertices: List[Tuple]
    param_grid: Optional[List[List]]
    is_outer_wire: bool = False

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'type': self.type_,
            'vertices': self.vertices,
            'edges': self.edges,
            'faces': self.faces,
            'is_outer_wire': self.is_outer_wire,
            'param_grid': self.param_grid
        }

def _get_2d_spline_params(spline: NURBSObject) -> Optional[NurbsParams]:
    NU = spline.NbUPoles()
    NV = spline.NbVPoles()
    DU = spline.UDegree()
    DV = spline.VDegree()
    KU = spline.NbUKnots()
    KV = spline.NbVKnots()

    U_pass = NU + 1 == KU + DU
    V_pass = NV + 1 == KV + DV
    if not (U_pass and V_pass):
        pass

    poles_coords = []
    for i in range(1, NU + 1):
        for j in range(1, NV + 1):
            coord = spline.Pole(i, j).Coord()
            weight = spline.Weight(i, j)
            hpoint = np.array((*coord, weight))
            poles_coords.append(hpoint)
    nurbs_params = NurbsParams(NU, NV, DU, DV, poles_coords)
    return nurbs_params

def _get_1d_spline_params(spline: NURBSObject) -> Optional[NurbsParams]:
    pass

def _convert_to_nurbs(face: Any) -> Any:
    nurbs_face = topods_Face(BRepBuilderAPI_NurbsConvert(face).Shape())
    nurbs_surf = BRepAdaptor_Surface(nurbs_face)
    return nurbs_surf

def _compute_faces_from_verts(NU, NV) -> List:
    faces = []
    for i in range(NV - 1):
        f_v1 = i * NU
        for j in range(NU - 1):
            f_v2 = f_v1 + 1
            f_v3 = f_v2 + NU
            f_v4 = f_v1 + NU
            face = (f_v1, f_v2, f_v3, f_v4)
            faces.append(face)
            f_v1 += 1
        f_v1 += NU
    return faces

def _compute_edges_from_verts(NU):
    return [[i, i + 1] for i in range(NU - 1)]

def _compute_mesh_from_spline_surface(name: str, spline: NURBSObject) -> Mesh:
    U1, U2, V1, V2 = spline.Bounds()
    tol = 10.
    URES, VRES = spline.Resolution(tol)
    NU = int((U2 - U1) / URES)
    NV = int((V2 - V1) / VRES)
    NU = NV = 50
    Ulist = np.linspace(U1, U2, NU)
    Vlist = np.linspace(V1, V2, NV)
    Ugrid, Vgrid = np.meshgrid(Ulist, Vlist)
    UVgrid = np.column_stack((Ugrid.ravel(), Vgrid.ravel()))
    Npoints = UVgrid.shape[0]
    XYZgrid = np.zeros((Npoints, 3))
    for i in range(Npoints):
        u, v = UVgrid[i, :]
        point = spline.Value(u, v)
        XYZgrid[i, :] = point.Coord()
    verts = [tuple(row) for row in XYZgrid]
    faces = _compute_faces_from_verts(NU, NV)
    return Mesh(name=name, type_='surface', vertices=verts,
                edges=[], faces=faces, param_grid=UVgrid.tolist())

def _compute_mesh_from_spline_curve(name: str, spline: NURBSObject) -> Mesh:
    U1, U2 = spline.FirstParameter(), spline.LastParameter()
    tol = 10.
    URES = spline.Resolution(tol)
    NU = int((U2 - U1) / URES)
    NU = 200
    Ugrid = np.linspace(U1, U2, NU)
    Xgrid = np.zeros((NU, ))
    Ygrid = np.zeros((NU, ))
    Zgrid = np.zeros((NU, ))
    for i in range(NU):
        point = spline.Value(Ugrid[i])
        Xgrid[i], Ygrid[i], Zgrid[i] = point.Coord()
    verts = np.column_stack((Xgrid, Ygrid, Zgrid))
    verts = verts.tolist()
    edges = _compute_edges_from_verts(NU)
    return Mesh(name=name, type_='curve', vertices=verts,
                edges=edges, faces=[], param_grid=Ugrid.tolist())

def _bspline_curve_from_wire(wire: NURBSObject) -> NURBSObject:
    """
    Private method that takes a TopoDS_Wire and transforms it into a
    Bspline_Curve.
    """
    if not isinstance(wire, TopoDS_Wire):
        raise TypeError("wire must be a TopoDS_Wire")

    # joining all the wire edges in a single curve here
    # composite curve builder (can only join Bspline curves)
    composite_curve_builder = GeomConvert_CompCurveToBSplineCurve()

    # iterator to edges in the TopoDS_Wire
    # edge_explorer = TopologyExplorer(wire, ignore_orientation=False)
    edge_explorer = WireExplorer(wire)
    edges = list(edge_explorer.ordered_edges())
    for edge in edges:
        # edge can be joined only if it is not degenerated (zero length)
        if BRep_Tool.Degenerated(edge):
            continue

        # the edge must be converted to Nurbs edge
        nurbs_converter = BRepBuilderAPI_NurbsConvert(edge)
        nurbs_converter.Perform(edge)
        nurbs_edge = topods_Edge(nurbs_converter.Shape())

        # here we extract the underlying curve from the Nurbs edge
        nurbs_curve = BRep_Tool_Curve(nurbs_edge)[0]

        # we convert the Nurbs curve to Bspline curve
        bspline_curve = geomconvert_CurveToBSplineCurve(nurbs_curve)

        # we can now add the Bspline curve to the composite wire curve
        tolerance = 0.1
        composite_curve_builder.Add(bspline_curve, tolerance)

    # GeomCurve obtained by the builder after edges are joined
    comp_curve = composite_curve_builder.BSplineCurve()
    return comp_curve

def _partition_verts_by_wire(surface_spline: NURBSObject, surface_mesh: Mesh,
                             curve_spline: NURBSObject, kind: str) -> np.ndarray:
    M = surface_mesh
    verts = M.vertices
    uvs = M.param_grid
    is_interior_vert = np.zeros((len(verts), ), dtype=bool)
    n_verts = len(verts)

    for i in range(n_verts):
        # In the code below, several points and vectors are evaluated
        # for the surface and the curve. The quantities for the surfaces
        # and curves have suffixes `_s` or `s` and `_c` or `c`

        # Compute normal vector to the surface
        pt_s = gp_Pnt(*verts[i])
        us, vs = uvs[i]
        normalu_s = gp_Vec()
        normalv_s = gp_Vec()
        surface_spline.D1(us, vs, gp_Pnt(), normalu_s, normalv_s)
        normal_s = np.cross(normalu_s.Coord(), normalv_s.Coord())

        # Compute the projection pt_c of surface point pt_s on the
        # wire. Then compute the cross product of the vector connecting
        # pt_s to pt_c to the tangent vector at pt_c.
        projector = GeomAPI_ProjectPointOnCurve(pt_s, curve_spline)
        pt_c = projector.NearestPoint()
        uc = projector.LowerDistanceParameter()
        v_c2s = np.array(pt_s.Coord()) - np.array(pt_c.Coord())
        tangent_c = gp_Vec()
        curve_spline.D1(uc, gp_Pnt(), tangent_c)
        cx = np.cross(tangent_c.Coord(), v_c2s)

        # Now compute the angle between surface normal and cx
        cos = np.dot(normal_s, cx)
        if (kind == 'outer') and (cos > 0):
            is_interior_vert[i] = True
        elif (kind == 'inner') and (cos < 0):
            is_interior_vert[i] = True

    return is_interior_vert

def _trim(surface_spline: NURBSObject, surface_mesh: Mesh,
          inner_wire_splines: List, outer_wire_splines: List) -> np.ndarray:
    M = surface_mesh
    n_verts = len(M.vertices)
    is_interior_vert = np.ones((n_verts, ), dtype=np.bool)

    # Trim using outer wires; outer then inner
    for spline in outer_wire_splines:
        interior_verts_for_wire = _partition_verts_by_wire(surface_spline, M, spline, kind='outer')
        is_interior_vert = np.logical_and(is_interior_vert, interior_verts_for_wire)

    # Trim using inner wires
    for spline in inner_wire_splines:
        interior_verts_for_wire = _partition_verts_by_wire(surface_spline, M, spline, kind='inner')
        is_interior_vert = np.logical_and(is_interior_vert, interior_verts_for_wire)

    return is_interior_vert

def _recompute_mesh(name: str, old_mesh: Mesh, is_interior_vert: np.ndarray) -> Mesh:
    M = old_mesh
    n_verts = len(old_mesh.vertices)
    n_faces = len(M.faces)

    # Partition faces into interior and exterior
    is_interior_face = np.zeros((n_faces,), dtype=bool)
    for i, face in enumerate(M.faces):
        if all(is_interior_vert[np.array(face)]):
            is_interior_face[i] = True

    # Remap the indices of interior faces to new filtered vertex indices
    interior_verts_idx = np.where(is_interior_vert)[0]
    vertex_index_map = VM = dict(zip(interior_verts_idx, range(n_verts)))
    interior_faces = np.array(M.faces)[is_interior_face]
    new_verts = np.array(M.vertices)[is_interior_vert]
    new_faces = [(VM[i1], VM[i2], VM[i3], VM[i4]) for i1, i2, i3, i4 in interior_faces]
    new_mesh = Mesh(name=name, type_='surface', vertices=new_verts.tolist(),
                    edges=[], faces=new_faces, param_grid=None)
    return new_mesh


def main():
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(sys.argv[1])

    if status != IFSelect_RetDone:
        raise ValueError('Error parsing STEP file')

    failsonly = False
    step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
    step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
    step_reader.TransferRoot()
    shape = step_reader.Shape()
    topo_explorer = TopologyExplorer(shape)
    shape_faces = list(topo_explorer.faces())
    n_faces = len(shape_faces)
    nurbs_params_list = []
    meshes_list = []

    for i, face in enumerate(shape_faces):
        print(f'Processing faces {i}/{n_faces}')
        face_id = f'_FACE_{i:06d}'
        if i != 74: continue
        surface = BRepAdaptor_Surface(face)
        surface_type = surface.GetType()

        primitive_types = [G.GeomAbs_Cylinder, G.GeomAbs_Torus, G.GeomAbs_Sphere]
        if surface_type in primitive_types:
            surface = _convert_to_nurbs(face)

        if surface_type != G.GeomAbs_BSplineSurface:
            print(f'Ignored shape of type {surface_type}')
            continue

        surface_spline = surface.BSpline()

        # Compute mesh from NURBS params
        surface_mesh = _compute_mesh_from_spline_surface(face_id, surface_spline)

        # Export raw parameters
        nurbs_params = _get_2d_spline_params(surface_spline)
        nurbs_params_list.append(nurbs_params.to_dict())

        # Handle wires
        face_explorer = TopologyExplorer(face, ignore_orientation=True)
        wires = list(face_explorer.wires())
        inner_wire_splines = []
        outer_wire_splines = []

        for wire in wires:
            wire_spline = _bspline_curve_from_wire(wire)
            if wire == breptools_OuterWire(face):
                outer_wire_splines.append(wire_spline)
            else:
                inner_wire_splines.append(wire_spline.Reversed())
            wire_mesh = _compute_mesh_from_spline_curve(face_id, wire_spline)
            meshes_list.append(wire_mesh.to_dict())

        is_interior_vert = _trim(surface_spline, surface_mesh, inner_wire_splines, outer_wire_splines)
        # new_surface_mesh = _recompute_mesh(face_id, surface_mesh, is_interior_vert)
        new_surface_mesh = surface_mesh
        meshes_list.append(new_surface_mesh.to_dict())

    # Write meshes to disk
    with Path('_meshes.json').open('w') as f:
        json.dump(meshes_list, f, indent=2)

if __name__ == '__main__':
    main()

