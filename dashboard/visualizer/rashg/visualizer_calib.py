"""
Module for viewing calibration files
"""
from pathlib import Path
import param
import xarray as xr
import holoviews as hv
import panel as pn

pn.extension('plotly')
hv.extension('bokeh')

DATA_TYPE = "WavelengthPoweredCalib"


class Grapher(param.Parameterized):
    """visualizer for calibration files"""
    dataset = param.ObjectSelector(objects=["Pwr", "Pwrstd", "Vol", "Volstd"], default="Pwr")
    wavelength = param.Selector()

    def _update_dataset(self):
        """
        Opens selected dataset
        """
        self.data = xr.open_zarr(self.filename)
        self.param['wavelength'].objects = self.data["Pwr"].coords['wavelength'].values.tolist()
        self.wavelength = self.data["Pwr"].coords["wavelength"].min().values

    def __init__(self, filename, client_input):
        """
        :param filename: filename to open
        :param client_input: Dask Client
        """
        super().__init__()
        self.client = client_input
        self.filename = Path(filename)
        self._update_dataset()

    @param.depends("wavelength", "dataset")
    def nav(self):
        """
        Navigation graph
        :return:
        """
        output = self.data[self.dataset].sel(wavelength=self.wavelength)
        opts = [hv.opts.Image(colorbar=True, height=600,
                              title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True, logz=True)]
        return hv.Curve(output).opts(opts)

    def view(self):
        """
        wraps nav
        :return: navigation
        """
        return pn.Pane(self.nav)

    def widgets(self):
        """
        returns widgets
        :return: widgets
        """
        widgets = {"wavelength": pn.widgets.DiscreteSlider}
        return pn.Param(self.param, widgets=widgets)
