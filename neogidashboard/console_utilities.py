"""
Various Utilities for command line. Formerly converter.py
"""
import os
from pathlib import Path
import zarr
import xarray as xr
from zarr.errors import GroupNotFoundError
from neogidashboard import utils

compressor = zarr.Blosc(cname="zstd", clevel=3, shuffle=2)


def convert():
    """Converts all avalible files to zarr files and fills in missing attributes. Only to be used to update legacy
    files. """
    # client = Client()
    for file in list(Path("..").rglob("*.zarr")):
        print(file)
        ds1 = xr.open_dataset(file, engine="zarr")
        if not "data_type" in ds1.attrs:
            ds1.attrs["data_type"] = "RASHG"
            ds1.to_zarr(file, mode="w", compute=True)
    for file in list(Path("..").rglob("*.5nc")):
        filename = str(file).replace(f".{utils.extension(file)}", '.zarr')
        if filename not in list(Path("..").rglob("*.zarr")):
            dataset = utils.hotfix(xr.open_dataarray(file, engine="netcdf4"))
            coords = dataset.coords
            ds_coords = dataset.assign_coords(power=0).expand_dims("power")
            data = xr.Dataset(data_vars={"ds1": ds_coords},
                              attrs=dataset.attrs,
                              coords=coords)
            data.attrs["data_type"] = "RASHG"
            data.attrs["title"] = "RASHG"
            data.attrs["data_version"] = 2
            print(data)
            data.to_zarr(filename, encoding={"ds1": {"compressor": compressor}}, consolidated=True, compute=True)


def clean():
    """cleans all your empty files"""
    files = list(Path("").rglob("*.zarr"))
    for file in files:
        try:
            dataset = xr.open_dataset(file, engine="zarr")
            dataset.close()
        except GroupNotFoundError:
            os.removedirs(file)


if __name__ == '__main__':
    convert()
