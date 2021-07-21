import numpy as np
import time
import os
from pathlib import Path
import xarray as xr


def getDir(extensions: dict) -> dict:
    """
    Scans for readable files

    :param extensions: A mapping from data types to modules
    :type extensions: dict
    :return: Mapping from files to modules
    :rtype: dict
    """
    # parses directories for valid files
    files = list(Path("").rglob("*.zarr"))
    file_dict = {}
    for file in files:
        try:
            ds = xr.open_dataset(file, engine="zarr")
            data_type = ds.attrs["data_type"]
            ds.close()
            if data_type in extensions:
                file_dict[file] = extensions[data_type]
        except Exception as ex:
            print(f"{file} open failed. Exception: {ex} Skipping")
    return file_dict


def extension(file: str) -> os.path:
    """

    :param file:
    :type file: string or path
    :return:
    :rtype: path
    """
    return os.path.splitext(file)[1][1:]


def fname(file) -> str:
    """
    Helper function to get the name from a filename
    (IE: data/truncated_1.zarr -> truncated_1)

    :param file: filename or path
    :type file: str
    :return: just the filename with no extension
    :rtype: str
    """
    fname = os.path.basename(file)
    return fname.replace(extension(fname), '')


def hotfix(ds):
    ds.coords['wavelength'] = ds.coords['wavelength'] * 2 + 780
    ds.coords['Polarization'] = np.arange(0, 180, 1) / 90 * np.pi
    ds.coords['degrees'] = ("Polarization", np.arange(0, 360, 2))
    ds.coords['x_pixels'] = ("x", ds.coords['x'].values)
    ds.coords['y_pixels'] = ("y", ds.coords['y'].values)
    ds.coords['x'] = ds.coords['x'] * 0.05338  # TODO fix incorrect magic numbers
    ds.coords['y'] = ds.coords['y'] * 0.05338  # TODO fix incorrect magic numbers
    ds.attrs['x'] = "micrometers"
    ds.attrs['y'] = "micrometers"
    ds.attrs['Polarization'] = "radians"
    return ds


def getRange(dim: str, coords: xr.core.coordinates.DataArrayCoordinates) -> tuple[np.float64, np.float64]:
    """
    Gets maximum and minimum on a set of coordinates

    :param dim: dimension to get range on
    :type dim: str
    :param coords: coordinates
    :type coords: xarray.core.coordinates.DataArrayCoordinates
    :return: minimum and maximum values on dimension
    :rtype: Tuple[numpy.float64, numpy.float64]
    """
    return coords[dim].values.min(), coords[dim].values.max()


def convert(seconds):
    """

    :param seconds:
    :type seconds:
    :return:
    :rtype:
    """
    return time.strftime("%H:%M:%S", time.gmtime(seconds))



