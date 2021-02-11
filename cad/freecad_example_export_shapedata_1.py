import shutil
from pathlib import Path

import Import
import Part

faces_dir = Path('_faces')
if faces_dir.exists():
    shutil.rmtree(faces_dir)
faces_dir.mkdir()

doc = App.newDocument('doc')
# Import.insert('step_files/07-47916/47916.STEP', 'doc')
Import.insert('step_files/DC19-93640/Assem1.STEP', 'doc')


for o in doc.Objects:
    label = o.Label
    for i, face in enumerate(o.Shape.Faces):
        face_file = faces_dir/f'FACE_{label}_{i:06d}.txt'
        with face_file.open('w') as f:
            f.write(face.dumpToString())


