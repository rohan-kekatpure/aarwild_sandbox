from collections import Counter
from pathlib import Path
import Import


def count_objects(step_file_path):
    doc = App.newDocument('doc')
    Import.insert(step_file_path, 'doc')
    shape_types = [i.Shape.ShapeType for i in doc.Objects if hasattr(i, 'Shape')]
    print(shape_types)

    if len(shape_types) == 0:
        print('no shapes found')

    App.closeDocument('doc')
    counts = Counter(shape_types)
    return counts

def main():
    root = Path('../step_files')
    step_file_paths = list(root.glob('**/*.stp')) + list(root.glob('**/*.STEP'))
    outfile = Path('freecad_step_file_stats.csv')
    with outfile.open('w') as f:
        f.write('filepath,num_compsolids,num_compounds,num_solids\n')

    for step_file_path in step_file_paths:
        counts = count_objects(step_file_path.as_posix())
        print(counts)
        num_compsolids = counts.get('CompSolids', 0)
        num_compounds = counts.get('Compound', 0)
        num_solids = counts.get('Solid', 0)
        with outfile.open('a') as f:
            f.write(f'{step_file_path.as_posix()},{num_compsolids},{num_compounds},{num_solids}\n')

main()
