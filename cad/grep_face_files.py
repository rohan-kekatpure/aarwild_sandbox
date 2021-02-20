from pathlib import Path

root = Path('_faces')
for f in root.glob('*.txt'):
    with f.open() as g:
        s = g.read()
        if 'urational vrational' in s:
            print(s)

