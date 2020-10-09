import psutil
import xarray as xr
import panel as pn
import os
import colorcet as cc
import holoviews as hv
from panel.interact import fixed
from scipy.optimize import curve_fit
import plotly.express as px
import numpy as np
import colorcet as cc
import param
import pandas as pd
from dask.distributed import Client, LocalCluster
from fiveD import grapher
from grapher3D import grapher3D as grapher3D

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
from numba import jit, njit
import dask
import time
from dask.diagnostics import ProgressBar
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from utils import *
pbar = ProgressBar()
pbar.register()
client = None


class viewer(param.Parameterized):
    dirs = ["converted"]
    extensions = {'3nc': grapher3D, "5nc": grapher, "5ncu": grapher, "5nce": grapher,"5nca":grapher}
    files = getDir(dirs,extensions)
    if "converted/truncated_1.5ncu" in files:
        default = "converted/truncated_1.5ncu"
    else:
        default = "converted/truncated_1.5nc"
    filename = param.ObjectSelector(default=default, objects=files)

    def __init__(self):
        super().__init__()
        global client
        if client == None:
            self.client = Client()
            client = self.client
        else:
            self.client = client
        self.load()

    @param.depends('filename', watch=True)
    def load(self):
        self.grapher = self.extensions[self.filename.split(".")[1]](self.filename)

    @param.depends('filename')
    def widgets(self):
        return self.grapher.widgets()

    @param.depends('filename')
    def gView(self):
        return self.grapher.view()

    def view(self):
        return pn.Row(pn.Column(self.param, self.widgets), self.gView)


if __name__ == '__main__':
    view = viewer()
    view.view().show()
