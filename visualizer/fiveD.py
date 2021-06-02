import pandas as pd
import param
import plotly.express as px
import xarray as xr
import holoviews as hv
import panel as pn
import zarr

pn.extension('plotly')
hv.extension('bokeh', 'plotly')
from .utils import *


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
    button = pn.widgets.Button(name='Plot all Polar plots and save to file', button_type='primary')
    button2 = pn.widgets.Button(name='Save file as Zarr', button_type='primary')
    def _update_dataset(self):
        self.ds1 = hotfix(xr.open_dataarray(self.filename, chunks={'Orientation': 1, 'wavelength': 14},
                                            engine="netcdf4"))  # chunked for heatmap selected
        self.coords = self.ds1.coords
        if os.path.exists(str(self.filename) + "f"):
            ds = xr.open_dataset((str(self.filename) + "f"), chunks={'Orientation': 1,
                                                                     'wavelength': 20}, engine="netcdf4")
            self.ds2 = ds["ds2"]
            self.ds3 = ds["ds3"]
            self.dsf = ds["fitted"]
            self.dsf_covar = ds["covars"]

            self.fitted = True
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
            self.fitted = True
        self.attrs = {**self.ds1.attrs, **self.ds1.attrs}
        dattrs = {"Polarization": "radians", "Orientation": "Idk", "wavelength": "nm", "x": "micrometers",
                  "y": "micrometers"}
        self.attrs['Polarization'] = "radians"
        self.attrs['wavelength'] = "nm"
        self.fname = fname(self.filename)
        self.attrs["title"] = self.fname
        self.ds1.attrs["title"] = self.fname
        self.x = hv.Dimension('x', unit=self.attrs['x'])
        self.y = hv.Dimension('y', unit=self.attrs['y'])
        self.param['wavelength'].objects = self.ds1.coords['wavelength'].values.tolist()
        #self.to_zarr()

    def to_zarr(self,event=None):
        #compressor = zarr.Blosc(cname="zstd", clevel=3, shuffle=2)
        filename = str(self.filename).replace(f".{extension(self.filename)}", '.zarr')
        print(filename)
        coords = self.ds1.coords
        ds = self.ds1
        ds_coords = ds.assign_coords(power=0).expand_dims("power")
        data = xr.Dataset(data_vars={"ds1":ds_coords },
                          attrs=self.attrs,
                          coords=coords)
        #data.to_zarr(filename, encoding={"ds1": {"compressor": compressor}}, consolidated=True)

        data.to_zarr(filename, consolidated=True)

    def fit(self):
        if self.selected:
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength).sel(
                x=slice(self.x0, self.x1), y=slice(self.y0, self.y1))
        else:
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength)
        pf = output.curvefit(["Polarization"], function, reduce_dims=["x", "y"])
        curvefit_coefficients = pf.curvefit_coefficients  # idk what to do with the covars
        return curvefit_coefficients.values

    def __init__(self, filename, client_input):
        super().__init__()
        self.client = client_input
        self.filename = Path(filename)
        self._update_dataset()

    @param.depends('Orientation', 'wavelength', 'colorMap')
    def nav(self):
        # self.selected = False
        polys = self.poly_generate()
        box_stream = hv.streams.BoxEdit(source=polys, num_objects=1)
        output = self.ds2.sel(Orientation=self.Orientation, wavelength=self.wavelength)
        box_stream.add_subscriber(self.tracker)
        self.zdim = hv.Dimension('Intensity', range=(output.values.min(), output.values.max()))
        opts = [hv.opts.Image(colorbar=True, height=600,
                              width=round(600 * self.ds1.coords['x'].size / self.ds1.coords['y'].size),
                              title=f"Wavelength: {self.wavelength}, Orientation: {self.Orientation}",
                              cmap=self.colorMap, tools=['hover'], framewise=True, logz=True)]
        return hv.Image(output, vdims=self.zdim).opts(opts).redim(x=self.x, y=self.y) * polys

    def poly_generate(self):
        if self.selected:
            avg_x = (self.x0 + self.x1) / 2
            avg_y = (self.y0 + self.y1) / 2
            width = self.x1 - self.x0
            height = self.y1 - self.y0
            return hv.Polygons([hv.Box(avg_x, avg_y, (width, height))]).opts(fill_alpha=0.2, line_color='white')
        else:
            return hv.Polygons([]).opts(fill_alpha=0.2, line_color='white')

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
            output = self.ds3.sel(Orientation=self.Orientation)
            title = f'''{self.fname}: Orientation: {self.Orientation}, Average across all points'''
        else:
            output = self.ds1.sel(Orientation=self.Orientation).sel(x=slice(self.x0, self.x1),
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

    @param.depends('Orientation', 'wavelength', 'x1', 'x0', 'y0', 'y1', 'selected', 'fitted')
    def Polar(self, dataset="Polarization"):
        thetaVals = self.coords[dataset].values
        thetaRadians = self.coords['Polarization'].values
        overall = self.ds3.sel(Orientation=self.Orientation, wavelength=self.wavelength)
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
            params = self.dsf.sel(Orientation=self.Orientation, wavelength=self.wavelength).values
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
        self.ignoreOverall = False
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
        #self.button.on_click(self.PolarsToFile)
        #self.button2.on_click(self.to_zarr())
        return pn.Column(pn.Param(self.param, widgets={"wavelength": pn.widgets.DiscreteSlider}), self.button,self.button2)
