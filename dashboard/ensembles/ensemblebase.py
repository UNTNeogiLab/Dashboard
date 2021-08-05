"""
Specifies base class
"""
import param


class EnsembleBase(param.Parameterized):
    """
    Base class for all ensembles. Other instrument groups should inherit from this
    """
    initialized = param.Boolean(default=False, precedence=-1)  # dummy variable to make code work
    type = "base"
    title = param.String(default="Power/Wavelength dependent RASHG")
    filename = param.String(default="data/testfolder.zarr")
    datasets = ["ds1"]
    live = True
    gather = True

    def initialize(self):
        pass

    def get_frame(self, xs):
        pass

    def live_call(self):
        pass

    def widgets(self):
        return self.param

    def start(self):
        pass

    def stop(self):
        pass

    def graph(self, live=False):
        return None
