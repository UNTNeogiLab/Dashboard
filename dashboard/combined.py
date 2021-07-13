import holoviews as hv
import param
import panel as pn
from . import visualizer
import argparse
import time
import socket
import sys
from . import instruments

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
from dask.diagnostics import ProgressBar

pbar = ProgressBar()
pbar.register()


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


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
            self.applet = visualizer.Viewer()
        elif self.applets == "instrumental":

            self.applet = instruments.dashboard.instrumental()

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


def main():
    parser = argparse.ArgumentParser(prog='combined', description='Deploys and runs panel server')
    parser.add_argument('-server', dest='server', help='Runs the panel server for multiple clients',
                        action='store_const', const=True, default=False)
    parser.add_argument('-local', dest='local', help='Runs the panel server for single clients', action='store_const',
                        const=True, default=False)
    parser.add_argument('--fit', dest='filename', help='fits datafile and saves to file from command line',
                        action='store', default=False)
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
    else:
        print("Defaulting to local server")
        local()


if __name__ == '__main__':
    main()
