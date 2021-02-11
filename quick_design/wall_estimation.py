import argparse
import json
from pathlib import Path
import numpy as np
import cv2
from aarwild_quick_design.skeleton import Skeleton
from scipy.spatial.transform import Rotation as R
from aarwild_quick_design.scene import Scene, SkeletonScene
import aarwild_quick_design.vizutils as viz
import aarwild_quick_design.mathutils as mu

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
    scene = Scene(img, layout, _2vp_mode='2vp')
    scene.build()

    scale = np.arctan(0.5 * scene.horizontal_fov) / np.arctan(np.arctan(3. / 4))
    print('image width: {}'.format(W))
    print('image height: {}'.format(H))
    print('focal length: {}'.format(scene.relative_focal_length))
    print('scale factor: {}'.format(scale))

    viz.draw_vps(scene, savefig=True)
    viz.draw_walls(scene, savefig=True)
    viz.draw_bounds(scene, savefig=True)
    viz.draw_skeleton(scene, image=img, savefig=True)

    Path('_wall_lines.png').rename('_wall_lines_o.png')
    Path('_wall_axes.png').rename('_wall_axes_o.png')
    Path('_wall_bounds.png').rename('_wall_bounds_o.png')
    Path('_wall_skeleton.png').rename('_wall_skeleton_o.png')

    # output hull quality
    hull_qualities = []
    for wt, wd in scene.walls.items():
        if not wd:
            continue
        if hasattr(wd, 'hull_quality'):
            hull_qualities.append('{}: {:0.2f}'.format(wt, wd.hull_quality))

    # Exports
    with open('_scene.json', 'w') as f:
        json.dump(scene.dict, f, indent=2)

    with open('_scene.babylon', 'w') as f:
        json.dump(scene.babylon, f, indent=2)

    # Rotation analysis
    euler_angles = R.from_matrix(scene.camera_matrix[:3, :3]).as_euler('xyz')
    tilt = (180. / np.pi) * euler_angles[1]
    # print('Euler angles: {}'.format(euler_angles))
    print('Estimated tilt: {:0.4f} deg'.format(tilt))

    # Use the computed scene and its skeleton to instantiate a skeleton scene
    scene_dict = json.loads(json.dumps(scene.dict))
    skeleton_dict_2vp = {
          "nodes": {
            "0": [0, 605],
            "1": [821, 699],
            "2": [821, 54],
            "3": [0, 92],
            "4": [130, 508],
            "5": [123, 171]
          },
          "edges": [
            ["0", "4"],
            ["1", "4"],
            ["3", "5"],
            ["2", "5"],
            ["4", "5"]
          ]
        }

    skeleton_dict_1vp = {
        "nodes": {
            "0": [392, 608],
            "1": [896, 808],
            "2": [1096, 103],
            "3": [392, 103],
            "4": [0, 850],
            "5": [1536, 1047],
            "6": [1536, -347],
            "7": [0, -245]
        },
        "edges": [
            ["0", "1"],
            ["1", "2"],
            ["2", "3"],
            ["3", "0"],
            ["0", "4"],
            ["1", "5"],
            ["2", "6"],
            ["3", "7"]
        ]
    }

    skeleton_dict_0vp = skeleton_dict_2vp
    skeleton_dict_2wv = {"nodes": {"0": [750, 852], "1": [750, 0]}, "edges": [["0", "1"]]}
    skeleton_dict_2wh = {"nodes": {"0": [0, 1320], "1": [998, 1320]}, "edges": [["0", "1"]]}
    skeleton_dict_1w = {"nodes": {"0": [563, 887]}, "edges": []}

    skeletons = {
        '2vp': skeleton_dict_2vp,
        '1vp': skeleton_dict_1vp,
        '0vp': skeleton_dict_0vp,
        '2wv': skeleton_dict_2wv,
        '2wh': skeleton_dict_2wh,
        '1w': skeleton_dict_1w
    }

    skeleton_dict = skeletons[scene.vanishing_point_mode]
    skscene = SkeletonScene(scene_dict, Skeleton.from_dict(skeleton_dict))
    skscene.build()

    viz.draw_vps(skscene, image=layout, savefig=True)
    viz.draw_walls(skscene, image=layout, savefig=True)
    viz.draw_bounds(skscene, image=layout, savefig=True)
    viz.draw_skeleton(skscene, image=img, savefig=True)

    with open('_skscene.babylon', 'w') as f:
        json.dump(skscene.babylon, f, indent=2)

    from IPython import embed; embed(); exit(0)

if __name__ == '__main__':
    main()

