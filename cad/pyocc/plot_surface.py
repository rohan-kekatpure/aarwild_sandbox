import matplotlib.pyplot as pl
import numpy as np
import json
from pathlib import Path

def plot_surf(ax, mesh) -> None:
    UV = np.array(mesh['param_grid'])
    faces = mesh['faces']
    # ax.plot(UV[:, 0], UV[:, 1], '+', alpha=0.5)
    for face in faces:
        i1, i2, i3, i4, face_type = face
        loop = [(i1, i2), (i2, i3), (i3, i4), (i4, i1)]
        for start_idx, end_idx in loop:
            u1, v1 = UV[start_idx]
            u2, v2 = UV[end_idx]
            ax.plot([u1, u2], [v1, v2], 'k-', alpha=0.5)

def plot_pcurve(ax, mesh, color) -> None:
    print('pcurve')
    verts = mesh['vertices']
    for start_idx, end_idx in mesh['edges']:
        u1, v1 = verts[start_idx]
        u2, v2 = verts[end_idx]
        ax.plot([u1, u2], [v1, v2], '-', color=color, alpha=0.5)

def plot() -> None:
    """
    2D plot of surface mesh
    """

    with Path('_meshes.json').open() as f:
        meshes = json.load(f)
    fig = pl.figure()
    ax = fig.add_subplot(111)

    # Plot the surface mesh
    for m in meshes:
        if m['type'] == 'surface':
            plot_surf(ax, m)
            break

    # Plot the Pcurves
    colors = ['r', 'b']
    i = 0
    for m in meshes:
        if m['type'] == 'pcurve':
            plot_pcurve(ax, m, colors[i])
            i += 1

    ax.set_aspect('equal')
    pl.show()

def main() -> None:
    with Path('_meshes.json').open() as f:
        meshes = json.load(f)

    for m in meshes:
        if m['type'] == 'pcurve':
            verts = np.array(m['vertices'])
            x = verts[:, 0]
            y = verts[:, 1]

            from IPython import embed; embed(); exit(0)

if __name__ == '__main__':
    plot()
