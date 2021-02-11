import shutil
from pathlib import Path
from typing import Tuple, Any

from aarwild_utils.img import threshold_it
from aarwild_utils.transforms import StretchTransform, stretch
import cv2
import aarwild_utils.workers.workerutils as W
from aarwild_utils.workers.constants import types
import numpy as np
from aarwild_utils.img import pad_border

Image = types.ImageType
def _stretch_to_size(img: Image, mapping: Any, size: Tuple) -> Image:
    # Compute mask
    mask = threshold_it(img)

    # Stretch to bounding rectangle
    # mapping = StretchTransform.compute(mask)
    stretched_img = stretch(img, mapping.transform, output_shape=img.shape)
    x_min, y_min, x_max, y_max = mapping.bounds

    # Crop the Bounding rectangle and rescale to 1024
    stretched_img = stretched_img[y_min: y_max, x_min: x_max]

    # Normalize and change datatype
    stretched_img = cv2.normalize(stretched_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Extra crop to remove white border creted by transform
    stretched_img = W.crop_border(stretched_img, num_pixels=3)
    stretched_img = cv2.resize(stretched_img, size)

    return stretched_img

def main() -> None:
    images_dir = Path('images')
    frames_dir = images_dir/'frames'
    if images_dir.exists():
        shutil.rmtree(images_dir)
    frames_dir.mkdir(parents=True)

    img = cv2.imread('pillow.jpg')
    H, W = img.shape[:2]
    mask = threshold_it(img)
    mapping = StretchTransform.compute(mask)
    dy = 20
    frame_num = 0
    y = dy
    while y <= H + dy:
        patch = img[:y, :, :]
        h, w = patch.shape[:2]
        stretched_img = _stretch_to_size(patch, mapping, (w, y))
        stretched_img = pad_border(stretched_img, 30, (255, 255, 255))
        stretched_img = cv2.resize(stretched_img, (w, h))
        morphed_img = img.copy()
        morphed_img[:h, :w, :] = stretched_img
        output_path = frames_dir/f'_frame_{frame_num:03d}.jpg'
        cv2.imwrite(output_path.as_posix(), morphed_img)
        y += dy
        frame_num += 1

if __name__ == '__main__':
    main()
