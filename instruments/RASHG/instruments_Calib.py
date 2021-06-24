import numpy as np
import time

from instruments.instruments_base import instruments_base
import param
from neogiinstruments.MaiTai import MaiTai
from neogiinstruments.Photodiode import Photodiode
from neogiinstruments.PowerMeter import PowerMeter
from rotator import rotator

name = "WavelengthPoweredCalib"


class instruments(instruments_base):
    wavstart = param.Integer(default=780)
    wavend = param.Integer(default=800)
    wavstep = param.Integer(default=2)
    pstart = param.Integer(default=0)
    pstop = param.Integer(default=10)
    pstep = param.Number(default=0.5)
    pwait = param.Integer(default=1)
    mai_time = param.Integer(default=30)
    dimensions = ["wavelength", "power", "Orientation", "Polarization", "x", "y"]
    type = name
    data = "WavelengthPoweredCalib"
    dimensions = ["wavelength", "Polarization"]
    cap_coords = []
    loop_coords = ["wavelength", "Polarization"]
    datasets = ["Pwr", "Pwrstd", "Vol", "Volstd"]

    def stop(self):
        self.MaiTai.MaiTai.write('OFF')

    def __init__(self):
        super().__init__()
        self.param["filename"].default = "calib/WavelengthPowerCalib"

    def wav_step(self, xs):
        self.MaiTai.MoveWav(xs[0])
        print(f'moving to {xs[0]}')
        time.sleep(self.mai_time)
        self.MaiTai.Shutter(1)
        print(f'starting loop at {xs[0]}')
        self.pol_step(self.pstart - self.pstep)
        print("Homing")
        self.rotator.home()
        time.sleep(5)
        print('Homing finished')

    def initialize(self):
        self.MaiTai = MaiTai()
        self.PowerMeter = PowerMeter()
        self.rotator = rotator("DK0AHAJZ", type="elliptec")

    def init_vars(self):
        self.wavelength = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        self.Polarization = np.arange(self.pstart, self.pstop + self.pstep, self.pstep)

    def pol_step(self, xs):
        pol = xs[1]
        self.rotator.move_abs(pol)
        time.sleep(self.pwait)

    def get_frame(self, xs):
        p = self.PowerMeter.PowAvg()
        Pwr = p[0]
        Pwrstd = p[1]
        V, Vstd = Photodiode()
        return {"Pwr": Pwr, "Pwrstd": Pwrstd, "Vol": V, "Volstd": Vstd}
