import os

import visualizer.utils
from pathlib import Path
import xarray as xr
from dask.distributed import Client
if __name__ == '__main__':
    #client = Client()
    for file in list(Path(".").rglob("*.zarr")):
        print(file)
        ds1 = xr.open_dataset(file,engine="zarr")
        if not "data_type" in ds1.attrs:
            ds1.close()
            os.rename(file, "tempfile")
            ds = xr.open_dataset("tempfile",engine="zarr")
            ds.attrs["data_type"] = "RASHG"
            ds.to_zarr(file)
            print(ds)
            os.rmdir("tempfile")
    '''
    extensions = {"5nc": fiveD.grapher}
    for file in getDir(extensions):
        fiveD.grapher(file,client).to_zarr()
        '''