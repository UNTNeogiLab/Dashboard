## Decapretated Documentation
## Examples

![example](../examples/Parameterized.png)
## Server Deployment

Currently out of date for pipenv  
Requires environment with all files

### UNT servers

1. `poetry run python combined.py -server` on compute node
1. `ssh -L 5006:cX-X-X:5006 EUID@vis-01.acs.unt.edu` on local
1. open localhost:5006 on local browser

### Generally

1. `poetry run python combined.py -server` on server
1. port forwarding depending on network configuration
1. open address:5006 on local browser
## File formats
.3nc: Raman data, unsuported  
.5nc: old RASHG data, netCDF4, uses fiveD.py  
.zarr: new RASHG, zarr, uses sixD.py
## Submodule
Using a git submodule to reference files from the https://github.com/UNTNeogiLab/RASHG project
RASHG is developed in parellel with the project    
When cloning use --recurse-submodules or run  
`git submodule init`  
`git submodule update`



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