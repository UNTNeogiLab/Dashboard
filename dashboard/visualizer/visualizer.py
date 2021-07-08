from dask.distributed import Client
import param
import panel as pn
from . import types
from . import utils


class Viewer(param.Parameterized):
    filename = param.ObjectSelector()

    def __init__(self, filename=None):
        super().__init__()
        self.client = Client()
        if not filename == None:
            self.filename = filename
        files = utils.getDir(types)
        if len(files) == 0:
            raise Exception("must have at least one file")
        self.param["filename"].default = list(files.keys())[0]
        self.param["filename"].objects = files.keys()
        self.load()

    def reload_files(self):
        self.param["filename"].objects = utils.getDir(types)

    @param.depends('filename', watch=True)
    def load(self):
        self.reload_files()  # temp solution
        visualizer = self.files[self.filename].grapher
        self.grapher = visualizer(self.filename, self.client)

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
