from typing import Any

import cv2
import numpy as np
from aarwild_utils.workers.constants import types
from scipy.optimize import minimize

ImageType = types.ImageType

def score(X: np.ndarray, *args: Any) -> float:
    x0, y0, width, height = X.astype(np.int)
    image: ImageType = args[0]
    H, W = image.shape[:2]
    patch = image[y0: y0 + height, x0: x0 + width, :]
    if patch.size == 0:
        return np.inf

    true_height, true_width = patch.shape[:2]
    num_tiles_x, num_tiles_y = 1 + W // true_width, 1 + H // true_height
    tiled_texture = np.tile(patch, (num_tiles_y, num_tiles_x, 1))
    template_match_result = cv2.matchTemplate(tiled_texture, image, cv2.TM_SQDIFF_NORMED)
    min_val, max_val, _, _ = cv2.minMaxLoc(template_match_result)
    return min_val

def tile():
    img = cv2.imread('./input1.png')
    H, W = img.shape[:2]

    # Search over entire image
    # init_X = np.array([77, 56, 120, 150], dtype=np.int)
    # bounds_X = [(0, W), (0, H), (10, W), (10, H)]

    # For source5.jpg Search over trust region
    # init_X = np.array([143, 92, 290, 163])
    # bounds_X = [(123, 163), (72, 112), (270, 310), (143, 183)]

    # For source4.jpg Search over trust region
    # init_X = np.array([100, 100, 377, 196], dtype=np.int)
    # bounds_X = [(80, 120), (80, 120), (360, 400), (180, 220)]

    # For source3.jpg Search over trust region
    init_X = np.array([195, 126, 120, 145], dtype=np.int)
    dpx = 30
    bounds_X = [(p - dpx, p + dpx) for p in init_X]

    # TODO: Try other derivative-free optimization methods !
    sol = minimize(score, init_X, (img,), method='Powell', bounds=bounds_X, tol=1.0e-4)

    print(sol)
    px, py, pw, ph = sol.x.astype(int)
    best_patch = img[py: py + ph, px: px + pw]
    best_texture = np.tile(best_patch, (5, 6, 1))
    cv2.imwrite('_best_patch.jpg', best_patch)
    cv2.imwrite('_best_texture.jpg', best_texture)

if __name__ == '__main__':
    tile()
