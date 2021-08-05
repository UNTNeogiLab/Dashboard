"""
Renders a dashboard using a selected instruments file and gui.py
Main function is to select the instrument
"""
from typing import Union
import param
import stellarnet
import panel as pn
import holoviews as hv
from dask.diagnostics import ProgressBar

from . import gui

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
pbar = ProgressBar()
pbar.register()


class Instrumental(param.Parameterized):
    """
    Renders a dashboard using a selected instruments file and gui.py
    Main function is to select the instrument
    """
    instruments = param.ObjectSelector()  # us
    confirmed = param.Boolean(default=False, precedence=-1)
    button = pn.widgets.Button(name='Confirm', button_type='primary')

    def __init__(self, instruments):
        self.instrument_classes = instruments
        instruments = list(instruments.keys())
        i = 0
        while i < len(instruments):
            try:
                self.param["instruments"].default = instruments[i]
            except stellarnet.stellarnet.NotFoundError:
                print("Skipping stellarnet due to lack of stellarnet")
            except:
                print(f"{instruments[i]} failed")
            i += 1
        self.param["instruments"].objects = instruments
        """

        :rtype: object
        """
        super().__init__()
        self.load()
        self.gui = gui.gui()

    @param.depends('instruments', watch=True)
    def load(self) -> None:
        """
        Loads selected instrument
        :rtype: None
        """
        self.confirmed = False
        self.button.disabled = False
        self.instrument = self.instrument_classes[self.instruments].instruments()

    @param.depends('instruments', 'confirmed')
    def widgets(self) -> pn.Row:
        """
        Renders everything but the graph
        :return: widgets
        """
        self.button.on_click(self.initialize)
        return pn.Row(pn.Column(self.param, self.gui.param, self.button, self.gui.widgets), self.instrument.param,
                      self.instrument.widgets)

    def initialize(self, event=None):
        self.instrument.initialize()
        self.gui.initialize(self.instrument)  # initialize the GUI with the instruments
        self.button.disabled = True
        self.confirmed = True
        self.gui.live_view()  # start live view immediately

    @param.depends('instruments', 'confirmed')
    def gView(self) -> Union[None, pn.Row]:
        # more complicated due to instruments and gui relationship
        if self.confirmed:
            return pn.Row(self.gui.output)
        else:
            pass

    def stop(self):
        self.gui.stop()
