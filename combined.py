import holoviews as hv
import param
from dask.distributed import Client
import panel as pn
from visualizer.utils import *
from visualizer.fiveD import grapher
from visualizer.sixD import grapher as grapher6
from visualizer.grapher3D import grapher3D as grapher3D
import argparse
import time
import socket
import sys

# try import RASHG.instruments_RASHG
pn.extension('plotly')
hv.extension('bokeh', 'plotly')
from dask.diagnostics import ProgressBar

pbar = ProgressBar()
pbar.register()


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


class Viewer(param.Parameterized):
    extensions = {'3nc': grapher3D, "5nc": grapher, "zarr": grapher6}
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
        return pn.Column(self.param, self.grapher.widgets(), self.dask)

    @param.depends('filename')
    def gView(self):
        return self.grapher.view()

    def dask(self):
        return self.client

    def view(self):
        return pn.Row(self.widgets, self.gview)

    def stop(self):
        pass


# wrapper around viewer class to interface with instrumental class
class combined(param.Parameterized):
    applets = ["viewer", "instrumental"]
    applets = param.ObjectSelector(default="instrumental", objects=applets)
    button = pn.widgets.Button(name="STOP", button_type='primary')

    def __init__(self):
        super().__init__()
        self.load()

    @param.depends('applets', watch=True)
    def load(self):
        if self.applets == "viewer":
            self.applet = Viewer()
        elif self.applets == "instrumental":
            from instruments import instrumental
            self.applet = instrumental()

    @param.depends('applets')
    def widgets(self):
        return self.applet.widgets

    @param.depends('applets')
    def gView(self):
        return self.applet.gView

    def quit(self, event=None):
        self.applet.stop()
        sys.exit()

    def view(self):
        self.button.on_click(self.quit)
        return pn.Row(pn.Column(self.param, self.widgets, self.button), self.gView)


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
    parser.add_argument('--fit', dest='filename', help='fits datafile and saves to file from command line',
                        action='store', default=False)
    parser.add_argument('--Polar', dest='Polar', help='filename, X, Y Plots all polar plots across wavelength for',
                        action='store', default=False, nargs=3)  # TODO: add subparsers
    args = parser.parse_args()
    if args.server:
        server()
    elif args.local:
        local()
    elif not args.filename == False:
        start = time.time()
        view = Viewer(filename=Path(args.filename))  # use port 8787 to view stats
        end = time.time()
        print(end - start)
    elif not args.Polar == False:
        start = time.time()
        Filename, X, Y = args.Polar
        view = Viewer(filename=Path(Filename))  # use port 8787 to view stats
        view.grapher.x0 = int(X)
        view.grapher.y0 = int(Y)
        view.grapher.x1 = int(X) + 0.06  # get at least 1 pixel
        view.grapher.y1 = int(Y) + 0.06  # get at least 1 pixel
        view.grapher.selected = True
        wavelengths = view.grapher.ds1.coords['wavelength'].values.tolist()
        Orientations = view.grapher.ds1.coords['Orientation'].values.tolist()
        Folder = Filename.replace(f".{extension(Filename)}", '')
        if not os.path.isdir(Folder):
            os.mkdir(Folder)
        for Orientation in Orientations:
            view.grapher.Orientation = Orientation
            for wavelength in wavelengths:
                view.grapher.wavelength = wavelength
                view.grapher.Polar().write_image(f"{Folder}/Polar_X{X}Y{Y}O{Orientation}W{wavelength}.png")
        # view = viewer(filename=Path(args.filename)) #use port 8787 to view stats
        end = time.time()
        print(end - start)
    else:
        print("Defaulting to local server")
        local()
