import shutil

import Part
from pathlib import Path

doc = App.newDocument('doc')
sph_shape = Part.makeSphere(1.0)
sph_shape_nurbs = sph_shape.toNurbs()

sph_obj = doc.addObject('Part::Feature', 'mysphere')
sph_obj.Shape = sph_shape_nurbs

faces_dir = Path('_faces')
if faces_dir.exists():
    shutil.rmtree(faces_dir)
faces_dir.mkdir()

for i, face in enumerate(sph_shape.Faces):
    face_file = faces_dir/f'FACE_{i:06d}.txt'
    with face_file.open('w') as f:
        f.write(face.dumpToString())
#
# with Path('_sphere_brep.txt').open('w') as g:
#     g.write(sph_shape_nurbs.exportBrepToString())


