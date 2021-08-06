"""
Renders a dashboard using a selected ensembles file and gui.py
Main function is to select the ensemble
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
    Main function is to select the ensemble
    """
    ensembles = param.ObjectSelector()  # us
    confirmed = param.Boolean(default=False, precedence=-1)
    button = pn.widgets.Button(name='Confirm', button_type='primary')

    def __init__(self, ensembles):
        self.ensemble_classes = ensembles
        ensembles = list(ensembles.keys())
        i = 0
        while i < len(ensembles):
            try:
                self.param["ensembles"].default = ensembles[i]
            except stellarnet.stellarnet.NotFoundError:
                print("Skipping stellarnet due to lack of stellarnet")
            except:
                print(f"{ensembles[i]} failed")
            i += 1
        self.param["ensembles"].objects = ensembles
        """

        :rtype: object
        """
        super().__init__()
        self.load()
        self.gui = gui.gui()

    @param.depends('ensembles', watch=True)
    def load(self) -> None:
        """
        Loads selected ensemble
        :rtype: None
        """
        self.confirmed = False
        self.button.disabled = False
        self.ensemble = self.ensemble_classes[self.ensembles].Ensemble()

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
        """
        Initializes the gui with the selected ensemble
        :param event:
        :return:
        """
        self.ensemble.initialize()
        self.gui.initialize(self.ensemble)  # initialize the GUI with the ensembles
        self.button.disabled = True
        self.confirmed = True
        self.gui.live_view()  # start live view immediately

    @param.depends('ensembles', 'confirmed')
    def graph(self) -> Union[None, pn.Row]:
        """
        If confirmed, return the graph from the GUI
        :return:
        """
        # more complicated due to ensembles and gui relationship
        if self.confirmed:
            return pn.Row(self.gui.output)
        pass

    def stop(self):
        """
        stops the GUI if possible
        :return: None
        """
        self.gui.stop()
