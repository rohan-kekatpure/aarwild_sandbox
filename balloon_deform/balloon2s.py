import pickle
import cv2
import matplotlib.pyplot as pl
import numpy as np
from aarwild_utils.img import threshold_it
from aarwild_utils.transforms import StretchTransform, stretch, shrink, Bounds, Mapping

def _compute_bounds(boundary_pts: np.ndarray) -> Bounds:
    x_min, y_min, W, H = cv2.boundingRect(boundary_pts)
    x_max, y_max = x_min + W, y_min + H
    bbox = Bounds(x_min, y_min, x_max, y_max)
    return bbox


def _main() -> None:
    # ref = cv2.resize(cv2.imread('reference.jpg'), None, fx=0.25, fy=0.25)
    ref = cv2.imread('reference.jpg')
    ref_mask = threshold_it(ref)
    ref_edges = cv2.Canny(ref_mask, 100, 200)
    ref_boundary_pts = np.column_stack(ref_edges.nonzero())
    # From here we switch to x-y system, from row-col system
    # Swap columns of boundary_pts to go from row-col to x-y
    ref_boundary_pts[:, [0, 1]] = ref_boundary_pts[:, [1, 0]]
    x1, y1, x2, y2 = ref_bounds = _compute_bounds(ref_boundary_pts)
    ref_bbox_mask = ref_mask[y1: y2, x1: x2]
    ref_bbox_image = ref[y1: y2, x1: x2, :]
    ref_t = StretchTransform.compute(ref_bbox_mask)

    # src = cv2.resize(cv2.imread('source2.jpg'), None, fx=0.25, fy=0.25)
    src = cv2.imread('source4.jpg')
    src_mask = threshold_it(src)
    src_edges = cv2.Canny(src_mask, 100, 200)
    src_boundary_pts = np.column_stack(src_edges.nonzero())
    # From here we switch to x-y system, from row-col system
    # Swap columns of boundary_pts to go from row-col to x-y
    src_boundary_pts[:, [0, 1]] = src_boundary_pts[:, [1, 0]]
    u1, v1, u2, v2 = src_bounds = _compute_bounds(src_boundary_pts)
    src_bbox_mask = src_mask[v1: v2, u1: u2]
    src_bbox_image = src[v1: v2, u1: u2, :]
    src_t = StretchTransform.compute(src_bbox_mask)
    src_stretched = stretch(src_bbox_image, src_t.transform, src_bbox_image.shape)
    src_stretched = cv2.normalize(src_stretched, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    with open('_srctx.pkl', 'wb+') as f:
        pickle.dump(src_t, f)

    cv2.imwrite('_tex.jpg', src_stretched)

    ref_width = x2 - x1
    ref_height = y2 - y1
    src_stretched = cv2.resize(src_stretched, (ref_width, ref_height))
    src_deformed = shrink(src_stretched, ref_t.transform, (ref_width, ref_height))
    src_deformed[src_deformed == 0] = 1.

    cv2.imwrite('_tex.jpg', cv2.normalize(src_stretched, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8))

    return

def main() -> None:
    src = cv2.imread('source4.jpg')
    src_mask = threshold_it(src)
    src_edges = cv2.Canny(src_mask, 100, 200)
    src_boundary_pts = np.column_stack(src_edges.nonzero())

    # From here we switch to x-y system, from row-col system
    # Swap columns of boundary_pts to go from row-col to x-y
    src_boundary_pts[:, [0, 1]] = src_boundary_pts[:, [1, 0]]
    u1, v1, u2, v2 = src_bounds = _compute_bounds(src_boundary_pts)
    src_bbox_mask = src_mask[v1: v2, u1: u2]
    src_bbox_image = src[v1: v2, u1: u2, :]
    src_t = StretchTransform.compute(src_bbox_mask)
    src_stretched = stretch(src_bbox_image, src_t.transform, src_bbox_image.shape)
    src_stretched = cv2.normalize(src_stretched, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    with open('_srctx.pkl', 'wb+') as f:
        pickle.dump(src_t, f)

    cv2.imwrite('_tex.jpg', src_stretched)

if __name__ == '__main__':
    main()
