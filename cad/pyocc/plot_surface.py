import matplotlib.pyplot as pl
import numpy as np
import json
from pathlib import Path

def main():
    with Path('_surfaces.json').open() as f:
        surfaces: dict = json.load(f)

    fig = pl.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    for face_id, surface_info in surfaces.items():
        u1, u2, v1, v2 = surface_info['surface_bounds']
        # Ulist = np.arange(u1, u2, .1)
        # Vlist = np.arange(v1, v2, .1)
        Ulist = np.linspace(u1, u2, 50)
        Vlist = np.linspace(v1, v2, 50)
        Ugrid, Vgrid = np.meshgrid(Ulist, Vlist)
        UV = np.column_stack((Ugrid.ravel(), Vgrid.ravel()))
        ax.plot(UV[:, 0], UV[:, 1], '+', color='green', ms=4, alpha=0.1)
        ax.set_aspect('equal')
        for edge in surface_info['edges']:
            edge_type = edge['type']
            points = np.array(edge['points'])
            color = 'b' if edge_type == 'outer' else 'r'
            ax.plot(points[:, 0], points[:, 1], '-', color=color)

        pl.show()
if __name__ == '__main__':
    main()
