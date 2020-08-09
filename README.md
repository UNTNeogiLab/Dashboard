# 2020SummerResearch 
## Installing and Running (requires python and anaconda)  
`python setup.py`
##Jupyter Lab:
`jupyter lab`     
Export jupyter lab files  
`jupyter lab workspaces export > config/lab.json`  
##Server Deployment
  
###UNT servers  
`panel serve holoviz.ipynb --address 0.0.0.0` on compute node   
`ssh -L 5006:cX-X-X:5006 EUID@vis-01.acs.unt.edu` on local   
then open it on browser
###Generally)  
`panel serve holoviz.ipynb --address 0.0.0.0` on server  
`ssh -L 5006:localhost:5006 user@server` on local  
then open it on browser
