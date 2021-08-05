from typing import Union

import param
from . import gui
import panel as pn
import holoviews as hv
from dask.diagnostics import ProgressBar

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
pbar = ProgressBar()
pbar.register()


class Instrumental(param.Parameterized):
    instruments = param.ObjectSelector()  # us
    confirmed = param.Boolean(default=False, precedence=-1)
    button = pn.widgets.Button(name='Confirm', button_type='primary')

    def __init__(self, instruments):
        self.instrument_classes = instruments
        instruments = list(instruments.keys())
        self.param["instruments"].default = instruments[0]
        self.param["instruments"].objects = instruments
        """

        :rtype: object
        """
        super().__init__()
        self.load()
        self.gui = gui.gui()

    @param.depends('instruments', watch=True)
    def load(self):
        self.confirmed = False
        self.button.disabled = False
        self.instrument = self.instrument_classes[self.instruments].instruments()

    @param.depends('instruments', 'confirmed')
    def widgets(self) -> pn.Row:
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
