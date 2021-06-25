import os
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
from . import gui
instruments = {}
for directory in os.scandir(str(Path(__file__).resolve().parent)) :
     if directory.is_dir():
         for file in os.listdir(directory):
                 if str(file).__contains__("instruments_"):
                     if not str(file).__contains__("base"):
                         sname = file.replace(".py","")
                         try:
                             module = import_module(f"{__name__}.{directory.name}.{sname}")
                         except:
                             print(f"{file} import failed")
                         else:
                             instruments[module.name] = module
from . import dashboard
