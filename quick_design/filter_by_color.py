import cv2
import sys
import matplotlib.pyplot as pl


COL_RIGHT_LOW = (170, 195, 135)
COL_RIGHT_HIGH = (190, 215, 155)

def _filter_by_color_limits(image, color_low, color_high):
    """
    Returns pixels that are between `color_low` and `color_high`.
    `color_low` and `color_high` are BGR tuples in OpenCV format.
    The return values is a binary image (mask).

    MOVE TO aarwild_utils.img
    """
    mask = cv2.inRange(image, color_low, color_high)
    return mask

def main():
    img = cv2.imread(sys.argv[1])
    mask = _filter_by_color_limits(img, COL_RIGHT_LOW, COL_RIGHT_HIGH)
    pl.imshow(mask, cmap='gray')
    pl.show()

if __name__ == '__main__':
    main()
