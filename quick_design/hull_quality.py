from pathlib import Path
from aarwild_quick_design.scene import Scene
import cv2
import json
import pandas as pd
import matplotlib.pyplot as pl
import numpy as np


WALL_TYPES = ['LEFT', 'RIGHT', 'FRONT', 'FLOOR', 'WALL']

def _compute_hull_quality():
    layouts_path = Path('./layouts')
    hull_qualities = []
    i = 0
    for l in layouts_path.glob('*.png'):
        print(l)
        img = cv2.imread(l.as_posix())
        scene = Scene(img)
        scene.build()

        hq = dict.fromkeys([
            'id',
            'left_quality', 'left_ndefects', 'left_complexity',
            'right_quality', 'right_ndefects', 'right_complexity',
            'front_quality', 'front_ndefects', 'front_complexity',
            'ceil_quality', 'ceil_ndefects', 'ceil_complexity',
            'floor_quality', 'floor_ndefects', 'floor_complexity',
        ])

        hq['id'] = l.stem
        for wall_type, wall_data in scene.walls.items():
            wt = wall_type.lower()
            if wall_data:
                hq[wt + '_quality'] = wall_data.hull.quality
                hq[wt + '_ndefects'] = wall_data.hull.defect_count
                hq[wt + '_complexity'] = wall_data.hull.complexity

        hull_qualities.append(hq)

    with open('hull_quality.json', 'w') as f:
        json.dump(hull_qualities, f, indent=2)


def main():
    df_qual = pd.read_json('./hull_quality.json')
    df_labels = pd.read_csv('./assigned_classes.csv')
    df = pd.merge(df_qual, df_labels, on='id', how='inner')
    del df_qual
    del df_labels

    wall_types = ['left', 'right', 'front', 'ceil', 'floor']
    quality_cols = [w + '_quality' for w in wall_types]
    complexity_cols = [w + '_complexity' for w in wall_types]
    ndefect_cols = [w + '_ndefects' for w in wall_types]

    df['max_qual'] = np.log10(df[quality_cols].max(axis=1))
    df['max_ndefects'] = df[ndefect_cols].max(axis=1)
    df['max_complexity'] = df[complexity_cols].max(axis=1)
    df['combined'] = df.max_qual + np.log10(df.max_ndefects) + np.log10(df.max_complexity)

    # Plotting
    good_idx = df.good == 1
    bad_idx = df.bad == 1

    attr = 'combined'
    histargs = dict(histtype='step', bins='auto', density=True, fill=True, alpha=0.4)
    pl.hist(df.loc[good_idx][attr], color='g', **histargs)
    pl.hist(df.loc[bad_idx][attr], color='r', **histargs)
    pl.xlabel('defect score', fontsize=16)
    pl.ylabel('normalized count', fontsize=16)
    pl.show()

if __name__ == '__main__':
    main()

