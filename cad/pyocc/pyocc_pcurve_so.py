import sys
from typing import Any, NewType

from OCC.Core.BOPTools import BOPTools_AlgoTools, BOPTools_AlgoTools2D_CurveOnSurface

from OCC.Core.BRep import BRep_Tool, BRep_Tool_Curve
from OCC.Core.BRepBuilderAPI import (BRepBuilderAPI_NurbsConvert,
                                     BRepBuilderAPI_MakeEdge,
                                     BRepBuilderAPI_MakeFace,
                                     BRepBuilderAPI_MakeWire)
from OCC.Core.BRepTools import breptools_OuterWire
from OCC.Core.GeomConvert import GeomConvert_CompCurveToBSplineCurve, geomconvert_CurveToBSplineCurve, \
    geomconvert_SurfaceToBSplineSurface
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopoDS import topods_Face, TopoDS_Wire, topods_Edge, topods_Wire, TopoDS_Face
from OCC.Extend.TopologyUtils import TopologyExplorer, WireExplorer
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.ShapeAnalysis import ShapeAnalysis_WireOrder
from OCC.Core.BRep import BRep_CurveOnSurface
from OCC.Core.BRepBuilderAPI import (BRepBuilderAPI_WireDone,
                                     BRepBuilderAPI_EmptyWire,
                                     BRepBuilderAPI_DisconnectedWire,
                                     BRepBuilderAPI_NonManifoldWire)

NURBSObject = NewType('NURBSObject', Any)

def _buildWiresFromEdgeset(edgelist):
    wb_errdict = {
        BRepBuilderAPI_WireDone: "No error",
        BRepBuilderAPI_EmptyWire:"Empty wire",
        BRepBuilderAPI_DisconnectedWire:"disconnected wire",
        BRepBuilderAPI_NonManifoldWire:"non-manifold wire"
    }
    sawo_statusdict = {
        0: "all edges are direct and in sequence",
        1:"all edges are direct but some are not in sequence",
        2:"unresolved gaps remain",
        -1:"some edges are reversed, but no gaps remain",
        -2:"some edges are reversed and some gaps remain",
        -10:"failure on reorder"
    }
    TE = TopExp_Explorer
    DS = TopoDS()
    isclosed = False # in general, wires will not be closed
    mode3d = True
    SAWO = ShapeAnalysis_WireOrder(mode3d, Precision().PConfusion())
    for edge in edgelist:
        V1 = TE.FirstVertex(DS.Edge(edge))
        V2 = TE.LastVertex(DS.Edge(edge))
        pnt1 = BRep_Tool().Pnt(V1)
        pnt2 = BRep_Tool().Pnt(V2)
        SAWO.Add(pnt1.XYZ(), pnt2.XYZ())
        SAWO.SetKeepLoopsMode(True)
        SAWO.Perform(isclosed)
        if not SAWO.IsDone():
            raise RuntimeError
        else:
            if SAWO.Status() not in [0, -1]:
                pass # not critical
        SAWO.SetChains(Precision().PConfusion())

    Wirelist = TT.IndexedListOfShape()
    for i in range(SAWO.NbChains()):
        wirebuilder = BRepBuilderAPI_MakeWire()
        estart, eend = SAWO.Chain(i+1)

        if (eend - estart + 1) == 0:
            continue

        for j in range(estart, eend+1):
            idx = abs(SAWO.Ordered(j))
            wirebuilder = _addToWireBuilder(wirebuilder, edgelist[idx-1])
            if wirebuilder is None:
                raise RuntimeError
        err = wirebuilder.Error()
        if err != BRepBuilderAPI_WireDone:
            raise RuntimeError
    try:
        wirebuilder.Build()
        aWire = wirebuilder.Wire()
        Wirelist.append(aWire)
    except Exception:
        raise RuntimeError
    return Wirelist

def _addToWireBuilder(wirebuilder, aShape):
    DS=TopoDS()
    st = aShape.ShapeType()
    if not st in [TopAbs_WIRE, TopAbs_EDGE]:
        raise RuntimeError

    edgelist = allEdges(aShape)
    for i, edge in enumerate(edgelist):
        try:
            wirebuilder.Add(DS.Edge(edge))
        except Exception:
            raise RuntimeError
    return wirebuilder

def _bspline_curve_from_wire(wire: NURBSObject) -> NURBSObject:
    if not isinstance(wire, TopoDS_Wire):
        raise TypeError("wire must be a TopoDS_Wire")

    composite_curve_builder = GeomConvert_CompCurveToBSplineCurve()
    edge_explorer = WireExplorer(wire)
    edges = list(edge_explorer.ordered_edges())
    for edge in edges:
        if BRep_Tool.Degenerated(edge):
            continue

        # convert to Nurbs edge
        nurbs_converter = BRepBuilderAPI_NurbsConvert(edge)
        nurbs_converter.Perform(edge)
        nurbs_edge = topods_Edge(nurbs_converter.Shape())
        nurbs_curve = BRep_Tool_Curve(nurbs_edge)[0]
        bspline_curve = geomconvert_CurveToBSplineCurve(nurbs_curve)
        tolerance = 1e-4
        composite_curve_builder.Add(bspline_curve, tolerance)

    comp_curve = composite_curve_builder.BSplineCurve()
    return comp_curve

def _bspline_surface_from_face(face):
    if not isinstance(face, TopoDS_Face):
        raise TypeError("face must be a TopoDS_Face")

    nurbs_face = topods_Face(BRepBuilderAPI_NurbsConvert(face).Shape())
    surface = BRep_Tool.Surface(nurbs_face)
    return geomconvert_SurfaceToBSplineSurface(surface)


def _new_wire_by_combining_edges(wire):
    wire = topods_Wire(wire)
    composite_curve = _bspline_curve_from_wire(wire)
    composite_edge = BRepBuilderAPI_MakeEdge(composite_curve).Edge()
    wire_builder = BRepBuilderAPI_MakeWire()
    wire_builder.Add(composite_edge)
    modified_wire = wire_builder.Wire()
    return modified_wire


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

    for i, face in enumerate(shape_faces):
        if i != 22:
            continue

        surface_spline = _bspline_surface_from_face(face)
        face_explorer = TopologyExplorer(face)
        wires = list(face_explorer.wires())
        newwire = None
        for wire in wires:
            if wire == breptools_OuterWire(face):
                newwire = _new_wire_by_combining_edges(wire)
                break

        if newwire is None:
            return  # nothing to do

        # Make new face with new wire
        face_maker = BRepBuilderAPI_MakeFace(surface_spline, newwire)
        newface = face_maker.Face()

        # Now we get the PCurve of this wire
        newface_explorer = TopologyExplorer(newface)
        newface_wires = list(newface_explorer.wires())
        assert len(newface_wires) == 1

        newface_wire_explorer = WireExplorer(newface_wires[0])
        newface_edges = list(newface_wire_explorer.ordered_edges())
        # assert len(newface_edges) == 1

        bt = BRep_Tool()
        pcurve_object = bt.CurveOnSurface(newface_edges[0], newface)
        composite_edge_curve, _, _ = BRep_Tool.Curve(newface_edges[0])


        from IPython import embed; embed(); exit(0)

if __name__ == '__main__':
    main()

