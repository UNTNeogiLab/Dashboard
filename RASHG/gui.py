import time
import math
import holoviews as hv
import xarray as xr
import numpy as np
import panel as pn
import param
from tqdm.notebook import tqdm
import os
import zarr

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
compressor = zarr.Blosc(cname="zstd", clevel=3, shuffle=2)


class gui(param.Parameterized):
    colorMap = param.ObjectSelector(default="fire", objects=hv.plotting.util.list_cmaps())
    cPol = param.Number(default=0, precedence=-1)
    pol_step = param.Number(default=2, bounds=(1, 2))  # TODO: figure out how this works
    pow_start = param.Integer(default=0)
    pow_stop = param.Integer(default=5)
    pow_step = param.Integer(default=5)
    wavstart = param.Integer(default=780)
    wavend = param.Integer(default=800)
    wavstep = param.Integer(default=2)
    wavwait = param.Number(default=5)  # value is in seconds
    filename = param.String(default="data/testfolder.zarr")
    title = param.String(default="Power/Wavelength dependent RASHG")
    institution = param.String(default="University of North Texas")
    sample = param.String(default="MoS2")
    GUIupdate = param.Boolean(default=True)
    button = pn.widgets.Button(name='Gather Data', button_type='primary')
    button2 = pn.widgets.Button(name='refresh', button_type='primary')
    live = param.Boolean(default=True, precedence=-1)
    refresh = 5  # refresh every 5 seconds #make it a parameter

    @param.depends('cPol')
    def progressBar(self):
        return pn.Column(self.pbar, self.wbar, self.obar)

    def __init__(self):
        super().__init__()
        self.pbar = tqdm(desc="power")  # power
        self.wbar = tqdm(desc="wavelength")  # wavelength
        self.obar = tqdm(desc="orientation")  # orientation
        self.polbar = tqdm(desc="Polarization")  # Polarization
        self.cache = np.random.rand(100, 100)
        self.button.disabled = True
        self.button2.disabled = True

    def initialize(self, instruments):
        self.instruments = instruments
        self.x1, self.x2, self.y1, self.y2 = self.instruments.x1, self.instruments.x2, self.instruments.y1, self.instruments.y2
        self.xbin, self.ybin = self.instruments.xbin, self.instruments.ybin
        self.init_vars()
        self.button.disabled = False
        self.button2.disabled = False
        self.button.on_click(self.gather_data)
        self.button2.on_click(self.live_view)
        params = ["pol_step", "pow_start", "pow_stop", "pow_step", "wavstart", "wavend", "wavstep", "wavwait",
                  "filename", "title", "institution", "sample"]
        for param in params:
            self.param[param].constant = True

    def init_vars(self):
        x = int((self.x2 - self.x1) / self.xbin)
        y = int((self.y2 - self.y1) / self.ybin)
        # populate metadata
        self.attrs = {
            "title": self.title,
            "institution": self.institution,
            "sample": self.sample,
            "source": self.instruments.type,
            "x_pxls": "pixels",
            "x": "micrometers",
            "y_pxls": "pixels",
            "y": "micrometers",
            "wavelength": "nanometer",
            "Polarization": "radians",
            "degrees": "degrees",
            "pwr": "milliwatts"
        }
        # data.date = str(datetime.date.today()) #out of date
        # create variables; in this case, the only dependent variable is 'shg',
        # which is the shg intensity along the specified dimensions
        self.xDim = hv.Dimension('x', unit="micrometers")
        self.yDim = hv.Dimension('y', unit="micrometers")
        # populate coordinate dimensions
        self.x = np.arange(x, dtype=np.uint16)
        self.x_mm = np.arange(x, dtype=np.uint16) * 0.05338
        self.y = np.arange(y, dtype=np.uint16)
        self.y_mm = np.arange(y, dtype=np.uint16) * 0.05338
        self.Orientation = np.arange(0, 2)
        self.Polarization = np.arange(0, 360, self.pol_step, dtype=np.uint16)
        self.Polarization_radians = np.arange(0, 360, self.pol_step, dtype=np.uint16) * math.pi / 180
        self.pwr = np.arange(self.pow_start, self.pow_stop, self.pow_step, dtype=np.uint16)
        self.wavelength = np.arange(self.wavstart, self.wavend, self.wavstep, dtype=np.uint16)
        self.cache = np.random.rand(x, y)
        self.zeros = np.zeros(
            (1, self.pwr.size, self.Orientation.size, self.Polarization.size, self.x.size, self.y.size))
        if os.path.isdir(self.filename):
            print("Zarr store exists, exiting")
            quit()
        else:
            os.mkdir(self.filename)

    def gather_data(self, event=None):
        self.button.disabled = True
        self.button2.disabled = True
        self.live = False
        pit = self.pwr  # power, polarization, wavelength, orientation respectively
        polit = self.Polarization_radians
        wit = self.wavelength
        self.wbar.reset(total=len(wit))
        oit = self.Orientation
        First = True
        print("Gathering Data, Get Out")
        if self.instruments.type == "RASHG":
            if not self.instruments.debug:
                time.sleep(120)
        for w in wit:
            coords = {
                "wavelength": (["wavelength"], [w]),
                "power": (["power"], self.pwr),
                "Orientation": (["Orientation"], self.Orientation),
                "Polarization": (["Polarization"], self.Polarization_radians),
                "degrees": (["Polarization"], self.Polarization),
                "x_pxls": (["x"], self.x),
                "x": (["x"], self.x_mm),
                "y_pxls": (["y"], self.y),
                "y": (["y"], self.y_mm),
            }
            dims = ["wavelength", "power", "Orientation", "Polarization", "x", "y"]
            self.instruments.wav_step()
            self.pbar.reset(total=len(pit))
            self.data = xr.Dataset(
                data_vars={"ds1": (dims, self.zeros, self.attrs)},
                coords=coords,
                attrs=self.attrs
            )
            for pw in pit:
                self.instruments.power_step()
                self.obar.reset(total=len(oit))
                for o in oit:
                    self.polbar.reset(total=len(polit))
                    for p in polit:
                        self.cache = self.instruments.get_frame(o, p)
                        mask = {"wavelength": w, "power": pw, "Polarization": p, "Orientation": o}
                        self.data["ds1"].loc[mask] = xr.DataArray(self.cache, dims=["x_pxls", "y_pxls"])
                        if self.GUIupdate and self.instruments.type == "RASHG":
                            self.cPol = p
                            self.polbar.update()
                    if self.GUIupdate:
                        self.cPol = o
                        self.obar.update()
                if self.GUIupdate:
                    self.pbar.update()
            if First:
                self.data.to_zarr(self.filename, encoding={"ds1": {"compressor": compressor}}, consolidated=True)
                First = False
            else:
                self.data.to_zarr(self.filename, append_dim="wavelength")
            if self.GUIupdate:
                self.wbar.update()
        print("Finished")
        self.cPol = self.cPol + 1
        self.data.close()
        quit()

    def live_view(self, event=None):
        self.button.disabled = True
        print("Initializing live view")
        self.cache = self.instruments.live()
        self.cPol = self.cPol + 1
        self.button.disabled = False

    @param.depends('cPol')
    def graph(self):
        output = self.cache
        self.zdim = hv.Dimension('Intensity', range=(output.min(), output.max()))
        opts = [hv.opts.Image(colorbar=True, cmap=self.colorMap, tools=['hover'], framewise=True, logz=True)]
        return hv.Image(output, vdims=self.zdim).opts(opts).redim(x=self.xDim, y=self.yDim)

    def widgets(self):
        return pn.Column(self.button, self.button2)

    def output(self):

        return pn.Row(self.progressBar, self.graph)
