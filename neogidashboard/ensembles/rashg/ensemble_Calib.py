import time

import neogiinstruments
import numpy as np
import panel as pn
import param

from ..ensemblebase import EnsembleBase, Coordinate, Coordinates

name = "WavelengthPoweredCalib"


class Ensemble(EnsembleBase):
    wavstart = param.Integer(default=780)
    wavend = param.Integer(default=800)
    wavstep = param.Integer(default=2)
    pstart = param.Integer(default=0)
    pstop = param.Integer(default=10)
    pstep = param.Number(default=0.5)
    pwait = param.Integer(default=1)
    mai_time = param.Integer(default=30)
    type = name
    data = "WavelengthPoweredCalib"
    dimensions = ["wavelength", "Polarization"]
    cap_coords = []
    loop_coords = ["wavelength", "Polarization"]
    datasets = ["Pwr", "Pwrstd", "Vol", "Volstd"]
    debug = param.Boolean(default=False)
    live = False
    def start(self):
        self.rotator.home()
    def __init__(self):
        super().__init__()
        self.filename = "calib/WavelengthPowerCalib.zarr"
        self.rotator = neogiinstruments.rotator("rotator")
        self.MaiTai = neogiinstruments.MaiTai()
        self.PowerMeter = neogiinstruments.PowerMeter()
        self.Photodiode = neogiinstruments.Photodiode()

    def wav_step(self, xs):
        if self.debug:
            print(f'moving to {xs[0]}')
        self.MaiTai.instrument.Set_Wavelength(xs[0])
        time.sleep(self.mai_time)
        self.pol_step(xs)
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
        for parameter in self.param:
            if parameter not in exclude:
                self.param[parameter].constant = True

        self.init_vars()
        self.coords = Coordinates(
            [
                Coordinate("wavelength", "nanometer", "wavelength", self.wavelength, self.wav_step),
                Coordinate("Polarization", "degrees", "Polarization", self.Polarization, self.pol_step)
            ]
        )

    def init_vars(self):
        self.wavelength = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        self.Polarization = np.arange(self.pstart, self.pstop, self.pstep)

    def pol_step(self, xs):
        pol = xs[1]
        if self.debug:
            print(f"moving to {pol}")
        self.rotator.instrument.move_abs(pol)
        time.sleep(self.pwait)

    def get_frame(self, coords):
        if self.debug:
            print("Gathering power data")
        p = self.PowerMeter.instrument.PowAvg()
        Pwr = p[0]
        Pwrstd = p[1]
        if self.debug:
            print("Gathering Photodiode data")
        V, Vstd = self.Photodiode.instrument.gather_data()
        if self.debug:
            print(f"Pwr: {Pwr}, Pwrstd: {Pwrstd}, Vol: {V}, Volstd: {Vstd}")
        return {"Pwr": Pwr, "Pwrstd": Pwrstd, "Vol": V, "Volstd": Vstd}

    def widgets(self):
        if self.initialized:
            return pn.Column(self.rotator.view, self.PowerMeter.view, self.Photodiode.view, self.MaiTai.view)
        else:
            return None
