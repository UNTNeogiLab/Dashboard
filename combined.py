import param
from dask.distributed import Client, LocalCluster
import posixpath
from visualizer.utils import *
from visualizer.fiveD import grapher
from visualizer.grapher3D import grapher3D as grapher3D

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
#from numba import jit, njit
import dask
import time
from dask.diagnostics import ProgressBar
from plotly.subplots import make_subplots
import plotly.graph_objects as go

pbar = ProgressBar()
pbar.register()
client = None


class viewer(param.Parameterized):
    extensions = {'3nc': grapher3D, "5nc": grapher, "5ncu": grapher, "5nce": grapher, "5nca": grapher}
    files = getDir(extensions)
    if posixpath.exists("data/truncated_1.5ncu"):
        default = Path("data/truncated_1.5ncu")
    else:
        default = Path("data/truncated_1.5nc")
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

    def reload_files(self):
        extensions = {'3nc': grapher3D, "5nc": grapher, "5ncu": grapher, "5nce": grapher, "5nca": grapher}
        self.param["filename"].objects = getDir(extensions)

    @param.depends('filename', watch=True)
    def load(self):
        self.reload_files()  # temp solution
        self.grapher = self.extensions[extension(self.filename)](self.filename, self.client)

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
