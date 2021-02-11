#! /usr/bin/env python

import sys
import cv2

print(sys.argv[1])
img1 = cv2.imread(sys.argv[1])

print(sys.argv[2])
img2 = cv2.imread(sys.argv[2])

img3 = 0.3 * img1 + 0.7 * img2
cv2.imwrite('_blended.jpg', img3)
