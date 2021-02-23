import sys
from pathlib import Path

from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity

def get_topo_explorer_from_step_file(filepath):
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(filepath)

    if status != IFSelect_RetDone:
        raise ValueError('Eror parsing STEP file')

    failsonly = False
    step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
    step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
    step_reader.TransferRoot()
    shape = step_reader.Shape()
    topo_explorer = TopologyExplorer(shape)
    return topo_explorer

def main():
    root = Path('../step_files')
    step_files = list(root.glob('**/*.stp')) + list(root.glob('**/*.STEP'))
    outfile = Path('pyocc_step_file_stats.csv')
    with outfile.open('w') as f:
        f.write('filepath,num_compsolids,num_compounds,num_solids,num_faces\n')

    for step_file in step_files:
        print(f'processing {step_file}')
        t = get_topo_explorer_from_step_file(step_file.as_posix())
        num_compsolids = t.number_of_comp_solids()
        num_compounds = t.number_of_compounds()
        num_solids = t.number_of_solids()
        num_faces = t.number_of_faces()
        with outfile.open('a') as f:
            f.write(f'{step_file.as_posix()},{num_compsolids},{num_compounds},{num_solids},{num_faces}\n')

if __name__ == '__main__':
    main()
