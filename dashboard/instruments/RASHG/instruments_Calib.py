import numpy as np
import time

from dashboard.instruments.instruments_base import instruments_base
import param
import neogiinstruments
import panel as pn
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
    live = False

    def stop(self):
        self.MaiTai.instrument.MaiTai.write('OFF')

    def __init__(self):
        super().__init__()
        self.param["filename"].default = "calib/WavelengthPowerCalib"
        self.rotator = neogiinstruments.rotator("rotator")
        self.MaiTai = neogiinstruments.MaiTai()
        self.PowerMeter = neogiinstruments.PowerMeter()
        self.Photodiode = neogiinstruments.Photodiode()
    def wav_step(self, xs):
        self.MaiTai.instrument.Set_Wavelength(xs[0])
        print(f'moving to {xs[0]}')
        time.sleep(self.mai_time)
        self.MaiTai.instrument.MaiTai.Shutter(1)
        print(f'starting loop at {xs[0]}')
        self.pol_step(self.pstart - self.pstep)
        print("Homing")
        self.rotator.instrument.home()
        time.sleep(5)
        print('Homing finished')

    def initialize(self):
        self.initialized = True
        exclude = []
        for param in self.param:
            if not param in exclude:
                self.param[param].constant = True

        self.init_vars()
        self.coords = {
            "wavelength": {"name": "wavelength", "unit": "nanometer", "dimension": "wavelength",
                           "values": self.wavelength, "function": self.wav_step},
            "Polarization": {"name": "Polarization", "unit": "degrees", "dimension": "Polarization",
                             "values": self.Polarization, "function": self.pol_step},
        }

    def init_vars(self):
        self.wavelength = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        self.Polarization = np.arange(self.pstart, self.pstop + self.pstep, self.pstep)

    def pol_step(self, xs):
        pol = xs[1]
        self.rotator.instrument.move_abs(pol)
        time.sleep(self.pwait)

    def get_frame(self, xs):
        p = self.PowerMeter.instrument.PowAvg()
        Pwr = p[0]
        Pwrstd = p[1]
        V, Vstd = self.Photodiode.instrument.gather_data()
        return {"Pwr": Pwr, "Pwrstd": Pwrstd, "Vol": V, "Volstd": Vstd}

    def widgets(self):
        if self.initialized:
            return pn.Column(self.rotator.view,self.PowerMeter.view,self.Photodiode.view,self.MaiTai.view)
        else:
            return None
