import sys
import Import
import Mesh

def _clean_label(label: str) -> str:
    return label.replace(' ', '_').upper()

def _split_by_object() -> None:
    step_file_path = sys.argv[3]
    output_dir = sys.argv[4]
    doc = App.newDocument('doc')
    Import.insert(step_file_path, 'doc')
    for obj in doc.Objects:
        label = obj.Label
        if hasattr(obj, 'Shape'):
            # For some reason OBJ export based on importOBJ.export is lower
            # resolution than Mesh.export.
            # TODO: Ask this on FreeCAD forum
            # importOBJ.export([obj], f'{output_dir}/_{label}.obj')
            Mesh.export([obj], f'{output_dir}/_{label}.obj', tolerance=0.01)

def _split_by_faces() -> None:
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
            del face_obj
            doc.recompute()

# The usual if __name__ == '__main__' guard does not work with FreeCAD,
# the main function has to be called in a bare way as shown below.


_split_by_object()
# _split_by_faces()
