import argparse
import json
from pathlib import Path
import numpy as np
import cv2
from aarwild_quick_design.scene import Scene
import aarwild_quick_design.vizutils as viz
import aarwild_quick_design.mathutils as mu
import aarwild_quick_design.fspy as fspy
from scipy.spatial.transform import Rotation as R

np.set_printoptions(threshold=np.inf, floatmode='fixed', precision=5, suppress=True)

def _process_args():
    parser = argparse.ArgumentParser(description='Wall estimation')

    parser.add_argument('-i', '--image', dest='img_path', action='store',
                        help='Path to image', required=True)
    parser.add_argument('-l', '--layout', dest='layout_path', action='store',
                        help='Path to layout image', required=True)

    args = parser.parse_args()
    return args

def main():
    args = _process_args()

    image_path = Path(args.img_path)
    layout_path = Path(args.layout_path)

    if not image_path.exists():
        print('Image not found')
        exit(1)
    if not layout_path.exists():
        print('Layout image not found')
        exit(1)

    img = cv2.imread(image_path.as_posix())
    layout = cv2.imread(layout_path.as_posix())
    H, W = layout.shape[:2]
    scene = Scene(img, layout)
    scene.build()

    scale = np.arctan(0.5 * scene.horizontal_fov) / np.arctan(np.arctan(3. / 4))
    print('image width: {}'.format(W))
    print('image height: {}'.format(H))
    print('focal length: {}'.format(scene.relative_focal_length))
    print('scale factor: {}'.format(scale))

    viz.draw_vps(scene, savefig=True)
    viz.draw_walls(scene, savefig=True)
    viz.draw_bounds(scene, savefig=True)

    # output hull quality
    hull_qualities = []
    for wt, wd in scene.walls.items():
        if not wd:
            continue
        if hasattr(wd, 'hull_quality'):
            hull_qualities.append('{}: {:0.2f}'.format(wt, wd.hull_quality))

    # Exports
    with open('_scene.json', 'w') as f:
        json.dump(scene.to_dict(), f, indent=2)

    with open('_scene.babylon', 'w') as f:
        json.dump(scene.babylon, f, indent=2)

    # Rotation analysis
    euler_angles = R.from_matrix(scene.camera_matrix[:3, :3]).as_euler('xyz')
    tilt = (180. / np.pi) * euler_angles[1]
    # print('Euler angles: {}'.format(euler_angles))
    print('Estimated tilt: {:0.4f} deg'.format(tilt))

    camera_params = fspy.solve(image_path.as_posix(), layout_path.as_posix(), True)

    C_fspy = np.array(camera_params['cameraTransform']['rows'])
    print('[FSPY] camera matrix\n{}'.format(C_fspy))
    f_fspy = camera_params['relativeFocalLength']
    print('\n[FSPY] focal length -> {}'.format(f_fspy))

    print('\n[SCENE] camera matrix\n{}'.format(scene.camera_matrix))
    print('\n[SCENE] focal length -> {}'.format(scene.relative_focal_length))
    print('\n')


if __name__ == '__main__':
    main()
