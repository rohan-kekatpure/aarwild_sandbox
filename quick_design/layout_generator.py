from wget import download
from aarwild_utils.io import S3Connection
import requests
from pathlib import Path

def get_layout(img_path: Path, output_path: Path) -> None:
    # Upload
    s3 = S3Connection()
    bucket = 'arinthewild'
    s3_base_key = '_layout_quality'
    s3_path = '{}/{}'.format(s3_base_key, img_path.name)
    s3.upload_file(img_path.as_posix(), bucket, s3_path)
    s3.set_permission(bucket, s3_path, acl='public-read')
    print('\nuploaded {} -> {}'.format(img_path, s3_path))

    # Generate layout
    s3_url_tmpl = 'https://arinthewild.s3.amazonaws.com/{}/{}'
    layout_gen_url = 'http://ec2-18-191-147-2.us-east-2.compute.amazonaws.com:8000/get_dump'
    img_url = s3_url_tmpl.format(s3_base_key, img_path.name)
    response = requests.get(layout_gen_url, params={'url': img_url})

    # Download
    try:
        download(response.json()['url'], output_path.as_posix())
    except:
        print(response.text)
