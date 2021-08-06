import holoviews as hv
import simple_pid
import param
import panel as pn
from . import ensemble_RASHG

name = "RASHG_PID"

hv.extension('bokeh')
raise Exception("This code doesn't even work why are you using it???")


class Ensemble(ensemble_RASHG.Ensemble):
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
            return pn.Column(super().widgets)
        else:
            return None
