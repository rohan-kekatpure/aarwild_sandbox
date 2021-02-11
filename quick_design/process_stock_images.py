import json
from pathlib import Path
from shutil import rmtree, copy
from layout_generator import get_layout
from aarwild_quick_design.scene import Scene
import aarwild_quick_design.img as IMG
import cv2

def resize():
    root = Path('test_images')/'stock'/'imgs'
    for img_path in root.glob('*'):
        print(img_path)
        subdir = root.parent/img_path.stem
        subdir.mkdir()

        img = cv2.imread(img_path.as_posix())
        H, W = img.shape[:2]
        target_width = 1600
        scale = float(target_width) / W
        img_scaled = cv2.resize(img, None, fx=scale, fy=scale)
        cv2.imwrite((subdir/'img.jpg').as_posix(), img_scaled)

def compute_layouts():
    root = Path('test_images')/'stock'
    for subdir in root.glob('*'):
        if subdir.name == '.DS_Store':
            continue

        if subdir.name != '355578037':
            continue

        img_path = subdir/'img.jpg'
        new_img_path = subdir/'preproc.jpg'
        img = cv2.imread(img_path.as_posix())
        new_img = img[:, :1320, :]
        scale = 1600 / new_img.shape[1]
        new_img = cv2.resize(new_img, None, fx=scale, fy=scale)
        new_img = IMG._Pipeline(new_img).grayscale().erode().image
        cv2.imwrite(new_img_path.as_posix(), new_img)
        get_layout(new_img_path, subdir/'layout.png')


def process():
    scales = {
        '122027071': 2.03,
        '213012902': 2.03,
        '213639267': 1.85,
        '218786674': 1.67,
        '232550447': 2.25,
        '238686556': 0.79,
        '286189564': 2.20,
        '292543579': 1.60,
        '295360149': 1.25,
        '310188775': 2.00,
        '314828589': 2.54,
        '335885149': 2.68,
        '354807710': 1.47,
        '355578037': 2.00,
        '361703280': 2.05,
        '52396260': 2.20
    }

    stock_images_path = Path('test_images') / 'stock'
    output_root = Path('_stock_images')
    if output_root.exists():
        print(f'deleting {output_root}')
        rmtree(output_root)
    output_root.mkdir()

    for subdir in stock_images_path.glob('*'):
        if subdir.name == '.DS_Store':
            subdir.unlink()
            continue

        print(subdir.name)
        img_path = subdir/'img.jpg'
        layout_path = subdir/'layout.png'
        img = cv2.imread(img_path.as_posix())
        image_height, image_width = img.shape[:2]
        layout = cv2.imread(layout_path.as_posix())
        scene = Scene(img, layout)
        scene.build()
        babylon = scene.babylon
        skeleton = scene.skeleton

        # Add more properties to babylon dict
        babylon['layout_score'] = 1.0
        babylon['skeleton'] = skeleton
        babylon['width'] = image_width
        babylon['height'] = image_height
        babylon['scale'] = scales[subdir.name]
        babylon['background'] = None
        babylon['status'] = 1
        babylon['confidence'] = 1.0

        output_dir = output_root/subdir.name
        output_dir.mkdir()
        copy(img_path, output_dir)
        with (output_dir/'babylon.json').open('w') as f:
            json.dump(babylon, f, indent=2)


if __name__ == '__main__':
    # resize()
    # compute_layouts()
    process()
