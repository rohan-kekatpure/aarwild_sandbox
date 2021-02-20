from aarwild_utils.tiling import find_tileable_patch, tile
import cv2
import matplotlib.pyplot as pl

img = cv2.imread('input8.jpg')
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
patch, (x, y, w, h) = find_tileable_patch(img, 288, 34, 429, 429, 20)
cpatch = img[y: y + h, x: x + w]
tiled = tile(cpatch, (2048, 2048))
pl.imshow(tiled, cmap='gray')
pl.show()
