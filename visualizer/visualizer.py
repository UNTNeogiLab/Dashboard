from dask.distributed import Client
import param
import panel as pn
from . import extensions, types
from .utils import *


class Viewer(param.Parameterized):
    files = getDir(extensions)
    filename = param.ObjectSelector(objects=files)

    def __init__(self, filename=None):
        super().__init__()
        self.client = Client()
        if not filename == None:
            self.filename = filename
        self.load()

    def reload_files(self):
        self.param["filename"].objects = getDir(self.extensions)

    @param.depends('filename', watch=True)
    def load(self):
        self.reload_files()  # temp solution
        self.grapher = self.extensions[extension(self.filename)](self.filename, self.client)

    @param.depends('filename')
    def widgets(self):
        return pn.Column(self.param, self.grapher.widgets(), self.dask)

    @param.depends('filename')
    def gView(self):
        return self.grapher.view()

    def dask(self):
        return self.client

    def view(self):
        return pn.Row(self.widgets, self.gview)

    def stop(self):
        pass
