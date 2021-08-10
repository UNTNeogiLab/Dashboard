"""
Wraps visualizer and ensembles to serve dashboard. Also includes command line parsing
"""
import argparse
import socket
import sys
import time
from typing import Union, Optional

import holoviews as hv
import panel as pn
import param

from .ensembles import instruments, Gui
from .visualizer import types, Viewer

pn.extension('plotly')
hv.extension('bokeh', 'plotly')


def is_port_in_use(port):
    """
    Checks if port is in use

    :param port: port to check
    :type port: int
    :return: if port is in use
    :rtype: bool
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_to_check:
        return socket_to_check.connect_ex(('localhost', port)) == 0


# wrapper around viewer class to interface with instrumental class
class Combined(param.Parameterized):
    """
    Combined viewer for Visualizer and Instruments
    """
    applet: Union[Gui, Viewer]
    applets = ["viewer", "instrumental"]
    applets = param.ObjectSelector(default="instrumental", objects=applets)
    button = pn.widgets.Button(name="STOP", button_type='primary')

    def __init__(self) -> None:
        """

        :rtype: None
        """
        super().__init__()
        self.applet = Gui(instruments)

    @param.depends('applets', watch=True)
    def load(self) -> None:
        """
        Loads the currently selected applet

        :rtype: None
        """
        self.applet.stop()
        if self.applets == "viewer":
            self.applet = Viewer(types)
        elif self.applets == "instrumental":
            self.applet = Gui(instruments)

    @param.depends('applets')
    def widgets(self) -> Union[pn.Row, pn.Column]:
        """
        Renders widgets from the applet

        :return: widgets
        :rtype: pn.Column
        """
        return self.applet.widgets

    @param.depends('applets')
    def applet_view(self) -> Union[Optional[pn.Row], pn.Column]:
        """
        wraps applet view

        :return: applet view
        :rtype: pn.Column
        """
        return self.applet.graph

    def quit(self, event: tuple = None) -> None:
        """
        closes dashboard

        :param event: allows this to be used with a button
        :type event: tuple
        """
        self.applet.stop()
        sys.exit()

    def view(self) -> pn.layout.base.Row:
        """
        Returns widgets and applet view


        :return: dashboard to be rendered
        :rtype: panel.layout.base.Row
        """
        self.button.on_click(self.quit)
        return pn.Row(pn.Column(self.param, self.widgets, self.button), self.applet_view)


# these two functions are basically identical for now
def serve(port: int = 5006, open_browser: bool = True) -> None:
    """
    serves the combined panel applet

    Parameters
    ----------
    :rtype: None
    :param open_browser: whether to open the browser
    :type open_browser: bool
    :param port: default port number to use
    :type port: int
    """
    view = Combined()
    while is_port_in_use(port):
        port += 1
    view.view().show(port=port, open=open_browser)
    # if you need to change this, change this on your own or implement ports yourself. It
    # isn't very hard


def main() -> None:
    """

    :rtype: None
    """
    parser = argparse.ArgumentParser(prog='combined', description='Deploys and runs panel server')
    parser.add_argument('-server', dest='server', help='Runs the panel server for multiple clients',
                        action='store_const', const=True, default=False)
    parser.add_argument('-local', dest='local', help='Runs the panel server for single clients', action='store_const',
                        const=True, default=False)
    parser.add_argument('--fit', dest='filename', help='fits datafile and saves to file from command line',
                        action='store', default=False)
    args = parser.parse_args()
    if args.server:
        serve(open_browser=False)
    elif args.local:
        serve()
    elif args.filename:
        start = time.time()
        view = Viewer(filename=args.filename, types=types)  # use port 8787 to view stats
        view.view().show()
        end = time.time()
        print(end - start)
    else:
        print("Defaulting to local server")
        serve()


if __name__ == '__main__':
    main()
