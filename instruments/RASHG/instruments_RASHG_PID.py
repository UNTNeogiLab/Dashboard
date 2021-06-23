import math

import elliptec
import numpy as np
import panel
from pyvcam import pvc
from pyvcam.camera import Camera
from .rotator import rotator
from .instruments_base import instruments_base
import neogiinstruments
import simple_pid
import time
import param
name = "RASHG_PID"


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
    type = name
    data = "RASHG"
    dimensions = ["wavelength", "power", "Orientation", "Polarization", "x", "y"]
    pid_time = param.Number(default=1)
    pid = simple_pid.PID(sample_time= sample_time)
    def start(self):
        print("Gathering Data, Get Out")
        if not self.debug:
            time.sleep(120)

    def __init__(self):
        super().__init__()

    def init_cam(self):
        pvc.init_pvcam()  # Initialize PVCAM
        try:
            cam = next(Camera.detect_camera())  # Use generator to find first camera
            cam.open()  # Open the camera.
            if cam.is_open:
                print("Camera open")
        except:
            raise Exception("Error: camera not found")
        return cam

    def pid_step(self):
        control = self.pid(value)
        self.atten.move_abs(control)
    def initialize(self):
        self.initialized = True
        exclude = []
        for param in self.param:
            if not param in exclude:
                self.param[param].constant = True
        self.cam = self.init_cam()

        self.rbot, self.rtop = [rotator(i, type="K10CR1") for i in ["55001000", "55114554", "55114654"]]
        self.atten = rotator("DK0AHAJZ",type="elliptec")
        self.cam.roi = (self.x1, self.x2, self.y1, self.y2)
        self.cam.binning = (self.xbin, self.ybin)
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
        self.cap_coords = ["x", "y"]
        self.loop_coords = ["wavelength", "power", "Orientation", "Polarization"]
        #do something with the PID
        panel.state.add_periodic_callback(self.pid,self.pid_time)
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
        self.rtop.moveabs(pos_top)
        if self.debug:
            print(f"Moving B to {pos_bot}")
        self.rbot.moveabs(pos_bot)
        if self.debug:
            print(f"Capturing frame")
        return self.cam.get_frame(exp_time=self.exp_time)

    def live(self):
        return self.cam.get_frame(exp_time=self.exp_time)

    def wav_step(self, xs):
        time.sleep(self.wavwait)

    def widgets(self):
        return self.param

