import shutil
from pathlib import Path
import matplotlib.pyplot as pl
from matplotlib.gridspec import GridSpec
from aarwild_utils.img import transfer_color_lab
import cv2

def format_axes(fig):
    for ax in fig.axes:
        ax.tick_params(labelbottom=False, labelleft=False, tick1On=False)


def _frame(color_image, pattern_image, transfer_result, output_path):
    pl.close('all')
    fig = pl.figure(tight_layout=True, figsize=(4, 6))
    gs = GridSpec(3, 2, figure=fig)
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[1:, :])
    ax0.imshow(pattern_image)
    ax1.imshow(color_image)
    ax2.imshow(transfer_result)
    format_axes(fig)
    fig.savefig(output_path.as_posix())

def main():
    images_dir = Path('images')
    frames_dir = images_dir/'frames'
    if images_dir.exists():
        shutil.rmtree(images_dir)
    frames_dir.mkdir(parents=True)

    col = cv2.imread('color.jpg')
    col = cv2.cvtColor(col, cv2.COLOR_BGR2RGB)
    pat = cv2.imread('pattern.jpg')
    pat = cv2.cvtColor(pat, cv2.COLOR_BGR2RGB)
    transfer_result = pat.copy()
    new_img = transfer_color_lab(col, pat)
    dy = 20
    H, W = pat.shape[:2]
    row = -dy
    frame_num = 0
    while row <= H + dy:
        transfer_result[row: row + dy, :, :] = new_img[row: row + dy, :, :]
        output_path = frames_dir/f'frame_{frame_num:03d}.jpg'
        _frame(col, pat, transfer_result, output_path)
        row += dy
        frame_num += 1
if __name__ == '__main__':
    main()
