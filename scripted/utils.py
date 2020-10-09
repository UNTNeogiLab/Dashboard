import panel as pn
import holoviews as hv
import numpy as np
from numba import njit, jit
import time
import os
from itertools import chain

pn.extension('plotly')
hv.extension('bokeh', 'plotly')


def getDir(dirs, extensions):
    # parses directories for valid files
    return list(chain.from_iterable(
        [[folder + "/" + file for file in os.listdir(folder) if file.split('.')[1] in extensions] for folder in dirs]))


@njit(cache=True)
def function(phi, delta, A, B, theta, C):
    return (A * np.cos(3 * phi - 3 * delta) + B * np.cos(phi - 3 * delta + 2 * theta)) ** 2 + C


def functionN(phi, delta, A, B, theta, C):
    return (A * np.cos(3 * phi - 3 * delta) + B * np.cos(phi - 3 * delta + 2 * theta)) ** 2 + C


def hotfix(ds):
    ds.coords['wavelength'] = ds.coords['wavelength'] * 2 + 780
    ds.coords['Polarization'] = np.arange(0, 180, 1) / 90 * np.pi
    ds.coords['degrees'] = ("Polarization", np.arange(0, 360, 2))
    ds.coords['x'] = ds.coords['x'] * 0.05338
    ds.coords['y'] = ds.coords['y'] * 0.05338
    ds.attrs['x'] = "micrometers"
    ds.attrs['y'] = "micrometers"
    ds.attrs['Polarization'] = "radians"
    return ds


def getRange(dim, coords):
    return coords[dim].values.min(), coords[dim].values.max()


def convert(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))
