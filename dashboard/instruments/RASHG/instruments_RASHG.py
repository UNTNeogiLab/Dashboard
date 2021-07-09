import math
import holoviews as hv
import numpy as np
import neogiinstruments
from dashboard.instruments.instruments_base import instruments_base
import time
import param
import panel as pn
name = "RASHG"

hv.extension('bokeh')

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
    xbin = param.Integer(default=1)
    ybin = param.Integer(default=1)  # TODO add bounds
    exp_time = param.Number(default=10000)
    escape_delay = param.Integer(default=120)  # should beep at 45
    wavwait = param.Number(default=5)
    debug = param.Boolean(default=True)
    colorMap = param.ObjectSelector(default="fire", objects=hv.plotting.util.list_cmaps())
    cam = neogiinstruments.camera("Camera")
    rbot, rtop, atten = [neogiinstruments.rotator(name) for name in ["rbot", "rtop", "atten"]]
    type = name
    data = "RASHG"
    dimensions = ["wavelength", "power", "Orientation", "Polarization", "x", "y"]
    cap_coords = ["x", "y"]
    loop_coords = ["wavelength", "power", "Orientation", "Polarization"]

    def start(self):
        print("Gathering Data, Get Out")
        if not self.debug:
            time.sleep(120)

    def __init__(self):
        super().__init__()
        self.xDim = hv.Dimension('x', unit="micrometers")
        self.yDim = hv.Dimension('y', unit="micrometers")

    def initialize(self):
        self.initialized = True
        exclude = []
        for param in self.param:
            if not param in exclude:
                self.param[param].constant = True

        self.cam.instrument.roi(self.x1, self.x2, self.y1, self.y2)
        self.cam.instrument.binning(self.xbin, self.ybin)
        if self.xbin != self.ybin:
            print('X-bin and Y-bin must be equal, probably')
        self.init_vars()
        self.coords = {
            "wavelength": {"name": "wavelength", "unit": "nanometer", "dimension": "wavelength",
                           "values": self.wavelength, "function": self.wavstep},
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

    def init_vars(self):
        self.x = self.x2 - self.x1
        self.y = self.y2 - self.y1  # TODO: fix binning
        self.wavelength = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        self.pwr = np.arange(self.pow_start, self.pow_stop, self.pow_step, dtype=np.uint16)
        x = int((self.x2 - self.x1) / self.xbin)
        y = int((self.y2 - self.y1) / self.ybin)
        self.cache = self.live()
        self.x_coords = np.arange(x, dtype=np.uint16)
        self.x_mm = np.arange(x, dtype=np.uint16) * 0.05338  # magic
        self.y_coords = np.arange(y, dtype=np.uint16)
        self.y_mm = np.arange(y, dtype=np.uint16) * 0.05338  # magic
        self.Orientation = np.arange(0, 2)
        self.Polarization = np.arange(0, 360, self.pol_step, dtype=np.uint16)
        self.Polarization_radians = np.arange(0, 360, self.pol_step, dtype=np.uint16) * math.pi / 180
        self.pwr = np.arange(self.pow_start, self.pow_stop, self.pow_step, dtype=np.uint16)

    def get_frame(self, xs):
        o = xs[2]
        p = xs[3]
        if o == 1:
            sys_offset = 45
        else:
            sys_offset = 0
        pos = p * 90 / np.pi
        pos_top = pos + sys_offset
        pos_bot = pos
        if self.debug:
            print(f"Moving A to {pos_top}")
        self.rtop.instrument.moveabs(pos_top)
        if self.debug:
            print(f"Moving B to {pos_bot}")
        self.rbot.instrument.moveabs(pos_bot)
        if self.debug:
            print(f"Capturing frame")
        self.cache = self.live()
        return {"ds1": self.cache}

    def graph(self, live=False):
        if live:
            self.cache = self.live()
        output = self.cache
        self.zdim = hv.Dimension('Intensity', range=(output.min(), output.max()))
        opts = [hv.opts.Image(colorbar=True, cmap=self.colorMap, tools=['hover'], framewise=True, logz=True)]
        return hv.Image(output, vdims=self.zdim).opts(opts).redim(x=self.xDim, y=self.yDim)

    def live(self):
        return self.cam.instrument.get_frame(exp_time=self.exp_time)

    def wav_step(self, xs):
        time.sleep(self.wavwait)

    def widgets(self):
        if self.initialized:
            return pn.Column(self.atten.view,self.rbot.view,self.rtop.view,self.cam.view)
        else:
            return None
