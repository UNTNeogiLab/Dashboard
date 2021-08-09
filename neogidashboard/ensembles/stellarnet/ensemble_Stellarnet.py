import time
from array import array

import neogiinstruments
import numpy as np
import panel as pn
import param

from ..ensemblebase import EnsembleBase, Coordinate, Coordinates
from ... import utils

name = "stellarnet"


def get_calibs() -> list:
    """
    Scans for calibration files

    :return: list of all calibration files
    :rtype: list of PosixPath
    """
    return list(utils.scan_directory({"WavelengthPoweredCalib": None}).keys())


class Ensemble(EnsembleBase):
    wavstart = param.Integer(default=780)
    wavend = param.Integer(default=900)
    wavstep = param.Integer(default=2)
    pstart = param.Integer(default=0)
    pstop = param.Integer(default=10)
    pstep = param.Number(default=0.5)
    mai_time = param.Integer(default=30)
    pwait = param.Integer(default=1)
    type = name
    data = "stellarnet"
    datasets = ["Stellarnet", "V", "Vstd"]
    dimensions = {"Stellarnet": ["wavelength", "power", "emission_wavelength"], "V": ["wavelength", "power"],
                  "Vstd": ["wavelength", "power"]}
    cap_coords = {"Stellarnet": ["emission_wavelength"], "V": [], "Vstd": []}
    loop_coords = ["wavelength", "power"]
    debug = param.Boolean(default=False)
    live = False
    calibration_file = param.ObjectSelector()

    def __init__(self):
        files = get_calibs()
        if len(files) == 0:
            print("Needs calibration file ")
        self.param["calibration_file"].objects = files
        self.param["calibration_file"].default = files[0]
        super().__init__()
        self.filename = "data/stellarnet.zarr"
        self.rotator = neogiinstruments.rotator("rotator")
        self.MaiTai = neogiinstruments.MaiTai()
        self.StellarNet = neogiinstruments.StellarNet()
        self.Photodiode = neogiinstruments.Photodiode()
        self.coords = Coordinates([
            Coordinate("wavelength", "nanometer", "wavelength", step_function=self.wav_step),
            Coordinate("power", "degrees", "power", step_function=self.pow_step),
            Coordinate("emission_wavelength", "nanometers", "emission_wavelength")]
        )

    def wav_step(self, xs):
        self.MaiTai.instrument.Set_Wavelength(xs[0])
        if self.debug:
            print(f'moving to {xs[0]}')
        time.sleep(self.mai_time)
        self.pow_step(xs)
        if not self.debug:
            time.sleep(10)
        self.MaiTai.instrument.Shutter(1)
        if self.debug:
            print(f'starting loop at {xs[0]}')
        if not self.debug:
            time.sleep(5)

    def initialize(self):
        self.initialized = True
        exclude = []
        for param in self.param:
            if not param in exclude:
                self.param[param].constant = True

        self.init_vars()

    def start(self):
        self.rotator.instrument.home()

    def init_vars(self):
        self.coords["wavelength"].values = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        power = np.arange(self.pstart, self.pstop, self.pstep)
        self.coords["power"].values = power
        emission_wavelength = self.StellarNet.instrument.GetSpec()[0]
        self.emission_length = len(emission_wavelength)
        self.coords["emission_wavelength"].values = emission_wavelength
        self.pc_reverse = utils.interpolate(self.calibration_file, pwr=power)

    def pow_step(self, xs: array):
        pow = xs[1]
        wav = xs[0]
        pol = self.pc_reverse.sel(power=pow, wavelength=wav).values
        if self.debug:
            print(f"moving to {pol}")
        if -360 < pol < 360:
            self.rotator.instrument.move_abs(pol)
        time.sleep(self.pwait)

    def get_frame(self, coords):
        data = self.StellarNet.instrument.GetSpec()[1]
        V, Vstd = self.Photodiode.instrument.gather_data()
        return {"Stellarnet": data, "V": V, "Vstd": Vstd}

    def widgets(self):
        if self.initialized:
            return pn.Column(self.rotator.view, self.StellarNet.view, self.MaiTai.view, self.Photodiode.view)
        else:
            return None
