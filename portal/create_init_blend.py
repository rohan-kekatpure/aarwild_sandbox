import json
from pathlib import Path
from shutil import rmtree
from subprocess import check_call
from typing import List, Dict
import cv2
from aarwild_utils.img import url_to_image
from aarwild_utils.workers import constants

BLENDER_CMD = constants.env.blender

def _download_images(urls: List, download_dir: Path) -> None:
    for i, url in enumerate(urls):
        image = url_to_image(url)
        filename = download_dir/f'image_{i:03d}.jpg'
        cv2.imwrite(filename.as_posix(), image)

def create_init_blend(feed_obj: Dict) -> None:
    # Create downloads directory
    download_dir = Path(f'images_{feed_obj["sku"]}_{feed_obj["option_id"]}')
    if download_dir.exists():
        rmtree(download_dir)
    download_dir.mkdir()

    # Download images
    urls = feed_obj['image_urls']
    _download_images(urls, download_dir)

    # Validate dimensions
    dimensions = feed_obj['dimensions'][0]['parsed']

    # Run a blender script with download dir and dimensions
    bpy_script = Path('bpy_create_init_blend.py')
    cmd_list = [
        BLENDER_CMD,
        '-noaudio',
        '-b',
        '-P', bpy_script.as_posix(),
        '--',
        '--images-dir', download_dir.as_posix(),
        '--width', str(dimensions['width']['value']),
        '--height', str(dimensions['height']['value']),
        '--depth', str(dimensions['depth']['value']),
    ]
    _ = check_call(cmd_list)


def main() -> None:
    with Path('feed.json').open() as f:
        feed_obj = json.load(f)
    create_init_blend(feed_obj)

if __name__ == '__main__':
    main()
