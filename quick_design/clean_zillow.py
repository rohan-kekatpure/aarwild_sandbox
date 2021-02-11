from pathlib import Path
from shutil import rmtree

with open('failed_screenshos.txt') as f:
    failed_ss = f.read().splitlines()

root = Path('zillow')
for dir_ in root.glob('*'):
    if dir_.name not in failed_ss:
        rmtree(dir_)
    

