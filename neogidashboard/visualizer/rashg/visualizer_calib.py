"""
Module for viewing calibration files
"""
from pathlib import Path, PosixPath

import holoviews as hv
import numpy as np
import panel as pn
import param
import xarray as xr

from ... import utils

pn.extension('plotly')
hv.extension('bokeh')

DATA_TYPE = "WavelengthPoweredCalib"


class Grapher(param.Parameterized):
    """visualizer for calibration files"""
    dataset = param.ObjectSelector(objects=["Pwr", "Pwrstd", "Vol", "Volstd"], default="Pwr")
    wavelength = param.Selector()
    pstart = param.Integer(default=0)
    pstop = param.Integer(default=100)
    pstep = param.Number(default=5)
    throw = param.Number(default=0)

    def _update_dataset(self):
        """
        Opens selected dataset
        """
        self.interpolate()
        self.data = xr.open_zarr(self.filename)
        self.param['wavelength'].objects = self.data["Pwr"].coords['wavelength'].values.tolist()
        self.wavelength = self.data["Pwr"].coords["wavelength"].min().values

    @param.depends("pstart", "pstop", "pstep","throw", watch=True)
    def interpolate(self):
        power = np.arange(self.pstart, self.pstop, self.pstep)
        self.pc_reverse = utils.interpolate(PosixPath(self.filename), pwr=power,throw=self.throw)
        self.pol_dim = hv.Dimension('Polarization', soft_range=(0, 10), unit="degrees")
        self.pwr_dim = hv.Dimension("Power", range=(self.pstart, self.pstop))

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
        opts = [hv.opts.Curve(title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True)]
        return hv.Curve(output).opts(opts)

    @param.depends("wavelength", "pstart", "pstop", "pstep")
    def reverse_nav(self):
        """Reversed navigation graph"""
        output = self.pc_reverse.sel(wavelength=self.wavelength)
        opts = [hv.opts.Curve(title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True)]
        return hv.Curve(output, "power", "polarization").opts(opts).redim(polarization=self.pol_dim, power=self.pwr_dim)

    def view(self):
        """
        wraps nav
        :return: navigation
        """
        return pn.Row(self.nav, self.reverse_nav)

    def widgets(self):
        """
        returns widgets
        :return: widgets
        """
        widgets = {"wavelength": pn.widgets.DiscreteSlider}
        return pn.Param(self.param, widgets=widgets)
