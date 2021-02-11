import argparse
import json
from pathlib import Path
import numpy as np
import cv2
from aarwild_quick_design.scene import Scene
import aarwild_quick_design.vizutils as viz
import matplotlib.pyplot as pl
from shutil import rmtree

np.set_printoptions(threshold=np.inf, floatmode='fixed', precision=5, suppress=True)

def _process_args():
    parser = argparse.ArgumentParser(description='Wall estimation')

    parser.add_argument('-l', '--layout-images-dir', dest='layout_images_dir', action='store',
                        help='Path to segmented image dir', required=True)

    args = parser.parse_args()
    return args

def main():
    args = _process_args()

    layout_paths = Path(args.layout_images_dir)

    if not layout_paths.exists():
        print('Layout image directory not found')
        exit(1)

    test_output_dir = Path('_test_output')
    if test_output_dir.exists():
        rmtree(test_output_dir)
    test_output_dir.mkdir(exist_ok=True)

    for layout_path in layout_paths.glob('**/layout.png'):
        print(layout_path, end=' ')
        asset_dir = layout_path.parent
        img_path_jpg = asset_dir / 'img.jpg'
        img_path_png = asset_dir / 'img.png'

        try:
            if img_path_jpg.exists():
                img = cv2.cvtColor(cv2.imread(img_path_jpg.as_posix()), cv2.COLOR_BGR2RGB)
            elif img_path_png.exists():
                img = cv2.cvtColor(cv2.imread(img_path_png.as_posix()), cv2.COLOR_BGR2RGB)
            else:
                img = None
        except cv2.error:
            img = None

        if img is None:
            print('')
            continue

        layout = cv2.imread(layout_path.as_posix())

        pl.close('all')
        fig, axes = pl.subplots(nrows=2, ncols=2, figsize=(7, 7))
        axes = axes.ravel()
        try:
            scene = Scene(img, layout)
            scene.build()
            if scene.vanishing_point_mode == '0vp':
                with open('0vp.txt', 'a') as f:
                    f.write(f'{asset_dir.name}\n')

            if img is not None:
                axes[0].imshow(img)
                viz.draw_skeleton(scene, axis=axes[0])
                axes[0].text(0.5, 0.5, 'f = {:0.4f}'.format(scene.relative_focal_length),
                             transform=axes[0].transAxes, fontsize=12, color='#83f52c', backgroundcolor='k')
                axes[0].set_axis_off()

            viz.draw_vps(scene, axis=axes[1])
            viz.draw_walls(scene, axis=axes[2])
            viz.draw_bounds(scene, axis=axes[3])
            test_output_file = test_output_dir / '{}.jpg'.format(asset_dir.name)
            fig.savefig(test_output_file.as_posix())
            _ = scene.dict
            _ = scene.babylon
            _ = scene.skeleton
            json.dumps(scene.dict)
            json.dumps(scene.babylon)
            json.dumps(scene.skeleton)

            print('(success)')
        except Exception as e:
            print('(failed, {})'.format(e.args))

        del scene

if __name__ == '__main__':
    main()
