"""
Provides collections of ensembles for gathering data
"""
import os
from pathlib import Path
from importlib import import_module
from . import gui
instruments = {}
for directory in os.scandir(str(Path(__file__).resolve().parent)):
    if directory.is_dir():
        for file in os.listdir(directory):
            if str(file).__contains__("ensemble_"):
                if not str(file).__contains__("base"):
                    sname = file.replace(".py", "")
                    try:
                        module = import_module(f"{__name__}.{directory.name}.{sname}")
                    except Exception as ex:
                        print(f"{file} import failed. Exception {Exception}")
                    else:
                        instruments[module.name] = module
