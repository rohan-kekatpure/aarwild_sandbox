import cv2
import numpy as np
from aarwild_utils.workers.constants import types

ImageType = types.ImageType

def tile():
    img_color = cv2.imread('./input1.png')
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    H, W = img_gray.shape[:2]
    w_min, w_max = 110, 130
    h_min, h_max = 140, 160
    x0_min, x0_max = 134, 134
    y0_min, y0_max = 125, 125
    w_list = range(w_min, w_max + 1)
    h_list = range(h_min, h_max + 1)
    x0_list = range(x0_min, x0_max + 1)
    y0_list = range(y0_min, y0_max + 1)

    N = len(h_list) * len(w_list) * len(x0_list) * len(y0_list)
    scores = np.zeros((N, 5))
    r = 0
    for h in h_list:
        for w in w_list:
            num_tiles_x, num_tiles_y = 1 + W // w, 1 + H // h
            for x0 in x0_list:
                for y0 in y0_list:
                    patch = img_gray[y0: y0 + h, x0: x0 + w]
                    tiled_texture = np.tile(patch, (num_tiles_y, num_tiles_x))
                    template_match_result = cv2.matchTemplate(tiled_texture, img_gray, cv2.TM_SQDIFF_NORMED)
                    min_val, _, _, _ = cv2.minMaxLoc(template_match_result)
                    scores[r, :] = [x0, y0, w, h, min_val]
                    r += 1
                    print(x0, y0, w, h)

    scores = scores[scores[:, -1].argsort()]
    px, py, pw, ph, _ = scores[0]
    px, py, pw, ph = int(px), int(py), int(pw), int(ph)
    best_patch = img_color[py: py + ph, px: px + pw]
    best_texture = np.tile(best_patch, (10, 10, 1))
    cv2.imwrite('_best_patch.jpg', best_patch)
    cv2.imwrite('_best_texture.jpg', best_texture)

if __name__ == '__main__':
    tile()
