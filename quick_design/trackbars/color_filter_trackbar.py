import sys
import cv2
import numpy as np

COLOR_FLOOR = [119, 81, 81]
COLOR_CEILING = [210, 247, 241]
COLOR_FRONT_WALL = [93, 69, 249]
COLOR_LEFT_WALL = [170, 229, 255]
COLOR_RIGHT_WALL = [181, 206, 144]

def _pass(_):
    pass

def trackbar(img):
    cv2.namedWindow('image')

    # create trackbars for color change
    cv2.createTrackbar('B_lo', 'image', 0, 255, _pass)
    cv2.createTrackbar('B_hi', 'image', 255, 255, _pass)
    cv2.createTrackbar('G_lo', 'image', 0, 255, _pass)
    cv2.createTrackbar('G_hi', 'image', 255, 255, _pass)
    cv2.createTrackbar('R_lo', 'image', 0, 255, _pass)
    cv2.createTrackbar('R_hi', 'image', 255, 255, _pass)
    cv2.createTrackbar('blur', 'image', 1, 20, _pass)
    cv2.createTrackbar('kernel', 'image', 1, 20, _pass)

    while True:
        k = cv2.waitKey(1) & 0xFF

        if k == 27:
            break

        b_lo = cv2.getTrackbarPos('B_lo', 'image')
        b_hi = cv2.getTrackbarPos('B_hi', 'image')
        g_lo = cv2.getTrackbarPos('G_lo', 'image')
        g_hi = cv2.getTrackbarPos('G_hi', 'image')
        r_lo = cv2.getTrackbarPos('R_lo', 'image')
        r_hi = cv2.getTrackbarPos('R_hi', 'image')
        bsize = cv2.getTrackbarPos('blur', 'image')
        ksize = cv2.getTrackbarPos('kernel', 'image')

        lo = (b_lo, g_lo, r_lo)
        hi = (b_hi, g_hi, r_hi)
        blur = 2 * bsize + 1
        kernel = np.ones((ksize, ksize), np.uint8)
        ximg = np.copy(img)

        mask = cv2.inRange(ximg, lo, hi)
        ximg = cv2.bitwise_and(ximg, ximg, mask=mask)
        ximg = cv2.morphologyEx(ximg, cv2.MORPH_CLOSE, kernel)
        ximg = cv2.medianBlur(ximg, blur)
        cv2.imshow('image', ximg)

    cv2.destroyAllWindows()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python {} <image_path>'.format(sys.argv[0]))
        exit(1)

    img = cv2.imread(sys.argv[1])
    H, W = img.shape[:2]
    a = float(H) / float(W)
    f = 600.0 / W
    img = cv2.resize(img, None, fx=f, fy=f)

    trackbar(img)
