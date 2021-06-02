import numpy as np

from .instruments_base import instruments_base
from . import RASHG_functions as RASHG
import time
import param


class instruments(instruments_base):
    x1 = param.Integer(default=0, bounds=(0, 2047))
    x2 = param.Integer(default=100, bounds=(0, 2047))
    y1 = param.Integer(default=0, bounds=(0, 2047))
    y2 = param.Integer(default=100, bounds=(0, 2047))
    xbin = param.Integer(default=1)
    ybin = param.Integer(default=1) #TODO add bounds
    exp_time = param.Number(default=10000)
    escape_delay = param.Integer(default=120)  # should beep at 45
    wavwait = param.Number(default=5)
    debug=param.Boolean(default=True)
    type = "RASHG"
    def __init__(self):
        super().__init__()

    def initialize(self):
        params = ["x1", "x2", "y1", "y2", "exp_time", "escape_delay", "wavwait","xbin","ybin"]  # list of parameters to lock
        for param in params:
            self.param[param].constant = True
        self.initialized = True
        self.cam, self.rbot, self.rtop, self.atten = RASHG.InitializeInstruments()
        self.cam.roi = (self.x1, self.x2, self.y1, self.y2)
        self.cam.binning = (self.xbin, self.ybin)
        if self.xbin != self.ybin:
            print('X-bin and Y-bin must be equal, probably')

    def get_frame(self, o, p):
        if o == 1:
            sys_offset = 45
        else:
            sys_offset = 0
        pos = p*90/np.pi
        pos_top = pos + sys_offset
        pos_bot = pos
        if self.debug:
            print(f"Moving A to {pos_top}")
        self.rtop.moveabs(pos_top)
        if self.debug:
            print(f"Moving B to {pos_bot}")
        self.rbot.moveabs(pos_bot)
        if self.debug:
            print(f"Capturing frame")
        return self.cam.get_frame(exp_time=self.exp_time)

    def live(self):
        return self.cam.get_frame(exp_time=self.exp_time)

    def wav_step(self):
        time.sleep(self.wavwait)

    def widgets(self):
        return self.param
