from pathlib import Path

import holoviews as hv
import param
import xarray as xr
import panel as pn

DATA_TYPE = "stellarnet"


class Grapher(param.Parameterized):
    wavelength = param.Selector()

    def _update_dataset(self):
        """
        Opens selected dataset
        """
        self.data = xr.open_zarr(self.filename)
        self.param['wavelength'].objects = self.data["Stellarnet"].coords['wavelength'].values.tolist()
        self.wavelength = self.data["Stellarnet"].coords["wavelength"].min().values

    def __init__(self, filename, client_input):
        """
        :param filename: filename to open
        :param client_input: Dask Client
        """
        super().__init__()
        self.client = client_input
        self.filename = Path(filename)
        self._update_dataset()

    @param.depends("wavelength")
    def maximum(self):
        """
        Maximum graph of intensity for all emission wavelength against power per wavelength
        :return:
        """
        output = self.data["Stellarnet"].sel(wavelength=self.wavelength).max(dim="emission_wavelength")
        opts = [hv.opts.Curve(title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True)]
        return hv.Curve(output, "power", "maximum intensity").opts(opts)

    @param.depends("wavelength")
    def integrated(self):
        output = self.data["Stellarnet"].sel(wavelength=self.wavelength).sum(dim="emission_wavelength")
        opts = [hv.opts.Image(colorbar=True,
                              title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True, logz=True)]
        return hv.Image(output).opts(opts)

    def view(self):
        """
        wraps nav
        :return: navigation
        """
        return pn.Row(self.integrated, self.maximum)

    def widgets(self):
        """
        returns widgets
        :return: widgets
        """
        widgets = {"wavelength": pn.widgets.DiscreteSlider}
        return pn.Param(self.param, widgets=widgets)