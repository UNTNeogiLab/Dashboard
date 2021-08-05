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
        """
        Initializes the instrument. Runs when you hit confirm
        :return:
        """
        pass

    def get_frame(self, coords):
        """
        Captures the frame
        :param coords: list of data in order of loop_coords
        :return: data
        """
        pass

    def widgets(self):
        """
        Widgets to pass to dashboard
        :return:
        """
        return self.param

    def start(self):
        """
        Any functions to run at start
        :return:
        """
        pass

    def stop(self):
        """
        Any functions to run at stop
        :return:
        """
        pass

    def graph(self, live=False):
        """
        returns a graph
        :param live: whether or not it is a live view
        :type live: bool
        :return:
        """
        return None
