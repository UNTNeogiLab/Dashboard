"""
Visualizer for various data types
"""
import os
from pathlib import Path
from importlib import import_module
from .visualizer import Viewer

types = {}
for directory in os.scandir(str(Path(__file__).resolve().parent)):
    if directory.is_dir():
        for file in os.listdir(directory):
            if str(file).__contains__("visualizer_"):
                sname = file.replace(".py", "")
                try:
                    module = import_module(f"{__name__}.{directory.name}.{sname}")
                except ImportError:
                    print(f"{file} import failed")
                else:
                    types[module.DATA_TYPE] = module
