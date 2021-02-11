import cv2
from aarwild_utils.brightness import equalize_brightness
from pathlib import Path
def main():
    input_path = Path('source5.jpg')
    output_path = input_path.with_name(input_path.stem + '_output.jpg')

    image = cv2.imread(input_path.as_posix())
    new_image = equalize_brightness(image, scan_method='RANDOM')
    cv2.imwrite(output_path.as_posix(), new_image)

if __name__ == '__main__':
    main()
