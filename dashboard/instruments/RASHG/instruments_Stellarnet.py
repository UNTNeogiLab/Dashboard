import numpy as np
import time
from ... import utils
from dashboard.instruments.instruments_base import instruments_base
import param
import neogiinstruments
import panel as pn

name = "Stellarnet"


def get_calibs() -> list:
    """
    Scans for calibration files

    :return: list of all calibration files
    :rtype: list of PosixPath
    """
    return list(utils.getDir({"WavelengthPoweredCalib": None}).keys())


class instruments(instruments_base):
    wavstart = param.Integer(default=780)
    wavend = param.Integer(default=800)
    wavstep = param.Integer(default=2)
    pstart = param.Integer(default=0)
    pstop = param.Integer(default=10)
    pstep = param.Number(default=0.5)
    type = name
    data = "Stellarnet"
    dimensions = ["power"]
    cap_coords = []
    loop_coords = ["wavelength", "power"]
    debug = param.Boolean(default=False)
    live = False
    files = get_calibs()
    if len(files) is 0:
        print("Needs calibration file ")
    calibration_file = param.ObjectSelector(objects=files, default=files[0])

    def __init__(self):
        super().__init__()
        self.filename = "calib/WavelengthPowerCalib.zarr"
        self.rotator = neogiinstruments.rotator("rotator")
        self.StellarNet = neogiinstruments.StellarNet()

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
            "power": {"name": "Polarization", "unit": "degrees", "dimension": "Polarization",
                      "values": self.power, "function": self.pow_step},
        }
        pc_reverse = utils.interpolate()

    def init_vars(self):
        self.wavelength = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        self.power = np.arange(self.pstart, self.pstop, self.pstep)

    def pow_step(self, xs):
        pow = xs[1]
        pol = pc_reverse
        if self.debug:
            print(f"moving to {pol}")
        self.rotator.instrument.move_abs(pol)
        time.sleep(self.pwait)

    def get_frame(self, xs):
        data = self.StellarNet
        return {"ds1"}

    def widgets(self):
        if self.initialized:
            return pn.Column(self.rotator.view, self.PowerMeter.view, self.Photodiode.view, self.MaiTai.view)
        else:
            return None
