import visualizer.fiveD as fiveD
from visualizer.utils import *
from dask.distributed import Client
if __name__ == "__main__":
    client = Client()
    extensions = {"5nc": fiveD.grapher}
    for file in getDir(extensions):
        fiveD.grapher(file,client).to_zarr()