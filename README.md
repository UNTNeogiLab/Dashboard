# Dashboard
Visualization, analsyis and aqusition dashboard

Originally the _holoviz_ branch of [2020SummerResearch](https://github.com/UNTNeogiLab/2020SummerResearch)
## Pypi installation 
*coming soon*
## Development installation

### Using Poetry (requires python)
https://python-poetry.org/  
to download another version of python install `curl https://pyenv.run | bash`  
`poetry install` (installs dependencies)  
### Old Python
Debian/Ubuntu Pip or poetry may be broken  
The best option is to install [pyenv](https://github.com/pyenv/pyenv) with its build dependencies
### Linux data aqusition/PyVcam  
You'll need [PyVcam](https://github.com/Photometrics/PyVCAM) and the accompanying SDK first
For internal use, run `poetry install -E pyvcam`with PVCAM (not the SDK) installed
### Windows
Data aqusition is unsupported on windows but fully possible  
Substitute thorpy with thorlabs-apt
### MAC
Data aqusition is unsupported on mac and impossible
### Scanimage
there's some placeholder scanimage code for now
### Updating dependencies

`poetry install`

## Running

`poetry run dashboard` (runs visualization script)
or
```shell
poetry shell
dashboard
```
## Development environment
You'll need to run `poetry shell` to get into the `poetry` virtual environment  
The better option is to use fish and [fish-poetry](https://github.com/ryoppippi/fish-poetry)
## Other documentation
[ensembles](doc/ensembles.md) Guide to writing an ensembles file  
[old](doc/old.md) Old documentation  
[pypy](doc/pypy.md) Guide to running this with pypy  
Various docstrings inside the code



