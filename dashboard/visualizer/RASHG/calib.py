import param
import xarray as xr
from pathlib import Path
import holoviews as hv

name = "calib"
data_type = "WavelengthPoweredCalib"


class grapher(param.Parameterized):
    dataset = param.ObjectSelector(objects=["Pwr", "Pwrstd", "Vol", "Volstd"], default="Pwr")
    wavelength = param.Selector()
    colorMap = param.ObjectSelector(default="fire", objects=hv.plotting.list_cmaps())

    def _update_dataset(self):
        self.ds = xr.open_dataset(self.filename)
        self.param['wavelength'].objects = self.ds["Pwr"].coords['wavelength'].values.tolist()
        self.wavelength = self.ds["Pwr"].coords["wavelength"].min().values

    def __init__(self, filename, client_input):
        super().__init__()
        self.client = client_input
        self.filename = Path(filename)
        self._update_dataset()

    @param.depends("wavelength", "dataset")
    def view(self):
        output = self.ds[self.dataset].sel(wavelength=self.wavelength)
        opts = [hv.opts.Image(colorbar=True, height=600,
                              title=f"Wavelength: {self.wavelength}",
                              cmap=self.colorMap, tools=['hover'], framewise=True, logz=True)]
        return hv.Image(output).opts(opts)

    def widgets(self):
        return self.param
