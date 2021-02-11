#  #Copyright (c) 2020. AARWILD, Inc. All Rights Reserved.
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import argparse
import json
from pathlib import Path
import cv2
from aarwild_quick_design.scene import Scene, DefaultScene
from shutil import rmtree, copy

def _process_args():
    parser = argparse.ArgumentParser(description='Wall estimation')

    parser.add_argument('-n', '--name', dest='name', action='store',
                        help='Name of the output', required=True)

    args = parser.parse_args()
    return args

def create_scene(image_path, layout_path, templates_dir, output_root, output_dir_name):
    image = cv2.imread(image_path.as_posix())
    layout = cv2.imread(layout_path.as_posix())
    H, W = layout.shape[:2]
    scene = Scene(image, layout)
    # scene = DefaultScene(image)
    scene.build()

    assert scene.vanishing_point_mode == '2vp'

    # Create output_dir
    output_dir = output_root / output_dir_name
    if output_dir.exists():
        rmtree(output_dir)
    output_dir.mkdir()

    # Copy scene assets to output_dir
    copy(image_path, output_dir/'babylon.jpg')
    copy(layout_path, output_dir/'layout.png')
    copy(templates_dir / 'jquery.fancybox.css', output_dir)
    copy(templates_dir / 'stylesheet.css', output_dir)

    # Export babylon scene
    babylon_file = output_dir / 'babylon.babylon'
    with babylon_file.open('w') as f:
        json.dump(scene.babylon, f, indent=2)

    # Create scene HTML
    html_tmpl_file = templates_dir / 'scene_template.html'
    with html_tmpl_file.open() as f:
        html = f.read()

    html = html.replace('IMG_WIDTH', str(W))\
               .replace('IMG_HEIGHT', str(H))

    html_output_file = output_dir / 'scene.html'
    with html_output_file.open('w') as f:
        f.write(html)

    # Create Javascript
    js_tmpl_file = templates_dir / 'scene_template.js'
    with js_tmpl_file.open() as f:
        js = f.read()

    js = js.replace('XXXXX', output_dir_name)

    js_output_file = output_dir / 'scene.js'
    with js_output_file.open('w') as f:
        f.write(js)

def main():
    # Ensure image, layout, template and output directory exist
    image_path = Path('img.jpg')
    layout_path = Path('layout.png')
    templates_dir = Path('templates')
    output_root = Path('dist')
    assert image_path.exists(), 'image not found, expected "./img.jpg"'
    assert layout_path.exists(), 'layout not found, expected "./layout.png"'
    assert templates_dir.exists(), 'template directory not found, expected "./templates/*"'
    assert output_root.exists(), 'output root directory not found, expected "./dist"'

    args = _process_args()
    create_scene(image_path, layout_path, templates_dir, output_root, args.name)

if __name__ == '__main__':
    main()
