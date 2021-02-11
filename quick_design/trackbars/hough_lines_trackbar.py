import cv2
import sys
import numpy as np
from IPython import embed

def no_op(x):
    pass


img = cv2.imread(sys.argv[1])
H, W = img.shape[:2]
aspect = float(H) / float(W)
dst_size = 600, int(600 * aspect)
img = cv2.resize(img, dst_size)
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
img_gray = cv2.Canny(img_gray, 100, 200, apertureSize=7, L2gradient=True)

win_name = 'Tuner'
cv2.namedWindow(win_name)
cv2.createTrackbar('rho', win_name, 0, 100, no_op)
cv2.createTrackbar('theta', win_name, 0, 100, no_op)
cv2.createTrackbar('thresh', win_name, 0, 1000, no_op)
cv2.createTrackbar('min_len', win_name, 0, 100, no_op)
cv2.createTrackbar('max_gap', win_name, 0, 100, no_op)

while True:

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

    rho_tb = cv2.getTrackbarPos('rho', win_name)
    theta_tb = cv2.getTrackbarPos('theta', win_name)
    thresh_tb = cv2.getTrackbarPos('thresh', win_name)
    min_len_tb = cv2.getTrackbarPos('min_len', win_name)
    max_gap_tb = cv2.getTrackbarPos('max_gap', win_name)

    rho = max(1, rho_tb)
    theta = 0.0009 * theta_tb + 0.01  # theta_tb = (0, 100) -> theta = (0.01, 0.1)
    thresh = max(1, thresh_tb)
    min_len = max(1, min_len_tb)
    max_gap = max(1, max_gap_tb)

    vals = (rho, theta, thresh, min_len, max_gap)
    print('rho -> {}, theta -> {:0.4f}, thresh -> {:0.2f}, min_len -> {}, max_gap -> {}'.format(*vals))

    img_copy = img.copy()
    lines = cv2.HoughLinesP(
        img_gray.copy(),
        rho,
        theta,
        threshold=thresh,
        minLineLength=min_len,
        maxLineGap=max_gap
    )

    if lines is None:
        continue

    for line in lines:
        x1, y1, x2, y2 = line[0]
        cv2.line(img_copy, (x1, y1), (x2, y2), (255, 0, 255), 1, 8)

    cv2.imshow(win_name, img_copy)

cv2.waitKey()
cv2.destroyAllWindows()
