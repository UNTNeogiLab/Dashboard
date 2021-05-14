# 5d spectral visualizer

Originally the _holoviz_ branch of [2020SummerResearch](https://github.com/UNTNeogiLab/2020SummerResearch)

## Submodule

(expiremental)  
Using a git submodule to reference files from the https://github.com/UNTNeogiLab/RASHG project  
When cloning use --recurse-submodules or run  
`git submodule init`  
`git submodule update`

## Installing Dependencies

### Using Pipfile (requires python)
If running debian or ubuntu or other derivatives, read the next section first  
`pip install --user pipenv` (unpriviledged installation, use `pip install pipenv` or use package manager for global
install)  
(optionally use `module load python/3.7.4` for UNT server support)  
(to download another version of python install `curl https://pyenv.run | bash`)  
`pipenv sync` (installs dependencies)
### debian/ubuntu
Do not use the debian/ubuntu versions of pip and pipenv since they are out of date  (5/14/21)  
instead use https://github.com/pyenv/pyenv#installation from source  
also dependencies needed before pipenv sync  
`sudo apt install python3-aiohttp`  
Actually current Ubuntu has broken pip, leaving us with expiremental conda support again

### Updating dependencies

`pipenv sync`

## Running

`pipenv run python combined.py` (runs visualization script)

## Server Deployment

Currently out of date for pipenv  
Requires environment with all files

### UNT servers

1. `pipenv run python combined.py -server` on compute node
1. `ssh -L 5006:cX-X-X:5006 EUID@vis-01.acs.unt.edu` on local
1. open localhost:5006 on local browser

### Generally

1. `pipenv run python combined.py -server` on server
1. port forwarding depending on network configuration
1. open address:5006 on local browser

## Examples

![example](examples/Parameterized.png)

## Decapretated Documentation

### Using setup.py (requires python and anaconda)

`python setup.py` (older script, depends upon mamba/conda, slower, harder to maintain)

### Using bare pip

`pip install -r config/requirements.txt`

### Jupyter Lab:

Jupyter lab is decapretated in favor of python scripts

## Server Deployment

Requires environment with all files

### UNT servers

1. `panel serve combined.py --address 0.0.0.0` on compute node
1. `ssh -L 5006:cX-X-X:5006 EUID@vis-01.acs.unt.edu` on local
1. open localhost:5006 on local browser

### Generally

1. `panel serve parameterized.ipynb --address 0.0.0.0` on server
1. port forwarding depending on network configuration
1. open address:5006 on local browser
## Troubleshooting information
Hangs on creating Virtual environment  
`virtualenv pyenv --read-only-app-data`  
then activate it (`source pyenv/bin/activate`) and run  
`pipenv sync`  
followed by 
`pipenv run` *whatever*
