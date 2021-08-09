import time

import holoviews as hv
import neogiinstruments
import numpy as np
import panel as pn
import param

from ..ensemblebase import EnsembleBase, Coordinate, Coordinates
from ... import utils

name = "RASHG"

hv.extension('bokeh')


def get_calibs() -> list:
    """
    Scans for calibration files

    :return: list of all calibration files
    :rtype: list of PosixPath
    """
    return list(utils.scan_directory({"WavelengthPoweredCalib": None}).keys())


class Ensemble(EnsembleBase):
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
    debug = param.Boolean(default=False)
    live = param.Boolean(default=True)
    colorMap = param.ObjectSelector(default="fire", objects=hv.plotting.util.list_cmaps())
    cam = neogiinstruments.camera("Camera")
    rbot, rtop, atten = [neogiinstruments.rotator(name) for name in ["rbot", "rtop", "atten"]]
    MaiTai = neogiinstruments.MaiTai("MaiTai")
    type = name
    data = "RASHG"
    dimensions = ["wavelength", "power", "Orientation", "Polarization", "x", "y"]
    cap_coords = ["x", "y"]
    loop_coords = ["wavelength", "power", "Orientation", "Polarization"]
    calibration_file = param.ObjectSelector()

    @param.depends("debug", watch=True)
    def no_wait(self):
        if self.debug:
            self.wavwait = 0
            self.escape_delay = 0
            self.exp_time = 0

    def start(self):
        print("Gathering Data, Get Out")
        self.rbot.instrument.home()
        self.rtop.instrument.home()
        self.atten.instrument.home()
        if not self.debug:
            # time.sleep(120)
            pass

    def __init__(self):
        files = get_calibs()
        if len(files) == 0:
            print("Needs calibration file ")
        self.param["calibration_file"].objects = files
        self.param["calibration_file"].default = files[0]
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
        self.coords = Coordinates(
            [
                Coordinate("wavelength", "nanometer", "wavelength", self.wavelength, self.wav_step),
                Coordinate("power", "milliwatts", "power", self.pwr, self.pow_step_func),
                Coordinate("degrees", "degrees", "Polarization", self.Polarization),
                Coordinate("Polarization", "pixels", "Polarization", self.Polarization_radians),
                Coordinate("x_pxls", "nanometer", "x", self.x_coords),
                Coordinate("x", "micrometers", "x", self.x_mm),
                Coordinate("y_pxls", "pixels", "y", self.y_coords),
                Coordinate("y", "micrometers", "y", self.y_mm),
                Coordinate("Orientation", "?", "Orientation", self.Orientation)
            ]
        )
        # self.PC, self.PCcov, self.WavPowAng, self.pc = PCFit(self.calibration_file)

    def init_vars(self):
        self.x = self.x2 - self.x1
        self.y = self.y2 - self.y1  # TODO: fix binning
        self.wavelength = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        self.pwr = np.arange(self.pow_start, self.pow_stop, self.pow_step, dtype=np.uint16)
        x = int((self.x2 - self.x1) / self.xbin)
        y = int((self.y2 - self.y1) / self.ybin)
        self.cache = self.live_call()
        self.x_coords = np.arange(x, dtype=np.uint16)
        self.x_mm = np.arange(x, dtype=np.uint16) * 0.05338  # magic
        self.y_coords = np.arange(y, dtype=np.uint16)
        self.y_mm = np.arange(y, dtype=np.uint16) * 0.05338  # magic
        self.Orientation = np.arange(0, 2)
        self.Polarization = np.arange(0, 360, self.pol_step, dtype=np.uint16)
        self.Polarization_radians = np.arange(0, 360, self.pol_step, dtype=np.uint16) * np.pi / 180
        self.pwr = np.arange(self.pow_start, self.pow_stop, self.pow_step, dtype=np.uint16)
        self.pc_reverse = utils.interpolate(self.calibration_file, self.pwr)

    def get_frame(self, coords):
        o = coords[2]
        p = coords[3]*180/np.pi
        if o == 1:
            sys_offset = 45
        else:
            sys_offset = 0
        pos = p * 180 / np.pi
        pos_top = int(pos + sys_offset)
        pos_bot = int(pos)
        if self.debug:
            print(f"Moving A to {pos_top}")
        self.rtop.instrument.move_abs(pos_top)
        if self.debug:
            print(f"Moving B to {pos_bot}")
        self.rbot.instrument.move_abs(pos_bot)
        if self.debug:
            print(f"Capturing frame")
        self.cache = self.live_call()
        return {"ds1": self.cache}

    def pow_step_func(self, xs):
        pw = xs[1]
        w = xs[0]
        atten_pos = self.pc_reverse.sel(wavelength=w, power=pw)  # technically can interp here again but don't need to
        if -360 < atten_pos < 360:
            self.atten.instrument.move_abs(atten_pos)

    def graph(self, live=False):
        if live:
            self.cache = self.live_call()
        output = self.cache
        self.zdim = hv.Dimension('Intensity', range=(output.min(), output.max()))
        opts = [hv.opts.Image(colorbar=True, cmap=self.colorMap, tools=['hover'], framewise=True, logz=True)]
        return hv.Image(output, vdims=self.zdim).opts(opts).redim(x=self.xDim, y=self.yDim)

    def live_call(self):
        return self.cam.instrument.get_frame(exp_time=self.exp_time)

    def wav_step(self, xs):
        time.sleep(self.wavwait)
        self.MaiTai.instrument.Set_Wavelength(xs[0])
        self.pow_step_func(xs)

    def widgets(self):
        if self.initialized:
            return pn.Column(self.atten.view, self.rbot.view, self.rtop.view, self.cam.view, self.MaiTai.view)
        else:
            return None
