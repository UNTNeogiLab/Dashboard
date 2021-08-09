from pathlib import Path

import holoviews as hv
import panel as pn
import param
import xarray as xr

from neogidashboard import utils

hv.extension("bokeh")
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
        self.power_dim = hv.Dimension("power", range=utils.get_range("power", self.data["Stellarnet"].coords))

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

        output = self.data["Stellarnet"].sel(wavelength=self.wavelength).idxmax("emission_wavelength")
        opts = [hv.opts.Curve(title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True)]
        return hv.Curve(output, "power", "emission wavelength for maximum intensity").opts(opts)

    @param.depends("wavelength")
    def integrated(self):
        output = self.data["Stellarnet"].sel(wavelength=self.wavelength).sum(dim="emission_wavelength")
        opts = [hv.opts.Curve(title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True)]
        return hv.Curve(output, self.power_dim, "summed intensity").opts(opts)

    @param.depends("wavelength")
    def overall(self):
        output = self.data["Stellarnet"].sel(wavelength=self.wavelength)
        opts = [hv.opts.QuadMesh(colorbar=True, tools=['hover'], framewise=True, logz=True, width=600)]
        return hv.QuadMesh(output, [self.power_dim, "emission_wavelength"]).opts(opts)

    def view(self):
        """
        wraps nav
        :return: navigation
        """
        return pn.Column(pn.Row(self.integrated, self.maximum), self.overall)

    def widgets(self):
        """
        returns widgets
        :return: widgets
        """
        widgets = {"wavelength": pn.widgets.DiscreteSlider}
        return pn.Param(self.param, widgets=widgets)


if __name__ == "__main__":
    viewer = Grapher("data/realtest.zarr", None)
    viewer.view().show()
    # print(viewer.power_dim)
