import json
import matplotlib.pyplot as pl
from pathlib import Path

with Path('../build/_surfaces.json').open() as f:
    surf_info = json.load(f)

for face_id, face_info in surf_info.items():
    print(face_id)
    outer_wire = face_info['outer_pcurve']
    inner_wires = face_info['inner_pcurves']

    # Plot outer wire
    pl.close('all')
    fig = pl.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)

    ax.plot(outer_wire['U'], outer_wire['V'], 'bx-')
    for pcurve in inner_wires:
        ax.plot(pcurve['U'], pcurve['V'], 'rx-')

    ax.set_aspect('equal')
    fig.savefig(f'./_images/_{face_id}.png')
