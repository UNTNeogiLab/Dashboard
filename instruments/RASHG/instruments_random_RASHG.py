from instruments.instruments_base import instruments_base
import numpy as np
import param
import panel as pn
from numba import njit
import math

pn.extension()
name = "random_RASHG"

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
    wavstart = param.Integer(default=780)
    wavend = param.Integer(default=800)
    wavstep = param.Integer(default=2)
    pol_step = param.Number(default=2, bounds=(1, 2))  # TODO: figure out how this works
    pow_start = param.Integer(default=0)
    pow_stop = param.Integer(default=5)
    pow_step = param.Integer(default=5)
    ybin = 1
    xbin = 1
    type = name
    data = "RASHG"
    dimensions = ["wavelength", "power", "Orientation", "Polarization", "x", "y"]

    def __init__(self):
        super().__init__()

    def initialize(self):

        self.initialized = True
        exclude = []
        for param in self.param:
            if not param in exclude:
                self.param[param].constant = True
        self.init_vars()
        self.coords = {
            "wavelength": {"name": "wavelength", "unit": "nanometer", "dimension": "wavelength",
                           "values": self.wavelength, "function": "none"},
            "power": {"name": "Power", "unit": "milliwatts", "dimension": "power", "values": self.pwr,
                    "function": "none"},
            "degrees": {"name": "Polarization", "unit": "degrees", "dimension": "Polarization",
                        "values": self.Polarization, "function": "none"},
            "Polarization": {"name": "Polarization", "unit": "pixels", "dimension": "Polarization",
                             "values": self.Polarization_radians, "function": "none"},
            "x_pxls": {"name": "X", "unit": "nanometer", "dimension": "x", "values": self.x_coords, "function": "none"},
            "x": {"name": "X", "unit": "micrometers", "dimension": "x", "values": self.x_mm, "function": "none"},
            "y_pxls": {"name": "Y", "unit": "pixels", "dimension": "y", "values": self.y_coords, "function": "none"},
            "y": {"name": "Y", "unit": "micrometers", "dimension": "y", "values": self.y_mm, "function": "none"},
            "Orientation": {"name": "Orientation", "unit": "?", "dimension": "Orientation", "values": self.Orientation,
                            "function": "none"},
        }
        self.cap_coords = ["x", "y"]
        self.loop_coords = ["wavelength", "power", "Orientation", "Polarization"]

    def init_vars(self):
        self.x = self.x2 - self.x1
        self.y = self.y2 - self.y1  # TODO: fix binning
        self.wavelength = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        self.pwr = np.arange(self.pow_start, self.pow_stop, self.pow_step, dtype=np.uint16)
        x = int((self.x2 - self.x1) / self.xbin)
        y = int((self.y2 - self.y1) / self.ybin)
        self.x_coords = np.arange(x, dtype=np.uint16)
        self.x_mm = np.arange(x, dtype=np.uint16) * 0.05338  # magic
        self.y_coords = np.arange(y, dtype=np.uint16)
        self.y_mm = np.arange(y, dtype=np.uint16) * 0.05338  # magic
        self.Orientation = np.arange(0, 2)
        self.Polarization = np.arange(0, 360, self.pol_step, dtype=np.uint16)
        self.Polarization_radians = np.arange(0, 360, self.pol_step, dtype=np.uint16) * math.pi / 180
        self.pwr = np.arange(self.pow_start, self.pow_stop, self.pow_step, dtype=np.uint16)

        # seperates all the variables

    def get_frame(self, xs):
        return random(self.x, self.y)

    def live(self):
        return random(self.x, self.y) * 10

    def widgets(self):
        return self.param
