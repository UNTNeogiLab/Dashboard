"""
Contains Viewer class
"""
from typing import Union

from dask.distributed import Client
import param
import panel as pn

from .. import utils


class Viewer(param.Parameterized):
    """
    Allows user to select file and loads appropriate visualizer for file
    """
    filename: str = param.ObjectSelector()

    def __init__(self, types, filename: str = None):
        self.types = types
        """

        :param filename: specify default filename, otherwise choose files
        :type filename: str
        :rtype: Viewer
        """
        super().__init__()
        self.client = Client()
        self.reload_files()
        if filename is None:
            self.filename = self.files[0]
        else:
            self.filename = filename
        self.load()

    def reload_files(self) -> None:
        """
        Checks for files with given extensions

        :rtype: None

        """
        self.file_dict = utils.scan_directory(self.types)
        if len(self.file_dict) == 0:
            raise Exception("must have at least one file")
        self.files = list(self.file_dict.keys())
        self.param["filename"].objects = self.files

    @param.depends('filename', watch=True)
    def load(self) -> None:
        """
        Loads currently selected file
        """
        self.reload_files()  # temp solution
        visualizer = self.file_dict[self.filename].grapher
        self.grapher = visualizer(self.filename, self.client)

    @param.depends('filename')
    def widgets(self) -> pn.Column:
        return pn.Column(self.param, self.grapher.widgets(), self.dask)

    @param.depends('filename')
    def graph(self) -> Union[pn.Row, pn.Column]:
        return self.grapher.view()

    def dask(self):
        return self.client

    def view(self):
        return pn.Row(self.widgets, self.graph)

    def stop(self):
        pass
