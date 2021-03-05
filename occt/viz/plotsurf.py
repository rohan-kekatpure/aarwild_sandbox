import json
import matplotlib.pyplot as pl
from pathlib import Path

with Path('../build/_surface.json').open() as f:
    surf_info = json.load(f)

face = surf_info['FACE']
outer_wire = face['outer_pcurve']
inner_wires = face['inner_pcurves']

# Plot outer wire
fig = pl.figure(figsize=(10, 10))
ax = fig.add_subplot(111)

ax.plot(outer_wire['U'], outer_wire['V'], 'bx-')

for pcurve in inner_wires:
    ax.plot(pcurve['U'], pcurve['V'], 'rx-')

ax.set_aspect('equal')

pl.show()

