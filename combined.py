import param
from dask.distributed import Client, LocalCluster
import posixpath
from visualizer.utils import *
from visualizer.fiveD import grapher
from visualizer.grapher3D import grapher3D as grapher3D
import argparse
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
        self.client = Client()
        client = self.client
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


def local():
    view = viewer()
    view.view().show()
def server(reload=False):
    view = viewer()
    view.view().show(port=5006,threaded=True)
if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='combined', description='Deploys and runs panel server')
    parser.add_argument('-server', dest='server', help='Runs the panel server for multiple clients', action='store_const', const=True, default=False)
    parser.add_argument('-local', dest='local', help='Runs the panel server for single clients', action='store_const', const=True, default=False)
    args = parser.parse_args()
    if args.server:
        server()
    elif args.local:
        local()
    else:
        print ("Defaulting to local server")
        local()