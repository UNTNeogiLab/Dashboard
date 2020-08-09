import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import hyperspy.api as hs
from PIL import Image
import xarray as xr
from renishawWiRE import WDFReader
import os


def read(filename, output = ""):
    # loadables = pd.read_csv("config/import_config.csv")

    name = filename.split('.', 1)[0]
    extension = filename.split('.', 1)[1]
    if output == "":
        output = name
    if (extension == "hspy"):
        data = hs.load(filename)
        order = []
        shape = list(data.data.shape)
        for i in range (0,5):
            index = shape.index(data.axes_manager[i].size)
            order.append(index)
            shape[index] = 0
        udims = ["Orientation", "wavelength", "x", "y", "Polarization"]
        Dims = [udims[order[i]] for i in range(0,5)]
        coords = {}
        attrs = {}
        for i, dimension in enumerate(Dims):
            coords[dimension] = range(0,data.axes_manager[i].size)
            attrs[dimension] = data.axes_manager[i].units
        data = xr.DataArray(data, dims=udims, coords=coords,name="5data", attrs = attrs)
        data.to_netcdf(output + ".5nc", engine="h5netcdf")
    elif (extension == "wdf"):
        reader = WDFReader(filename)
        reader.spectra = np.flip(reader.spectra, axis=2)
        attrs = {'x':str(reader.xpos_unit).replace('μ','u'),'y':str(reader.ypos_unit).replace('μ','u'),'wavelength':str(reader.xlist_unit)}
        w = range(0,reader.spectra.shape[2])
        x = range(0,reader.spectra.shape[0])
        y = range(0,reader.spectra.shape[1])
        data = xr.DataArray(reader.spectra,dims = ('x','y',"wavelength"), name = (reader.title),coords = {'x': x,'y': y,'wavelength': w},attrs = attrs)
        ds = data.to_dataset()
        ds.to_netcdf(output + ".3nc")
    else:
        print(filename+": "+extension)
        print("INVALID FILE TYPE")
    # Old Code for hyperspy
    '''if (extension == "jpg"):
        im = Image.open(filename)
        im.save("temp.png")
        data = hs.load("temp.png")
        os.remove("temp.png")
        return data
    if (extension == "txt"):
        raw = np.genfromtxt(filename, delimiter="\t", skip_header=1, dtype=float, names =("X","Y","Wavelength","Intensity"))
        #raw["X"] *= -1
        xCoords = np.unique(raw["X"]).__len__()
        yCoords = np.unique(raw["Y"]).__len__()
        wavesize = int(np.shape(raw)[0]/xCoords/yCoords)
        raw = np.sort(raw, axis=-1, order = ("Y","X","Wavelength"))
        raw = (raw["Intensity"].reshape((xCoords, yCoords, wavesize)))
        data = hs.signals.Signal1D(raw)
        data.metadata.General.title = filename.split('.',1)[0]
        data.axes_manager[0].name = 'x'
        data.axes_manager[1].name = 'y'
        data.axes_manager[2].name = 'wavelength'
        data.axes_manager[0].units = "um"
        data.axes_manager[1].units = "um"
        data.axes_manager[2].units = "1/cm"
        return data
    
    if (extension in loadables["extension"]):
        if (loadables["extension" == extension]["signal"] == ""):
            return hs.load(filename, signal_type=loadables["extension" == extension]["signal"])
        else:
            return hs.load(filename)
    if (extension == "wdf"):
        reader = WDFReader(filename)
        reader.spectra = np.flip(reader.spectra,axis=2)
        data = hs.signals.Signal1D(reader.spectra)
        data.metadata.General.title = reader.title
        data.metadata.General.authors = reader.username
        data.axes_manager[0].name = 'x'
        data.axes_manager[1].name = 'y'
        data.axes_manager[2].name = 'wavelength'
        data.axes_manager[0].units = str(reader.xpos_unit).replace('μ', 'u')
        data.axes_manager[1].units = str(reader.ypos_unit).replace('μ', 'u')
        data.axes_manager[2].units = str(reader.xlist_unit)
        return data
    '''

