import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
import OCC.Core.GeomAbs as G
from OCC.Core.TopoDS import topods_Face

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

def _get_spline_params(spline) -> Optional[NurbsParams]:
    NU = spline.NbUPoles()
    NV = spline.NbVPoles()
    DU = spline.UDegree()
    DV = spline.VDegree()
    KU = spline.NbUKnots()
    KV = spline.NbVKnots()

    U_pass = NU + 1 == KU + DU
    V_pass = NV + 1 == KV + DV
    if not (U_pass and V_pass):
        return

    poles_coords = []
    for i in range(1, NU + 1):
        for j in range(1, NV + 1):
            coord = spline.Pole(i, j).Coord()
            weight = spline.Weight(i, j)
            hpoint = np.array((*coord, weight))
            poles_coords.append(hpoint)
    nurbs_params = NurbsParams(NU, NV, DU, DV, poles_coords)
    return nurbs_params

def _convert_to_nurbs(face: Any) -> Any:
    nurbs_face = topods_Face(BRepBuilderAPI_NurbsConvert(face).Shape())
    nurbs_surf = BRepAdaptor_Surface(nurbs_face)
    return nurbs_surf

def main():
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(sys.argv[1])

    if status != IFSelect_RetDone:
        raise ValueError('Eror parsing STEP file')

    failsonly = False
    step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
    step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
    step_reader.TransferRoot()
    shape = step_reader.Shape()
    topo_explorer = TopologyExplorer(shape)
    nurbs_params_list = []
    for face in topo_explorer.faces():
        surface = BRepAdaptor_Surface(face)
        surface_type = surface.GetType()

        if surface_type not in [G.GeomAbs_BSplineSurface, G.GeomAbs_Torus]:
            print(f'Ignored shape of type {surface_type}')
            continue

        if surface_type == G.GeomAbs_Torus:  # Handle Torus
            surface = _convert_to_nurbs(face)

        spline = surface.BSpline()
        spline.IncreaseDegree(3, 3)
        nurbs_params = _get_spline_params(spline)

        if nurbs_params is not None:
            print(f'NurbsP`arams are None for face {face}')
            nurbs_params_list.append(nurbs_params)

    # from IPython import embed; embed(); exit(0)
    nurbs_params_se = [ns.to_dict() for ns in nurbs_params_list]
    with Path('_nurbs_surfaces.json').open('w') as f:
        json.dump(nurbs_params_se, f, indent=2)

if __name__ == '__main__':
    main()

