import numpy as np
import cv2
from aarwild_quick_design.scene import Scene, DefaultScene
from aarwild_quick_design.constants import Constants
from aarwild_utils.img import pad_border
import matplotlib.pyplot as pl


img = cv2.imread('img.jpg')
scene = DefaultScene(img)
scene.build()
from IPython import embed; embed(); exit(0)
