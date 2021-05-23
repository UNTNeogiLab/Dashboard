import pandas as pd
import param
import plotly.express as px
import xarray as xr
import holoviews as hv
import panel as pn

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
from .utils import *


class grapher(param.Parameterized):
    Orientation = param.Integer(default=0, bounds=(0, 1))
    wavelength = param.Selector()
    power = param.Selector()
    x0 = param.Number(default=0, precedence=-1)
    x1 = param.Number(default=1, precedence=-1)
    y0 = param.Number(default=0, precedence=-1)
    y1 = param.Number(default=1, precedence=-1)
    selected = param.Boolean(default=False, precedence=-1)
    colorMap = param.ObjectSelector(default="fire", objects=hv.plotting.util.list_cmaps())
    button = pn.widgets.Button(name='Plot all Polar plots and save to file', button_type='primary')

    def _update_dataset(self):
        self.ds1 = xr.open_dataarray(self.filename, chunks={'Orientation': 1, 'wavelength': 14},
                                     engine="zarr")  # chunked for heatmap selected
        self.coords = self.ds1.coords
        if os.path.exists(str(self.filename) + "f"):
            ds = xr.open_dataset((str(self.filename) + "f"), chunks={'Orientation': 1, 'wavelength': 20},
                                 engine="netcdf4")
            self.ds2 = ds["ds2"]
            self.ds3 = ds["ds3"]
            self.dsf = ds["fitted"]
            self.dsf_covar = ds["covars"]
        else:

            self.ds2 = self.ds1.mean(dim='Polarization').compute()  # chunked for navigation
            self.ds3 = self.ds1.mean(dim=['x', 'y']).compute()  # chunked for heatmap all
            self.dsf_all = self.ds3.curvefit(["Polarization"], function,
                                             kwargs={"maxfev": 1000000, "xtol": 10 ** -9, "ftol": 10 ** -9}).compute()
            self.dsf = self.dsf_all.curvefit_coefficients
            self.dsf_covar = self.dsf_all.curvefit_covariance
            ds = xr.Dataset(coords=self.coords,
                            data_vars={"ds2": self.ds2, "ds3": self.ds3, "fitted": self.dsf_all.curvefit_coefficients,
                                       "covars": self.dsf_all.curvefit_covariance})
            filename = str(self.filename) + "f"  # We're sticking a f to the filename
            ds.to_netcdf(filename, engine="netcdf4")
        self.attrs = {**self.ds1.attrs, **self.ds1.attrs}
        self.fname = self.attrs["title"]
        self.x = hv.Dimension('x', unit=self.attrs['x'])
        self.y = hv.Dimension('y', unit=self.attrs['y'])
        self.param['wavelength'].objects = self.ds1.coords['wavelength'].values.tolist()
        self.param['power'].objects = self.ds1.coords['power'].values.tolist()
        self.wavelength = self.ds1.coords["wavelength"].min().values
        self.power = self.ds1.coords["power"].min().values

    def fit(self):
        if self.selected:
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength,power=self.power).sel(
                x=slice(self.x0, self.x1), y=slice(self.y0, self.y1))
        else:
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength,power=self.power)
        pf = output.curvefit(["Polarization"], function, reduce_dims=["x", "y"])
        curvefit_coefficients = pf.curvefit_coefficients  # idk what to do with the covars
        return curvefit_coefficients.values

    def __init__(self, filename, client_input):
        super().__init__()
        self.ignoreOverall = False
        self.client = client_input
        self.filename = Path(filename)
        self._update_dataset()

    @param.depends('Orientation', 'wavelength', 'colorMap', 'power')
    def nav(self):
        #self.selected = False
        polys = hv.Polygons([]).opts(fill_alpha=0.2, line_color='white')
        box_stream = hv.streams.BoxEdit(source=polys, num_objects=1)
        output = self.ds2.sel(Orientation=self.Orientation, wavelength=self.wavelength, power=self.power)
        box_stream.add_subscriber(self.tracker)
        self.zdim = hv.Dimension('Intensity', range=(output.values.min(), output.values.max()))
        opts = [hv.opts.Image(colorbar=True, height=600,
                              width=round(600 * self.ds1.coords['x'].size / self.ds1.coords['y'].size),
                              title=f"Wavelength: {self.wavelength}, Orientation: {self.Orientation}",
                              cmap=self.colorMap, tools=['hover'], framewise=True, logz=True)]
        return hv.Image(output, vdims=self.zdim).opts(opts).redim(x=self.x, y=self.y) * polys

    def tracker(self, data):
        if not data or not any(len(d) for d in data.values()):
            self.selected = False
        else:
            self.x0 = data['x0'][0]
            self.x1 = data['x1'][0]
            self.y0 = data['y0'][0]
            self.y1 = data['y1'][0]
            self.selected = True

    @param.depends('Orientation', 'wavelength', 'colorMap', 'x1', 'x0', 'y0', 'y1', 'selected', 'power')
    def title(self):
        if self.selected:
            return pn.pane.Markdown(
                f'''##{self.fname}: Orientation: {self.Orientation}, wavelength: {self.wavelength}, power: {self.power},x0: {self.x0},x1: {self.x1}, y0: {self.y0}, y1: {self.y1}''',
                width=1800)
        else:
            return pn.pane.Markdown(
                f'''##{self.fname}: Orientation: {self.Orientation},wavelength: {self.wavelength}, power: {self.power}, Average across all points''',
                width=1800)

    @param.depends('Orientation', 'wavelength', 'colorMap', 'x1', 'x0', 'y0', 'y1', 'selected', 'power')
    def heatMap(self):
        if not self.selected:
            output = self.ds3.sel(Orientation=self.Orientation, power=self.power)
            title = f'''{self.fname}: Orientation: {self.Orientation}, Average across all points'''
        else:
            output = self.ds1.sel(Orientation=self.Orientation, power=self.power).sel(x=slice(self.x0, self.x1),
                                                                                      y=slice(self.y0, self.y1)).mean(
                dim=['x', 'y'])
            title = f'''{self.fname}: Orientation: {self.Orientation}, x0: {self.x0},x1: {self.x1}, y0: {self.y0}, y1: {self.y1}'''
        self.PolarizationDim = hv.Dimension('Polarization', range=getRange('Polarization', self.coords),
                                            unit=self.attrs['Polarization'])
        self.wavelengthDim = hv.Dimension('wavelength', range=getRange('wavelength', self.coords),
                                          unit=self.attrs['wavelength'])
        line = hv.HLine(self.wavelength).opts(line_width=600 / self.coords['wavelength'].values.size, alpha=0.6)
        opts = [hv.opts.Image(cmap=self.colorMap, height=600, width=900, colorbar=True, title=title, tools=['hover'],
                              framewise=True, logz=True)]
        return hv.Image(output).opts(opts).redim(wavelength=self.wavelengthDim,
                                                 Polarization=self.PolarizationDim) * line

    @param.depends('Orientation', 'wavelength', 'x1', 'x0', 'y0', 'y1', 'selected', 'power')
    def Polar(self, dataset="Polarization"):
        thetaVals = self.coords[dataset].values
        thetaRadians = self.coords['Polarization'].values
        overall = self.ds3.sel(Orientation=self.Orientation, wavelength=self.wavelength, power=self.power)
        if self.selected:
            title = f'''{self.fname}: Orientation: {self.Orientation}, wavelength: {self.wavelength}, x0: {self.x0},x1: {self.x1}, y0: {self.y0}, y1: {self.y1}'''
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength).sel(
                x=slice(self.x0, self.x1), y=slice(self.y0, self.y1)).mean(dim=['x', 'y'])
            df = pd.DataFrame(np.vstack((output, thetaVals, np.tile("Raw Data, over selected region", 180))).T,
                              columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
            fitted = functionN(thetaRadians, *self.fit())
            df2 = pd.DataFrame(np.vstack((fitted, thetaVals, np.tile("Fitted Data, to selected points", 180))).T,
                               columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
            df = df.append(df2)
        else:
            title = f'''{self.fname}: Orientation: {self.Orientation},wavelength: {self.wavelength}, Average across all points'''
            df = pd.DataFrame(np.vstack((overall, thetaVals, np.tile("Raw Data, over all points", 180))).T,
                              columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
            params = self.dsf.sel(Orientation=self.Orientation, wavelength=self.wavelength, power=self.power).values
            fitted = functionN(thetaRadians, *params)
            df2 = pd.DataFrame(np.vstack((fitted, thetaVals, np.tile("Fitted Data, to all points", 180))).T,
                               columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
            df = df.append(df2)
        df = df.astype({'Polarization': 'float', 'Intensity': "float", "Data": "string"})
        return px.scatter_polar(df, theta="Polarization", r='Intensity', color='Data', title=title, start_angle=0,
                                direction="counterclockwise",
                                range_r=(df['Intensity'].min() * 0.8, df['Intensity'].max() * 1.2), )

    def PolarsToFile(self, event=None):
        start = time.time()
        ori_Wavelength, ori_Orientation = self.wavelength, self.Orientation
        self.param["Orientation"].precedence = -1
        self.param["wavelength"].precedence = -1
        wavelengths = self.ds1.coords['wavelength'].values.tolist()
        Orientations = self.ds1.coords['Orientation'].values.tolist()
        Folder = str(self.filename).replace(f".{extension(self.filename)}", '')
        if not os.path.isdir(Folder):
            os.mkdir(Folder)
        for Orientation in Orientations:
            selected = self.selected
            self.Orientation = Orientation
            self.selected = selected
            for wavelength in wavelengths:
                selected = self.selected
                self.wavelength = wavelength
                self.selected = selected  # prevent it resetting like it should
                if self.selected:
                    title = f"{Folder}/Polar_X{self.x0}:{self.x1}Y{self.y0}:{self.y1},O{Orientation}W{wavelength}.png"
                else:
                    title = f"{Folder}/Polar_O{Orientation}W{wavelength}.png"
                self.Polar("degrees").write_image(title)
        self.nav()
        self.param["Orientation"].precedence = 1
        self.param["wavelength"].precedence = 1
        self.wavelength, self.Orientation = ori_Wavelength, ori_Orientation
        end = time.time()
        print(end - start)

    def xarray(self):
        return pn.panel(self.ds1, width=700)

    def view(self):
        return pn.Column(self.title, pn.Row(self.nav, self.heatMap), pn.Row(self.Polar, self.xarray))

    def sidebar(self):
        return pn.pane.Markdown(f'''
            ##NOTES
            TBD probably will move to README
            ''')

    def widgets(self):
        self.button.on_click(self.PolarsToFile)
        if self.ds1.coords["power"].size > 1:
            widgets = {"wavelength": pn.widgets.DiscreteSlider, "power": pn.widgets.DiscreteSlider}
        else:
            widgets = {"wavelength": pn.widgets.DiscreteSlider}
            self.param["power"].precedence = -1  # effectively a 5d graph
        return pn.Column(pn.Param(self.param, widgets=widgets), self.button)
