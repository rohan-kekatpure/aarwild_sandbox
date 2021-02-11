import argparse
from pathlib import Path
from shutil import copy
from layout_generator import get_layout

def _process_args():
    parser = argparse.ArgumentParser(description='Wall estimation')

    parser.add_argument('-d', '--directory', dest='images_dir', action='store',
                        help='Path to directory containing room images', required=True)

    args = parser.parse_args()
    return args

def _standardize(images_root):
    for img_path in images_root.glob('*'):
        if img_path.name == '.DS_Store':
            img_path.unlink()
            continue

        if img_path.suffix != 'jpg':
            img_path.rename(img_path.with_suffix('.jpg'))

def main():
    args = _process_args()
    images_root = Path(args.images_dir)
    _standardize(images_root)

    # Because of the call to _standardize above,
    # at this point we have no .DS_Store and all
    # file extensions are .jpg
    for img_path in images_root.glob('*.jpg'):
        print(img_path)
        subdir = img_path.parents[1]/img_path.stem
        subdir.mkdir(exist_ok=True)
        copy(img_path, subdir/'img.jpg')
        get_layout(img_path, subdir/'layout.png')


if __name__ == '__main__':
    main()
