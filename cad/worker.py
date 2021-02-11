import shutil
from pathlib import Path
from subprocess import check_call

def run_freecad(input_file: Path, output_dir: Path) -> None:
    freecad_cmd = '/Applications/FreeCAD.app/Contents/Resources/bin/FreeCADCmd'
    freecad_script = 'freecad_split_objects.py'
    cmd_list = [
        freecad_cmd,
        freecad_script,
        '--',
        input_file.as_posix(),
        output_dir.as_posix()
    ]
    print(' '.join(cmd_list))
    _ = check_call(cmd_list)

def run_blender(obj_dir: Path, output_file: Path) -> None:
    blender_cmd = '/Applications/Blender.app/Contents/MacOS/Blender'
    blender_script = './bpy_collect_meshes.py'
    cmd_list = [
        blender_cmd,
        '-b', '-P',
        blender_script,
        '--',
        '--object-dir', obj_dir.as_posix(),
        '--output-file', output_file.as_posix()
    ]
    print(' '.join(cmd_list))
    _ = check_call(cmd_list)

def main() -> None:
    input_root = Path('.')
    g = input_root.glob('**/*.[sS][tT]*[pP]')
    obj_root = Path('_objs')
    blend_root = Path('_blendfiles')
    for root in [obj_root, blend_root]:
        if root.exists():
            shutil.rmtree(root)
        root.mkdir()

    for step_file_path in g:
        print('='*40)
        print(step_file_path, step_file_path.exists())
        pfx = f'{step_file_path.parent.name}_{step_file_path.stem}'
        obj_dir = obj_root/f'_{pfx}'
        obj_dir.mkdir()
        run_freecad(step_file_path, obj_dir)
        blend_output_file = blend_root/f'_{pfx}.blend'
        run_blender(obj_dir, blend_output_file)

if __name__ == '__main__':
    main()
