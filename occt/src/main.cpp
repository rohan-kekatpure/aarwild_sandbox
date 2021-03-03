#include<cstdio>
#include<string>
#include<stdexcept>
#include<STEPControl_Reader.hxx>
#include<TopExp_Explorer.hxx>
#include<TopoDS.hxx>
#include<TopoDS_Face.hxx>
#include<BRepBuilderAPI_NurbsConvert.hxx>
#include<BRepBuilderAPI_MakeFace.hxx>
#include<BRepBuilderAPI_MakeEdge.hxx>
#include<BRep_Builder.hxx>
#include<BRep_Tool.hxx>
#include<BRepTools.hxx>
#include<Geom_Surface.hxx>
#include<Geom_BSplineSurface.hxx>
#include<Geom_Curve.hxx>
#include<Standard_Handle.hxx>
#include<GeomConvert.hxx>
#include<TopoDS_Wire.hxx>
#include<gp_XY.hxx>
#include<ShapeConstruct_ProjectCurveOnSurface.hxx>
#include<GeomConvert_CompCurveToBSplineCurve.hxx>
#include<BRepTools_WireExplorer.hxx>
#include<BRepBuilderAPI_MakeWire.hxx>
#include<boost/program_options.hpp>

using namespace std;

/*
 def _get_composite_edge_from_wire(wire: Any) -> Any:
    wire = topods_Wire(wire)
    composite_curve = _bspline_curve_from_wire(wire)
    composite_edge = BRepBuilderAPI_MakeEdge(composite_curve).Edge()
    return composite_edge
*/

/*
 * Returns the geometric surface of a face in BSpline format. The surface is first extracted
 * as raw, then converted to NURBS and finally to BSpline.
 */
Handle(Geom_BSplineSurface) getBSplineSurfaceFromFace(const TopoDS_Face& face){
    BRepBuilderAPI_NurbsConvert converter = BRepBuilderAPI_NurbsConvert();
    converter.Perform(face);
    TopoDS_Face nurbsFace = TopoDS::Face(converter.Shape());
    Handle(Geom_Surface) surface = BRep_Tool::Surface(nurbsFace); // surface->...
    Handle(Geom_BSplineSurface) bsplineSurface = GeomConvert::SurfaceToBSplineSurface(surface);
    return bsplineSurface;
}

/*
 * Combines all curves from all edges of a wire into a single BSpline curve. The constituent curves
 * may be of various types. They are all first converted to NURBS curve type before being converted
 * again into BSpline type curves.
 *
 * Combining all edges into a single curve allows us to compute the orientation (or "sense") of the
 * curve, from which we eventually obtain a notion of an interior and exterior of the bounding curve.
 */
Handle(Geom_BSplineCurve) computeCompositeCurveFromWire(const TopoDS_Wire& wire) {
    GeomConvert_CompCurveToBSplineCurve compositeCurveMaker = GeomConvert_CompCurveToBSplineCurve();
    BRepTools_WireExplorer wireExplorer = BRepTools_WireExplorer(wire);

    while (wireExplorer.More()){
        TopoDS_Edge edge = TopoDS_Edge(wireExplorer.Current());
        if (BRep_Tool::Degenerated(edge)){
            continue;
        }
        BRepBuilderAPI_NurbsConvert converter = BRepBuilderAPI_NurbsConvert();
        converter.Perform(edge);
        TopoDS_Edge nurbsEdge = TopoDS::Edge(converter.Shape());
        double t1, t2, tolerance = 1.0e-4;
        Handle(Geom_Curve) nurbsCurve = BRep_Tool::Curve(nurbsEdge, t1, t2);  // Edge to curve
        Handle(Geom_BSplineCurve) bSplineCurve = GeomConvert::CurveToBSplineCurve(nurbsCurve);
        compositeCurveMaker.Add(bSplineCurve, tolerance);
        wireExplorer.Next();
    }
    Handle(Geom_BSplineCurve) compositeBSplineCurve = compositeCurveMaker.BSplineCurve();
    return compositeBSplineCurve;
}

/*
 * Parse commandline options
 */
bool processArgs(int argc, const char *argv[], string& stepFilePath){
    namespace po = boost::program_options;

    try {
        po::options_description desc("Program Usage");
        desc.add_options()
                ("help,h", "help message")
                ("stepfile-path", po::value<string>(&stepFilePath)->required(),"Step file path");

        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);

        if (vm.count("help")) {
            std::cout << desc << endl;
            return false;
        }

        po::notify(vm);
    } catch(const po::error &e) {
        printf("Error: %s\n", e.what());
        return false;
    }
    return true;
}

int main(int argc, const char *argv[]){

    // Process commandline arguments
    string stepFilePath;
    bool parseResult = processArgs(argc, argv, stepFilePath);
    if (!parseResult){
        printf("Error parsing commandline options\n");
        return 1;
    }

    // Read STEP file
    STEPControl_Reader reader;
    IFSelect_ReturnStatus status = reader.ReadFile(stepFilePath.c_str());
    
    if (status != IFSelect_RetDone){
        printf("Error importing STEP file %s\n", stepFilePath.c_str());
        return 1;
    } else {
        printf("STEP import succeeded\n");
    }
    
    reader.TransferRoots();
    TopoDS_Shape shape = reader.Shape();
    
    TopExp_Explorer shapeEx = TopExp_Explorer(shape, TopAbs_FACE);
    int i = 0;
    while (shapeEx.More()){
        if (i == 22){
            break;
        }
        i++;
        shapeEx.Next();
    }

    // Get surface bspline
    const TopoDS_Face &face = TopoDS::Face(shapeEx.Current());
    Handle(Geom_BSplineSurface) bSplineSurface = getBSplineSurfaceFromFace(face);

    // Get list of wires
    TopExp_Explorer faceEx = TopExp_Explorer(face, TopAbs_WIRE);
    TopoDS_Wire wire;
    while (faceEx.More()) {
        wire = TopoDS::Wire(faceEx.Current());
        if (BRepTools::OuterWire(face) == wire){
            printf("\t outer wire\n");
            break;
        } else {
            printf("\t inner wire\n");
        }
        faceEx.Next();
    }

    //Explore wires
    TopExp_Explorer wireex = TopExp_Explorer(wire, TopAbs_EDGE);
    TopoDS_Edge edge;
    while (wireex.More()){
        edge = TopoDS::Edge(wireex.Current());
        double t1, t2;
        Handle(Geom2d_Curve) curve = BRep_Tool::CurveOnSurface(edge, face, t1, t2);
        gp_XY pt = curve->Value(t1).Coord();
        printf("curve_value = (%f, %f)\n", pt.Coord(1), pt.Coord(2));
        break;
        wireex.Next();
    }
    // Make composite edge out of the outer wire
    Handle(Geom_Curve) compositeCurve = computeCompositeCurveFromWire(wire);
    double firstParam = compositeCurve->FirstParameter();
    double lastParam = compositeCurve->LastParameter();

    // Compute pCurve of composite curve on the BSpline surface of the face
    Handle(Geom2d_Curve) pCurve;
    ShapeConstruct_ProjectCurveOnSurface pCurveMaker = ShapeConstruct_ProjectCurveOnSurface();
    pCurveMaker.Init(bSplineSurface, 1e-4);
    bool pCurveStatus = pCurveMaker.Perform(compositeCurve, firstParam, lastParam, pCurve);
    if (pCurveStatus){
        printf("pCurve computation successful\n");
    }

    // Make new edge with the composite curve
    BRepBuilderAPI_MakeEdge edgeMaker = BRepBuilderAPI_MakeEdge(compositeCurve);
    const TopoDS_Edge newEdge = edgeMaker.Edge();

    // Make new wire from Edge
    BRepBuilderAPI_MakeWire wireMaker = BRepBuilderAPI_MakeWire(newEdge);
    const TopoDS_Wire newWire = wireMaker.Wire();

    // Make new face from BSpline of original face and the wire
    BRepBuilderAPI_MakeFace faceMaker = BRepBuilderAPI_MakeFace(bSplineSurface, wire);
    const TopoDS_Face newFace = faceMaker.Face();

    // Update newEdge with pCurve information
    BRep_Builder bRepBuilder = BRep_Builder();
    bRepBuilder.UpdateEdge(newEdge, pCurve, newFace, 1.0e-4);

    Handle(Geom2d_Curve) newCurve = BRep_Tool::CurveOnSurface(newEdge, newFace, firstParam, lastParam);
    if (!newCurve){
        throw runtime_error("Could not compute pCurve");
    }

    
    // Query the new pCurve
    gp_XY pt = newCurve->Value(firstParam).Coord();
    printf("curve_value = (%f, %f)\n", pt.Coord(1), pt.Coord(2));

    return 0;
}
