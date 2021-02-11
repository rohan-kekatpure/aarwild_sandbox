import shutil
from pathlib import Path

import numpy as np
import matplotlib.pyplot as pl
from matplotlib.gridspec import GridSpec
import cv2

def format_axes(fig):
    for ax in fig.axes:
        ax.tick_params(labelbottom=False, labelleft=False, tick1On=False)


def score(X, *args):
    x0, y0, width, height = X.astype(np.int)
    image = args[0]
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

def _frame(img, x, y, w, h, score_, path):
    pl.close('all')
    fig = pl.figure(tight_layout=True)
    gs = GridSpec(3, 3)
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[0, 2])
    ax3 = fig.add_subplot(gs[1:, :])

    patch = img[y: y + h, x: x + w, :]
    ax1.imshow(patch)
    ax2.text(0.5, 0.5, f'{1.0-score_:0.2f}', va='center', ha='center', fontsize=36)

    tiled_size = sx, sy = 2048, 1024
    nx, ny = sx // w, sy // h
    tiled = np.tile(patch, (ny, nx, 1))
    tiled = cv2.resize(tiled, (sx, sy))
    ax3.imshow(tiled)
    ax0.imshow(cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 4))
    pl.subplots_adjust(wspace=0.0)
    format_axes(fig)
    fig.savefig(path.as_posix())

def main():
    images_path = Path('images')
    if images_path.exists():
        shutil.rmtree(images_path)
    images_path.mkdir()

    img = cv2.imread('input1.png')
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    best_patch = cv2.imread('_best_patch.jpg')
    H, W = img.shape[:2]
    h, w = best_patch.shape[:2]
    n_frames = 100
    param_vals = []
    delta = 10
    for i in range(n_frames):
        w1 = np.random.randint(w - delta, w + delta, 1)[0]
        h1 = np.random.randint(h - delta, h + delta, 1)[0]
        y = np.random.randint(0, H - h1, 1)[0]
        x = np.random.randint(0, W - w1, 1)[0]
        param_vals.append((x, y, w1, h1))
    param_vals.append((204, 145, 120, 146))

    scores = []
    for p in param_vals:
        scores.append(score(np.array(p), img))

    param_vals_w_score = [(*p, s) for p, s in zip(param_vals, scores)]
    param_vals_w_score.sort(key=lambda s: s[-1], reverse=True)

    for i, p in enumerate(param_vals_w_score):
        output_path = images_path/f'frame_{i:03d}.png'
        _frame(img.copy(), *p, path=output_path)

if __name__ == '__main__':
    main()
