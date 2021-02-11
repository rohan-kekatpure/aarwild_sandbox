import wget
from pathlib import Path

output_root = Path('test_images/zillow')

with open('babylon_scenes.csv') as f:
    for i, line in enumerate(f):
        scene_url = line.strip()
        print('\ndownloading -> {}'. format(scene_url))
        layout_url = scene_url.replace('scene_template.html', 'layout.png')
        img_url = scene_url.replace('scene_template.html', 'babylon.jpg')

        output_dir = output_root / '{:04d}'.format(i)
        if output_dir.exists():
            continue

        output_dir.mkdir(exist_ok=True)

        layout_download_pth = output_dir / 'layout.png'
        img_download_pth = output_dir / 'img.jpg'
        wget.download(layout_url, layout_download_pth.as_posix())
        wget.download(img_url, img_download_pth.as_posix())

