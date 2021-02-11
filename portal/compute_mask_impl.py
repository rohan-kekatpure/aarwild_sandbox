from pathlib import Path
import json
import numpy as np
import cv2
from aarwild_utils.img import threshold_it, url_to_image, threshold_it_with_gc
from aarwild_utils.io import S3Connection

def _compute_masks(image: np.ndarray) -> str:
    assert image is not None
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # image = cv2.resize(image, (256, 256))
    thresholds = np.linspace(230, 255, 16)
    s3 = S3Connection()
    result = []
    for threshold in thresholds:
        print(f'threshold: {threshold}')
        # mask = threshold_it(image, min_intensity=threshold)
        mask, _, _ = threshold_it_with_gc(image, min_intensity=threshold, max_hole_fraction=0.0025)
        threshold_str = f'{threshold:0.2f}'
        filename = Path(f'_mask_threshold_{threshold_str}.jpg')
        cv2.imwrite(filename.as_posix(), mask)
        s3_key = f'rdk.delemete/{filename.name}'
        s3.upload_file(filename.as_posix(), 'arinthewild', s3_key)
        url = s3.get_presigned_url('arinthewild', s3_key)
        result.append({
            'threshold': threshold_str,
            'url': url
        })
    j = json.dumps(result, indent=2)
    print(j)
    return j

def _compute_masks_from_url(image_url: str) -> str:
    image = url_to_image(image_url)
    return _compute_masks(image)

if __name__ == '__main__':
    # # img_url = 'https://media.kohlsimg.com/is/image/kohls/3726978_Playful_Pups?wid=1200&hei=1200&op_sharpen=1'
    # img_url = 'https://media.kohlsimg.com/is/image/kohls/2487491_ALT'
    # _compute_masks_from_url(img_url)

    image = cv2.imread('shape_image.jpg')
    _compute_masks(image)
