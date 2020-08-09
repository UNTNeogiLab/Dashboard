# 5d spectral visualizer
Originally the _holoviz_ branch of [2020SummerResearch](https://github.com/UNTNeogiLab/2020SummerResearch)
## Installing and Running 
### Using setup.py (requires python and anaconda)
`python setup.py`
### Jupyter Lab:
`jupyter lab`     
Export jupyter lab files  
`jupyter lab workspaces export > config/lab.json`  
## Server Deployment
Requires environment with all files
### UNT servers  
1. `panel serve parameterized.ipynb --address 0.0.0.0` on compute node   
1. `ssh -L 5006:cX-X-X:5006 EUID@vis-01.acs.unt.edu` on local   
1. open localhost:5006 on local browser
### Generally 
1. `panel serve parameterized.ipynb --address 0.0.0.0` on server  
1. `ssh -L 5006:localhost:5006 user@server` on local  
1. open localhost:5006 on local browser
## Examples
![example](examples/Parameterized.png)


