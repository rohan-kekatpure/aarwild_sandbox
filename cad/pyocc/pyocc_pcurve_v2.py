import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, NewType
import numpy as np

import OCC.Core.GeomAbs as G
from OCC.Core.BRep import BRep_Tool, BRep_Tool_Curve, BRep_Builder
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve, BRepAdaptor_CompCurve
from OCC.Core.BRepBuilderAPI import (BRepBuilderAPI_NurbsConvert,
                                     BRepBuilderAPI_MakeEdge,
                                     BRepBuilderAPI_MakeFace,
                                     BRepBuilderAPI_MakeWire)
from OCC.Core.BRepTools import breptools_OuterWire
from OCC.Core.GeomConvert import GeomConvert_CompCurveToBSplineCurve, geomconvert_CurveToBSplineCurve, \
    geomconvert_SurfaceToBSplineSurface
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import topods_Face, TopoDS_Wire, topods_Edge, topods_Wire, TopoDS_Face, TopoDS_Edge
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_OX2d
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnCurve
from OCC.Core.Geom import Geom_Curve
from OCC.Core.GeomAdaptor import GeomAdaptor_Curve
from OCC.Core.TopAbs import TopAbs_Orientation
from OCC.Core.BOPTools import BOPTools_AlgoTools2D_BuildPCurveForEdgeOnFace
from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.TopExp import topexp
from OCC.Core.Geom2d import Geom2d_Curve, Geom2d_Circle
from OCC.Core.ShapeConstruct import ShapeConstruct_ProjectCurveOnSurface
from OCC.Core.GeomProjLib import geomprojlib
from OCC.Core.Adaptor2d import Adaptor2d_Curve2d,  Adaptor2d_HCurve2d
from OCC.Core.Geom2dAdaptor import geom2dadaptor_MakeCurve, Geom2dAdaptor_Curve

NURBSObject = NewType('NURBSObject', Any)

def _convert_to_nurbs(face: Any) -> Any:
    nurbs_face = topods_Face(BRepBuilderAPI_NurbsConvert(face).Shape())
    nurbs_surf = BRepAdaptor_Surface(nurbs_face)
    return nurbs_surf

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
        tolerance = 1e-9
        composite_curve_builder.Add(bspline_curve, tolerance)

    # GeomCurve obtained by the builder after edges are joined
    comp_curve = composite_curve_builder.BSplineCurve()
    return comp_curve

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

def _get_composite_edge_from_wire(wire: Any) -> Any:
    wire = topods_Wire(wire)
    composite_curve = _bspline_curve_from_wire(wire)
    composite_edge = BRepBuilderAPI_MakeEdge(composite_curve).Edge()
    return composite_edge

def _generate_points(edge_curve, t1, t2) -> List:
    npts = 50
    tlist = np.linspace(t1, t2, npts)
    points = [edge_curve.Value(t).Coord() for t in tlist]
    return points

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

    surfaces = {}
    for i, face in enumerate(shape_faces):
        print(f'Processing faces {i}/{n_faces}')
        face_id = f'_FACE_{i:06d}'

        # Initialize structure to hold surface information
        surface_info = {'surface_bounds': [], 'edges': []}

        brep_surface = BRepAdaptor_Surface(face)
        surface = BRep_Tool.Surface(face)
        surface_type = brep_surface.GetType()

        primitive_types = [G.GeomAbs_Cylinder, G.GeomAbs_Torus, G.GeomAbs_Sphere]
        if surface_type in primitive_types:
            surface = _convert_to_nurbs(face)

        # surface_spline = surface.BSpline()
        surface_spline = _bspline_surface_from_face(face)
        surface_info['surface_bounds'] = list(surface_spline.Bounds())

        face_explorer = TopologyExplorer(face)
        wires = list(face_explorer.wires())
        for j, wire in enumerate(wires):
            wire_type = 'outer' if wire == breptools_OuterWire(face) else 'inner'
            print(f'\t wire type: {wire_type} ({j + 1}/{len(wires)})')
            wire_explorer = WireExplorer(wire)
            edges = list(wire_explorer.ordered_edges())
            for edge in edges:
                edge_curve, t1, t2 = BRep_Tool().CurveOnSurface(edge, face)
                edge_points = _generate_points(edge_curve, t1, t2)
                edge_info = {'type': wire_type, 'points': edge_points}
                surface_info['edges'].append(edge_info)

        surfaces.update({face_id: surface_info})

        # continue
        # Handle wires
        composite_edge = _get_composite_edge_from_wire(wires[0])
        composite_edge_curve, _, _ = BRep_Tool.Curve(composite_edge)
        pcurve_maker = ShapeConstruct_ProjectCurveOnSurface()
        pcurve_maker.Init(surface_spline, 1.0e-4)
        first, last = -1., -1.
        circle = Geom2d_Circle(gp_OX2d(), 1, True)
        h = Geom2dAdaptor_Curve(circle)
        from IPython import embed; embed(); exit(0)
        pcurve_maker.Perform(composite_edge_curve, first, last, h.Curve())
        pcurve_maker.PerformByProjLib(composite_edge_curve, first, last, h.Curve())
        print('here')
        # projected_curve = geomprojlib.Project(composite_edge_curve, surface)

    with Path('_surfaces.json').open('w') as f:
        json.dump(surfaces, f, indent=2)


if __name__ == '__main__':
    main()

