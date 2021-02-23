import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import OCC.Core.GeomAbs as G
import numpy as np
from OCC.Core.BRep import BRep_Tool, BRep_Tool_Curve
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
from OCC.Core.GeomConvert import GeomConvert_CompCurveToBSplineCurve, geomconvert_CurveToBSplineCurve
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import topods_Face, TopoDS_Wire, topods_Edge
from OCC.Extend.TopologyUtils import TopologyExplorer


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
    type_: str
    edges: List[List]
    faces: List[List]
    vertices: List[Tuple]
    is_outer_wire: bool = False

    def to_dict(self) -> Dict:
        return {
            'type': self.type_,
            'vertices': self.vertices,
            'edges': self.edges,
            'faces': self.faces,
            'is_outer_wire': self.is_outer_wire
        }

def _get_2d_spline_params(spline) -> Optional[NurbsParams]:
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

def _get_1d_spline_params(spline) -> Optional[NurbsParams]:
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

def _compute_mesh_from_spline_surface(spline) -> Mesh:
    U1, U2, V1, V2 = spline.Bounds()
    tol = 10.
    URES, VRES = spline.Resolution(tol)
    NU = int((U2 - U1) / URES)
    NV = int((V2 - V1) / VRES)
    NU = NV = 50
    Ulist = np.linspace(U1, U2, NU)
    Vlist = np.linspace(V1, V2, NV)
    Ugrid, Vgrid = np.meshgrid(Ulist, Vlist)
    Xgrid = np.zeros((NV, NU))
    Ygrid = np.zeros((NV, NU))
    Zgrid = np.zeros((NV, NU))
    for i in range(NV):
        for j in range(NU):
            point = spline.Value(Ugrid[i, j], Vgrid[i, j])
            Xgrid[i, j], Ygrid[i, j], Zgrid[i, j] = point.Coord()
    verts = np.column_stack((Xgrid.ravel(), Ygrid.ravel(), Zgrid.ravel()))
    verts = verts.tolist()
    faces = _compute_faces_from_verts(NU, NV)
    return Mesh(type_='surface', vertices=verts, edges=[], faces=faces)

def _compute_mesh_from_spline_curve(spline) -> Mesh:
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
    return Mesh(type_='curve', vertices=verts, edges=edges, faces=[])

def _bspline_curve_from_wire(wire):
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
    edge_explorer = TopologyExplorer(wire, ignore_orientation=True)
    edges = list(edge_explorer.edges())
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
    nurbs_params_list = []
    meshes_list = []

    for i, face in enumerate(shape_faces):
        print(f'Processing faces {i}/{n_faces}')
        face_id = f'_FACE_{i:06d}'
        if i != 22:
            continue
        surface = BRepAdaptor_Surface(face)
        surface_type = surface.GetType()

        primitive_types = [G.GeomAbs_Cylinder, G.GeomAbs_Torus, G.GeomAbs_Sphere]
        if surface_type in primitive_types:
            surface = _convert_to_nurbs(face)

        if surface_type != G.GeomAbs_BSplineSurface:
            print(f'Ignored shape of type {surface_type}')
            continue

        spline = surface.BSpline()

        # Compute mesh from NURBS params
        surface_mesh = _compute_mesh_from_spline_surface(spline)
        meshes_list.append(surface_mesh.to_dict())

        # Export raw parameters
        nurbs_params = _get_2d_spline_params(spline)
        nurbs_params_list.append(nurbs_params.to_dict())

        # Handle wires
        face_explorer = TopologyExplorer(face, ignore_orientation=True)
        wires = list(face_explorer.wires())
        for wire in wires:
            wire_spline = _bspline_curve_from_wire(wire)
            from IPython import embed; embed(); exit(0)
            wire_mesh = _compute_mesh_from_spline_curve(wire_spline)
            meshes_list.append(wire_mesh.to_dict())

    # Write meshes to disk
    with Path('_meshes.json').open('w') as f:
        json.dump(meshes_list, f, indent=2)

if __name__ == '__main__':
    main()

