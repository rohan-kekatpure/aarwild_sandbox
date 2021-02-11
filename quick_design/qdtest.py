import argparse
import time
from pathlib import Path

import cv2
from selenium import webdriver
from shutil import rmtree
import random
from scene_analysis import create_scene

def _process_args():
    parser = argparse.ArgumentParser(description='Wall estimation')

    parser.add_argument('-d', '--directory', dest='scene_dir', action='store',
                        help='Path to directory containing scene image and layouts', required=True)

    args = parser.parse_args()
    return args

def create_blended_image(image_path, layout_path, screenshot_dir):
    img = cv2.imread(image_path.as_posix())
    layout = cv2.imread(layout_path.as_posix())
    blended = 0.3 * img + 0.7 * layout
    blended_path = screenshot_dir / '_blended.jpg'
    cv2.imwrite(blended_path.as_posix(), blended)

def take_screenshots(screenshots_root):
    print('Taking screenshots...')
    driver = webdriver.Firefox()
    base_url = 'http://0.0.0.0:5000'
    driver.get(base_url)
    folder_list = driver\
        .find_element_by_xpath('/html/body/ul')\
        .find_elements_by_tag_name('a')

    folder_names = [a.text for a in folder_list]
    scene_urls = ['{}/{}scene.html'.format(base_url, fn) for fn in folder_names]

    for fn, url in zip(folder_names, scene_urls):
        driver.get(url)
        time.sleep(10)
        fn = fn[:-1]
        output_dir = screenshots_root / fn
        output_dir.mkdir(exist_ok=True)

        inner_div = driver.find_element_by_id('inner')
        buttons = inner_div.find_elements_by_tag_name('button')
        canvas = driver.find_element_by_tag_name('canvas')
        driver.find_element_by_xpath('/html/body/div/div[1]/a[1]').click()

        for btn in buttons:
            btn_text = btn.text
            if btn_text != 'SAVE':
                btn.click()
                time.sleep(0.5)
                img_pth = output_dir / '{}.png'.format(btn_text)
                canvas.screenshot(img_pth.as_posix())

    driver.close()

def make_html(screenshots_root):
    print('Generating results HTML...')
    template = '''
    <html>
        <head>
        <style>
            table, th, td {
              border: 1px solid black;
            }
            
            img {
                width=300;
            }
        </style>        
        <h1>QD results </h1>
        </head>
        <body>
            <table>
                <th> NAME </th>
                <th> LAYOUT </th>
                <th> FLOOR </th>
                <th> LEFT </th>
                <th> FRONT </th>
                <th> RIGHT </th>
                {{ROWS}}
            </table> 
        </body>
    </html>
    '''

    rows_list = []
    for dir_ in sorted(screenshots_root.iterdir()):
        cols_list = [
            '<td>{}</td>'.format(dir_.stem),
            '<td> <img src="{}" alt="0" width="500"> </td>'.format(dir_ / '_blended.jpg')
        ]

        walls = ['FLOOR', 'LEFT', 'FRONT', 'RIGHT']
        for wall in walls:
            src = dir_ / '{}.png'.format(wall)
            cols_list.append('<td> <img src="{}" alt="0" width="500"> </td>'.format(src))

        cols_str = '\n'.join(cols_list)
        row = '<tr>\n{}\n</tr>'.format(cols_str)
        rows_list.append(row)

    rows_str = '\n'.join(rows_list)

    html = template.replace('{{ROWS}}', rows_str)
    with open('_qdresults.html', 'w') as f:
        f.write(html)

def create_scenes(layouts_root, screenshots_root, randomize=False, random_frac=0.1):
    for room_dir in layouts_root.iterdir():
        if randomize:
            if random.random() > random_frac:
                continue

        if room_dir.name == '.DS_Store':
            room_dir.unlink()
            continue

        if not room_dir.is_dir():
            continue

        image_path = room_dir / 'img.jpg'
        layout_path = room_dir / 'layout.png'

        if not image_path.exists():
            image_path = layout_path

        if not layout_path.exists():
            print('skipping {}'.format(room_dir.as_posix()))
            continue

        print(room_dir, end=' ')
        templates_dir = Path('templates')
        output_root = Path('dist')
        if (output_root / room_dir.name).exists():
            print('(exists)')
            continue

        try:
            create_scene(
                image_path,
                layout_path,
                templates_dir,
                output_root,
                room_dir.name
            )
        except AttributeError as ae:
            if ae.args[0] == "'NoneType' object has no attribute 'copy'":
                print('(deleting)')
                rmtree(room_dir)
                continue
        except AssertionError:
            print('(filtered)')
            continue
        except Exception:
            print('exception')
            continue

        # Create a blended image for layout classification
        screenshot_dir = screenshots_root / room_dir.name
        screenshot_dir.mkdir(exist_ok=True)
        create_blended_image(image_path, layout_path, screenshot_dir)
        print('(success)')

def create_scenes_from_layouts(root):
    templates_dir = Path('templates')
    output_root = Path('dist')
    for layout_path in root.iterdir():
        if layout_path.name == '.DS_Store':
            layout_path.unlink()
            continue

        print(layout_path, end=' ')
        layout_image_name = layout_path.stem
        scene_dir = layout_image_name

        if (output_root / scene_dir).exists():
            print('(exists)')
            continue

        try:
            create_scene(
                layout_path,
                layout_path,
                templates_dir,
                output_root,
                scene_dir
            )
        except Exception as e:
            print('exception')
            continue

        print('(success)')

def main():
    # Set up output directories
    args = _process_args()
    room_images_root = Path(args.scene_dir)
    screenshots_root = Path('_screenshots')

    # if screenshots_root.exists():
    #     rmtree(screenshots_root)
    #
    # screenshots_root.mkdir(exist_ok=True)

    # Compute scenes
    # create_scenes(room_images_root, screenshots_root, randomize=False)
    # create_scenes_from_layouts(room_images_root)

    # Take the screenshots
    take_screenshots(screenshots_root)
    make_html(screenshots_root)


if __name__ == '__main__':
    main()


