"""
houses gui class
"""
import sys
import time
import xarray as xr
import numpy as np
import panel as pn
import param
from numba import njit
import os
import zarr
from tqdm.contrib.itertools import product

compressor = zarr.Blosc(cname="zstd", clevel=3, shuffle=2)


@njit(cache=True)
def compare(coords, dim_cache):
    """
    Get first different dimension
    :param coords: new coordinates
    :param dim_cache: old coordinates
    :return: index of changed coordinate
    """
    for i, coord in enumerate(coords):
        if coord > dim_cache[i]:
            return i
    raise Exception("Coordinates identical")


class Gui(param.Parameterized):
    """
    Essentially the backbone of the data collection
    Loops through dimensions
    """
    c_pol = param.Number(default=0, precedence=-1)
    institution = param.String(default="University of North Texas")
    sample = param.String(default="MoS2")
    GUIupdate = param.Boolean(default=True)
    button = pn.widgets.Button(name='Gather Data', button_type='primary')
    button2 = pn.widgets.Button(name='refresh', button_type='primary')
    live = param.Boolean(default=False, precedence=-1)
    refresh = 5  # refresh every 5 seconds #make it a parameter
    live_refresh = param.Integer(default=5)
    dim_cache = np.array([0, 0, 0, 0])

    def __init__(self):
        super().__init__()
        self.callback = pn.state.add_periodic_callback(self.live_view, period=self.live_refresh * 1000, start=False)
        self.button.disabled = True
        self.button2.disabled = True

    def initialize(self, ensemble):
        """
        Initializes the GUI. Sets all parameters to constant and allows the user to start the expirement. If the live
        view is enabled, start the callback.

        :param ensemble:
        :return: None
        """
        self.ensemble = ensemble
        self.init_vars()
        if self.ensemble.gather:
            self.button.disabled = False
        self.button.on_click(self.gather_data)
        if self.ensemble.live:
            self.live = True
            self.callback.start()
        exclude = ["cPol", "live"]
        for parameter in self.param:
            if not parameter in exclude:
                self.param[parameter].constant = True

    def init_vars(self):
        """
        Initialize all the variables. Should probably be in initialize
        :return:
        """
        # populate metadata
        self.attrs = {
            "title": self.ensemble.title,
            "institution": self.institution,
            "sample": self.sample,
            "source": self.ensemble.type,
            "data_type": self.ensemble.data,
            "time": time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),
            "fit_version": 0,
            "data_version": 2
        }
        self.coords = {}
        for coord in self.ensemble.coords:
            values = self.ensemble.coords[coord]
            self.attrs[coord] = values["unit"]
            self.coords[coord] = ([values["dimension"]], values["values"])
        # data.date = str(datetime.date.today()) #out of date
        # create variables; in this case, the only dependent variable is 'shg',
        # which is the shg intensity along the specified dimensions
        # populate coordinate dimensions

        zero_array = [self.ensemble.coords[coord]["values"].size for coord in self.ensemble.dimensions]
        zero_array[0] = 1
        self.zeros = xr.DataArray(np.zeros(zero_array), dims=self.ensemble.dimensions)
        self.datasets = {dataset: (self.ensemble.dimensions, self.zeros.copy(deep=True), self.attrs) for dataset in
                         self.ensemble.datasets}
        self.encoders = {dataset: {"compressor": compressor} for dataset in self.ensemble.datasets}
        # Get filename
        fname = self.ensemble.filename
        i = 2
        while os.path.isdir(self.ensemble.filename):
            self.ensemble.param["filename"].constant = False
            self.ensemble.filename = fname.replace(".zarr", f"{i}.zarr")
            i += 1
            print(f"Zarr store exists, trying {self.ensemble.filename}")
            self.ensemble.param["filename"].constant = True
        os.makedirs(self.ensemble.filename)

    def gather_data(self, event=None):
        """
        Starts data gathering loop. Iterates over self.instruments.loop_coords
        :param event: needed for button
        :return:
        """
        if self.ensemble.live:
            self.callback.stop()
        self.button.disabled = True
        self.button2.disabled = True
        self.live = False
        first = 0
        ranges = [self.ensemble.coords[coord]["values"] for coord in self.ensemble.loop_coords]
        self.ensemble.start()
        '''
        The infinite loop:
        not because it is an actual infinite loop but because it supports a theoretical infinite number of dimensions
        memory limits nonwithstanding
        The generator should be lazy and not overflow your memory. Theoretically.
        '''
        try:
            self.mask = {dim: min(self.ensemble.coords[dim]["values"]) for dim in self.ensemble.loop_coords}
        except ValueError:
            print("Empty list or 0 pol step. Check your parameters")
            sys.exit()
        for coords in product(*ranges):
            dim, dim_num = self.find_dim(coords)
            if dim_num == 0:
                if first == 0:
                    first = 1
                elif first == 1:
                    self.data.to_zarr(self.ensemble.filename, encoding=self.encoders, consolidated=True)
                    first += 1
                else:
                    self.data.to_zarr(self.ensemble.filename, append_dim=self.ensemble.loop_coords[0])
                self.coords[self.ensemble.loop_coords[0]] = ([dim], [coords[0]])  # update 1st coord after saving
                self.data = xr.Dataset(
                    data_vars=self.datasets,
                    coords=self.coords,
                    attrs=self.attrs
                )
            self.mask[dim] = coords[dim_num]
            function = self.ensemble.coords[dim]["function"]
            if not function == "none":
                function(coords)
            data = self.ensemble.get_frame(coords)
            for dataset in self.ensemble.datasets:
                self.data[dataset].loc[self.mask] = xr.DataArray(data[dataset],
                                                                 dims=self.ensemble.cap_coords)
            if self.GUIupdate:
                self.c_pol += 1  # refresh the GUI
        self.data.to_zarr(self.ensemble.filename, append_dim=self.ensemble.loop_coords[0])
        self.ensemble.stop()
        print("Finished")
        self.c_pol = self.c_pol + 1
        self.data.close()
        sys.exit()

    def find_dim(self, xs):
        """
        finds the changed dimension and the index of the changed dimension
        :param xs:
        :return: changed dimension name and index of changed dimension
        """
        typed_a = np.array(xs, dtype=np.float64)
        dim = compare(typed_a, self.dim_cache)
        self.dim_cache = typed_a
        return self.ensemble.loop_coords[dim], dim

    def live_view(self):
        """
        Actually all this does is update the c_pol parameter to make param update the live view
        :return:
        """
        if self.live:
            if self.ensemble.debug:
                print("Updating live view")
            self.c_pol = self.c_pol + 1

    @param.depends('cPol')
    def graph(self):
        """
        returns the graph from the ensemble

        :return:
        """
        return self.ensemble.graph(live=self.live)

    def widgets(self) -> pn.Column:
        """
        All this does now is display the Gather Data button
        :return:
        """
        return pn.Column(self.button)

    def output(self) -> pn.Pane:
        """
        Returns the graph from the ensemble
        :return:
        """
        if self.ensemble.live:
            return pn.Pane(self.graph)
        else:
            return None

    def stop(self):
        """
        Stops the server
        :return:
        """
        if self.ensemble.live:
            self.callback.stop()
        print("shutting down live view")  # doesn't currently  work
