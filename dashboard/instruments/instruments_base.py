import param


class instruments_base(param.Parameterized):
    initialized = param.Boolean(default=False, precedence=-1)  # dummy variable to make code work
    type = "base"
    title = param.String(default="Power/Wavelength dependent RASHG")
    filename = param.String(default="data/testfolder.zarr")
    datasets = ["ds1"]
    live = True
    gather = True
    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def get_frame(self, xs):
        pass

    def live(self):
        pass

    def widgets(self):
        return self.param

    def start(self):
        pass

    def stop(self):
        pass

    def graph(self, live=False):
        return None
