import os
import pandas as pd
import param
import plotly.express as px
from dask.distributed import Client
from scipy.optimize import curve_fit

import xarray as xr
import holoviews as hv
import panel as pn
import numpy as np
pn.extension('plotly')
hv.extension('bokeh', 'plotly')
from numba import njit
import posixpath
client = None
if not "scripted" in os.listdir():
    from utils import *
else:
    from scripted.utils import *
class grapher(param.Parameterized):
    fileChoosing = True
    Orientation = param.Integer(default=0, bounds=(0, 1))
    wavelength = param.Selector(default=780)
    x0 = param.Number(default=0)
    x1 = param.Number(default=1)
    y0 = param.Number(default=0)
    y1 = param.Number(default=1)
    fitted = param.Boolean(default=False)
    selected = param.Boolean(default=False)
    extensions = ["5nc", "5nce", "5ncu", "5nca"]
    files = getDir(extensions)
    if posixpath.exists("converted/truncated_1.5ncu"):
        default = Path("converted/truncated_1.5ncu")
    else:
        default = Path("converted/truncated_1.5nc")
    filename = param.ObjectSelector(default=default, objects=files)
    colorMap = param.ObjectSelector(default="fire", objects=hv.plotting.util.list_cmaps())
    fitData = param.Boolean(default=False)
    fitAll = param.Boolean(default=False)
    button = pn.widgets.Button(name='Fit All Blocks', button_type='primary')
    button2 = pn.widgets.Button(name='Upgrade file', button_type='primary')
    button3 = pn.widgets.Button(name='Update file', button_type='primary')
    def Compare(self):
        self.attrs = attrs = {"fitted": self.fitted, "averaged": self.averaged, "logged": self.logged}
        #Compares against immediate relative
    def Update(self, event=None):
        attrs = {"fitted": self.fitted, "averaged": True, "logged": self.logged}  # will force the average of everything
        if self.logged:
            print("Please don't try to upgrade a logged file")
            return
        if self.fitted:
            data = {"ds1": self.ds1, "ds2": self.ds2, "ds3": self.ds3, "fitted": self.dsf}
        else:
            data = {"ds1": self.ds1, "ds2": self.ds2, "ds3": self.ds3}
        ds = xr.Dataset(coords=self.coords, data_vars=data, attrs=attrs)
        filename = str(self.filename).split(".")[
                       0] + ".5nca"  # We're using the 5nca file extension for all files from now on
        ds.to_netcdf(filename, engine="h5netcdf", invalid_netcdf=True)
        #self.filename = filename  # load the new file one its written
        #Actually a bad idea, causes too many issues

    def Upgrade(self, event=None):
        if not (self.fitted):
            self.fitBlocks()
        self.Update()

    def fitBlocks(self, event=None):
        if not (self.fitted):
            O = self.coords['Orientation']
            w = self.coords['wavelength']
            C = ["delta", "A", "B", "theta", "C"]
            dims = len(C)
            xcoords = self.ds1.coords['Polarization'].values
            xdata = np.tile(xcoords, int(self.ds1.coords['x'].size * self.ds1.coords['y'].size))
            template = xr.DataArray(np.zeros((dims, O.size, w.size)), dims=["C", "Orientation", "wavelength"],
                                    coords=[C, O, w],
                                    name="fitted").chunk({"wavelength": 1, "Orientation": 1})

            @njit(cache=True)
            def fitx_blocks(data):
                ydata = data.values.flatten(order="C")
                pf, pcov = curve_fit(function, xdata, ydata, maxfev=1000000, xtol=1e-9, ftol=1e-9,
                                     p0=[2, 20, 5, 2, 400])
                return xr.DataArray(pf.reshape((dims, 1, 1)), dims=["C", "Orientation", "wavelength"],
                                    coords={"C": C, "Orientation": data.coords["Orientation"],
                                            "wavelength": data.coords["wavelength"]})

            self.dsf = xr.map_blocks(fitx_blocks, self.ds1, template=template).compute()
            self.button.disabled = True
            self.fitted = True

    @param.depends('filename', watch=True)
    def _update_dataset(self):
        extension = str(self.filename).split('.')[1]
        if extension == '5nc':

            self.ds = hotfix(xr.open_dataarray(self.filename, chunks={'Orientation': 1,
                                                                       'wavelength': 1}))  # chunked for heatmap selected
            self.ds1 = self.ds
            self.ds2 = self.ds1.mean(dim='Polarization')  # chunked for navigation
            self.ds3 = self.ds1.mean(dim=['x', 'y'])  # chunked for heatmap all
            self.attrs = {**self.ds.attrs, **self.ds1.attrs}
            self.averaged = False
            self.fitted = False
            self.logged = False
        elif extension == '5nca':
            self.ds = xr.open_dataset(self.filename, chunks={'Orientation': 1, 'wavelength': 1}, engine="h5netcdf")
            self.ds1 = self.ds['ds1']
            self.ds2 = self.ds['ds2'].persist()
            self.ds3 = self.ds['ds3'].persist()
            self.attrs = {**self.ds.attrs, **self.ds1.attrs}  # copy the attrs
            self.fitted = bool(self.attrs["fitted"])
            self.logged = bool(self.attrs["logged"])
            self.averaged = bool(self.attrs["averaged"])
            if self.attrs["fitted"]:
                self.dsf = self.ds['fitted'].persist()
        elif extension == '5nce':
            self.ds = hotfix(xr.open_dataset(self.filename, chunks={'Orientation': 1, 'wavelength': 1}))
            self.ds1 = self.ds['da1']
            self.ds2 = self.ds['da2'].persist()
            self.ds3 = self.ds['da3'].persist()
            self.attrs = {**self.ds.attrs, **self.ds1.attrs}
            self.averaged = True
            self.logged = True
            self.fitted = False
        elif extension == "5ncu":
            self.ds = xr.open_dataset(self.filename, chunks={'Orientation': 1, 'wavelength': 1})
            self.ds1 = self.ds['ds1']
            self.ds2 = self.ds['ds2'].persist()
            self.ds3 = self.ds['ds3'].persist()
            self.dsf = self.ds['fitted'].persist()
            self.attrs = {**self.ds.attrs, **self.ds1.attrs}
            self.averaged = True
            self.logged = False
            self.fitted = True
        else:
            print("ERROR: INVALID FILE")
        self.button2.disabled = self.logged or self.fitted
        self.button.disabled = self.fitted
        self.button3.disabled = self.logged
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
                x=slice(self.x0, self.x1), y=slice(self.y0, self.y1)).compute()
        else:
            output = self.ds1.sel(Orientation=self.Orientation, wavelength=self.wavelength).compute()
        xcoords = self.coords['Polarization'].values
        xdata = np.tile(xcoords, int(output.coords['x'].size * output.coords['y'].size))
        ydata = output.values.flatten(order="C")
        pf, pcov = curve_fit(function, xdata, ydata, maxfev=1000000, xtol=1e-9, ftol=1e-9, p0=[2, 20, 5, 2, 400],
                             bounds=[[0, 0, 0, 0, 0], [np.pi, np.inf, np.inf, np.pi, np.inf]])
        return pf

    def __init__(self, filename=False, client_input = None):
        super().__init__()
        global client
        if client is None:
            self.client = Client()
            client = self.client
        if not client_input is None:
            self.client = client_input
        else:
            self.client = client  # Has to execute so the class knows the client before the filename checks happen
        if not False == filename:
            self.filename = Path(filename)
            self.fileChoosing = False

        self._update_dataset()

    @param.depends('Orientation', 'wavelength', 'colorMap', 'filename')
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

    @param.depends('Orientation', 'wavelength', 'colorMap', 'filename', 'x1', 'x0', 'y0', 'y1', 'selected')
    def title(self):
        if self.selected:
            return pn.pane.Markdown(
                f'''##{self.fname}: Orientation: {self.Orientation}, wavelength: {self.wavelength},x0: {self.x0},x1: {self.x1}, y0: {self.y0}, y1: {self.y1}''',
                width=1800)
        else:
            return pn.pane.Markdown(
                f'''##{self.fname}: Orientation: {self.Orientation},wavelength: {self.wavelength}, Average across all points''',
                width=1800)

    @param.depends('Orientation', 'wavelength', 'colorMap', 'filename', 'x1', 'x0', 'y0', 'y1', 'selected')
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

    @param.depends('Orientation', 'wavelength', 'filename', 'x1', 'x0', 'y0', 'y1', 'fitData', 'selected', 'fitted')
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

    @param.depends('filename')
    def xarray(self):
        return pn.panel(self.ds, width=700)

    @param.depends('filename', watch=True)
    def view(self):
        return pn.Column(self.title, pn.Row(self.nav, self.heatMap), pn.Row(self.Polar, self.xarray))

    @param.depends('filename')
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

    @param.depends('filename', watch=True)
    def widgets(self):
        self.button.on_click(self.fitBlocks)
        self.button2.on_click(self.Upgrade)
        self.button3.on_click(self.Update)
        if self.fileChoosing:
            params = ['filename', 'colorMap', 'fitData', 'Orientation', 'wavelength']
        else:
            params = ['colorMap', 'fitData', 'Orientation', 'wavelength']
        return pn.Column(pn.Param(self.param, parameters=params, widgets={"wavelength": pn.widgets.DiscreteSlider}),
                         self.button, self.button2, self.button3, self.dask, self.sidebar, )
# graph = grapher()
# pn.Row(graph.widgets(),graph.view()).show()
