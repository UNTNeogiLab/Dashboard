from .instruments_base import instruments_base
import numpy as np
import param
import panel as pn
from numba import njit

pn.extension()


@njit(cache=True)
def zeros(x, y):
    return np.zeros((x, y))


@njit(cache=True)
def random(x, y):
    return np.random.rand(x, y)


class instruments(instruments_base):
    x1 = param.Integer(default=0, bounds=(0, 2047))
    x2 = param.Integer(default=100, bounds=(0, 2047))
    y1 = param.Integer(default=0, bounds=(0, 2047))
    y2 = param.Integer(default=100, bounds=(0, 2047))
    ybin = 1
    xbin = 1
    type = "random"

    def __init__(self):
        super().__init__()

    def initialize(self):
        self.x = self.x2 - self.x1
        self.y = self.y2 - self.y1
        self.initialized = True
        params = ["x1", "x2", "y1", "y2"]
        for param in params:
            self.param[param].constant = True

    def get_frame(self, o, p):
        return random(self.x, self.y)

    def live(self):
        return zeros(self.x, self.y)

    def widgets(self):
        return self.param
