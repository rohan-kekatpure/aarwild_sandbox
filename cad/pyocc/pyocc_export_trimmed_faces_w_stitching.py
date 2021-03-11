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
from OCC.Core.GeomConvert import GeomConvert_CompCurveToBSplineCurve, geomconvert_CurveToBSplineCurve, \
    geomconvert_SurfaceToBSplineSurface
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import topods_Face, TopoDS_Wire, topods_Edge, TopoDS_Face
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Pnt2d
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnCurve
from OCC.Core.TopAbs import TopAbs_Orientation, TopAbs_IN, TopAbs_ON
from OCC.Core.BOPTools import BOPTools_AlgoTools2D_BuildPCurveForEdgeOnFace
from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.BRepClass import BRepClass_FaceClassifier

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

def _convert_to_nurbs(face: Any) -> Any:
    nurbs_face = topods_Face(BRepBuilderAPI_NurbsConvert(face).Shape())
    nurbs_surf = BRepAdaptor_Surface(nurbs_face)
    return nurbs_surf

def _compute_faces_from_verts(NU, NV) -> np.ndarray:
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
    return np.array(faces)

def _compute_edges_from_verts(NU):
    return [[i, i + 1] for i in range(NU - 1)]

def _classify_points(UVgrid, face):
    """
    Classifies if points in `uvgrid` lie on trimmed `face` or outside of it
    """
    Npts = UVgrid.shape[0]
    is_point_on_face = np.ones((Npts, ), dtype=bool)
    for i in range(Npts):
        u, v = UVgrid[i]
        pnt = gp_Pnt2d(u, v)
        fc = BRepClass_FaceClassifier()
        fc.Perform(face, pnt, 1e-3)
        state = fc.State()
        if state not in [TopAbs_IN, TopAbs_ON]:
            is_point_on_face[i] = False

    return is_point_on_face

def _classify_faces(faces: np.ndarray, is_point_on_face: np.ndarray) -> np.ndarray:
    # Partition faces into interior and exterior
    n_faces = faces.shape[0]
    is_interior_face = np.ones((n_faces,), dtype=bool)
    for i, face in enumerate(faces):
        if not any(is_point_on_face[np.array(face)]):
            is_interior_face[i] = False
    return is_interior_face

def _mesh_from_spline_surface(name: str, face: NURBSObject) -> Mesh:
    bspline_sirface = _bspline_surface_from_face(face)
    U1, U2, V1, V2 = bspline_sirface.Bounds()
    tol = 10.
    URES, VRES = bspline_sirface.Resolution(tol)
    NU = int((U2 - U1) / URES)
    NV = int((V2 - V1) / VRES)
    NU = NV = 64
    Ulist = np.linspace(U1, U2, NU)
    Vlist = np.linspace(V1, V2, NV)
    Ugrid, Vgrid = np.meshgrid(Ulist, Vlist)
    UVgrid = np.column_stack((Ugrid.ravel(), Vgrid.ravel()))
    n_pts = UVgrid.shape[0]
    all_mesh_faces = _compute_faces_from_verts(NU, NV)

    # Compute points strictly in the interior of wires
    interior_pts = _classify_points(UVgrid, face)

    # Discard faces whose _all_ points are exterior
    interior_faces = _classify_faces(all_mesh_faces, interior_pts)

    # Create points that have interior neighbors
    face_pts_idx = np.unique(all_mesh_faces[interior_faces].ravel())
    interior_pts_and_neighbors_idx = face_pts_idx
    interior_pts_and_neighbors = interior_pts.copy()
    interior_pts_and_neighbors[interior_pts_and_neighbors_idx] = True
    interior_pts = interior_pts_and_neighbors.copy()

    # Recompute vertex numbers and update faces with these new vertex indices
    included_points_idx = np.where(interior_pts)[0]
    vertex_index_map = VM = dict(zip(included_points_idx, range(n_pts)))
    interior_faces = all_mesh_faces[interior_faces]
    mesh_vert_UV = UVgrid[interior_pts]  # Mesh vertices in UV space
    mesh_faces = [(VM[i1], VM[i2], VM[i3], VM[i4]) for i1, i2, i3, i4 in interior_faces]

    # TODO: Change to filtered versions
    ### modification start
    mesh_vert_UV = UVgrid
    mesh_faces = all_mesh_faces.tolist()
    ### modification end

    n_verts = included_points_idx.shape[0]
    XYZgrid = np.zeros((n_verts, 3))
    for i in range(n_verts):
        u, v = mesh_vert_UV[i]
        point = bspline_sirface.Value(u, v)
        XYZgrid[i, :] = point.Coord()
    mesh_verts = [tuple(row) for row in XYZgrid]
    return Mesh(name=name, type_='surface', vertices=mesh_verts,
                edges=[], faces=mesh_faces, param_grid=UVgrid.tolist())


def _mesh_from_spline_curve(name: str, spline: NURBSObject) -> Mesh:
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

def _bspline_surface_from_face(face):
    if not isinstance(face, TopoDS_Face):
        raise TypeError("face must be a TopoDS_Face")
    # TopoDS_Face converted to Nurbs
    nurbs_face = topods_Face(BRepBuilderAPI_NurbsConvert(face).Shape())
    # GeomSurface obtained from Nurbs face
    surface = BRep_Tool.Surface(nurbs_face)
    # surface is now further converted to a bspline surface
    bspline_surface = geomconvert_SurfaceToBSplineSurface(surface)
    return bspline_surface

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
    meshes_list = []

    for i, face in enumerate(shape_faces):
        print(f'Processing faces {i}/{n_faces}')
        if i != 74: continue

        face_id = f'_FACE_{i:06d}'

        # Compute meshes for face
        mesh_surface = _mesh_from_spline_surface(face_id, face)
        meshes_list.append(mesh_surface.to_dict())

        # Compute meshes for face boundaries
        facex = TopologyExplorer(face)
        wires = list(facex.wires())
        for wire in wires:
            bspline_curve = _bspline_curve_from_wire(wire)
            mesh_boundary = _mesh_from_spline_curve(face_id, bspline_curve)
            meshes_list.append(mesh_boundary.to_dict())

    # Write meshes to disk
    # from IPython import embed; embed(); exit(0)
    with Path('_meshes.json').open('w') as f:
        json.dump(meshes_list, f, indent=2)

if __name__ == '__main__':
    main()

