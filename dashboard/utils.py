"""
Utilities for various components. Aims to contain any resuable functions needed elsewhere
"""
import os
import pathlib
import time
from pathlib import Path

import numpy as np
import xarray as xr
import zarr.errors
from numba import vectorize, float64
from scipy.interpolate import interp1d


@vectorize([float64(float64, float64, float64, float64)])
def inv_sin_sqr(y, mag, x_offset, y_offset):
    """Function to transform calibration. Superseded by interpolation
    :param y:
    :param mag:
    :param x_offset:
    :param y_offset:
    :return:
    """
    return np.mod(((180 / np.pi) * (np.arcsin(np.sqrt(np.abs((y - y_offset) / mag)))) + x_offset), 180)


@vectorize([float64(float64, float64, float64, float64)])
def sin_squared(x, mag, x_offset, y_offset):
    """
    Function that squares the sin of a number
    :param y:
    :param mag:
    :param x_offset:
    :param y_offset:
    :return:
    """
    return ((np.sin((x - x_offset) * np.pi / 180)) ** 2) * mag + y_offset


def interp(old, pol, pwr) -> np.array:
    """
    Interpolates a set of powers for polarization values to generate a new set of polarizations for given power
    :param old: original power values
    :param pol: polarization values
    :param pwr: new power values
    :return: list of polarizations for the new power values
    """
    function = interp1d(old, pol, fill_value="extrapolate")
    return function(pwr)


def interpolate(filename: pathlib.PosixPath, pwr: np.array = np.arange(0, 100, 5), throw: int = 0) -> xr.DataArray:
    """
    Interpolates a calibration file to get Polarizations for given powers and wavelength
    :param throw: throw everything at this polarization and lower
    :type throw: int
    :param filename: calibration file to interpolate from
    :type filename: pathlib.PosixPath
    :param pwr: powers to interpolate to
    :type pwr: np.array
    :return: Reversed calibration
    :rtype: xr.DataArray
    """
    power_calibration = xr.open_dataset(filename, engine="zarr")["Pwr"]
    power_calibration = power_calibration.where(power_calibration.Polarization > throw, drop=True)
    pc_pol = power_calibration.coords["Polarization"].values
    pc_reverse = xr.apply_ufunc(interp, power_calibration, input_core_dims=[["Polarization"]], vectorize=True,
                                output_core_dims=[["power"]], kwargs={"pwr": pwr, "pol": pc_pol})
    pc_reverse.coords["power"] = pwr
    return pc_reverse


def scan_directory(extensions: dict) -> dict:
    """
    Scans for readable files

    :return:
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
            dataset = xr.open_dataset(file, engine="zarr")
            data_type = dataset.attrs["data_type"]
            dataset.close()
            if data_type in extensions:
                file_dict[file] = extensions[data_type]
        except zarr.errors.GroupNotFoundError:
            print(f"{file} open failed. No data in folder")
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
    file_name = os.path.basename(file)
    return file_name.replace(extension(file_name), '')


def hotfix(dataset):
    """
    Fixes older datasets by adding coordinates and atttributes. DO NOT USE
    :param dataset:
    :type dataset: xr.Dataset
    :return: fixed dataset
    :rtype: xr.Dataset
    """
    dataset.coords['wavelength'] = dataset.coords['wavelength'] * 2 + 780
    dataset.coords['Polarization'] = np.arange(0, 180, 1) / 90 * np.pi
    dataset.coords['degrees'] = ("Polarization", np.arange(0, 360, 2))
    dataset.coords['x_pixels'] = ("x", dataset.coords['x'].values)
    dataset.coords['y_pixels'] = ("y", dataset.coords['y'].values)
    dataset.coords['x'] = dataset.coords['x'] * 0.05338  # TODO fix incorrect magic numbers
    dataset.coords['y'] = dataset.coords['y'] * 0.05338  # TODO fix incorrect magic numbers
    dataset.attrs['x'] = "micrometers"
    dataset.attrs['y'] = "micrometers"
    dataset.attrs['Polarization'] = "radians"
    return dataset


def get_range(dim: str, coords: xr.core.coordinates.DataArrayCoordinates) -> tuple[np.float64, np.float64]:
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
