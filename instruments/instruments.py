import param
import instruments
import panel as pn
import holoviews as hv
from dask.diagnostics import ProgressBar

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
pbar = ProgressBar()
pbar.register()


class instrumental(param.Parameterized):
    instrument_classes = instruments.instruments
    instruments = list(instruments.instruments.keys())
    instruments = param.ObjectSelector(default="random", objects=instruments)
    confirmed = param.Boolean(default=False, precedence=-1)
    button = pn.widgets.Button(name='Confirm', button_type='primary')

    def __init__(self):
        super().__init__()
        self.load()
        self.gui = instruments.gui.gui()

    @param.depends('instruments', watch=True)
    def load(self):
        self.confirmed = False
        self.button.disabled = False
        self.instrument = self.instrument_classes[self.instruments].instruments()

    @param.depends('instruments', 'confirmed')
    def widgets(self):
        self.button.on_click(self.initialize)
        return pn.Column(self.param, self.instrument.param, self.gui.param, self.button, self.gui.widgets)

    def initialize(self, event=None):
        self.instrument.initialize()
        self.gui.initialize(self.instrument)  # initialize the GUI with the instruments
        self.button.disabled = True
        self.confirmed = True
        self.gui.live_view()  # start live view immediately

    @param.depends('instruments', 'confirmed')
    def gView(self):
        # more complicated due to instruments and gui relationship
        if self.confirmed:
            return self.gui.output
        else:
            pass

    def stop(self):
        self.gui.stop()
