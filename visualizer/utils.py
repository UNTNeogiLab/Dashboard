import panel as pn
import holoviews as hv
import numpy as np
from numba import njit, jit
import time
import os
from itertools import chain
from pathlib import Path

pn.extension('plotly')
hv.extension('bokeh', 'plotly')


def getDir(extensions):
    # parses directories for valid files
    return list(chain.from_iterable(Path(".").rglob("*." + extension) for extension in extensions))


def find_best_file(files, smallest=True):
    pass


def extension(file):
    return os.path.splitext(file)[1][1:]


def get_file_val(file):
    extension = os.path.splitext(file)[1]
    # priorities are in order of highest to lowest
    if extension == "5nc":
        return 5
    elif extension == "5nce":
        return 6
    elif extension == "5ncu":
        return 4
    elif extension == "3nc":
        return 100000
    if (extension == "5nca"):
        xr.open_dataset(file, )


def fname(file):
    fname = os.path.basename(file)
    return fname.replace(extension(fname), '')


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
