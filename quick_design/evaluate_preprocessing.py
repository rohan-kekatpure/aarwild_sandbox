from pathlib import Path
import argparse
import cv2
from shutil import rmtree, copytree
from layout_generator import get_layout
import matplotlib.pyplot as pl
import numpy as np

def _process_args():
    parser = argparse.ArgumentParser(description='Buld layout generator')

    parser.add_argument('--input-dir', '-i', dest='input_dir', action='store',
                        help='Input directory', required=True)

    parser.add_argument('--output-dir', '-o', dest='output_dir', action='store',
                        help='Output directory', required=True)

    parser.add_argument('--clean', '-c', dest='clean', action='store_true',
                        help='Delete existing output directory', required=False)

    args = parser.parse_args()
    return args

def clean_mkdir(path):
    if path.exists():
        print('{} exists, deleting'.format(path))
        rmtree(path)
    path.mkdir()

def genlayout_all(input_dir, output_dir):
    for img_path in sorted(list(input_dir.glob('*'))):
        get_layout(img_path, output_dir)

class Pipeline:
    def __init__(self, input_image_path: Path, output_image_path: Path):
        self.input_image_path = input_image_path
        self.output_image_path = output_image_path
        self.image = cv2.imread(input_image_path.as_posix())

    def save(self):
        cv2.imwrite(self.output_image_path.as_posix(), self.image)

    def grayscale(self):
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        return self

    def redex(self, factor=4):
        img = self.image
        f = factor
        img = cv2.resize(img, None, fx=1./f, fy=1./f, interpolation=cv2.INTER_AREA)
        img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
        self.image = img
        return self

    def blur(self, ksize=11):
        self.image = cv2.blur(self.image, (ksize, ksize))
        return self

    def erode(self, ksize):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize)
        self.image = cv2.erode(self.image, kernel)
        return self

def preproc(input_dir, preproc_output_dir):
    for img_path in input_dir.glob('*'):
        pp = Pipeline(img_path, preproc_output_dir)
        pp.grayscale().blur(ksize=11).save()


def main():
    args = _process_args()
    input_dir = Path(args.input_dir)
    output_root = Path(args.output_dir)

    if args.clean:
        clean_mkdir(output_root)

    # Remove .DS_Store files
    for path in input_dir.glob('*'):
        if path.name == '.DS_Store':
            path.unlink()

    # make directory to store comparison images
    compare_dir = output_root/'_compare'
    compare_dir.mkdir(exist_ok=True)

    for src_dir in input_dir.glob('*'):
        print(f'\n{src_dir}')
        output_subdir = output_root/src_dir.name

        if output_subdir.exists():
            print(f'{output_subdir} exists, skipping')
            continue

        copytree(src_dir, output_subdir)

        input_img_path = output_subdir / 'img.jpg'
        preproc_img_path = output_subdir / '_preproc.jpg'
        old_layout_path = output_subdir / 'layout.png'
        new_layout_path = output_subdir / '_layout_preproc.png'
        old_blend_path = output_subdir/'_old_blend.jpg'
        new_blend_path = output_subdir/'_new_blend.jpg'

        # preprocess the image and store in subdir
        pipeline = Pipeline(input_img_path, preproc_img_path)
        # pipeline.grayscale().save()
        pipeline.grayscale().erode((9, 9)).save()

        # compute the layout of preproc image

        get_layout(preproc_img_path, new_layout_path)

        # blend the layout with original image
        img = cv2.imread(input_img_path.as_posix())
        old_layout = cv2.imread(old_layout_path.as_posix())
        new_layout = cv2.imread(new_layout_path.as_posix())

        old_blend = 0.5 * img + 0.5 * old_layout
        new_blend = 0.5 * img + 0.5 * new_layout
        cv2.imwrite(old_blend_path.as_posix(), old_blend)
        cv2.imwrite(new_blend_path.as_posix(), new_blend)

        preproc_img_path.unlink()
        old_layout_path.unlink()
        new_layout_path.unlink()

        # Make before/after plot
        H, W = img.shape[:2]
        aspect = float(W) / float(H)
        fig_height = 6
        fig_width = 0.5 * aspect * fig_height
        pl.close('all')
        fig, ax = pl.subplots(2, 1, figsize=(fig_width, fig_height))
        ax[0].imshow(cv2.cvtColor(old_blend.astype(np.uint8), cv2.COLOR_BGR2RGB))
        ax[0].set_axis_off()
        ax[1].imshow(cv2.cvtColor(new_blend.astype(np.uint8), cv2.COLOR_BGR2RGB))
        ax[1].set_axis_off()
        pl.subplots_adjust(left=0.01, right=0.99, bottom=0.05, hspace=0.05)
        pl.tight_layout(pad=0.5)
        fig.savefig((compare_dir/f'{output_subdir.name}.png').as_posix())


if __name__ == '__main__':
    main()
