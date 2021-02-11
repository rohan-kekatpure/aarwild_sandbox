"""
Application to create a babylon scene from an
image on your local machine
"""
import json
import uuid

import cv2
from aarwild_utils.io import S3Connection
from aarwild_quick_design.scene import Scene
import argparse
from pathlib import Path


def _process_args():
    script_name = Path(__file__).name
    help_msg = 'python [options]'.format(script_name)
    parser = argparse.ArgumentParser(description=help_msg)
    parser.add_argument('-l', '--layout-image', dest='layout_image', action='store',
                        help='Layout image', required=True)
    parser.add_argument('-i', '--input-image', dest='input_image', action='store',
                        help='Input image', required=True)
    args = parser.parse_args()
    return args


def main():
    args = _process_args()
    source_img_path = Path(args.input_image)
    layout_img_path = Path(args.layout_image)

    # Upload image to S3 and get background image URL
    s3 = S3Connection()
    bucket = 'arinthewild'
    s3_key = 'quick_design_images/{}'.format(source_img_path.name)
    print('Uploading image')
    s3.upload_file(source_img_path.as_posix(), bucket, s3_key)
    s3.set_permission(bucket, s3_key, 'public-read')
    bg_url = 'https://{}.s3.amazonaws.com/{}'.format(bucket, s3_key)

    # Build scene
    layout_img = cv2.imread(layout_img_path.as_posix())
    scene = Scene(layout_img)
    scene.build()
    babylon = scene.babylon

    # Read JS template
    with open('scene_template.js') as f:
        js = f.read()
    js = js.replace('{{SCENE_INFO}}', json.dumps(babylon, indent=2))
    js = js.replace('{{BACKGROUND_IMAGE}}', bg_url)

    with open('scene_template.js', 'w') as f:
        f.write(js)

    # with open('scene_template.html') as f:
    #     html = f.read()
    # html = html.replace('{{SCRIPT}}', js)
    #
    # with open('scene_{}.html'.format(uuid.uuid4().hex), 'w') as f:
    #     f.write(html)


if __name__ == '__main__':
    main()
