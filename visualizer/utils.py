import numpy as np
import time
import os
from pathlib import Path
import xarray as xr

def getDir(extensions):
    # parses directories for valid files
    files = list(Path(".").rglob("*.zarr"))
    file_dict = {}
    for file in files:
        try:
            ds = xr.open_dataset(file,engine="zarr")
            data_type = ds.attrs["data_type"]
            ds.close()
            if data_type in extensions:
                file_dict[file] = extensions[data_type]
        except:
            print(f"{file} open failed. Skipping")
    return file_dict


def extension(file):
    return os.path.splitext(file)[1][1:]


def fname(file):
    fname = os.path.basename(file)
    return fname.replace(extension(fname), '')




def hotfix(ds):
    ds.coords['wavelength'] = ds.coords['wavelength'] * 2 + 780
    ds.coords['Polarization'] = np.arange(0, 180, 1) / 90 * np.pi
    ds.coords['degrees'] = ("Polarization", np.arange(0, 360, 2))
    ds.coords['x_pixels'] = ("x",ds.coords['x'].values)
    ds.coords['y_pixels'] = ("y",ds.coords['y'].values)
    ds.coords['x'] = ds.coords['x'] * 0.05338 #TODO fix incorrect magic numbers
    ds.coords['y'] = ds.coords['y'] * 0.05338 #TODO fix incorrect magic numbers
    ds.attrs['x'] = "micrometers"
    ds.attrs['y'] = "micrometers"
    ds.attrs['Polarization'] = "radians"
    return ds


def getRange(dim, coords):
    return coords[dim].values.min(), coords[dim].values.max()


def convert(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def data_type(filename):
    try:
        return xr.open_dataset(filename, engine="zarr").attrs["data_type"]
    except:
        print("couldn't get data type")
        return ""