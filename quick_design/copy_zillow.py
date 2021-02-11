from pathlib import Path
from shutil import copytree

misclassified = '''
0165
0223
0228
0377
0386
0417
0488
0497
0510
0592
0604
'''

def _copy1():
    src_root = Path('test_images') / 'zillow'
    target_root = Path('test_images') / 'mcls_1w'

    for s in misclassified.split('\n'):
        if len(s) == 0:
            continue
        id_, issue = s.split(',')
        if issue == 'MC-1w':
            copytree(src_root / id_, target_root / id_)

def _copy2():
    src_root = Path('test_images') / 'zillow'
    target_root = Path('test_images') / 'good_layout_fails'

    for id_ in misclassified.split('\n'):
        if len(id_) == 0:
            continue
        copytree(src_root / id_, target_root / id_)


if __name__ == '__main__':
    _copy2()


