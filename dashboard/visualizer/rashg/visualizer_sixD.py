"""
Visualizer for RASHG data
"""
import time
import os
from pathlib import Path
from datetime import timedelta
import numpy as np
from numba import vectorize, float64
import pandas as pd
import param
import plotly.express as px
import xarray as xr
import holoviews as hv
import panel as pn
from holoviews import streams
from ... import utils

pn.extension('plotly')
hv.extension('bokeh')

DATA_TYPE = "RASHG"


@vectorize([float64(float64, float64, float64, float64, float64, float64)])
def function(phi: float64, delta: float64, A: float64, B: float64, theta: float64, C: float64) -> float64:
    """
    Function to fit to, accelerated using numba
    :param phi:
    :type phi:
    :param delta:
    :type delta:
    :param A:
    :type A:
    :param B:
    :type B:
    :param theta:
    :type theta:
    :param C:
    :type C:
    :return:
    :rtype: float64

    """
    return (A * np.cos(3 * phi - 3 * delta) + B * np.cos(phi - 3 * delta + 2 * theta)) ** 2 + C


class Grapher(param.Parameterized):
    """
    Visualizer for RASHG data
    """
    zdim: hv.Dimension
    orientation = param.Integer(default=0, bounds=(0, 1))
    wavelength = param.Selector()
    power = param.Selector()
    x0 = param.Number(default=0, precedence=-1)
    x1 = param.Number(default=1, precedence=-1)
    y0 = param.Number(default=0, precedence=-1)
    y1 = param.Number(default=1, precedence=-1)
    selected = param.Boolean(default=False, precedence=-1)
    colorMap = param.ObjectSelector(default="fire", objects=hv.plotting.list_cmaps())
    button = pn.widgets.Button(name='Plot all Polar plots and save to file', button_type='primary')

    def __init__(self, filename, client_input):
        super().__init__()

        self.ignore_overall = False
        self.client = client_input
        self.filename = Path(filename)
        self._update_dataset()

    def _update_dataset(self):
        self.ds = xr.open_dataset(self.filename,
                                  chunks={'Orientation': 1, 'wavelength': 14, 'x': -1, 'y': -1, 'Polarization': -1},
                                  engine="zarr")  # chunked for heatmap selected
        try:
            fit_ver = self.ds.attrs["fit_version"]
        except:
            fit_ver = 0
        try:
            data_ver = self.ds.attrs["data_version"]
        except:
            data_ver = 0
        current_fit_version = 1
        current_data_version = 2
        if fit_ver < current_fit_version:
            time1 = time.time()
            self.ds = self.ds.drop_vars(["fitted", "covariance"], errors="ignore")
            self.ds["navigation"] = self.ds["ds1"].mean(dim='Polarization').compute()  # chunked for navigation
            self.ds["heatmap_all"] = self.ds["ds1"].mean(dim=['x', 'y']).compute()  # chunked for heatmap all
            self.ds = self.ds.merge(self.ds["heatmap_all"].curvefit(["Polarization"], function,
                                                                    param_names=["delta", "A", "B", "theta", "C"]
                                                                    , kwargs={"maxfev": 1000000, "xtol": 10 ** -9,
                                                                              "ftol": 10 ** -9}).compute())
            self.ds.attrs["fit_version"] = current_fit_version
            self.ds = self.ds.rename({"curvefit_coefficients": "fitted", "curvefit_covariance": "covariance"})
            self.ds.to_zarr(self.filename, mode="a", compute=True)
            time2 = time.time()
            print(f"finished in {str(timedelta(seconds=time2 - time1))}")
        if data_ver == 1:
            print("fixing dataset innaccuracies")
            self.ds.attrs["data_version"] = current_data_version
            self.ds.coords['Polarization'] = np.arange(0, 180, 1) / 90 * np.pi
            self.ds.coords['degrees'] = ("Polarization", np.arange(0, 360, 2))
            self.ds.to_zarr(self.filename, mode="a", compute=True)
        self.coords = self.ds["ds1"].coords
        self.attrs = {**self.ds["ds1"].attrs, **self.ds.attrs}
        self.fname = self.attrs["title"]
        self.x = hv.Dimension('x', unit=self.attrs['x'])
        self.y = hv.Dimension('y', unit=self.attrs['y'])
        self.param['wavelength'].objects = self.ds["ds1"].coords['wavelength'].values.tolist()
        self.param['power'].objects = self.ds["ds1"].coords['power'].values.tolist()
        self.wavelength = self.ds["ds1"].coords["wavelength"].min().values
        self.power = self.ds["ds1"].coords["power"].min().values
        self.polarization_dim = hv.Dimension('Polarization', range=utils.get_range('Polarization', self.coords),
                                             unit=self.attrs['Polarization'])
        self.wavelength_dim = hv.Dimension('wavelength', range=utils.get_range('wavelength', self.coords),
                                           unit=self.attrs['wavelength'])

    def fit(self):
        """
        Fits the currently selected data. Only used when selected, otherwise fitted at load time and saved to file
        :return: curve fit results
        """
        if self.selected:
            output = self.ds["ds1"].sel(Orientation=self.orientation, wavelength=self.wavelength, power=self.power).sel(
                x=slice(self.x0, self.x1), y=slice(self.y0, self.y1))
        else:
            output = self.ds["ds1"].sel(Orientation=self.orientation, wavelength=self.wavelength, power=self.power)
        curvefit = output.curvefit(["Polarization"], function, reduce_dims=["x", "y"],
                                   param_names=["delta", "A", "B", "theta", "C"])
        curvefit_coefficients = curvefit.curvefit_coefficients  # idk what to do with the covars
        return curvefit_coefficients.values

    @param.depends('orientation', 'wavelength', 'colorMap', 'power')
    def nav(self):
        """
        renders plot for navigation: XY for specified Orientation, wavelength, and power, averaged against polarization
        :return:
        """
        polys = self.poly_generate()  # copy existing selection
        box_stream = streams.BoxEdit(source=polys, num_objects=1)  # create BoxEdit stream
        box_stream.add_subscriber(self.tracker)  # adds the subscriber to the BoxEdit stream
        output = self.ds["navigation"].sel(Orientation=self.orientation, wavelength=self.wavelength, power=self.power)
        self.zdim = hv.Dimension('Intensity', range=(output.values.min(), output.values.max()))
        opts = [hv.opts.Image(colorbar=True, height=600,
                              width=round(600 * self.ds["ds1"].coords['x'].size / self.ds["ds1"].coords['y'].size),
                              title=f"Wavelength: {self.wavelength}, Orientation: {self.orientation}",
                              cmap=self.colorMap, tools=['hover'], framewise=True, logz=True)]
        return hv.Image(output, vdims=self.zdim).opts(opts).redim(x=self.x, y=self.y) * polys

    def poly_generate(self):
        """
        regenerates existing polygons if they exist. This allows selections to persist across wavelengths/orientations/powers
        :return:
        """
        if self.selected:
            avg_x = (self.x0 + self.x1) / 2
            avg_y = (self.y0 + self.y1) / 2
            width = self.x1 - self.x0
            height = self.y1 - self.y0
            return hv.Polygons([hv.Box(avg_x, avg_y, (width, height))]).opts(fill_alpha=0.2, line_color='white')
        return hv.Polygons([]).opts(fill_alpha=0.2, line_color='white')

    def tracker(self, data):
        """
        Takes data from BoxEdit stream and updates variables accordingly

        :param data: data, supplied by boxedit stream
        :return:
        """
        if not data or not any(len(d) for d in data.values()):
            self.selected = False
        else:
            self.x0 = round(data['x0'][0], 3)
            self.x1 = round(data['x1'][0], 3)
            self.y0 = round(data['y0'][0], 3)
            self.y1 = round(data['y1'][0], 3)
            self.selected = True

    @param.depends('orientation', 'wavelength', 'colorMap', 'x1', 'x0', 'y0', 'y1', 'selected', 'power')
    def title(self):
        """
        renders the title
        :return:
        """
        if self.selected:
            return pn.pane.Markdown(
                f'''##{self.fname}: Orientation: {self.orientation}, wavelength: {self.wavelength}, power: {self.power},
                x0: {self.x0},x1: {self.x1}, y0: {self.y0}, y1: {self.y1}''',
                width=1800)
        return pn.pane.Markdown(
            f'''##{self.fname}: Orientation: {self.orientation},wavelength: {self.wavelength}, power: {self.power}, 
                Average across all points''',
            width=1800)

    @param.depends('orientation', 'wavelength', 'colorMap', 'x1', 'x0', 'y0', 'y1', 'selected', 'power')
    def heat_map(self):
        """
        generates the heatmap Polarization x Wavelength for given orientation
        :return:
        """
        if not self.selected:
            output = self.ds["heatmap_all"].sel(Orientation=self.orientation, power=self.power)
            title = f'''{self.fname}: Orientation: {self.orientation}, Average across all points'''
        else:
            output = self.ds["ds1"].sel(Orientation=self.orientation, power=self.power).sel(
                x=slice(self.x0, self.x1),
                y=slice(self.y0,
                        self.y1)).mean(
                dim=['x', 'y'])
            title = f'''{self.fname}: Orientation: {self.orientation}, x0: {self.x0},x1: {self.x1}, y0: {self.y0}, y1: 
                    {self.y1}'''
        line = hv.HLine(self.wavelength).opts(line_width=600 / self.coords['wavelength'].values.size, alpha=0.6)
        opts = [
            hv.opts.Image(cmap=self.colorMap, height=600, width=900, colorbar=True, title=title, tools=['hover'],
                          framewise=True, logz=True)]
        return hv.Image(output).opts(opts).redim(wavelength=self.wavelength_dim,
                                                 Polarization=self.polarization_dim) * line

    @param.depends('orientation', 'wavelength', 'x1', 'x0', 'y0', 'y1', 'selected', 'power')
    def polar(self, dataset="Polarization"):
        """
        Generates the polar plot. If self.selected, then filter to x1,x0,y0,y1
        :param dataset: not entirely sure why this is here, but this supplies the coordinate for theta_values.
        :return:
        """
        theta_values = self.coords[dataset].values  # units, plotly, radians and degrees are a mess.
        theta_radians = self.coords['Polarization'].values
        if self.selected:
            output = self.ds["ds1"].sel(Orientation=self.orientation, wavelength=self.wavelength, power=self.power,
                                        x=slice(self.x0, self.x1), y=slice(self.y0, self.y1)).mean(dim=['x', 'y'])
            data_frame = pd.DataFrame(
                np.vstack((output, theta_values, np.tile("Raw Data, over selected region", 180))).T,
                columns=['Intensity', 'Polarization', 'Data'], index=theta_values)
            fitted = function(theta_radians, *self.fit())
            data_frame2 = pd.DataFrame(
                np.vstack((fitted, theta_values, np.tile("Fitted Data, to selected points", 180))).T,
                columns=['Intensity', 'Polarization', 'Data'], index=theta_values)
            data_frame = data_frame.append(data_frame2)
        else:
            overall = self.ds["heatmap_all"].sel(Orientation=self.orientation, wavelength=self.wavelength,
                                                 power=self.power)
            data_frame = pd.DataFrame(np.vstack((overall, theta_values, np.tile("Raw Data, over all points", 180))).T,
                                      columns=['Intensity', 'Polarization', 'Data'], index=theta_values)
            params = self.ds["fitted"].sel(Orientation=self.orientation, wavelength=self.wavelength,
                                           power=self.power).values
            fitted = function(theta_radians, *params)
            data_frame2 = pd.DataFrame(np.vstack((fitted, theta_values, np.tile("Fitted Data, to all points", 180))).T,
                                       columns=['Intensity', 'Polarization', 'Data'], index=theta_values)
            data_frame = data_frame.append(data_frame2)
        data_frame = data_frame.astype({'Polarization': 'float', 'Intensity': "float", "Data": "string"})
        return px.scatter_polar(data_frame, theta="Polarization", r='Intensity', color='Data',
                                start_angle=0,
                                direction="counterclockwise",
                                range_r=(data_frame['Intensity'].min() * 0.8, data_frame['Intensity'].max() * 1.2), )

    def polars_to_file(self, event=None):
        """
        Plots all the polars to a file
        :param event: required for the button
        :return:
        """
        start = time.time()
        ori_wavelength, ori_orientation, ori_power = self.wavelength, self.orientation, self.power
        self.param["Orientation"].precedence = -1
        self.param["wavelength"].precedence = -1
        self.param["power"].precedence = -1
        wavelengths = self.ds["ds1"].coords['wavelength'].values.tolist()
        orientations = self.ds["ds1"].coords['Orientation'].values.tolist()
        powers = self.ds["ds1"].coords['power'].values.tolist()
        folder = str(self.filename).replace(f".{utils.extension(self.filename)}", '')
        if not os.path.isdir(folder):
            os.mkdir(folder)
        for power in powers:
            self.power = power
            for orientation in orientations:
                selected = self.selected
                self.orientation = orientation
                self.selected = selected
                for wavelength in wavelengths:
                    selected = self.selected
                    self.wavelength = wavelength
                    self.selected = selected  # prevent it resetting like it should
                    if self.selected:
                        title = f"{folder}/Polar_X{self.x0}:{self.x1}Y{self.y0}:{self.y1},O{orientation}W{wavelength}" \
                                f"P{power}.png "
                    else:
                        title = f"{folder}/Polar_O{orientation}W{wavelength}.png"
                    self.polar("degrees").write_image(title)
        self.nav()
        self.param["Orientation"].precedence = 1
        self.param["wavelength"].precedence = 1
        self.param["power"].precedence = 1
        self.wavelength, self.orientation, self.power = ori_wavelength, ori_orientation, self.power
        end = time.time()
        print(end - start)

    def xarray(self) -> pn.panel:
        """
        Renders the xarray dataset as a panel
        :return:
        """
        return pn.panel(self.ds, width=700)

    def view(self) -> pn.Column:
        """
        Renders everything but the widgets as a view
        :return: view of graphs and title
        """
        return pn.Column(self.title, pn.Row(self.nav, self.heat_map), pn.Row(self.polar, self.xarray))

    def widgets(self) -> pn.Column:
        """
        Renders the widgets
        :return: the widgets
        """
        self.button.on_click(self.polars_to_file)
        if self.ds["ds1"].coords["power"].size > 1:
            widgets = {"wavelength": pn.widgets.DiscreteSlider, "power": pn.widgets.DiscreteSlider}
        else:
            widgets = {"wavelength": pn.widgets.DiscreteSlider}
            self.param["power"].precedence = -1  # effectively a 5d graph
        return pn.Column(pn.Param(self.param, widgets=widgets), self.button)
