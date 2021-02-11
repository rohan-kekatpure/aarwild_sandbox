import functools
import shutil
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from aarwild_utils.workers.constants import types

Image = types.ImageType
SAVE_PERCENT = 0.001
Df = 0.8  # Final damping
D0 = 0.1  # initial damping

# Fraction of the number of steps after which the damping factor should
# reach 90% of its final value
m = 5

def _colorvector(image: Image) -> np.ndarray:
    """
    Returns normalized median color of a 3-channel image
    """
    mu = np.mean(image, axis=(0, 1))
    std = np.std(image, axis=(0, 1))
    vec = np.concatenate((mu, std))
    vec /= np.linalg.norm(vec)
    return vec

def _fast_colorvector(image: Image, image_sum: Image, image_sqsum: Image,
                      x1: int, x2: int, y1: int, y2: int) -> np.ndarray:
    assert image_sum.dtype == np.float
    assert image_sqsum.dtype == np.float
    IS = image_sum
    ISS = image_sqsum
    H, W = image.shape[:2]
    x2 = min(x2, W)
    y2 = min(y2, H)
    N = (y2 - y1) * (x2 - x1)
    S1 = IS[y2, x2] - IS[y2, x1] - IS[y1, x2] + IS[y1, x1]
    S2 = ISS[y2, x2] - ISS[y2, x1] - ISS[y1, x2] + ISS[y1, x1]
    mu = S1 / N
    var = (N * S2 - S1 * S1) / (N * N)
    std = np.sqrt(var)
    vec = np.concatenate((mu, std))
    vec /= np.linalg.norm(vec)
    return vec

def _colorcmp(color_vector_1: np.ndarray, color_vector_2: np.ndarray) -> Tuple:
    mu_1 = color_vector_1
    mu_2 = color_vector_2
    rms_diff = np.linalg.norm(mu_2 - mu_1)
    clipped_cosine = min(np.dot(mu_1, mu_2), 0.999999)
    color_sim = -np.log(1.0 - clipped_cosine)
    return color_sim, rms_diff

def _sample_color_similarity(image: Image,
                             image_sum: Image,
                             image_sqsum: Image,
                             patch_width: int, patch_height: int,
                             image_color_vector: np.ndarray,
                             n_samples: int = 10) -> np.ndarray:
    H, W = image.shape[:2]
    cv_image = image_color_vector
    color_similarity = np.zeros((n_samples, ))
    for i in range(n_samples):
        x1 = np.random.randint(0, W - patch_width, 1)[0]
        x2 = x1 + patch_width
        y1 = np.random.randint(0, H - patch_height, 1)[0]
        y2 = y1 + patch_height
        cv_patch = _fast_colorvector(image, image_sum, image_sqsum, x1, x2, y1, y2)
        sim, _ = _colorcmp(cv_patch, cv_image)
        color_similarity[i] = sim
    return color_similarity

def _find_smallest_similar_patch_dims(image: Image,
                                      image_sum: Image,
                                      image_sqsum: Image,
                                      color_similarity_threshold: float) -> Tuple:
    cv_image = _colorvector(image)  # color vector of whole image
    H, W = image.shape[:2]
    max_factor = 16
    factor = 1.1
    grow = 1.02
    factors = []
    while factor <= max_factor:
        patch_width = int(W / factor)
        patch_height = int(H / factor)
        color_similarity = _sample_color_similarity(
            image, image_sum, image_sqsum,
            patch_width, patch_height,
            cv_image, n_samples=1000
        )
        if color_similarity.min() >= color_similarity_threshold:
            factor *= grow
            factors.append(factor)
        else:
            break
    np.save('_factors.npy', factors)
    patch_width, patch_height = int(W / factor), int(H / factor)
    return patch_width, patch_height

def _get_next_patch_coords_raster(image_width: int, image_height: int,
                                  patch_width: int, patch_height: int) -> Tuple:
    W, H = image_width, image_height
    for y1 in range(H):
        y2 = y1 + patch_height
        for x1 in range(W):
            x2 = x1 + patch_width
            yield x1, y1, x2, y2

def _get_next_patch_coords_random(image_width: int, image_height: int,
                                  patch_width: int, patch_height: int,
                                  n_samples: int) -> Tuple:
    W, H = image_width, image_height
    for _ in range(n_samples):
        x1 = np.random.randint(-W, W, 1)[0]
        y1 = np.random.randint(-H, H, 1)[0]
        x2 = x1 + patch_width
        y2 = y1 + patch_height
        x1 = max(x1, 0)
        y1 = max(y1, 0)
        yield x1, y1, x2, y2

def _adjust_patch_luminosity(patch: Image,
                             target_luminosity: int,
                             damping: float,
                             brighten_only: bool) -> None:
    """
    Adjust luminosity of `image` in place
    """
    if patch.size == 0:
        return
    patch_luminosity = patch.mean()
    delta = int(target_luminosity - patch_luminosity)

    if brighten_only and delta < 0:
        delta = 0

    patch[:, :] = patch + damping * delta

def _adjust_image_luminosity(image: Image,
                             image_sum: Image,
                             image_sqsum: Image,
                             lum_image: Image,
                             patch_width: int,
                             patch_height: int,
                             scan_method: str,
                             n_samples_random_scan,
                             color_sim_threshold,
                             color_diff_threshold,
                             brighten_only) -> Image:
    cv_image = _colorvector(image)
    lum_image = lum_image.copy()
    mean_image_lum = lum_image.mean()
    H, W = lum_image.shape[:2]
    if scan_method == 'RANDOM':
        _get_next_patch = functools.partial(_get_next_patch_coords_random, n_samples=n_samples_random_scan)
    elif scan_method == 'RASTER':
        _get_next_patch = _get_next_patch_coords_raster
    else:
        raise ValueError(f'unsupported scan method {scan_method}, allowed methods: ["RANDOM", "RASTER"]')

    patch_coords = []
    idx = 0

    # alpha value is a sol of: (Df + D0)/2 = Df - (Df - D0) * exp(-alpha * N / m)
    alpha = m * np.log(2.) / n_samples_random_scan
    n = 0
    for x1, y1, x2, y2 in _get_next_patch(W, H, patch_width, patch_height):
        cv_patch = _fast_colorvector(image, image_sum, image_sqsum, x1, x2, y1, y2)
        col_similarity, col_difference = _colorcmp(cv_patch, cv_image)
        if (col_similarity > color_sim_threshold) and (col_difference > color_diff_threshold):
            damping = Df - (Df - D0) * np.exp(-alpha * n)
            n += 1
            _adjust_patch_luminosity(lum_image[y1: y2, x1: x2], mean_image_lum, damping, brighten_only)
            if np.random.random() < SAVE_PERCENT:
                patch_coords.append([x1, y1, x2, y2])
                cv2.imwrite(f'brightness_images/lum_images/_lum_{idx:03d}.png', lum_image)
                idx += 1

    patch_coords = np.array(patch_coords)
    np.save('_patch_coords.npy', patch_coords)
    return lum_image

def equalize_brightness(image: Image,
                        scan_method: str = 'RANDOM',
                        color_sim_threshold: float = 7.5,
                        color_diff_threshold: float = 0.0,
                        n_samples_random_scan: int = 10000,
                        brighten_only: bool = False) -> Image:
    """
    Equalize brightness of a 3-channel image using blockwise scanning.
    :param image: input image

    :param scan_method: Must be from ['RANDOM', 'RASTER', 'BOTH']. 'RANDOM' scan is fast and works well in most cases.
    'RASTER' scan is slower but works better on some images. 'BOTH' performs a run of 'RANDOM' scan followed by a run
    of 'RASTER' scan. This may may help remove rectangular streaks after a run of 'RANDOM' scan.

    :param color_sim_threshold: Minimum color similarity needed for a block to be deemed color-similar to the image.
    `color_sim_threshold` of 13.81 is the maximum possible and indicates perfect color matching. Lower values (all
    the way down to 0.0) indicate progressively lesser color similarity values. Default value of 7.5 works for most
    images. If you see dark or bright areas being left out, decrease the threshold. If you experience
    overcorrections, try increasing the threshold.

    :param color_diff_threshold: Minimum color RMS difference between color vectors of image and the block to
    perform the update. If the image-block color vector RMS difference  is below `color_diff_threshold` then the
    brightness update for that block is skipped.

    :param n_samples_random_scan: Number of samples for 'RANDOM' scan order.

    :param brighten_only: If True, perform only additive brightening updates and skip subtractive brightening updates.

    :return: Brightness-equalized image.
    """
    image_sum, image_sqsum = cv2.integral2(image, sdepth=cv2.CV_64F, sqdepth=cv2.CV_64F)
    best_patch_width, best_patch_height = _find_smallest_similar_patch_dims(image,
                                                                            image_sum,
                                                                            image_sqsum,
                                                                            color_sim_threshold)
    image_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lum_image = image_lab[:, :, 0]

    do_raster = do_random = False
    if scan_method == 'RASTER': do_raster = True
    if scan_method == 'RANDOM': do_random = True
    if scan_method == 'BOTH': do_raster = do_random = True

    if do_random:
        lum_image = _adjust_image_luminosity(
            image,
            image_sum,
            image_sqsum,
            lum_image,
            best_patch_width,
            best_patch_height,
            scan_method='RANDOM',
            color_sim_threshold=color_sim_threshold,
            color_diff_threshold=color_diff_threshold,
            brighten_only=brighten_only,
            n_samples_random_scan=n_samples_random_scan
        )

    if do_raster:
        lum_image = _adjust_image_luminosity(
            image,
            image_sum,
            image_sqsum,
            lum_image,
            best_patch_width,
            best_patch_height,
            scan_method='RASTER',
            color_sim_threshold=color_sim_threshold,
            color_diff_threshold=color_diff_threshold,
            brighten_only=brighten_only,
            n_samples_random_scan=n_samples_random_scan
        )

    image_lab[:, :, 0] = lum_image
    new_image = cv2.cvtColor(image_lab, cv2.COLOR_LAB2BGR)
    return new_image

def main() -> None:
    lum_images_dir = Path('brightness_images/lum_images')
    if lum_images_dir.exists():
        shutil.rmtree(lum_images_dir)
    lum_images_dir.mkdir(parents=True)
    img = cv2.imread('_darkened.jpg')
    final_image = equalize_brightness(img, n_samples_random_scan=100000, color_sim_threshold=5.5)

    color_images_dir = lum_images_dir.parent/'color_images'
    if color_images_dir.exists():
        shutil.rmtree(color_images_dir)
    color_images_dir.mkdir(parents=True)

    idx1 = 0
    factors = np.load('_factors.npy')
    H, W = img.shape[:2]
    for factor in factors:
        img_f = img.copy()
        h = H / factor
        w = W / factor
        x1 = W // 2 - int(w // 2)
        y1 = H // 2 - int(h // 2)
        x2 = W // 2 + int(w // 2)
        y2 = H // 2 + int(h // 2)
        cv2.rectangle(img_f, (x1, y1), (x2, y2), thickness=2, color=(0, 255, 0))
        color_image_path = color_images_dir / f'_img_{idx1:03d}.png'
        cv2.imwrite(color_image_path.as_posix(), img_f)
        idx1 += 1

    patch_coords = np.load('_patch_coords.npy')
    image_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    idx2 = -1
    for x1, y1, x2, y2 in patch_coords:
        idx2 += 1
        lum_image_path = lum_images_dir/f'_lum_{idx2:03d}.png'
        print(lum_image_path)
        lum_image = cv2.imread(lum_image_path.as_posix())
        image_lab[:, :, 0] = lum_image[:, :, 0]
        image_bgr = cv2.cvtColor(image_lab, cv2.COLOR_LAB2BGR)
        cv2.rectangle(image_bgr, (x1, y1), (x2, y2), thickness=2, color=(0, 255, 0))
        color_image_path = color_images_dir/f'_img_{idx1:03d}.png'
        cv2.imwrite(color_image_path.as_posix(), image_bgr)
        idx1 += 1
    final_image_path = color_images_dir/f'_img_{idx1:03d}.png'
    cv2.imwrite(final_image_path.as_posix(), final_image)
if __name__ == '__main__':
    main()
