import cv2
import numpy as np

def main():
    img = cv2.imread('source4.jpg')
    H, W = img.shape[:2]
    dw = dh = 20
    num_steps_x = W // dw
    num_steps_y = H // dh
    max_intensity = 70

    di_x = max_intensity / num_steps_x
    di_y = max_intensity / num_steps_y
    img = img.astype(np.float)
    for i in range(num_steps_y):
        start_row = i * dh
        end_row = start_row + dh
        di = i * di_y
        img[start_row: end_row, :, :] = img[start_row: end_row, :, :] - di

    for j in range(num_steps_x):
        start_col = j * dw
        end_col = start_col + dw
        di = j * di_x
        img[:, start_col: end_col, :] = img[:, start_col: end_col, :] - di

    img = np.clip(img, 0., 255.)
    img = img.astype(np.uint8)
    cv2.imwrite('_darkened.jpg', img)

if __name__ == '__main__':
    main()

