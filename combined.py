import param
from dask.distributed import Client
import posixpath
import panel as pn
from visualizer.utils import *
from visualizer.fiveD import grapher
from visualizer.grapher3D import grapher3D as grapher3D
import argparse
import time
import socket
from instruments import instrumental
# try import RASHG.instruments_RASHG
pn.extension('plotly')
hv.extension('bokeh', 'plotly')
from dask.diagnostics import ProgressBar


pbar = ProgressBar()
pbar.register()


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


class viewer(param.Parameterized):
    extensions = {'3nc': grapher3D, "5nc": grapher, "nc": grapher}
    files = getDir(extensions)
    default = Path("data/truncated_1.5nc")
    filename = param.ObjectSelector(default=default, objects=files)

    def __init__(self, filename=default):
        super().__init__()
        self.client = Client()
        self.filename = filename
        self.load()

    def reload_files(self):
        self.param["filename"].objects = getDir(self.extensions)

    @param.depends('filename', watch=True)
    def load(self):
        self.reload_files()  # temp solution
        self.grapher = self.extensions[extension(self.filename)](self.filename, self.client)

    @param.depends('filename')
    def widgets(self):
        return pn.Column(self.param, self.grapher.widgets(),self.dask)

    @param.depends('filename')
    def gView(self):
        return self.grapher.view()

    def dask(self):
        return self.client

    def view(self):
        return pn.Row(self.widgets, self.gView)




# wrapper around viewer class to interface with instrumental class
class combined(param.Parameterized):
    applets = ["viewer", "instrumental"]
    applets = param.ObjectSelector(default="instrumental", objects=applets)

    def __init__(self):
        super().__init__()
        self.load()

    @param.depends('applets', watch=True)
    def load(self):
        if self.applets == "viewer":
            self.applet = viewer()
        elif self.applets == "instrumental":
            self.applet = instrumental()

    @param.depends('applets')
    def widgets(self):
        return self.applet.widgets

    @param.depends('applets')
    def gView(self):
        return self.applet.gView

    def view(self):
        return pn.Row(pn.Column(self.param, self.widgets), self.gView)


# these two functions are basically identical for now
def local(port=5006):
    view = combined()
    if is_port_in_use(port):
        view.view().show()
    else:
        view.view().show(
            port=port)  # if you need to change this, change this on your own or implement ports yourself. It isn't very hard


def server(reload=False):
    view = combined()
    view.view().show(port=5006, open=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='combined', description='Deploys and runs panel server')
    parser.add_argument('-server', dest='server', help='Runs the panel server for multiple clients',
                        action='store_const', const=True, default=False)
    parser.add_argument('-local', dest='local', help='Runs the panel server for single clients', action='store_const',
                        const=True, default=False)
    parser.add_argument('-fit', dest='filename', help='fit FILENAME fits datafile and saves to file from command line',
                        action='store', default=False)
    args = parser.parse_args()
    if args.server:
        server()
    elif args.local:
        local()
    elif not args.filename == False:
        start = time.time()
        view = viewer(filename=Path(args.filename)) #use port 8787 to view stats
        end = time.time()
        print(end - start)
    else:
        print("Defaulting to local server")
        local()
