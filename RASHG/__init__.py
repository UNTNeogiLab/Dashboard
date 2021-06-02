import os
from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
from . import instruments_base
instruments = {}
package_dir = str(Path(__file__).resolve().parent)
print(package_dir)
for (_, module_name, _) in iter_modules([package_dir]):
    print (__name__)
    module = import_module(f"{__name__}.{module_name}")
    #if issubclass()
try:
    from . import instruments_random as random
except ImportError:
    print("random import failed")
else:
    instruments["random"] = random
try:
    from . import instruments_RASHG as RASHG
except ImportError:
    print("RASHG import failed")
else:
    instruments["RASHG"] = RASHG
try:
    from . import instruments_scanimage
except ImportError:
    print("scanimage import failed")
else:
    instruments["scanimage"] = instruments_scanimage
from . import gui
