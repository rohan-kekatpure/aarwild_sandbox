import sys
import Import
import Mesh

def _export_faces() -> None:
    step_file_path = sys.argv[3]
    output_dir = sys.argv[4]
    doc = App.newDocument('doc')
    Import.insert(step_file_path, 'doc')
    for obj in doc.Objects:
        label = obj.Label
        if not hasattr(obj, 'Shape'):
            continue
        for i, face in enumerate(obj.Shape.Faces):
            face_label = f'_FACE_{label}_{i:06d}'
            print(face_label)
            face_obj = doc.addObject('Part::Feature', face_label)
            face_obj.Shape = face
            Mesh.export([face_obj], f'{output_dir}/{face_label}.obj', tolerance=0.01)

# The usual if __name__ == '__main__' guard does not work with FreeCAD,
# the main function has to be called in a bare way as shown below.

_export_faces()
