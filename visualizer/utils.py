import numpy as np
from numba import njit, jit
import time
import os
from itertools import chain
from pathlib import Path

def getDir(extensions):
    # parses directories for valid files
    return list(chain.from_iterable(Path(".").rglob("*." + extension) for extension in extensions))


def extension(file):
    return os.path.splitext(file)[1][1:]


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
    ds.coords['x_pixels'] = ("x",ds.coords['x'].values)
    ds.coords['y_pixels'] = ("y",ds.coords['y'].values)
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
