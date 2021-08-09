"""
houses gui class
"""
import os
import sys
import time

import numpy as np
import panel as pn
import param
import stellarnet
import xarray as xr
import zarr
from numba import njit
from tqdm.contrib.itertools import product

from .ensemblebase import EnsembleBase, Coordinates

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
    ensemble: EnsembleBase
    coordinates: Coordinates
    c_pol = param.Number(default=0, precedence=-1)
    institution = param.String(default="University of North Texas")
    sample = param.String(default="MoS2")
    GUIupdate = param.Boolean(default=True)
    button = pn.widgets.Button(name='Gather Data', button_type='primary')
    live = param.Boolean(default=False, precedence=-1)
    refresh = 5  # refresh every 5 seconds #make it a parameter
    live_refresh = param.Integer(default=5)
    dim_cache = np.array([0, 0, 0, 0])
    ensembles = param.ObjectSelector()  # Initializes a blank object selector, fills it in later
    confirmed = param.Boolean(default=False, precedence=-1)
    button2 = pn.widgets.Button(name='Confirm', button_type='primary')
    cap_coords: dict
    attrs: dict
    datasets: dict
    mask: dict
    encoders: dict
    data: xr.Dataset

    def __init__(self, ensembles):
        self.ensemble_classes = ensembles
        ensembles = list(ensembles.keys())
        i = 0
        while i < len(ensembles):
            try:
                self.param["ensembles"].default = ensembles[i]
            except stellarnet.stellarnet.NotFoundError:
                print("Skipping stellarnet due to lack of stellarnet")
            except:
                print(f"{ensembles[i]} failed")
            i += 1
        self.param["ensembles"].objects = ensembles
        super().__init__()
        self.callback = pn.state.add_periodic_callback(self.live_view, period=self.live_refresh * 1000, start=False)
        self.button.disabled = True
        self.load()
        self.button2.on_click(self.initialize)

    @param.depends('ensembles', watch=True)
    def load(self) -> None:
        """
        Loads selected ensemble
        :rtype: None
        """
        self.confirmed = False
        try:
            self.ensemble = self.ensemble_classes[self.ensembles].Ensemble()
        except stellarnet.NotFoundError:
            print("You can't run stellarnet without stellarnet")

    def initialize(self, event=None):
        """
        Initializes the GUI. Sets all parameters to constant and allows the user to start the expirement. If the live
        view is enabled, start the callback.

        :return: None
        """
        self.ensemble.initialize()
        self.init_vars()
        self.button2.disabled = True
        self.confirmed = True
        if self.ensemble.gather:
            self.button.disabled = False
        self.button.on_click(self.gather_data)
        if self.ensemble.live:
            self.live = True
            self.callback.start()
        exclude = ["c_pol", "live"]
        for parameter in self.param:
            if parameter not in exclude:
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
        self.coordinates = self.ensemble.coords
        self.coords = {coord.name: ([coord.dimension], coord.values) for coord in self.coordinates}
        for coord in self.coordinates:
            self.attrs[coord.name] = coord.unit

        # data.date = str(datetime.date.today()) #out of date
        # create variables; in this case, the only dependent variable is 'shg',
        # which is the shg intensity along the specified dimensions
        # populate coordinate dimensions
        dimensions = self.ensemble.dimensions
        if type(dimensions) is list:
            dimensions = {dataset: dimensions for dataset in self.ensemble.datasets}
        self.cap_coords = self.ensemble.cap_coords
        if type(self.cap_coords) is list:
            self.cap_coords = {dataset: self.cap_coords for dataset in self.ensemble.datasets}
        zeros = {}
        for dataset in self.ensemble.datasets:
            zero_array = [self.ensemble.coords[coord].values.size for coord in dimensions[dataset]]
            zero_array[0] = 1
            zeros[dataset] = xr.DataArray(np.zeros(zero_array), dims=dimensions[dataset])
        self.datasets = {dataset: (dimensions[dataset], zeros[dataset], self.attrs) for dataset in
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
        ranges = [self.ensemble.coords[coord].values for coord in self.ensemble.loop_coords]
        self.ensemble.start()
        '''
        The infinite loop:
        not because it is an actual infinite loop but because it supports a theoretical infinite number of dimensions
        memory limits nonwithstanding
        The generator should be lazy and not overflow your memory. Theoretically.
        '''
        try:
            self.mask = {dim: min(self.ensemble.coords[dim].values) for dim in self.ensemble.loop_coords}
        except ValueError:
            print("Empty list or 0 pol step. Check your parameters")
            sys.exit()
        for coords in product(*ranges):
            dim, dim_num = self.find_dim(coords)
            if dim_num == 0:
                if first == 0:
                    first = 1
                elif first == 1:
                    self.data.to_zarr(self.ensemble.filename, encoding=self.encoders)
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
            self.ensemble.coords[dim](coords)
            data = self.ensemble.get_frame(coords)
            for dataset in self.ensemble.datasets:
                self.data[dataset].loc[self.mask] = xr.DataArray(data[dataset],
                                                                 dims=self.cap_coords[dataset])
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

    @param.depends('c_pol')
    def graph(self) -> pn.Row():
        """
        returns the graph from the ensemble

        :return:
        """
        if self.confirmed and self.ensemble.live:
            return self.ensemble.graph(live=self.live)
        return pn.Row()

    def widgets(self) -> pn.Row:
        """
        Renders everything but the graph
        :return:
        """
        return pn.Row(pn.Column(self.param, self.button2, self.button), self.ensemble.param,
                      self.ensemble.widgets)

    def stop(self):
        """
        Stops the server
        :return:
        """
        if self.ensemble.live:
            self.callback.stop()
        print("shutting down live view")  # doesn't currently  work
