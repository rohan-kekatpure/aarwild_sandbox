import matplotlib.pyplot as pl
import numpy as np

with open('FACE218.csv') as f:
    lines = f.read().splitlines()

vals = []
for l in lines:
    u, v, state = l.split(',')
    u = float(u)
    v = float(v)
    s = state == 'IN'
    vals.append([u, v, s])

vals = np.array(vals)
idx = vals[:, 2] == 1.
in_pts = vals[:, :2][idx]
out_pts = vals[:, :2][~idx]

fig = pl.figure(figsize=(10, 10))
ax = fig.add_subplot(111)
ax.plot(in_pts[:, 0], in_pts[:, 1], 'g+', ms=2)
# ax.plot(out_pts[:, 0], out_pts[:, 1], 'r.', ms=2)
ax.set_aspect('equal')
pl.show()
# from IPython import embed; embed(); exit(0)

