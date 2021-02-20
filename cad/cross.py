import numpy as np

D = np.array([6, 3, 2.])
D /= np.linalg.norm(D)
r01 = np.array([1., 1., 0.5])
r02 = np.array([3., -5., 0.07])

ra1 = r01 + 2.3 * D
ra2 = r01 + 4.7 * D

rb1 = r02 + 6.8 * D
rb2 = r02 - 41. * D

from IPython import embed; embed(); exit(0)
