import cv2
from aarwild_quick_design.img import watermark

img = cv2.imread('canvas4.jpg')
wimg = watermark(img)
cv2.imwrite('_watermarked.png', wimg)

