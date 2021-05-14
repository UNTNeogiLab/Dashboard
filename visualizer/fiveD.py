import pandas as pd
import param
import plotly.express as px
import xarray as xr
import holoviews as hv
import panel as pn

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
from .utils import *

'''
if not "visualizer" in os.listdir():
    from utils import *
else:
    from visualizer.utils import *
'''


class grapher(param.Parameterized):
    Orientation = param.Integer(default=0, bounds=(0, 1))
    wavelength = param.Selector(default=780)
    x0 = param.Number(default=0, precedence=-1)
    x1 = param.Number(default=1, precedence=-1)
    y0 = param.Number(default=0, precedence=-1)
    y1 = param.Number(default=1, precedence=-1)
    fitted = param.Boolean(default=False, precedence=-1)
    selected = param.Boolean(default=False, precedence=-1)
    colorMap = param.ObjectSelector(default="fire", objects=hv.plotting.util.list_cmaps())
    fitData = param.Boolean(default=False)
    fitAll = param.Boolean(default=False, precedence=-1)
    button = pn.widgets.Button(name='Fit All Blocks and save to file', button_type='primary')

    def Upgrade(self, event=None):
        self.fitBlocks()
        data = {"ds2": self.ds2, "ds3": self.ds3, "fitted": self.dsf,
                "covars": self.dsf_covar}
        ds = xr.Dataset(coords=self.coords, data_vars=data)
        filename = str(self.filename) + "f"  # We're sticking a f to the filename
        ds.to_netcdf(filename, engine="h5netcdf")

    def fitBlocks(self, event=None):
        if not (self.fitted):
            self.dsf_all = self.ds1.curvefit(["Polarization"], function, reduce_dims=["x", "y"])
            self.dsf = self.dsf_all.curvefit_coefficients
            self.dsf_covar = self.dsf_all.curvefit_covariance
            self.button.disabled = True
            self.fitted = True

    def _update_dataset(self):
        if extension(self.filename) == '5nc':  # innaccurate dimensions
            self.ds1 = hotfix(xr.open_dataarray(self.filename, chunks={'Orientation': 1, 'wavelength': 1},
                                                engine="h5netcdf"))  # chunked for heatmap selected
        elif extension(self.filename) == "nc":
            self.ds1 = xr.open_dataarray(self.filename, chunks={'Orientation': 1,
                                                                'wavelength': 1})  # chunked for heatmap selected
        if os.path.exists(str(self.filename) + "f"):
            ds = xr.open_dataset((str(self.filename) + "f"), chunks={'Orientation': 1,
                                                                     'wavelength': 20},engine="h5netcdf")
            self.ds2 = ds["ds2"]
            self.ds3 = ds["ds3"]
            self.dsf = ds["fitted"]
            self.averaged = True
            self.fitted = True
        else:
            self.ds2 = self.ds1.mean(dim='Polarization')  # chunked for navigation
            self.ds3 = self.ds1.mean(dim=['x', 'y'])  # chunked for heatmap all
            self.averaged = False
            self.fitted = False
        self.attrs = {**self.ds1.attrs, **self.ds1.attrs}

        self.logged = False
        self.button.disabled = self.fitted
        self.coords = self.ds1.coords
        dattrs = {"Polarization": "radians", "Orientation": "Idk", "wavelength": "nm", "x": "micrometers",
                  "y": "micrometers"}
        self.attrs['Polarization'] = "radians"
        self.attrs['wavelength'] = "nm"
        self.fname = fname(self.filename)
        self.x = hv.Dimension('x', unit=self.attrs['x'])
        self.y = hv.Dimension('y', unit=self.attrs['y'])
        self.param['wavelength'].objects = self.ds1.coords['wavelength'].values.tolist()

    def fit(self):
        if self.selected:
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength).sel(
                x=slice(self.x0, self.x1), y=slice(self.y0, self.y1))
        else:
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength)
        pf = output.curvefit(["Polarization"], function, reduce_dims=["x", "y"])
        curvefit_coefficients = pf.curvefit_coefficients #idk what to do with the covars
        return curvefit_coefficients.compute().values

    def __init__(self, filename, client_input):
        super().__init__()
        self.client = client_input
        self.filename = Path(filename)
        self.fileChoosing = False
        self._update_dataset()

    @param.depends('Orientation', 'wavelength', 'colorMap')
    def nav(self):
        self.selected = False
        polys = hv.Polygons([]).opts(fill_alpha=0.2, line_color='white')
        box_stream = hv.streams.BoxEdit(source=polys, num_objects=1)
        output = self.ds2.sel(Orientation=self.Orientation, wavelength=self.wavelength).persist()
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

    @param.depends('Orientation', 'wavelength', 'colorMap', 'x1', 'x0', 'y0', 'y1', 'selected')
    def title(self):
        if self.selected:
            return pn.pane.Markdown(
                f'''##{self.fname}: Orientation: {self.Orientation}, wavelength: {self.wavelength},x0: {self.x0},x1: {self.x1}, y0: {self.y0}, y1: {self.y1}''',
                width=1800)
        else:
            return pn.pane.Markdown(
                f'''##{self.fname}: Orientation: {self.Orientation},wavelength: {self.wavelength}, Average across all points''',
                width=1800)

    @param.depends('Orientation', 'wavelength', 'colorMap', 'x1', 'x0', 'y0', 'y1', 'selected')
    def heatMap(self):
        if not self.selected:
            output = self.ds3.sel(Orientation=self.Orientation).compute()
            title = f'''{self.fname}: Orientation: {self.Orientation}, Average across all points'''
        else:
            output = self.ds1.sel(Orientation=self.Orientation).sel(x=slice(self.x0, self.x1),
                                                                    y=slice(self.y0, self.y1)).mean(
                dim=['x', 'y']).compute()
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

    @param.depends('Orientation', 'wavelength', 'x1', 'x0', 'y0', 'y1', 'fitData', 'selected', 'fitted')
    def Polar(self):
        thetaVals = self.coords['Polarization'].values
        thetaRadians = self.coords['Polarization'].values
        overall = self.ds3.sel(Orientation=self.Orientation, wavelength=self.wavelength).persist()
        df = pd.DataFrame(np.vstack((overall, thetaVals, np.tile("Raw Data, over all points", 180))).T,
                          columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
        if self.selected:
            title = f'''{self.fname}: Orientation: {self.Orientation}, wavelength: {self.wavelength}, x0: {self.x0},x1: {self.x1}, y0: {self.y0}, y1: {self.y1}'''
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength).sel(
                x=slice(self.x0, self.x1), y=slice(self.y0, self.y1)).mean(dim=['x', 'y']).persist()
            df2 = pd.DataFrame(np.vstack((output, thetaVals, np.tile("Raw Data, over selected region", 180))).T,
                               columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
            df = df.append(df2)
        else:
            title = f'''{self.fname}: Orientation: {self.Orientation},wavelength: {self.wavelength}, Average across all points'''
        if self.fitData:
            if self.selected:
                fitted = functionN(thetaRadians, *self.fit())
                df2 = pd.DataFrame(np.vstack((fitted, thetaVals, np.tile("Fitted Data, to selected points", 180))).T,
                                   columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
                df = df.append(df2)
            elif not self.fitted:
                fitted = functionN(thetaRadians, *self.fit())
                df2 = pd.DataFrame(np.vstack((fitted, thetaVals, np.tile("Fitted Data, to all points", 180))).T,
                                   columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
                df = df.append(df2)
        if self.fitted:
            params = self.dsf.sel(Orientation=self.Orientation, wavelength=self.wavelength).values
            fitted = functionN(thetaRadians, *params)
            df2 = pd.DataFrame(np.vstack((fitted, thetaVals, np.tile("Fitted Data, to all points", 180))).T,
                               columns=['Intensity', 'Polarization', 'Data'], index=thetaVals)
            df = df.append(df2)
        df = df.astype({'Polarization': 'float', 'Intensity': "float", "Data": "string"})
        return px.scatter_polar(df, theta="Polarization", r='Intensity', color='Data', title=title, start_angle=0,
                                direction="counterclockwise",
                                range_r=(df['Intensity'].min() * 0.8, df['Intensity'].max() * 1.2))

    def dask(self):
        return self.client

    def xarray(self):
        return pn.panel(self.ds1, width=700)

    def view(self):
        return pn.Column(self.title, pn.Row(self.nav, self.heatMap), pn.Row(self.Polar, self.xarray))

    def sidebar(self):
        cores = sum(self.client.nthreads().values())
        estimate1 = convert(self.coords['x'].size * self.coords['y'].size * 0.006)
        estimate2 = convert(
            self.coords['wavelength'].size * self.coords['Orientation'].size * self.coords['x'].size *
            self.coords['y'].size * 0.006 / cores)
        return pn.pane.Markdown(f'''
        ##NOTES
        estimates are probably innacurate
        ###Fit data
        **estimated:** {estimate1} for all pixels

        Will fit data to point selections, dramatically increasing processing times when selecting new wavelengths, Orientations, or point selections
        ###Fit all
        **estimated:** {estimate2}

        will fit them upon selection, taking significant processing time, but will be much faster when changing wavelengths, orientations. Will not pay attention to point selections
        ###Using both
        Will fit both the whole dataset and selections, significant preformance considerations.
        ###Upgrading files
        Will only work on original .5nc files, not .5nce
        Most of the computation will be to Fit All
        ''')

    def widgets(self):
        self.button.on_click(self.Upgrade)
        return pn.Column(pn.Param(self.param, widgets={"wavelength": pn.widgets.DiscreteSlider}),
                         self.button, self.dask, self.sidebar)
