import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as R

def _process_args():
    script_name = Path(__file__).name
    help_msg = 'python [options] {}'.format(script_name)
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument('-b', '--babylon-data', dest='babylon_data', action='store',
                        help='Babylon export data', required=True)
    parser.add_argument('-s', '--scene-data', dest='scene_data', action='store',
                        help='Scene export data', required=True)
    args = parser.parse_args()
    return args

def main():
    args = _process_args()
    with open(args.babylon_data) as f:
        babylon_data = json.load(f)
    with open(args.scene_data) as g:
        scene_data = json.load(g)

    # print(babylon_data)
    # Camera positions
    cam_pos_b = babylon_data['cameras'][0]['position']
    cam_pos_s = cx, cy, cz = np.array(scene_data['camera_matrix'])[:3, 3]
    print('\nCamera position:')
    print('Scene: {}'.format(cam_pos_s))
    print('Babylon: {}'.format(cam_pos_b))
    print('Derived: {}'.format([cx, cz, cy]))

    # Camera rotations
    cam_rot_b = babylon_data['cameras'][0]['rotation']
    cam_rot_s = rx, ry, rz = R.from_matrix(np.array(scene_data['camera_matrix'])[:3, :3]).as_euler('xyz')
    print('\nCamera rotation')
    print('Scene: {}'.format(cam_rot_s))
    print('Babylon: {}'.format(cam_rot_b))
    print('Derived: {}'.format([np.pi / 2. - rx, -rz, ry]))

    # Planes
    print('\nPlanes:')
    for m in babylon_data['meshes']:
        wall_type = m['name']
        print('\n{}'.format(wall_type))
        wall_pos_b = m['position']
        wall_pos_s = px, py, pz = scene_data['walls'][wall_type]['plane']['origin']
        print('Scene: {}'.format(wall_pos_s))
        print('Babylon: {}'.format(wall_pos_b))
        print('Derived: {}'.format([px, pz, py]))


if __name__ == '__main__':
    main()
