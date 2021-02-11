import shutil

import Part
from pathlib import Path

def main():
    doc = App.newDocument('doc')
    shape_data = Part.makeCircle(1.0)

    shape_obj = doc.addObject('Part::Feature', 'myshape')
    shape_obj.Shape = shape_data

    faces_dir = Path('_edges')
    if faces_dir.exists():
        shutil.rmtree(faces_dir)
    faces_dir.mkdir()

    for i, edge in enumerate(shape_data.Edges):
        outfile = faces_dir / f'EDGE_{i:06d}.txt'
        with outfile.open('w') as f:
            f.write(edge.toNurbs().dumpToString())

main()
