"""
Renders a dashboard using a selected ensembles file and gui.py
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


class Ensembles(param.Parameterized):
    """
    Renders a dashboard using a selected ensembles file and gui.py
    Main function is to select the instrument
    """
    ensembles = param.ObjectSelector()  # us
    confirmed = param.Boolean(default=False, precedence=-1)
    button = pn.widgets.Button(name='Confirm', button_type='primary')

    def __init__(self, instruments):
        self.instrument_classes = instruments
        instruments = list(instruments.keys())
        i = 0
        while i < len(instruments):
            try:
                self.param["ensembles"].default = instruments[i]
            except stellarnet.stellarnet.NotFoundError:
                print("Skipping stellarnet due to lack of stellarnet")
            except:
                print(f"{instruments[i]} failed")
            i += 1
        self.param["ensembles"].objects = instruments
        """

        :rtype: object
        """
        super().__init__()
        self.load()
        self.gui = gui.gui()

    @param.depends('ensembles', watch=True)
    def load(self) -> None:
        """
        Loads selected instrument
        :rtype: None
        """
        self.confirmed = False
        self.button.disabled = False
        self.ensemble = self.instrument_classes[self.ensembles].Ensemble()

    @param.depends('ensembles', 'confirmed')
    def widgets(self) -> pn.Row:
        """
        Renders everything but the graph
        :return: widgets
        """
        self.button.on_click(self.initialize)
        return pn.Row(pn.Column(self.param, self.gui.param, self.button, self.gui.widgets), self.ensemble.param,
                      self.ensemble.widgets)

    def initialize(self, event=None):
        self.ensemble.initialize()
        self.gui.initialize(self.ensemble)  # initialize the GUI with the ensembles
        self.button.disabled = True
        self.confirmed = True
        self.gui.live_view()  # start live view immediately

    @param.depends('ensembles', 'confirmed')
    def gView(self) -> Union[None, pn.Row]:
        # more complicated due to ensembles and gui relationship
        if self.confirmed:
            return pn.Row(self.gui.output)
        else:
            pass

    def stop(self):
        self.gui.stop()
