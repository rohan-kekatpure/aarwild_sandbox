from pathlib import Path

path = Path('/Users/rohan/work/code/virtualenvs/aarwild/lib/python3.8/site-packages/OCC')
search_str = '-> "opencascade::handle< Geom2d_Curve >"'
for pyfile in path.glob('**/*.py'):
    with pyfile.open() as f:
        lines = f.read().splitlines()

    for line in lines:
        if search_str in line:
            print(f'[{pyfile.name}] {line}')


