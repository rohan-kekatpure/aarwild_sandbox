import cv2
import numpy as np
from pathlib import Path

def resize_and_save(img, new_width, new_height, output_dir, index):
    img = cv2.resize(img.copy(), (new_width, new_height))
    filename = 'layout_{:03d}_{}x{}.png'.format(index,new_width, new_height)
    filepath = output_dir / filename
    print(filepath)
    cv2.imwrite(filepath.as_posix(), img)

def crop_and_save(img, x1, x2, y1, y2, output_dir, index):
    img = img[y1: y2, x1: x2, :]
    h, w = img.shape[:2]
    filename = 'layout_{:03d}_{}x{}.png'.format(index, w, h)
    filepath = output_dir / filename
    print(filepath)
    cv2.imwrite(filepath.as_posix(), img)

def main():
    img = cv2.imread('layout.png')
    H, W = img.shape[:2]
    scales = np.linspace(0.2, 1.0, 20)
    output_dir = Path('_resized_images')
    if not output_dir.exists():
        output_dir.mkdir()

    # imax = 0
    # for i, f in enumerate(scales):
    #     resize_and_save(img, int(f * W), H, output_dir, i)
    #     imax += 1
    #
    # for i, f in enumerate(reversed(scales), start=imax + 1):
    #     resize_and_save(img, W, int(f * H), output_dir, i)

    for i, x1 in enumerate(range(0, W//3, 10)):
        crop_and_save(img.copy(), x1, W, 0, H, output_dir, i)

if __name__ == '__main__':
    main()
