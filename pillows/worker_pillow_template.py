import json
import logging
import os
from pathlib import Path
from shutil import rmtree
from subprocess import check_call
from typing import NewType, Tuple
import argparse

import cv2
import numpy as np
from aarwild_utils.img import threshold_it
from aarwild_utils.transforms import StretchTransform, stretch
from aarwild_utils.workers import workerutils as W
from aarwild_utils.workers.errors import WorkerError

logger = logging.getLogger(__name__)

BLENDER_CMD = os.environ.get('BLENDER_CMD', '/Applications/Blender.app/Contents/MacOS/Blender')
ImageType = NewType('ImageType', np.ndarray)

def _process_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='front_image_path', action='store',
                        help='front image path', required=True)
    parser.add_argument('-b', dest='back_image_path', action='store',
                        help='back image path', required=True)
    parser.add_argument('-t', dest='template_path', action='store',
                        help='template path', required=False)
    parser.add_argument('-d', dest='templates_dir', action='store',
                        help='template dir', required=False)
    parser.add_argument('-o', dest='output_dir', action='store',
                        help='output dir', required=True)

    return parser.parse_args()

def _stretch_to_size(img: ImageType, size: Tuple) -> ImageType:
    # Compute mask
    mask = threshold_it(img)

    # Stretch to bounding rectangle
    mapping = StretchTransform.compute(mask)
    stretched_img = stretch(img, mapping.transform, output_shape=img.shape)
    x_min, y_min, x_max, y_max = mapping.bounds

    # Crop the Bounding rectangle and rescale to 1024
    p = 2
    stretched_img = stretched_img[y_min + p: y_max - p, x_min + p: x_max - p]
    stretched_img = cv2.resize(stretched_img, size)

    # Normalize and change datatype
    stretched_img = cv2.normalize(stretched_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return stretched_img

def _compute_texture_image(front_image: ImageType,
                           back_image: ImageType,
                           size: Tuple) -> ImageType:
    front_image = _stretch_to_size(front_image, size)
    back_image = _stretch_to_size(back_image, size)
    if front_image.shape != back_image.shape:
        raise WorkerError(f'front_image.shape != back_image.shape, {front_image.shape}, {back_image.shape}')

    texture_img = np.column_stack((front_image, back_image))
    return texture_img

def _bpy_make_pillow(template_file_path: Path,
                     texture_image_path: Path,
                     width: float,
                     height: float,
                     depth: float,
                     output_file_path: Path,
                     material_dir: Path,
                     use_material: bool) -> None:
    """
    Make pillow with specified texture image and default material
    """

    # Run blender to apply texture image to mesh
    bpy_script = Path(__file__).parent/'bpy_pillow_template.py'
    cmd_list = [
        BLENDER_CMD,
        '-noaudio',
        '-b', template_file_path.as_posix(),
        '-P', bpy_script.as_posix(),
        '--',
        '--texture-image', texture_image_path.resolve().as_posix(),
        '--width', str(width),
        '--height', str(height),
        '--depth', str(depth),
        '--output-file', output_file_path.resolve().as_posix(),
        '--material-dir', material_dir.resolve().as_posix(),
    ]

    if use_material:
        cmd_list.append('--use-material')

    print(' '.join(cmd_list))
    _ = check_call(cmd_list)

def _get_texture_info_from_template(template_file_path: Path) -> Tuple:
    # Run blender to generate texture size
    expr_list = [
        "import bpy, json",
        "texture_info = {'size': bpy.data.images['pillow_texture'].size[:]}",
        "f = open('_texture_info.json', 'w')",
        "json.dump(texture_info, f, indent=2)",
        "f.close()"
    ]
    bpy_expr = ';'.join(expr_list)
    cmd_list = [
        BLENDER_CMD,
        '-noaudio',
        '-b', template_file_path.as_posix(),
        '--python-expr', bpy_expr,
    ]

    print(' '.join(cmd_list))
    _ = check_call(cmd_list)

    with open('_texture_info.json') as f:
        texture_info = json.load(f)

    return tuple(texture_info['size'])


def _make_pillow(front_image_path: Path,
                 back_image_path: Path,
                 template_path: Path,
                 output_dir: Path,
                 suffix: str) -> None:
    # Get texture size
    tex_width, tex_height = _get_texture_info_from_template(template_path)

    # Generate composite texture of standardized size
    # from front and back images
    front_img = cv2.imread(front_image_path.as_posix())
    back_img = cv2.imread(back_image_path.as_posix())
    texture_img = _compute_texture_image(front_img, back_img, (tex_width, tex_height))
    texture_image_path = output_dir/f'_texture_image_{suffix}.jpg'
    cv2.imwrite(texture_image_path.as_posix(), texture_img)

    # Assign material
    material_dir = Path('Fabric/m_b7256b')
    use_material = False

    # Resize material maps to 1K (1024x) to reduce model size
    if material_dir.exists():
        logger.info('Resizing PBR material maps')
        W.resize_material_maps(material_dir, 1024)

    # Replace diffuse map with computed texture
    if material_dir.exists():
        logger.info('Replacing diffuse map')
        use_material = True
        W.replace_diffuse_map(texture_image_path, material_dir)

    # Compute dimensions
    # Make pillow with texture and material
    dimensions = {'width': 18., 'height': 18., 'depth': 6.}
    _bpy_make_pillow(
        template_path,
        texture_image_path,
        dimensions['width'],
        dimensions['height'],
        dimensions['depth'],
        output_dir/f'_mesh_{suffix}.blend',
        material_dir,
        use_material
    )

def main() -> None:
    args = _process_args()
    front_image_path = Path(args.front_image_path)
    back_image_path = Path(args.back_image_path)
    output_dir = Path(args.output_dir)
    template_path = args.template_path
    templates_dir = args.templates_dir

    if (template_path is None) and (templates_dir is None):
        raise ValueError('Both template file and template dir are none, at least one must be provided')

    output_dir.mkdir()
    if template_path is not None:
        template_path = Path(template_path)
        _make_pillow(front_image_path, back_image_path, template_path, output_dir, template_path.stem)
        return

    templates_dir = Path(templates_dir)
    for template_path in templates_dir.glob('*.blend'):
        _make_pillow(front_image_path, back_image_path, template_path, output_dir, template_path.stem)

if __name__ == '__main__':
    main()
