#include<cstdio>
#include<iostream>
#include<sstream>
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
#include <BRepClass_FaceClassifier.hxx>
#include<boost/program_options.hpp>
#include<boost/json.hpp>

using namespace std;
namespace po = boost::program_options;
namespace json = boost::json;
typedef map<string, vector<double>> UVgrid;

/*
 * Parse commandline options
 */
bool processArgs(int argc, const char *argv[], string& stepFilePath){

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
            wireExplorer.Next();
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

UVgrid discretizeWire(const TopoDS_Wire& wire, const TopoDS_Face& face){
    TopExp_Explorer wireex = TopExp_Explorer(wire, TopAbs_EDGE);
    const int numPoints = 256;
    vector<double> U(numPoints), V(numPoints);
    while (wireex.More()){
        TopoDS_Edge edge = TopoDS::Edge(wireex.Current());
        double firstParam, lastParam;
        Handle(Geom2d_Curve) curve = BRep_Tool::CurveOnSurface(edge, face, firstParam, lastParam);

        if (!curve){
            printf("Could not get pCurve\n");
            return {};  //TODO: Throw exception here
        }

        double param = firstParam;
        double incr = (lastParam - firstParam) / numPoints;

        for (int i = 0; i < numPoints; i++){
            gp_XY xy = curve->Value(param).Coord();
            U[i] = xy.Coord(1);
            V[i] = xy.Coord(2);
            param += incr;
        }

        break; // TODO: Better way to ensure that wire has only 1 edge
    }

    UVgrid ret = {{"U", U}, {"V", V}};
    return ret;
}

TopoDS_Wire makeSingleEdgeWireForSurface(const TopoDS_Wire& wire, const Handle(Geom_Surface)& bSplineSurface) {
    // Make composite edge out of the outer wire
    Handle(Geom_Curve) compositeCurve = computeCompositeCurveFromWire(wire);
    double firstParam = compositeCurve->FirstParameter();
    double lastParam = compositeCurve->LastParameter();

    // Compute pCurve of composite curve on the BSpline surface of the face
    Handle(Geom2d_Curve) pCurve;
    ShapeConstruct_ProjectCurveOnSurface pCurveMaker = ShapeConstruct_ProjectCurveOnSurface();
    pCurveMaker.Init(bSplineSurface, 1e-4);
    bool pCurveStatus = pCurveMaker.Perform(compositeCurve, firstParam, lastParam, pCurve);
    if (!pCurveStatus){
        throw runtime_error("could not construct pCurve");
    }

    // Make new edge with the composite curve
    BRepBuilderAPI_MakeEdge edgeMaker = BRepBuilderAPI_MakeEdge(compositeCurve);
    const TopoDS_Edge newEdge = edgeMaker.Edge();

    // Update newEdge with pCurve information
    BRep_Builder bRepBuilder = BRep_Builder();
    bRepBuilder.UpdateEdge(newEdge, pCurve, bSplineSurface, wire.Location(), 1.0e-4);

    // Make new wire from Edge
    BRepBuilderAPI_MakeWire wireMaker = BRepBuilderAPI_MakeWire(newEdge);
    TopoDS_Wire newWire = wireMaker.Wire();
    return newWire;
}

TopoDS_Face makeNewFaceWithSingleEdgeWires(const TopoDS_Face& face) {
    // Get surface bspline, will be used later in construction of new Face
    Handle(Geom_BSplineSurface) bSplineSurface = getBSplineSurfaceFromFace(face);

    // Get list of wires
    TopExp_Explorer faceEx = TopExp_Explorer(face, TopAbs_WIRE);
    TopoDS_Wire wire, newWire, outerWire;
    vector<TopoDS_Wire> innerWires;

    while (faceEx.More()) {
        wire = TopoDS::Wire(faceEx.Current());
        newWire = makeSingleEdgeWireForSurface(wire, bSplineSurface);

        if (BRepTools::OuterWire(face) == wire){
            outerWire = newWire;
        } else {
            innerWires.push_back(newWire);
        }
        faceEx.Next();
    }

    // Make new face from BSpline of original face and the outer wire
    BRepBuilderAPI_MakeFace faceMaker = BRepBuilderAPI_MakeFace(bSplineSurface, outerWire);

    // Add inner wires
    for (const TopoDS_Wire& w: innerWires){
        faceMaker.Add(w);
    }

    // Make new Face and return
    return faceMaker.Face();
}

void generateInternalPointsForFace(const TopoDS_Face& face) {

}

void dumpFaceToJson(const string& faceId, const TopoDS_Face& face, json::object& obj) {
    Handle(Geom_Surface) bSplineSurface = BRep_Tool::Surface(face);
    double u1, u2, v1, v2;
    bSplineSurface->Bounds(u1, u2, v1, v2);

    // Explore Face
    TopExp_Explorer faceEx = TopExp_Explorer(face, TopAbs_WIRE);
    vector<UVgrid> innerWires;
    UVgrid outerWire = {};
    while (faceEx.More()) {
        TopoDS_Wire wire = TopoDS::Wire(faceEx.Current());
        map<string, vector<double>> wm = discretizeWire(wire, face);

        if (BRepTools::OuterWire(face) == wire) {
            outerWire = wm;
        } else {
            innerWires.push_back(wm);
        }
        faceEx.Next();
    }
    obj[faceId] = {
            {"surface_bounds", {{"u1", u1}, {"u2", u2}, {"v1", v1}, {"v2", v2}}},
            {"inner_pcurves", innerWires},
            {"outer_pcurve", outerWire}
    };
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
    string faceId;

    // Initialize object for jsonification
    json::object obj;

    while (shapeEx.More()){
        ostringstream buf;
        buf << "FACE_" << i;
        faceId = buf.str();

        if (i != 52){
            i++;
            shapeEx.Next();
            continue;
        }

        const TopoDS_Face face = TopoDS::Face(shapeEx.Current());
        Handle(Geom_BSplineSurface) bsplineSurface = getBSplineSurfaceFromFace(face);
        double u1, u2, v1, v2;
        bsplineSurface->Bounds(u1, u2, v1, v2);
        int numPtsU = 100, numPtsV = 100;
        double du = (u2 - u1) / (float)numPtsU;
        double dv = (v2 - v1) / (float)numPtsV;
        double u = u1;
        double v;
        for (int iu = 0; iu < numPtsU; iu++) {
            v = v1;
            for (int iv = 0; iv < numPtsV; iv++) {
                gp_Pnt2d pnt = gp_Pnt2d(u, v);
//                gp_Pnt pnt = bsplineSurface->Value(u, v);
                BRepClass_FaceClassifier fc = BRepClass_FaceClassifier();
                fc.Perform(face, pnt, 1.0e-3);
                TopAbs_State state = fc.State();
                string stateStr;
                switch (state) {
                    case TopAbs_IN:
                        stateStr = "IN";
                        break;
                    case TopAbs_OUT:
                        stateStr = "OUT";
                        break;
                    case TopAbs_ON:
                        stateStr = "ON";
                        break;
                    case TopAbs_UNKNOWN:
                        stateStr = "UNKNOWN";
                        break;
                    default:
                        stateStr = "<ERROR>";
                }

                printf("%lf,%lf,%s\n", u, v, stateStr.c_str());
                v += dv;
            }
            u += du;
        }
        return 1;
        printf("processing face %s\n", faceId.c_str());
        TopoDS_Face newFace = makeNewFaceWithSingleEdgeWires(face);

        // Dump to JSON
        dumpFaceToJson(faceId, newFace, obj);

        i++;
        shapeEx.Next();
    }

    string s = json::serialize(obj);
    ofstream outfile("_surfaces.json");
    outfile << s << endl;

    return 0;
}