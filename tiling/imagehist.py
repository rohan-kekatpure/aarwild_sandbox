from dataclasses import dataclass

import numpy as np
from numpy.linalg import norm
import cv2
import matplotlib.pyplot as pl

@dataclass
class ImageDelta:
    mean_diff: float
    color_similarity: float

def image_delta(image_a, image_b) -> ImageDelta:
    assert image_a.ndim == 3 and image_a.shape[2] == 3, 'expected 3 channel image'
    assert image_b.ndim == 3 and image_b.shape[2] == 3, 'expected 3 channel image'
    # mu_a = image_a.mean(axis=(0, 1))
    # mu_b = image_b.mean(axis=(0, 1))
    mu_a = np.percentile(image_a, 50, axis=(0, 1))
    mu_b = np.percentile(image_b, 50, axis=(0, 1))
    mean_diff = norm(mu_b - mu_a)
    cosine = np.dot(mu_a, mu_b) / (norm(mu_a) * norm(mu_b))
    cosine = min(cosine, 0.999999)
    color_sim = -np.log(1.0 - cosine)
    return ImageDelta(mean_diff, color_sim)

def main():
    img = cv2.imread('source9.jpg')
    # img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    H, W = img.shape[:2]
    img_left = img[:, :W//2]
    img_right = img[:, W//2:]
    img_top = img[:H//2, :]
    img_bottom = img[H//2:, :]

    fig, axes = pl.subplots(nrows=2, ncols=3, figsize=(15, 10))
    args = dict(bins=64, cumulative=True, density=True, histtype='step', lw=2)
    axes[0, 0].hist(img_left[:, :, 0].ravel(), color='b', **args)
    axes[0, 0].hist(img_right[:, :, 0].ravel(), color='#99ccff', **args)
    axes[0, 1].hist(img_left[:, :, 1].ravel(), color='g', **args)
    axes[0, 1].hist(img_right[:, :, 1].ravel(), color='#99ffcc', **args)
    axes[0, 2].hist(img_left[:, :, 2].ravel(), color='r', **args)
    axes[0, 2].hist(img_right[:, :, 2].ravel(), color='#ff99cc', **args)

    axes[1, 0].hist(img_top[:, :, 0].ravel(), color='b', **args)
    axes[1, 0].hist(img_bottom[:, :, 0].ravel(), color='#99ccff', **args)
    axes[1, 1].hist(img_top[:, :, 1].ravel(), color='g', **args)
    axes[1, 1].hist(img_bottom[:, :, 1].ravel(), color='#99ffcc', **args)
    axes[1, 2].hist(img_top[:, :, 2].ravel(), color='r', **args)
    axes[1, 2].hist(img_bottom[:, :, 2].ravel(), color='#ff99cc', **args)

    # pl.show()

    # print(f'color cosine = {color_cosine(img_left, img_right)}')

    # Print color cosine of different images
    img_5 = cv2.imread('source5.jpg')
    img_6 = cv2.imread('source6.jpg')
    img_8 = cv2.imread('source8.jpg')
    img_9 = cv2.imread('source9.jpg')

    print(f'diff = {image_delta(img_left, img_right)}')
    print(f'diff = {image_delta(img_top, img_bottom)}')

    print('with other images')
    print(f'diff = {image_delta(img, img_5)}')
    print(f'diff = {image_delta(img, img_6)}')
    print(f'diff = {image_delta(img, img_8)}')

if __name__ == '__main__':
    main()
