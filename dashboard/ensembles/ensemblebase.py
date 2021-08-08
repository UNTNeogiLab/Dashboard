"""
Specifies base class
"""
from array import array
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Union, ClassVar

import numpy as np
import param


@dataclass
class Coordinate:
    name: str
    unit: str
    dimension: str
    values: np.array = np.array([])
    step_function: Union[Callable[[array], None], str] = field(default="none")

    def __call__(self, coords: array) -> None:
        if self.step_function != "none":
            self.step_function(coords)


@dataclass
class Coordinates:
    """Essentially a hybrid between a dictionary and a list"""
    coordinates: list[Coordinate]
    lookup_table: ClassVar[dict]

    def __post_init__(self):
        self._gen_lookup_table()

    def append(self, coordinate: Coordinate):
        self.coordinates.append(coordinate)
        self._gen_lookup_table()

    def _gen_lookup_table(self):
        self.lookup_table = {coordinate.name: i for i, coordinate in enumerate(self.coordinates)}

    def __iter__(self):
        yield from self.coordinates

    def __getitem__(self, indices: str) -> Coordinate:
        return self.coordinates[self.lookup_table[indices]]


class EnsembleBase(param.Parameterized):
    """
    Base class for all ensembles. Other instrument groups should inherit from this
    """
    initialized: bool = param.Boolean(default=False, precedence=-1)  # dummy variable to make code work
    type: str = "base"
    title: str = param.String(default="Power/Wavelength dependent RASHG")
    filename: str = param.String(default="data/testfolder.zarr")
    datasets: array = ["ds1"]
    live: bool = True
    gather: bool = True
    coords: Coordinates

    def initialize(self):
        """
        Initializes the instrument. Runs when you hit confirm
        :return:
        """
        pass

    def get_frame(self, coords):
        """
        Captures the frame
        :param coords: list of data in order of loop_coords
        :return: data
        """
        pass

    def widgets(self):
        """
        Widgets to pass to dashboard
        :return:
        """
        return self.param

    def start(self):
        """
        Any functions to run at start
        :return:
        """
        pass

    def stop(self):
        """
        Any functions to run at stop
        :return:
        """
        pass

    def graph(self, live=False):
        """
        returns a graph
        :param live: whether or not it is a live view
        :type live: bool
        :return:
        """
        return None
