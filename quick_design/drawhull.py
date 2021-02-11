import matplotlib.pyplot as pl

def draw_hull(hull, arrow_width=0.2, arrow_length=0.2):
    ax = pl.axes()
    ax.plot(hull[:, 0], hull[:, 1])
    for i in range(hull.shape[0] - 1):
        x, y = hull[i]
        dx = hull[i + 1, 0] - hull[i, 0]
        dy = hull[i + 1, 1] - hull[i, 1]
        ax.arrow(x, y, dx, dy, head_width=arrow_width, head_length=arrow_length, fc='g', ec='g')

    pl.show()

