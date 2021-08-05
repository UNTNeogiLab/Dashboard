import math
import holoviews as hv
import numpy as np
import neogiinstruments
from dashboard.instruments.ensemblebase import EnsembleBase
import simple_pid
import time
import param
import panel as pn
from . import ensemble_RASHG

name = "RASHG_PID"

hv.extension('bokeh')


class Ensemble(ensemble_RASHG.ensemble):
    pid_time = param.Number(default=1)
    pid = simple_pid.PID()

    def __init__(self):
        super().__init__()

    def pid_step(self):
        control = self.pid(value)
        self.atten.move_abs(control)

    def initialize(self):
        super().initialize()
        self.pid.sample_time = self.pid_time
        pn.state.add_periodic_callback(self.pid_step, self.pid_time)

    def widgets(self):
        if self.initialized:
            return pn.Column(super().widgets) #todo include the additonal instruments
        else:
            return None
