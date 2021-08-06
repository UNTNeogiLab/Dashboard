from pathlib import Path

import holoviews as hv
import panel as pn
import param
import xarray as xr

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

        output = self.data["Stellarnet"].sel(wavelength=self.wavelength)
        powers = output.coords["power"].values.tolist()
        values = [output.sel(power=power).sortby(["emission_wavelength"]).coords["emission_wavelength"].values[0] for power in
                  powers]

        opts = [hv.opts.Curve(title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True)]
        return hv.Curve(values, "power", "emission_wavelength for maximum intensity").opts(opts)

    @param.depends("wavelength")
    def integrated(self):
        output = self.data["Stellarnet"].sel(wavelength=self.wavelength).sum(dim="emission_wavelength")
        opts = [hv.opts.Curve(title=f"Wavelength: {self.wavelength}",
                              tools=['hover'], framewise=True)]
        return hv.Curve(output, "power", "summed maximum intensity").opts(opts)

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
